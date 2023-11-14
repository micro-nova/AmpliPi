""" Test the authentication system """

from typing import Dict, List, Optional

# json utils
import json
from http import HTTPStatus

# temporary directory for each test config
import tempfile
import os
from copy import deepcopy # copy test config

from pathlib import Path

import time

import pytest
from fastapi.testclient import TestClient

# testing context
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from amplipi import auth, ctrl

import netifaces as ni

# pylint: disable=redefined-outer-name
# pylint: disable=invalid-name
# pylint: disable=too-many-locals

TEST_CONFIG = ctrl.Api.DEFAULT_CONFIG

NO_USERS_CONFIG = {}

# the password_hash below is for the string "test"
TEST_ADMIN_USER_CONFIG = {
  "admin": {
    "password_hash": "$argon2id$v=19$m=19456,t=2,p=1$FMgKBBEIZ+P6yoNCnSWsFQ$p4viI4pfxi8dNEpCxT1aFnQos8/L7j629D+Y73MUZBk",
    "type": "user",
    "access_key": "8b184dfe9c0c66b556ab050ffe4bc1a1ff6c1b10eba2c98c8e7e58bfb12b8d17",
    "access_key_updated": "2023-11-07 21:38:55"
  }
}


def test_configured_user(tmp_path, monkeypatch):
  """ Tests an existing configuration with an admin user. """
  # First we mock some things out.
  mockconfigdir = str(tmp_path)
  mockusersfile = str(os.path.join(tmp_path, "users.json"))
  with open(mockusersfile, 'w', encoding='utf-8') as users_config:
    users_config.write(json.dumps(TEST_ADMIN_USER_CONFIG))

  monkeypatch.setattr(auth, "USER_CONFIG_DIR", mockconfigdir)
  monkeypatch.setattr(auth, "USERS_FILE", mockusersfile)

  # AmpliPi instance with mocked ctrl and streams
  config_file = os.path.join(tmp_path, 'house.json')
  with open(config_file, 'w', encoding='utf') as cfg_file:
    cfg_file.write(json.dumps(TEST_CONFIG))
  # we import app here because we needed to monkeypatch the auth things first
  from amplipi import app
  client = TestClient(app.create_app(mock_ctrl=True, mock_streams=True, config_file=config_file, delay_saves=False))

  # Test that the admin user exists and has various things set; can auth; can fail auth
  assert auth.user_exists("admin")
  assert auth._user_password_set("admin")
  assert auth.user_access_key_set("admin")
  assert auth._authenticate_user_with_password("admin", "test")
  assert auth._authenticate_user_with_password("admin", "newpassword") == False
  assert client.get('/api/').status_code == HTTPStatus.UNAUTHORIZED
  assert client.get(f"/api/?api-key=notarealkey").status_code == HTTPStatus.UNAUTHORIZED
  cookie_header = {"Cookie": f"amplipi-session=notarealkey"}
  assert client.get("/api", headers=cookie_header).status_code == HTTPStatus.UNAUTHORIZED

  # Test if setting a new password and access key work
  orig_key = auth.get_access_key("admin")
  auth.set_password_hash("admin", "newpassword")
  assert auth._authenticate_user_with_password("admin", "newpassword")
  assert auth.get_access_key("admin") != orig_key

  # Test if unsetting the password works
  auth.unset_password_hash("admin")
  assert auth._authenticate_user_with_password("admin", "") == False
  assert auth._user_password_set("admin") == False
  assert client.get('/api/').status_code == HTTPStatus.OK

  # Test access key bits explicitly
  orig_key = auth.get_access_key("admin")
  assert orig_key
  assert auth._check_access_key(orig_key) == "admin"
  new_key = auth.create_access_key("admin")
  assert new_key
  assert auth._check_access_key(new_key) == "admin"

  # Test that a non-existant user fails various tests
  assert auth.user_exists("test") == False
  assert auth._user_password_set("test") == False
  assert auth.user_access_key_set("test") == False
  assert auth._authenticate_user_with_password("test", "test") == False
  assert auth._check_access_key("not a real key") == False

  # Create the previously non-existant user and ensure it passes those same tests
  assert auth.set_password_hash("test", "test") == None
  assert auth.user_exists("test")
  assert auth._user_password_set("test")
  assert auth.user_access_key_set("test")
  assert auth._authenticate_user_with_password("test", "test")
  key = auth.get_access_key("test")
  assert client.get(f"/api/?api-key={key}").status_code == HTTPStatus.OK
  cookie_header = {"Cookie": f"amplipi-session={key}"}
  assert client.get("/api", headers=cookie_header).status_code == HTTPStatus.OK

def test_config_creation(tmp_path, monkeypatch):
  """ Tests that we can use the UI, create users and a user configuration from nothing. """
  mockconfigdir = str(tmp_path)
  mockusersfile = str(os.path.join(tmp_path, "users.json"))

  monkeypatch.setattr(auth, "USER_CONFIG_DIR", mockconfigdir)
  monkeypatch.setattr(auth, "USERS_FILE", mockusersfile)

  # AmpliPi instance with mocked ctrl and streams
  config_file = os.path.join(tmp_path, 'house.json')
  with open(config_file, 'w', encoding='utf') as cfg_file:
    cfg_file.write(json.dumps(TEST_CONFIG))
  # we import app here because we needed to monkeypatch the auth things first
  from amplipi import app
  client = TestClient(app.create_app(mock_ctrl=True, mock_streams=True, config_file=config_file, delay_saves=False))

  assert auth._user_password_set("admin") == False
  assert auth._check_access_key("admin") == False
  assert client.get('/api/').status_code == HTTPStatus.OK

  assert auth.set_password_hash("admin", "test") == None
  assert auth.user_exists("admin")
  assert auth._user_password_set("admin")
  assert auth.user_access_key_set("admin")
  assert auth._authenticate_user_with_password("admin", "test")
  assert client.get('/api/').status_code == HTTPStatus.UNAUTHORIZED

  key = auth.get_access_key("admin")
  assert client.get(f"/api/?api-key={key}").status_code == HTTPStatus.OK
  cookie_header = {"Cookie": f"amplipi-session={key}"}
  assert client.get("/api", headers=cookie_header).status_code == HTTPStatus.OK
