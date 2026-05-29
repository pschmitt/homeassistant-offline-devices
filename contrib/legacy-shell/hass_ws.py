#!/usr/bin/env python3

import json
import os
import random
import re
import sys

from websocket import create_connection

PROTOCOL = "ws"
HASS_SERVER = os.environ.get("HASS_SERVER", "localhost:8123")
if HASS_SERVER.startswith("http://"):
    PROTOCOL = "ws"
    HASS_SERVER = re.sub("^http://", "", HASS_SERVER)
elif HASS_SERVER.startswith("http://"):
    PROTOCOL = "wss"
    HASS_SERVER = re.sub("^https://", "", HASS_SERVER)

ACCESS_TOKEN = os.environ.get("HASS_TOKEN")

if not ACCESS_TOKEN:
    print("Missing HASS_TOKEN!", file=sys.stderr)
    sys.exit(2)

HASS_WS_URL = f"{PROTOCOL}://{HASS_SERVER}/api/websocket"

ws = create_connection(HASS_WS_URL)
result = json.loads(ws.recv())

ws.send(json.dumps({"type": "auth", "access_token": ACCESS_TOKEN}))
result = json.loads(ws.recv())

request_id = random.randint(1, 9999)
ws.send(json.dumps({"id": request_id, "type": sys.argv[1]}))
result = json.loads(ws.recv())

if not result.get("success", False):
    print("Request failed", file=sys.stderr)
    print(result, file=sys.stderr)
    sys.exit(1)

if result.get("id") != request_id:
    print("Received wrong response", file=sys.stderr)
    sys.exit(1)

print(json.dumps(result.get("result")))
