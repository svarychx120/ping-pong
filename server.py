import socket
import json
import threading
import time
import random

WIDTH, HEIGHT = 800, 600
BALL_SPEED = 5
PADDLE_SPEED = 10
COUNTDOWN_START = 3

class GameServer:
    def __init__(self, host='localhost', port=8081):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(2)
        print("🎮 Server started")
        self.clients = {0: None, 1: None}
        self.connected = {0: False, 1: False}
        self.lock = threading.Lock()
        self.reset_game_state()
        self.sound_event = None

    def reset_game_state(self):
        self.paddles = {0: 250, 1: 250}
        self.scores = [0, 0]
        self.ball = {
            "x": WIDTH // 2,
            "y": HEIGHT // 2,
            "vx": BALL_SPEED * random.choice([-1, 1]),
            "vy": BALL_SPEED * random.choice([-1, 1])
        }
        self.countdown = COUNTDOWN_START
        self.game_over = False
        self.winner = None

    def reset_ball(self):
        self.ball = {
            "x": WIDTH // 2,
            "y": HEIGHT // 2,
            "vx": BALL_SPEED * random.choice([-1, 1]),
            "vy": BALL_SPEED * random.choice([-1, 1])
        }
        self.sound_event = None

    def handle_client(self, pid):
        conn = self.clients[pid]
        try:
            while True:
                data = conn.recv(64).decode()
                if not data:
                    break
                with self.lock:
                    if data == "UP":
                        self.paddles[pid] = max(60, self.paddles[pid] - PADDLE_SPEED)
                    elif data == "DOWN":
                        self.paddles[pid] = min(HEIGHT - 100, self.paddles[pid] + PADDLE_SPEED)
        except:
            pass
        with self.lock:
            self.connected[pid] = False
            if not self.game_over:
                self.game_over = True
                self.winner = 1 - pid
                print(f"Player {pid} disconnected. Player {1 - pid} wins.")

    def broadcast_state(self):
        state = json.dumps({
            "paddles": {str(k): v for k, v in self.paddles.items()},
            "ball": self.ball,
            "scores": self.scores,
            "countdown": max(self.countdown, 0),
            "winner": self.winner if self.game_over else None,
            "sound_event": self.sound_event
        }) + "\n"
        self.sound_event = None   # clear after broadcast so it only fires once
        for pid, conn in self.clients.items():
            if conn and self.connected[pid]:
                try:
                    conn.sendall(state.encode())
                except:
                    self.connected[pid] = False

    def ball_logic(self):
        # Countdown phase
        while self.countdown > 0:
            time.sleep(1)
            with self.lock:
                self.countdown -= 1
                self.broadcast_state()

        # Game phase
        while not self.game_over:
            time.sleep(1 / 60)
            with self.lock:
                self.ball['x'] += self.ball['vx']
                self.ball['y'] += self.ball['vy']

                # Wall bounce (top = 60 for HUD, bottom = HEIGHT-10)
                if self.ball['y'] <= 60 or self.ball['y'] >= HEIGHT - 10:
                    self.ball['vy'] *= -1
                    self.sound_event = "wall_hit"

                # Paddle collisions
                if (self.ball['x'] <= 40 and
                        self.paddles[0] <= self.ball['y'] <= self.paddles[0] + 100):
                    self.ball['vx'] = abs(self.ball['vx'])  # always bounce right
                    self.sound_event = 'platform_hit'

                if (self.ball['x'] >= WIDTH - 40 and
                        self.paddles[1] <= self.ball['y'] <= self.paddles[1] + 100):
                    self.ball['vx'] = -abs(self.ball['vx'])  # always bounce left
                    self.sound_event = 'platform_hit'

                # Scoring
                if self.ball['x'] < 0:
                    self.scores[1] += 1
                    self.reset_ball()
                elif self.ball['x'] > WIDTH:
                    self.scores[0] += 1
                    self.reset_ball()

                # Win condition
                if self.scores[0] >= 10:
                    self.game_over = True
                    self.winner = 0
                elif self.scores[1] >= 10:
                    self.game_over = True
                    self.winner = 1

                self.broadcast_state()

        # Send final state one more time so clients see the winner
        with self.lock:
            self.broadcast_state()

    def accept_clients(self):
        print("Waiting for players...")
        pid = 0
        while pid < 2:
            conn, addr = self.server.accept()
            self.clients[pid] = conn
            self.connected[pid] = True
            conn.send(str(pid).encode())
            print(f"Player {pid} connected from {addr}")
            threading.Thread(target=self.handle_client, args=(pid,), daemon=True).start()
            pid += 1
        print("Both players connected — starting game!")
        threading.Thread(target=self.ball_logic, daemon=True).start()

    def run(self):
        self.accept_clients()
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Server shutting down.")
            self.server.close()

if __name__ == "__main__":
    GameServer().run()
