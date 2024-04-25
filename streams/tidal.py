import tidalapi
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
import uvicorn
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tidal = tidalapi.Session()

def save_session():
  """Save session data to a file"""
  with open("file.json", "w", encoding="utf-8") as f:
    json.dump({
      "token_type": tidal.token_type,
      "access_token": tidal.access_token,
      "refresh_token": tidal.refresh_token,
      "expiry_time": tidal.expiry_time
    }, f)


def load_session():
  """Load session data from a file"""
  with open("file.json", "r", encoding="utf-8") as f:
    data = json.load(f)
    tidal.load_oauth_session(data["token_type"], data["access_token"], data["refresh_token"], data["expiry_time"])
  return True


@app.get('/login')
def login():
  """Checks if the session is logged in, if not send forward the authentication link to automagically gather an authtoken from Tidal"""
  if tidal.check_login():
    save_session()
    return "Session already logged in"
  else:
    if load_session():
      save_session()
      return "Session loaded"
    else:
      login, future = tidal.login_oauth()
      return login.verification_uri_complete


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
