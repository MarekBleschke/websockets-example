var game = new Phaser.Game(400, 300, Phaser.CANVAS, '', {preload: preload, create: create, update: update});

var HOSTNAME = '127.0.0.1';
var PORT = 8765;

var player, otherPlayers, cursors;
var PLAYER_VELOCITY = 50;
var prevPos = {x: 0, y: 0};

function preload() {
  game.load.image('player', 'img/player.png');
  game.load.image('otherPlayer', 'img/other_player.png');
}

function create() {
  game.physics.startSystem(Phaser.Physics.ARCADE);

  player = game.add.sprite(0, 0, 'player');
  game.physics.arcade.enable(player);
  player.body.collideWorldBounds = true;

  otherPlayers = game.add.group();

  cursors = game.input.keyboard.createCursorKeys();

  // Setup websocket connection.
  ws = new WebSocket('ws://' + HOSTNAME + ':' + PORT);
  ws.onmessage = function (event) {
    var data = JSON.parse(event.data);

    // Player was successfully registered. Save id and send my position to
    // notify others.
    if (data.action === 'registered') {
      player.id = data.player_id;

      ws.send(JSON.stringify({
        action: 'position',
        x: player.body.position.x,
        y: player.body.position.y
      }));
    }
    // Notification about other players.
    else if (data.action === 'position') {
      var other = otherPlayers.getByName(data.player_id);

      if (!other) {
        // New player, create object for him.
        other = otherPlayers.create(data.x, data.y, 'otherPlayer');
        other.name = data.player_id;
      }
      else {
        other.position.x = data.x;
        other.position.y = data.y;
      }
    }
    else if (data.action === 'player_disconnected') {
      var other = otherPlayers.getByName(data.player_id);
      otherPlayers.remove(other, true);
    }
  };
}

function update() {
  player.body.velocity.x = 0;
  player.body.velocity.y = 0;

  if (cursors.left.isDown) {
    player.body.velocity.x = -PLAYER_VELOCITY;
  }

  if (cursors.right.isDown) {
    player.body.velocity.x = PLAYER_VELOCITY;
  }

  if (cursors.up.isDown) {
    player.body.velocity.y = -PLAYER_VELOCITY;
  }

  if (cursors.down.isDown) {
    player.body.velocity.y = PLAYER_VELOCITY;
  }

  var newPos = {x: player.body.position.x, y: player.body.position.y};
  // Don't be too noisy. Notify only when position has changed.
  if (newPos.x !== prevPos.x || newPos.y !== prevPos.y) {
    ws.send(JSON.stringify({
      action: 'position', x: newPos.x, y: newPos.y
    }));
    prevPos = newPos;
  }
}
