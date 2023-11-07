import os
import json
import time
import secrets

from typing import Union, Dict
from typing_extensions import Literal
from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, HTTPException, status, APIRouter, Request
from fastapi.responses import Response, RedirectResponse, FileResponse
from fastapi.security import APIKeyCookie, APIKeyQuery, OAuth2PasswordRequestForm
from fastapi.openapi.models import APIKey
from fastapi.templating import Jinja2Templates
from starlette.templating import _TemplateResponse as TemplateResponse
from argon2 import PasswordHasher, Parameters as Argon2Params, Type as Argon2Type
from hmac import compare_digest

# pylint: disable=no-name-in-module
from pydantic import BaseModel

# The below takes ~200ms to hash on a RPi3 CM and is currently (fall 2023) recommended
# as a 'safer' default by OWASP. These will only be used when instantiating a new hash;
# existing hashes encode these parameters within the hash.
argon2_params = Argon2Params(
  time_cost=2,
  memory_cost=19456,
  parallelism=1,
  type=Argon2Type.ID,
  hash_len=32,
  salt_len=16,
  version=19
)
pwd_context = PasswordHasher.from_parameters(argon2_params)

prefix = '/auth'

router = APIRouter(prefix=prefix)

# the template dir ought to be alongside this file
template_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "templates")
templates = Jinja2Templates(directory=template_dir)

USER_CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.config', 'amplipi')

USERS_FILE = os.path.join(USER_CONFIG_DIR, 'users.json')

class UserData(BaseModel):
  type: Literal["user", "api"]
  access_key: Union[str, None]
  access_key_updated: Union[datetime, None]
  password_hash: Union[str, None]

def _get_users() -> dict:
  """ Returns the users file contents """
  users : Dict[str, Dict] = {}
  # Load fields from users file (if it exists), falling back to no users.
  try:
    with open(USERS_FILE, encoding='utf-8') as users_file:
      potential_users = json.load(users_file)
      users.update(potential_users)
  except FileNotFoundError as e:
    print(f'Error loading users file: {e}')
    print('Creating a users file from defaults.')
    os.makedirs(USER_CONFIG_DIR, mode=0o700, exist_ok=True)
    with open(USERS_FILE, encoding='utf-8', mode='w') as repair_file:
      json.dump(users, repair_file)
  except json.JSONDecodeError as e:
    print(f'Error loading users file as JSON: {e}')
    print('Moving the old one to a backup and creating a users file from defaults.')
    os.rename(USERS_FILE, f"{USERS_FILE}.{time.time()}")
    with open(USERS_FILE, encoding='utf-8', mode='w') as repair_file:
      json.dump(users, repair_file)
  except Exception as e:
    print(f'Error loading identity file: {e}')
    raise e
  return users

def _set_users(users_update: Dict[str, UserData]) -> None:
  users = _get_users()
  users.update(users_update)
  with open(USERS_FILE, encoding='utf-8', mode='w') as users_file:
    json.dump(users, users_file)

def _get_password_hash(user) -> str:
  users = _get_users()
  return users[user]['password_hash']

def _verify_password(plain_password, hashed_password) -> bool:
  return pwd_context.verify(hashed_password, plain_password)

def _hash_password(password) -> str:
  return pwd_context.hash(password)

def _get_access_key(user) -> str:
  users = _get_users()
  return users[user]["access_key"]

def set_password_hash(user, password) -> None:
  """ Sets a password for a given user. """
  users = _get_users()
  if user not in users.keys():
    users[user] = {}
  users[user]["password_hash"] = _hash_password(password)
  users[user]["type"] = "user"
  _set_users(users)

def unset_password_hash(user) -> None:
  """ Removes a password for a given user. """
  users = _get_users()
  del users[user]["password_hash"]
  _set_users(users)

def user_exists(username: str) -> bool:
  """ Utility function for determining if a user exists """
  users = _get_users()
  return username in users.keys()

def user_password_set(username: str) -> bool:
  """ Utility function for determining if a user has a password set. """
  users = _get_users()

  # No user exists
  if not user_exists(username):
    return False

  # User is an API consumer, not a human
  if users[username]['type'] != "user":
    return False

  # Password is not set
  if 'password_hash' not in users[username].keys():
    return False

  return True


def _authenticate_user_with_password(username: str, password: str) -> bool:
  if not user_password_set(username):
    return False
  try:
    return _verify_password(password, _get_password_hash(username))
  except Exception as e:
    print(f"exception in _verify_password(): {e}")
    return False

def create_access_key(user: str) -> str:
  """ Creates an access key. Also creates the user if it does not already exist. """
  users = _get_users()
  access_key = secrets.token_hex()
  if user not in users.keys():
    users.update({user: {}})
  users[user].update({
    "access_key": access_key,
    "access_key_updated": datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
  })
  _set_users(users)
  return access_key

def _check_access_key(key: APIKey) -> bool:
  for username in _get_users().keys():
    if compare_digest(_get_access_key(username), str(key)):
      return True
  return False

def _next_url(request: Request) -> str:
  """ Gets the next URL after a login, given a Request. """
  if "next_url" in request.query_params.keys() and request.query_params['next_url']:
    return request.query_params['next_url']
  if request.url.path == "/auth/login":
    return "/"
  return request.url.path

# The following class & function need to be added to the `app` using `.add_exception_handler`.
# See: https://github.com/tiangolo/fastapi/issues/1667
class NotAuthenticatedException(Exception):
  pass

async def not_authenticated_exception_handler(request: Request, exc: NotAuthenticatedException) -> TemplateResponse:
  """ Render the login page; used as an exception handler. Code that lands here will
      appear to come from the original API endpoint; thus we set `next_url` to the current
      request path if the next_url query param is not present.
  """
  return templates.TemplateResponse("login.html", {"request": request, "next_url": _next_url(request)}, status_code=401)

def cookie_auth(session: APIKey = Depends(APIKeyCookie(name="amplipi-session", auto_error=False))) -> bool:
  if not session:
    return False
  return _check_access_key(session)

def query_param_auth(api_key : APIKey = Depends(APIKeyQuery(name="api-key", auto_error=False))) -> bool:
  if not api_key:
    return False
  return _check_access_key(api_key)

async def CookieOrParamAPIKey(cookie_result = Depends(cookie_auth), query_param = Depends(query_param_auth)) -> bool:
  if not (cookie_result or query_param):
    raise NotAuthenticatedException
  return True

@router.get("/login")
def login_page(request: Request) -> TemplateResponse:
  """ Render the login page. """
  return templates.TemplateResponse("login.html", {"request": request, "next_url": _next_url(request)})

@router.post("/login")
def login(request: Request, next_url: str = "/", form_data: OAuth2PasswordRequestForm = Depends()):
  print(f"request.query_params: {request.query_params}")
  print(f"next_url: {next_url}")
  if not form_data:
    return templates.TemplateResponse("login.html", {"request": request, "next_url": _next_url(request)})
  authed = _authenticate_user_with_password(form_data.username, form_data.password)
  if not authed:
    raise NotAuthenticatedException
  access_token = _get_access_key(form_data.username)
  response = RedirectResponse(url=next_url, status_code=status.HTTP_303_SEE_OTHER)
  response.set_cookie(key="amplipi-session", value=access_token)
  return response
