# Python websockets example

Example of simple websocket game server app using python's websockets
library and JavaScript's Phaser "game" as client.

Handles sending notifications about players positions to all clients. Also
handles cases of connecting and disconnecting clients.

## Installation and running

```
# Install dependencies - python 3.6 required.
pip install -r requirements.txt

# Run websockets server.
python src/game_server.py

# Run web server in new terminal session.
python -m http.server
```

Open "game" client in multiple browser tabs: http://127.0.0.1:8000/src/client.html.
