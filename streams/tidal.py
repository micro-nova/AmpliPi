import tidalapi # Note pydantic objects below before importing anything more specific from this package
from tidalapi.page import PageItem, PageLink

# pylint: disable=no-name-in-module
from pydantic import BaseModel

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from typing import Optional, Union, Dict
import uvicorn
import json
from enum import Enum

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tidal = tidalapi.Session()

# Pydantic Objects to reflect a pared down version of tidalapi objects, but in a way that you can send back to the frontend

class Filtration_Query(Enum):
  ALBUM = "album"
  ALBUMS = "albums"

  MIX = "mix"
  MIXES = "mixes"

  PLAYLIST = "playlist"
  PLAYLISTS = "playlists"

  TRACK = "track"
  TRACKS = "tracks"

  PAGE = "page"
  PAGES = "pages"

class Playlist(BaseModel):
  type = "Playlist"
  name: str
  id: str
  art: Optional[str]

class Mix(BaseModel):
  type = "Mix"
  name: str
  id: str
  art: Optional[str]

class Page(BaseModel):
  type = "Page"
  name: str
  path: Optional[str]
  art: Optional[str]

class Track(BaseModel):
  type = "Track"
  name: str
  id: str
  art: Optional[str]
  duration: Optional[str]

class Album(BaseModel):
  type = "Album"
  name: str
  id: str
  artists: Optional[Union[str, list]]
  art: Optional[str]
  tracks: Optional[Dict[str, Track]]


class HomeScreen(BaseModel):
  title: str
  items: dict[str, Page, Album, Track, Mix, Playlist] #Oops, all Pages!
#(everything is getting parsed into type Page so I need a TODO to fix that)


def save_session(): #TODO: Make file saving more secure, I don't want unencrypted tokens sitting around
  """Save session data to a file"""
  with open("file.json", "w", encoding="utf-8") as f:
    json.dump({
      "token_type": tidal.token_type,
      "access_token": tidal.access_token,
      "refresh_token": tidal.refresh_token,
    }, f)


def load_session() -> bool:
  """Load session data from a file"""
  try:
    with open("file.json", "r", encoding="utf-8") as f: #TODO: Give session files actual names and locations
      data = json.load(f)
      tidal.load_oauth_session(data["token_type"], data["access_token"], data["refresh_token"])
    return True
  except Exception:
    return False

def check_session() -> bool:
  """Checks if the session is logged in, or if it's loadable from a file, and returns a bool"""
  if not tidal.check_login():
    return load_session()
  return True

def trackify_album(album_id: str) -> dict[Track]:
  album = tidal.album(album_id)
  tracks = {}
  for track in album.tracks():
    tracks[track.name] = Track(name=track.name, id=track.id, artist=track.artist, art=track.album.cover, duration=track.duration)
  return tracks


@app.get('/login/')
def login():
  """Checks if the session is logged in, if not send forward the authentication link to automagically gather an authtoken from Tidal"""
  if tidal.check_login():
    save_session()
    return "Session already logged in"

  if load_session():
    save_session()
    return "Session loaded"
  else:
    login, future = tidal.login_oauth()
    return login.verification_uri_complete


@app.get('/pages/home/')
def get_homepage() -> Union[str, Dict[str, HomeScreen]]:
  """Gets all data from the homepage"""
  if not check_session():
    return ("You must log in before you use this function, go to GET /login/ to do so.")

  home = tidal.home()
  home.categories.extend(tidal.explore().categories)
  categories = {}
  for category in home.categories:
    items = {}
    for item in category.items:
      if isinstance(item, tidalapi.Album):
        items[item.name] = Album(name=item.name, id=item.id, artists=item.artists, art=item.cover)

      elif isinstance(item, tidalapi.Mix):
        items[item.title] = Mix(name=item.title, id=item.id, art=item.images.medium)

      elif isinstance(item, tidalapi.Playlist):
        items[item.name] = Playlist(name=item.name, id=item.id, art=item.square_picture)

      elif isinstance(item, tidalapi.Track):
        items[item.name] = Track(name=item.name, id=item.id, artist=item.artist, art=item.album.cover, duration=item.duration)

      elif isinstance(item, PageLink):
        items[item.title] = Page(name=item.title, path=item.api_path, art=item.image_id)

    categories[category.title] = HomeScreen(title=category.title, items=items)

  return categories


@app.get('/pages/home/{filter_query}/')
def get_filtered_homepage(filter_query: Filtration_Query) -> Union[str, Dict[str, HomeScreen]]:
  """Gets all data from the homepage, filtered to a single data type"""
  if not check_session():
    return ("You must log in before you use this function, go to GET /login/ to do so.")

  filter_query = filter_query.value.lower()

  home = tidal.home()
  home.categories.extend(tidal.explore().categories)
  categories = {}
  for category in home.categories:
    items = {}
    for item in category.items:
      if isinstance(item, tidalapi.Album) and filter_query in ("album", "albums"):
        items[item.name] = Album(name=item.name, id=item.id, artists=item.artists, art=item.cover)

      elif isinstance(item, tidalapi.Mix) and filter_query in ("mix", "mixes"):
        items[item.title] = Mix(name=item.title, id=item.id, art=item.images.medium)

      elif isinstance(item, tidalapi.Playlist) and filter_query in ("playlist", "playlists"):
        items[item.name] = Playlist(name=item.name, id=item.id, art=item.square_picture)

      elif isinstance(item, tidalapi.Track) and filter_query in ("track", "tracks"):
        items[item.name] = Track(name=item.name, id=item.id, artist=item.artist, art=item.album.cover, duration=item.duration)

      elif isinstance(item, PageLink) and filter_query in ("page", "pages"):
        items[item.title] = Page(name=item.title, path=item.api_path, art=item.image_id)

    categories[category.title] = HomeScreen(title=category.title, items=items)

  return categories


@app.get('/pages/album/{album_id}/')
def get_album_tracks(album_id: str) -> Dict[str, Track]:
  if not check_session():
    return ("You must log in before you use this function, go to GET /login/ to do so.")
  return trackify_album(album_id)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
