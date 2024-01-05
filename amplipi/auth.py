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

# This is duplicated from amplipi.config intentionally. This file is pulled in
# via the updater and we'd like to avoid as many external Amplipi dependencies in the updater
# as possible.
USER_CONFIG_DIR = os.path.join(os.path.expanduser('~'), '.config', 'amplipi')

USERS_FILE = os.path.join(USER_CONFIG_DIR, 'users.json')


class UserData(BaseModel):
  type: Literal["user", "api"]
  access_key: Union[str, None]
  access_key_updated: Union[datetime, None]
  password_hash: Union[str, None]


def _get_users() -> dict:
  """ Returns the users file contents """
  users: Dict[str, UserData] = {}
  # Load fields from users file (if it exists), falling back to no users.
  # TODO: We should guard around edge cases more. If a user is able to trick any
  # component into messing with this file, authentication gets removed. however, we
  # don't have the resources for being more sophisticated about this at the moment;
  # this will have to do for now. It may also obviate itself should we move to a real DB.
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
  """ Sets the user file. This takes a partial or full representation of the
      user data and .update()'s it; to note, this means it will not delete
      keys, only add or modify existing keys.
  """
  users = _get_users()
  users.update(users_update)
  with open(USERS_FILE, encoding='utf-8', mode='w') as users_file:
    json.dump(users, users_file)


def _get_password_hash(user: str) -> str:
  """ Get a user password hash. This does not handle KeyError exceptions;
      this should explicitly be handled by the caller.
  """
  users = _get_users()
  return users[user]['password_hash']


def _verify_password(plain_password: str, hashed_password: str) -> bool:
  """ Verify a plaintext password using constant-time hashing. """
  return pwd_context.verify(hashed_password, plain_password)


def _hash_password(password: str) -> str:
  """ Given a plaintext password, return a hashed password. """
  return pwd_context.hash(password)


def _get_access_key(user: str) -> str:
  """ Get a username's access key. This does not handle KeyError exceptions;
      this should explicitly be handled by the caller
  """
  users = _get_users()
  return users[user]["access_key"]


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


def set_password_hash(user: str, password: str) -> None:
  """ Sets a password for a given user. (Re/)sets the session/access key for a user.
      If the user does not exist, it is created.
  """
  users = _get_users()
  if user not in users.keys():
    users[user] = {}
  users[user]["password_hash"] = _hash_password(password)
  users[user]["type"] = "user"
  _set_users(users)
  create_access_key(user)


def unset_password_hash(user) -> None:
  """ Removes a password for a given user. """
  users = _get_users()
  try:
    del users[user]["password_hash"]
  except KeyError:  # user doesn't exist, or has no "password_hash"
    pass
  _set_users(users)


def user_exists(username: str) -> bool:
  """ Utility function for determining if a user exists """
  users = _get_users()
  return username in users.keys()


def _user_password_set(username: str) -> bool:
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


def user_access_key_set(username: str) -> bool:
  """ Utility function for determing if a user has a session key set """
  users = _get_users()

  # No user exists
  if not user_exists(username):
    return False

  # Password is not set
  if 'access_key' not in users[username].keys():
    return False

  return True


def get_access_key(username: str) -> str:
  """ Given a username, return its access key. """
  assert user_access_key_set(username)
  users = _get_users()
  return users[username]["access_key"]


def _authenticate_user_with_password(username: str, password: str) -> bool:
  """ Given a username and a plaintext password, authenticate the user. """
  if not _user_password_set(username):
    return False
  try:
    return _verify_password(password, _get_password_hash(username))
  except Exception as e:
    print(f"exception in _verify_password(): {e}")
    return False


def _check_access_key(key: APIKey) -> Union[bool, str]:
  """ Check a user's access key using constant-time comparison. """
  for username in _get_users().keys():
    if 'access_key' in _get_users()[username]:
      if compare_digest(_get_access_key(username), str(key)):
        return username
  return False


def no_user_passwords_set() -> bool:
  """ Determines if there are no user passwords set. """
  for user in _get_users():
    if _user_password_set(user):
      return False
  return True


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
  """ An exception used for handling unauthenticated requests """
  pass


async def not_authenticated_exception_handler(request: Request, exc: NotAuthenticatedException) -> TemplateResponse:
  """ Render the login page; used as an exception handler. Code that lands here will
      appear to come from the original API endpoint; thus we set `next_url` to the current
      request path if the next_url query param is not present.
  """
  return templates.TemplateResponse("login.html", {"request": request, "next_url": _next_url(request)}, status_code=401)


def cookie_auth(session: APIKey = Depends(APIKeyCookie(name="amplipi-session", auto_error=False))) -> Union[bool, str]:
  """ Attempt cookie authentication, using the key stored in `amplipi-session`. """
  if not session:
    return False
  return _check_access_key(session)


def query_param_auth(api_key: APIKey = Depends(APIKeyQuery(name="api-key", auto_error=False))) -> Union[bool, str]:
  """ Attempt query parameter authentication, using the key provided with the parameter `api-key` """
  if not api_key:
    return False
  return _check_access_key(api_key)


async def CookieOrParamAPIKey(cookie_result=Depends(cookie_auth), query_param=Depends(query_param_auth), no_passwords=Depends(no_user_passwords_set)) -> bool:
  """ Authentication scheme. Any one of cookie auth, query param auth, or having no user passwords
      set will pass this authentication.
  """
  if not (no_passwords or cookie_result or query_param):
    raise NotAuthenticatedException
  return True


@router.get("/login", response_class=Response, tags=["auth"])
def login_page(request: Request) -> TemplateResponse:
  """ Render the login page. """
  return templates.TemplateResponse("login.html", {"request": request, "next_url": _next_url(request)})


@router.post("/login", response_class=Response, tags=["auth"])
def login(request: Request, next_url: str = "/", form_data: OAuth2PasswordRequestForm = Depends()):
  """ Handle a POST to the login page. """
  if not form_data:
    return templates.TemplateResponse("login.html", {"request": request, "next_url": _next_url(request)})
  authed = _authenticate_user_with_password(form_data.username, form_data.password)
  if not authed:
    raise NotAuthenticatedException
  access_token = _get_access_key(form_data.username)
  response = RedirectResponse(url=next_url, status_code=status.HTTP_303_SEE_OTHER)
  response.set_cookie(key="amplipi-session", value=access_token)
  return response
