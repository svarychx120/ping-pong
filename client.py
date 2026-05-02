from pygame import *
import socket
import json
from threading import Thread
import math
import random

# ---PYGAME НАЛАШТУВАННЯ ---
WIDTH, HEIGHT = 800, 600
init()
screen = display.set_mode((WIDTH, HEIGHT))
clock = time.Clock()
display.set_caption("Пінг-Понг")

# --- COLORS ---
NEON_BLUE = (0, 255, 255)
NEON_PINK = (255, 0, 200)
NEON_GREEN = (0, 255, 100)
NEON_PURPLE = (200, 0, 255)
BG_DARK = (10, 10, 20)
ACCENT_LIGHT = (255, 255, 255)

# --- PARTICLE SYSTEM ---
class Particle:
    def __init__(self, x, y, vx, vy, color, lifetime=30):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.size = 8
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2  # gravity
        self.lifetime -= 1
        self.size = max(1, int(8 * (self.lifetime / self.max_lifetime)))
    
    def draw(self, surface):
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        color_adjusted = tuple(int(c * (self.lifetime / self.max_lifetime)) for c in self.color)
        draw.circle(surface, color_adjusted, (int(self.x), int(self.y)), self.size)

# --- MOTION BLUR TRAIL ---
class MotionTrail:
    def __init__(self, x, y, color, lifetime=8):
        self.x = x
        self.y = y
        self.color = color
        self.lifetime = lifetime
        self.max_lifetime = lifetime
    
    def draw(self, surface):
        alpha = int(255 * (self.lifetime / self.max_lifetime)) // 2
        color_adjusted = tuple(int(c * (self.lifetime / self.max_lifetime) * 0.6) for c in self.color)
        draw.circle(surface, color_adjusted, (int(self.x), int(self.y)), 8)

particles = []
motion_trails = []
last_ball_pos = None
screen_shake_intensity = 0

# ---СЕРВЕР ---
def connect_to_server():
    while True:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect(('localhost', 8080))  # ---- Підключення до сервера
            buffer = ""
            game_state = {}
            my_id = int(client.recv(24).decode())
            return my_id, game_state, buffer, client
        except:
            pass

def receive():
    global buffer, game_state, game_over, screen_shake_intensity
    while not game_over:
        try:
            data = client.recv(1024).decode()
            buffer += data
            while "\n" in buffer:
                packet, buffer = buffer.split("\n", 1)
                if packet.strip():
                    old_state = game_state.copy()
                    game_state = json.loads(packet)
                    # Spawn particles on collision
                    if old_state and 'sound_event' in old_state:
                        if game_state.get('sound_event') == 'platform_hit':
                            ball_x = game_state['ball']['x']
                            ball_y = game_state['ball']['y']
                            create_collision_particles(ball_x, ball_y, NEON_BLUE, 25)
                            screen_shake_intensity = 8
                        elif game_state.get('sound_event') == 'wall_hit':
                            ball_x = game_state['ball']['x']
                            ball_y = game_state['ball']['y']
                            create_collision_particles(ball_x, ball_y, NEON_PINK, 20)
                            screen_shake_intensity = 4
        except:
            game_state["winner"] = -1
            break

# --- ШРИФТИ ---
font_win = font.Font(None, 96)
font_main = font.Font(None, 48)
font_small = font.Font(None, 28)
font_title = font.Font(None, 64)

# --- ЗОБРАЖЕННЯ ----
background = image.load("background.jpg")
background = transform.scale(background, (WIDTH, HEIGHT))

# --- ДОПОМІЖНІ ФУНКЦІЇ ---
def create_collision_particles(x, y, color, count=12):
    global particles
    for i in range(count):
        angle = (2 * math.pi * i) / count
        speed = 4 + (i % 3)
        vx = math.cos(angle) * speed
        vy = math.sin(angle) * speed
        particles.append(Particle(x, y, vx, vy, color, lifetime=40))

def draw_glow(surface, x, y, radius, color, intensity=3):
    """Draw a glowing effect around a point"""
    for i in range(intensity, 0, -1):
        alpha_color = tuple(int(c * (1 - i/intensity) * 0.3) for c in color)
        draw.circle(surface, alpha_color, (x, y), radius + i * 2)

def draw_paddle(surface, x, y, color, is_left=True):
    """Draw paddle with semi-transparent effect blended with background"""
    # Create paddle surface with transparency
    paddle_surf = Surface((20, 100))
    paddle_surf.set_colorkey((0, 0, 0))
    paddle_surf.set_alpha(200)
    
    # Draw gradient effect on paddle
    for i in range(100):
        alpha_val = int(255 * (1 - abs(i - 50) / 50) * 0.7)
        color_faded = tuple(int(c * (0.3 + 0.7 * (1 - abs(i - 50) / 50))) for c in color)
        draw.line(paddle_surf, color_faded, (0, i), (20, i), 1)
    
    surface.blit(paddle_surf, (x, y))
    
    # Add glowing edges
    draw_glow(surface, x + 10, y + 50, 12, color, intensity=3)
    
    # Draw bright outline
    draw.rect(surface, color, (x, y, 20, 100), 3)
    draw.rect(surface, ACCENT_LIGHT, (x, y, 20, 100), 1)

def draw_ball_with_motion_blur(surface, x, y, color, trail_list):
    """Draw ball with motion blur trail effect"""
    # Draw motion blur trails first (behind the ball)
    for trail in trail_list:
        trail.draw(surface)
    
    # Draw multiple semi-transparent circles for blur effect
    for i in range(3, 0, -1):
        blur_color = tuple(int(c * (1 - i / 4) * 0.5) for c in color)
        draw.circle(surface, blur_color, (int(x), int(y)), 10 + i * 2)
    
    # Draw the main ball with glow
    draw_glow(surface, x, y, 12, color, intensity=5)
    draw.circle(surface, color, (x, y), 10)
    draw.circle(surface, ACCENT_LIGHT, (x, y), 10, 1)
# --- ЗВУКИ ---
# --- ГРА ---
game_over = False
winner = None
you_winner = None
my_id, game_state, buffer, client = connect_to_server()
Thread(target=receive, daemon=True).start()
frame_count = 0
last_score = [0, 0]
last_ball_pos = None

while True:
    frame_count += 1
    for e in event.get():
        if e.type == QUIT:
            quit()

    # Update particles
    for p in particles[:]:
        p.update()
        if p.lifetime <= 0:
            particles.remove(p)
    
    # Update motion trails
    for trail in motion_trails[:]:
        trail.lifetime -= 1
        if trail.lifetime <= 0:
            motion_trails.remove(trail)
    
    # Apply screen shake
    shake_offset = (0, 0)
    if screen_shake_intensity > 0:
        shake_offset = (random.randint(-int(screen_shake_intensity), int(screen_shake_intensity)), 
                       random.randint(-int(screen_shake_intensity), int(screen_shake_intensity)))
        screen_shake_intensity *= 0.85

    if "countdown" in game_state and game_state["countdown"] > 0:
        screen.blit(background, (0, 0))
        
        # Draw semi-transparent overlay
        overlay = Surface((WIDTH, HEIGHT))
        overlay.set_alpha(100)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        countdown_val = game_state["countdown"]
        # Animated countdown scale
        scale = 1.0 + 0.3 * math.sin(frame_count * 0.3)
        countdown_surf = font_title.render(str(countdown_val), True, NEON_PURPLE)
        countdown_scaled = transform.scale(countdown_surf, 
            (int(countdown_surf.get_width() * scale), int(countdown_surf.get_height() * scale)))
        rect = countdown_scaled.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(countdown_scaled, rect)
        
        # Glowing effect around countdown
        draw.circle(screen, (*NEON_PURPLE, 50), (WIDTH // 2, HEIGHT // 2), int(150 * scale), 3)
        
        display.update()
        continue

    if "winner" in game_state and game_state["winner"] is not None:
        screen.blit(background, (0, 0))
        overlay = Surface((WIDTH, HEIGHT))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        if you_winner is None:
            if game_state["winner"] == my_id:
                you_winner = True
            else:
                you_winner = False
        
        # Pulsing animation
        pulse = 0.8 + 0.2 * math.sin(frame_count * 0.1)
        
        if you_winner:
            text = "Ти переміг!"
            color = NEON_GREEN
        else:
            text = "Пощастить наступним разом!"
            color = NEON_PINK
        
        win_text = font_win.render(text, True, color)
        win_text_scaled = transform.scale(win_text, 
            (int(win_text.get_width() * pulse), int(win_text.get_height() * pulse)))
        text_rect = win_text_scaled.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 80))
        screen.blit(win_text_scaled, text_rect)
        
        # Draw glow
        draw_glow(screen, WIDTH // 2, HEIGHT // 2 - 80, 200, color, 5)
        
        # Restart instruction with fade
        fade = 0.5 + 0.5 * math.sin(frame_count * 0.08)
        restart_surf = font_main.render('K - рестарт', True, tuple(int(c * fade) for c in NEON_BLUE))
        restart_rect = restart_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 100))
        screen.blit(restart_surf, restart_rect)
        
        display.update()
        continue

    if game_state:
        screen.blit(background, (0, 0))
        
        # Create motion trail for ball
        current_ball_pos = (game_state['ball']['x'], game_state['ball']['y'])
        if last_ball_pos and last_ball_pos != current_ball_pos:
            # Add trails between last and current position
            trail_dist = math.hypot(current_ball_pos[0] - last_ball_pos[0], 
                                   current_ball_pos[1] - last_ball_pos[1])
            if trail_dist > 0:
                trail_steps = max(2, int(trail_dist / 3))
                for i in range(trail_steps):
                    t = i / trail_steps
                    trail_x = last_ball_pos[0] + (current_ball_pos[0] - last_ball_pos[0]) * t
                    trail_y = last_ball_pos[1] + (current_ball_pos[1] - last_ball_pos[1]) * t
                    motion_trails.append(MotionTrail(trail_x, trail_y, NEON_BLUE, lifetime=6))
        last_ball_pos = current_ball_pos
        
        # Check for score changes and create particles
        if last_score != game_state['scores']:
            if game_state['scores'][0] > last_score[0]:
                create_collision_particles(WIDTH - 150, HEIGHT // 2, NEON_GREEN, 40)
            elif game_state['scores'][1] > last_score[1]:
                create_collision_particles(150, HEIGHT // 2, NEON_PINK, 40)
            last_score = game_state['scores'][:]
        
        # Apply screen shake
        shake_x, shake_y = shake_offset
        
        # Draw paddles with glow (with shake offset)
        draw_paddle(screen, 20 + shake_x, int(game_state['paddles']['0']) + shake_y, NEON_GREEN, is_left=True)
        draw_paddle(screen, WIDTH - 40 + shake_x, int(game_state['paddles']['1']) + shake_y, NEON_PINK, is_left=False)
        
        # Draw ball with motion blur (with shake offset)
        ball_color = NEON_BLUE
        draw_ball_with_motion_blur(screen, 
                                   game_state['ball']['x'] + shake_x, 
                                   game_state['ball']['y'] + shake_y, 
                                   ball_color, motion_trails)
        
        # Draw particles
        for p in particles:
            p.draw(screen)
        
        # Draw center line with glow effect
        for y in range(0, HEIGHT, 20):
            # Main line
            draw.line(screen, ACCENT_LIGHT, (WIDTH // 2 + shake_x, y + shake_y), 
                     (WIDTH // 2 + shake_x, y + 10 + shake_y), 2)
            # Glow effect
            draw.line(screen, (*NEON_PURPLE, 20), (WIDTH // 2 + shake_x - 2, y + shake_y), 
                     (WIDTH // 2 + shake_x - 2, y + 10 + shake_y), 1)
        
        # Draw scores with better styling
        score_text = f"{game_state['scores'][0]} : {game_state['scores'][1]}"
        score_surf = font_main.render(score_text, True, ACCENT_LIGHT)
        score_rect = score_surf.get_rect(center=(WIDTH // 2, 40))
        
        # Draw score background
        draw.rect(screen, (*NEON_PURPLE, 30), score_rect.inflate(40, 30))
        draw.rect(screen, NEON_PURPLE, score_rect.inflate(40, 30), 3)
        screen.blit(score_surf, score_rect)
        
    else:
        screen.blit(background, (0, 0))
        overlay = Surface((WIDTH, HEIGHT))
        overlay.set_alpha(80)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Animated waiting text with dots
        dots = "." * (1 + (frame_count // 20) % 4)
        waiting_text = f"Очікування гравців{dots}"
        waiting_surf = font_main.render(waiting_text, True, NEON_BLUE)
        waiting_rect = waiting_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50))
        
        # Pulsing animation
        pulse = 0.7 + 0.3 * math.sin(frame_count * 0.08)
        waiting_scaled = transform.scale(waiting_surf, 
            (int(waiting_surf.get_width() * pulse), int(waiting_surf.get_height() * pulse)))
        screen.blit(waiting_scaled, waiting_rect)
        
        # Draw floating circles as decoration
        for i in range(3):
            circle_y = HEIGHT // 2 + 100 + 40 * i + 30 * math.sin((frame_count + i * 20) * 0.05)
            draw.circle(screen, NEON_PINK, (int(circle_y), int(circle_y)), 5)

    display.update()
    clock.tick(60)

    keys = key.get_pressed()
    if keys[K_w]:
        client.send(b"UP")
    elif keys[K_s]:
        client.send(b"DOWN")
