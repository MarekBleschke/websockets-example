import asyncio
import json
import logging
import logging.config
import uuid
from collections import defaultdict

import websockets

HOSTNAME = '127.0.0.1'
PORT = 8765

logging.config.dictConfig({
    'version': 1,
    'formatters': {
        'simple': {
            'class': 'logging.Formatter',
            'format': '[%(levelname)s]%(asctime)s - %(filename)s:%(lineno)d - %(message)s'  # noqa: E501
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'DEBUG'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console'],
        'propagate': True
    }
})

logger = logging.getLogger(__name__)


class GameServerException(Exception):
    pass


PLAYERS = defaultdict(dict)


async def broadcast_others(player_id, payload):
    for pid, data in PLAYERS.items():
        if pid != player_id:
            await data['connection'].send(json.dumps(payload))


def load_frame(frame):
    try:
        loaded = json.loads(frame)
    except json.JSONDecodeError:
        raise GameServerException(
            'Request frame isn\'t valid JSON: {}'.format(frame)
        )
    return loaded


async def game_server(websocket, path):
    logger.info('New websocket connection opened.')
    # Unique identifier of player (websocket connection)
    player_id = uuid.uuid4().hex

    logger.debug('Registering player id: {}'.format(player_id))
    # Save new connection in memory.
    PLAYERS[player_id]['connection'] = websocket
    # Send player's unique id.
    await websocket.send(
        json.dumps({'action': 'registered', 'player_id': player_id})
    )

    # Notify others about new player.
    for pid in PLAYERS:
        if pid != player_id:
            position = PLAYERS[pid]['position']
            await websocket.send(json.dumps(
                {
                    'action': 'position',
                    'player_id': pid,
                    'x': position['x'],
                    'y': position['y']
                }
            ))

    # Listen to messages from player.
    try:
        async for frame in websocket:
            logger.debug('Started processing message: {}'.format(frame))
            data = load_frame(frame)
            # Here is all logic of deciding what to do with incoming message.
            if data['action'] == 'position':
                # Set player's position.
                PLAYERS[player_id]['position'] = {
                    'x': data['x'],
                    'y': data['y']
                }
                # Notify others about new position.
                await broadcast_others(player_id, {
                    'action': 'position',
                    'player_id': player_id,
                    'x': data['x'],
                    'y': data['y']
                })
    finally:
        try:
            del PLAYERS[player_id]
        except KeyError:
            pass
        # Connection was dropped for some reason.
        # Notify other about disconnecting player.
        await broadcast_others(player_id, {
            'action': 'player_disconnected',
            'player_id': player_id
        })


start_server = websockets.serve(game_server, HOSTNAME, PORT)

logger.info('Server started {}:{}'.format(HOSTNAME, PORT))

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
