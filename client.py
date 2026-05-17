import pygame
import socket
import json
import math
import random
from threading import Thread
from menu import start_menu

# ── Window ────────────────────────────────────────────────────────────────────
WIDTH, HEIGHT = 800, 600
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
pygame.display.set_caption("PING PONG — АРКАДА")

# ── Palette ───────────────────────────────────────────────────────────────────
NEON_CYAN   = (0,   255, 240)
NEON_PINK   = (255,  20, 147)
NEON_PURPLE = (160,  32, 240)
NEON_ORANGE = (255, 140,   0)
NEON_GREEN  = (57,  255,  20)
DARK_BG     = (6,    4,  20)
WHITE       = (255, 255, 255)
DIM_WHITE   = (160, 160, 190)
COURT_LINE  = (30,  25,  60)

# ── Fonts ─────────────────────────────────────────────────────────────────────
def load_font(size, bold=False):
    for name in ["fonts/Orbitron-Bold.ttf", "fonts/orbitron.ttf"]:
        try:
            return pygame.font.Font(name, size)
        except:
            pass
    return pygame.font.SysFont("Arial", size, bold=bold)

font_score  = load_font(52, bold=True)
font_big    = load_font(56, bold=True)
font_mid    = load_font(30, bold=True)
font_small  = load_font(18)
font_hint   = load_font(16)

# ── Initial menu ──────────────────────────────────────────────────────────────
settings = start_menu(WIDTH, HEIGHT, screen)

# ── Particle system ───────────────────────────────────────────────────────────
class Particle:
    def __init__(self, x, y, color):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(1, 5)
        self.x, self.y = float(x), float(y)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.uniform(0.3, 0.8)
        self.max_life = self.life
        self.size = random.uniform(2, 5)
        self.color = color

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, x, y, color, count=8):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def update(self, dt):
        for p in self.particles:
            p.x += p.vx * dt * 60
            p.y += p.vy * dt * 60
            p.vy += 0.05 * dt * 60   # gravity
            p.life -= dt
        self.particles = [p for p in self.particles if p.life > 0]

    def draw(self, surf):
        for p in self.particles:
            alpha = p.life / p.max_life
            r, g, b = p.color
            col = (int(r * alpha), int(g * alpha), int(b * alpha))
            pygame.draw.circle(surf, col, (int(p.x), int(p.y)),
                               max(1, int(p.size * alpha)))

particles = ParticleSystem()

# ── Glow helper ───────────────────────────────────────────────────────────────
def draw_glow(surf, color, rect_or_circle, radius=10, layers=3, circle=False):
    r, g, b = color
    for i in range(layers, 0, -1):
        exp = i * 5
        alpha = max(0, 60 - i * 16)
        if circle:
            cx, cy, rad = rect_or_circle
            s = pygame.Surface((rad * 2 + exp * 2, rad * 2 + exp * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (r, g, b, alpha), (rad + exp, rad + exp), rad + exp)
            surf.blit(s, (cx - rad - exp, cy - rad - exp))
        else:
            rect = rect_or_circle
            s = pygame.Surface((rect.width + exp * 2, rect.height + exp * 2), pygame.SRCALPHA)
            pygame.draw.rect(s, (r, g, b, alpha), s.get_rect(), border_radius=radius + i * 2)
            surf.blit(s, (rect.x - exp, rect.y - exp))

# ── Court drawing ─────────────────────────────────────────────────────────────
TOP_BAR = 60     # HUD height at top
PLAY_TOP = TOP_BAR

def draw_court(surf, t):
    # Background
    surf.fill(DARK_BG)

    # Subtle vertical gradient overlay
    grad = pygame.Surface((WIDTH, HEIGHT - PLAY_TOP), pygame.SRCALPHA)
    for y in range(0, HEIGHT - PLAY_TOP, 4):
        prog = y / (HEIGHT - PLAY_TOP)
        alpha = int(20 * (1 - prog))
        pygame.draw.line(grad, (0, 180, 255, alpha), (0, y), (WIDTH, y))
    surf.blit(grad, (0, PLAY_TOP))

    # Court outline
    court_rect = pygame.Rect(10, PLAY_TOP + 6, WIDTH - 20, HEIGHT - PLAY_TOP - 12)
    pygame.draw.rect(surf, COURT_LINE, court_rect, width=2, border_radius=4)

    # Center dashed line
    dash_h = 14
    dash_gap = 10
    x = WIDTH // 2
    y = PLAY_TOP + 16
    while y < HEIGHT - 16:
        pygame.draw.line(surf, COURT_LINE, (x, y), (x, min(y + dash_h, HEIGHT - 16)), 2)
        y += dash_h + dash_gap

    # Center circle
    pygame.draw.circle(surf, COURT_LINE, (WIDTH // 2, (PLAY_TOP + HEIGHT) // 2), 50, 2)

    # Scanline shimmer
    scan_y = int((t * 35) % (HEIGHT - PLAY_TOP)) + PLAY_TOP
    s = pygame.Surface((WIDTH, 2), pygame.SRCALPHA)
    s.fill((0, 200, 255, 8))
    surf.blit(s, (0, scan_y))


def draw_hud(surf, scores, t):
    # HUD background bar
    hud_rect = pygame.Rect(0, 0, WIDTH, TOP_BAR)
    pygame.draw.rect(surf, (10, 8, 30), hud_rect)
    pygame.draw.line(surf, NEON_CYAN, (0, TOP_BAR), (WIDTH, TOP_BAR), 1)

    # Score
    left_score  = str(scores[0])
    right_score = str(scores[1])

    # Left player name
    p1_surf = font_small.render("P1", True, NEON_CYAN)
    surf.blit(p1_surf, (18, 8))
    ls = font_score.render(left_score, True, NEON_CYAN)
    surf.blit(ls, (WIDTH // 4 - ls.get_width() // 2, 6))

    # Right player name
    p2_surf = font_small.render("P2", True, NEON_PINK)
    surf.blit(p2_surf, (WIDTH - 18 - p2_surf.get_width(), 8))
    rs = font_score.render(right_score, True, NEON_PINK)
    surf.blit(rs, (3 * WIDTH // 4 - rs.get_width() // 2, 6))

    # Center separator
    sep = font_mid.render(":", True, DIM_WHITE)
    surf.blit(sep, (WIDTH // 2 - sep.get_width() // 2, 10))

    # Animated center logo pulse
    pulse = 0.8 + 0.2 * math.sin(t * 3)
    logo = font_hint.render("PING PONG", True,
                             (int(80 * pulse), int(80 * pulse), int(130 * pulse)))
    surf.blit(logo, (WIDTH // 2 - logo.get_width() // 2, TOP_BAR - logo.get_height() - 2))


# ── Paddle drawing ────────────────────────────────────────────────────────────
PADDLE_W = 12
PADDLE_H = 100

def draw_paddle(surf, x, y, color, side="left"):
    rect = pygame.Rect(x, y, PADDLE_W, PADDLE_H)
    draw_glow(surf, color, rect, radius=6, layers=3)
    pygame.draw.rect(surf, color, rect, border_radius=6)
    # Shine strip
    shine = pygame.Surface((4, PADDLE_H - 8), pygame.SRCALPHA)
    shine.fill((255, 255, 255, 50))
    surf.blit(shine, (x + (2 if side == "left" else PADDLE_W - 6), y + 4))


# ── Ball drawing ──────────────────────────────────────────────────────────────
BALL_R = 10
ball_trail = []   # list of (x, y)

def draw_ball(surf, x, y, t):
    # Trail
    for i, (tx, ty) in enumerate(ball_trail):
        alpha = int(80 * (i / max(len(ball_trail), 1)))
        r_t = max(1, BALL_R - (len(ball_trail) - i))
        s = pygame.Surface((r_t * 2 + 2, r_t * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*NEON_CYAN, alpha), (r_t + 1, r_t + 1), r_t)
        surf.blit(s, (int(tx) - r_t, int(ty) - r_t))

    # Glow
    draw_glow(surf, NEON_CYAN, (x, y, BALL_R), layers=3, circle=True)
    # Main ball
    pygame.draw.circle(surf, NEON_CYAN, (int(x), int(y)), BALL_R)
    # Inner highlight
    pygame.draw.circle(surf, WHITE, (int(x) - 3, int(y) - 3), 3)


# ── Overlay screens ───────────────────────────────────────────────────────────
def draw_countdown(surf, value, t):
    surf.fill(DARK_BG)
    # Pulsing ring
    pulse = 0.7 + 0.3 * math.sin(t * 6)
    for i in range(4, 0, -1):
        alpha = int(40 * pulse * (i / 4))
        r = int(80 * pulse * (5 - i))
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*NEON_CYAN, alpha), (r, r), r)
        surf.blit(s, (WIDTH // 2 - r, HEIGHT // 2 - r))

    num_surf = font_big.render(str(value), True, WHITE)
    surf.blit(num_surf, (WIDTH // 2 - num_surf.get_width() // 2,
                         HEIGHT // 2 - num_surf.get_height() // 2))

    label = font_hint.render("ГОТУЙСЯ!", True, NEON_PINK)
    surf.blit(label, (WIDTH // 2 - label.get_width() // 2, HEIGHT // 2 + 60))


def draw_win_screen(surf, you_winner, t, ps):
    # Dark overlay with particles
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((4, 2, 14, 210))
    surf.blit(overlay, (0, 0))
    ps.draw(surf)

    if you_winner:
        title_text = "ТИ ПЕРЕМІГ!"
        color = NEON_GREEN
    else:
        title_text = "ПОЩАСТИТЬ НАСТУПНОГО РАЗУ"
        color = NEON_PINK

    # Glowing title
    pulse = 0.85 + 0.15 * math.sin(t * 2.5)
    r, g, b = color
    c = (int(r * pulse), int(g * pulse), int(b * pulse))
    ts = font_big.render(title_text, True, c)
    tx = WIDTH // 2 - ts.get_width() // 2
    ty = HEIGHT // 2 - 80
    # Glow pass
    for i in range(3, 0, -1):
        ghost = ts.copy()
        ghost.set_alpha(40)
        surf.blit(ghost, (tx - i * 3, ty))
        surf.blit(ghost, (tx + i * 3, ty))
    surf.blit(ts, (tx, ty))

    # Restart hint box
    hint_rect = pygame.Rect(WIDTH // 2 - 160, HEIGHT // 2 + 20, 320, 52)
    pygame.draw.rect(surf, (20, 15, 45), hint_rect, border_radius=10)
    pygame.draw.rect(surf, NEON_CYAN, hint_rect, width=1, border_radius=10)
    r_surf = font_mid.render("[  R  ]  рестарт", True, NEON_CYAN)
    surf.blit(r_surf, r_surf.get_rect(center=hint_rect.center))

    # Trophy or broken heart
    emoji_text = "🏆" if you_winner else "💔"
    try:
        e_surf = pygame.font.SysFont("Segoe UI Emoji", 72).render(emoji_text, True, color)
        surf.blit(e_surf, (WIDTH // 2 - e_surf.get_width() // 2, HEIGHT // 2 - 180))
    except:
        pass


def draw_waiting(surf, t):
    surf.fill(DARK_BG)
    dots = "." * (int(t * 2) % 4)
    ws = font_mid.render(f"Очікування гравців{dots}", True, NEON_CYAN)
    surf.blit(ws, (WIDTH // 2 - ws.get_width() // 2, HEIGHT // 2 - 20))
    hint = font_hint.render("Підключіться до сервера для початку гри", True, DIM_WHITE)
    surf.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT // 2 + 30))


# ── Server connection ─────────────────────────────────────────────────────────
def connect_to_server():
    global settings
    while True:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((settings.host, int(settings.port)))
            buffer = ""
            game_state = {}
            my_id = int(client.recv(24).decode())
            return my_id, game_state, buffer, client
        except:
            settings = start_menu(WIDTH, HEIGHT, screen, settings)

def receive():
    global buffer, game_state, game_over
    while not game_over:
        try:
            data = client.recv(1024).decode()
            buffer += data
            while "\n" in buffer:
                packet, buffer = buffer.split("\n", 1)
                if packet.strip():
                    game_state = json.loads(packet)
        except:
            game_state["winner"] = -1
            break

# ── Sounds ────────────────────────────────────────────────────────────────────
def safe_load_sound(path):
    try:
        s = pygame.mixer.Sound(path)
        s.set_volume(settings.volume)
        return s
    except:
        return None

try:
    pygame.mixer.music.load('sounds/newbattle.wav')
except:
    pass

WALL_HIT_SOUND     = safe_load_sound('sounds/Fire 2.mp3')
PLATFORM_HIT_SOUND = safe_load_sound('sounds/Fire 4.mp3')
LOSE_SOUND         = safe_load_sound('sounds/Game Over.mp3')

# ── Game state ────────────────────────────────────────────────────────────────
game_over   = False
winner      = None
you_winner  = None
is_start_play_music = False
lose_sound_played   = False
my_id, game_state, buffer, client = connect_to_server()
Thread(target=receive, daemon=True).start()

t = 0.0
win_particles_emitted = False
prev_ball = None

# ── Main loop ─────────────────────────────────────────────────────────────────
while True:
    dt = clock.tick(60) / 1000.0
    t += dt

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            exit()

    # ── COUNTDOWN ─────────────────────────────────────────────────────────────
    if "countdown" in game_state and game_state["countdown"] > 0:
        draw_countdown(screen, game_state["countdown"], t)
        pygame.display.update()
        is_start_play_music = True
        continue

    # ── WIN / LOSE ────────────────────────────────────────────────────────────
    if "winner" in game_state and game_state["winner"] is not None:
        pygame.mixer.music.stop()
        if you_winner is None:
            you_winner = (game_state["winner"] == my_id)
            if not you_winner and not lose_sound_played:
                if LOSE_SOUND: LOSE_SOUND.play()
                lose_sound_played = True

        # Emit celebratory particles
        if you_winner and not win_particles_emitted:
            for _ in range(6):
                px = random.randint(50, WIDTH - 50)
                py = random.randint(50, HEIGHT - 50)
                particles.emit(px, py, random.choice([NEON_GREEN, NEON_CYAN, WHITE]), count=15)
            win_particles_emitted = True

        particles.update(dt)
        draw_win_screen(screen, you_winner, t, particles)
        pygame.display.update()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_r]:
            client.close()
            game_over = True          # stop the receive thread
            settings = start_menu(WIDTH, HEIGHT, screen, settings)
            game_over = False
            my_id, game_state, buffer, client = connect_to_server()
            you_winner = None
            lose_sound_played = False
            win_particles_emitted = False
            ball_trail.clear()
            particles.particles.clear()
            Thread(target=receive, daemon=True).start()
        continue

    # ── PLAYING ───────────────────────────────────────────────────────────────
    if game_state:
        bx = game_state['ball']['x']
        by = game_state['ball']['y']

        # Ball trail
        ball_trail.append((bx, by))
        if len(ball_trail) > 10:
            ball_trail.pop(0)

        # Sound events + particles
        se = game_state.get('sound_event')
        if se == 'wall_hit':
            if WALL_HIT_SOUND: WALL_HIT_SOUND.play()
            particles.emit(bx, by, NEON_CYAN, count=6)
        elif se == 'platform_hit':
            if PLATFORM_HIT_SOUND: PLATFORM_HIT_SOUND.play()
            particles.emit(bx, by, NEON_ORANGE, count=10)

        particles.update(dt)

        draw_court(screen, t)
        draw_hud(screen, game_state['scores'], t)

        # Left paddle (P1)
        p1_y = game_state['paddles']['0']
        draw_paddle(screen, 20, p1_y, NEON_CYAN, side="left")

        # Right paddle (P2)
        p2_y = game_state['paddles']['1']
        draw_paddle(screen, WIDTH - 20 - PADDLE_W, p2_y, NEON_PINK, side="right")

        # Ball
        draw_ball(screen, bx, by, t)

        # Particles on top
        particles.draw(screen)

        # Controls hint (fades after 5s)
        if t < 8:
            alpha_val = max(0, int(255 * (1 - (t - 5) / 3))) if t > 5 else 200
            hint = font_hint.render("W / S — рух гравця", True, DIM_WHITE)
            hint.set_alpha(alpha_val)
            screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 24))

    else:
        draw_waiting(screen, t)

    pygame.display.update()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_w]:
        client.send(b"UP")
    elif keys[pygame.K_s]:
        client.send(b"DOWN")

    if is_start_play_music and settings.music_enabled:
        try:
            pygame.mixer.music.play(-1)
        except:
            pass
        is_start_play_music = False
