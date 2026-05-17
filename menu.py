import pygame
import sys
from settings import Settings, settings_loop

# ── Palette ──────────────────────────────────────────────────────────────────
NEON_CYAN   = (0,   255, 240)
NEON_PINK   = (255,  20, 147)
NEON_ORANGE = (255, 140,   0)
DARK_BG     = (6,    4,  20)
WHITE       = (255, 255, 255)
DIM_WHITE   = (180, 180, 200)

BUTTONS = [
    {"label": "ПОЧАТИ",      "accent": NEON_CYAN},
    {"label": "НАЛАШТУВАННЯ","accent": NEON_PINK},
    {"label": "ВИХІД",       "accent": NEON_ORANGE},
]


# ── Button ───────────────────────────────────────────────────────────────────
class Button:
    def __init__(self, data, font_label, rect):
        self.label  = data["label"]
        self.accent = data["accent"]
        self.font_label  = font_label
        self.rect   = rect
        self.hover_t = 0.0

    def update(self, selected, dt):
        target = 1.0 if selected else 0.0
        self.hover_t += (target - self.hover_t) * min(1, dt * 8)

    def draw(self, surf, selected):
        t = self.hover_t
        r, g, b = self.accent

        # Simple background
        bg_col = (int(8 + t * r * 0.08), int(6 + t * g * 0.08), int(22 + t * b * 0.12))
        pygame.draw.rect(surf, bg_col, self.rect, border_radius=6)

        # Border only when selected
        if selected:
            pygame.draw.rect(surf, self.accent, self.rect, width=2, border_radius=6)
        else:
            pygame.draw.rect(surf, (40, 35, 60), self.rect, width=1, border_radius=6)

        # Label
        label_col = WHITE if selected else DIM_WHITE
        label_surf = self.font_label.render(self.label, True, label_col)
        label_rect = label_surf.get_rect(center=self.rect.center)
        surf.blit(label_surf, label_rect)


# ── Main menu loop ────────────────────────────────────────────────────────────
def menu_loop(screen_width, screen_height, screen, settings):
    pygame.display.set_caption("PING PONG — АРКАДА")
    clock = pygame.time.Clock()
    play_menu_music(settings)
    pygame.event.clear()
    pygame.time.wait(80)

    try:
        choice_snd = pygame.mixer.Sound('sounds/Menu Choice.mp3')
    except:
        choice_snd = None

    def load_font(size, bold=False):
        for name in ["fonts/Orbitron-Bold.ttf", "fonts/orbitron.ttf"]:
            try:
                return pygame.font.Font(name, size)
            except:
                pass
        return pygame.font.SysFont("Arial", size, bold=bold)

    font_title  = load_font(64, bold=True)
    font_btn    = load_font(26, bold=True)
    font_hint   = load_font(16)

    bw, bh = 420, 68
    gap = 14
    total_h = len(BUTTONS) * bh + (len(BUTTONS) - 1) * gap
    by_start = screen_height // 2 - total_h // 2 + 60

    buttons = []
    for i, data in enumerate(BUTTONS):
        bx = screen_width // 2 - bw // 2
        by = by_start + i * (bh + gap)
        buttons.append(Button(data, font_btn, pygame.Rect(bx, by, bw, bh)))

    selected = 0

    while True:
        dt = clock.tick(60) / 1000.0

        # ── Events
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(buttons)
                    if choice_snd: choice_snd.play()
                elif e.key == pygame.K_UP:
                    selected = (selected - 1) % len(buttons)
                    if choice_snd: choice_snd.play()
                elif e.key == pygame.K_RETURN:
                    pygame.mixer.music.stop()
                    lbl = buttons[selected].label
                    if lbl == "ПОЧАТИ":
                        return
                    elif lbl == "ВИХІД":
                        pygame.quit(); sys.exit()
                    elif lbl == "НАЛАШТУВАННЯ":
                        play_menu_music(settings)
                        settings_loop(screen, screen_width, screen_height, settings)

        # ── Draw background (solid dark)
        screen.fill(DARK_BG)

        # ── Title (centered at top)
        title = font_title.render("PING  PONG", True, NEON_CYAN)
        tx = screen_width // 2 - title.get_width() // 2
        screen.blit(title, (tx, 40))

        # ── Buttons
        for i, btn in enumerate(buttons):
            btn.update(i == selected, dt)
            btn.draw(screen, i == selected)

        # ── Hint
        hint = font_hint.render("↑ ↓  вибір     ENTER  старт", True, (80, 80, 120))
        screen.blit(hint, (screen_width // 2 - hint.get_width() // 2,
                           screen_height - 30))

        pygame.display.flip()


def play_menu_music(settings):
    if settings.music_enabled:
        try:
            pygame.mixer.music.set_volume(settings.volume)
            pygame.mixer.music.load('sounds/menu.mp3')
            pygame.mixer.music.play(-1)
        except:
            pass


def stop_music():
    pygame.mixer.music.stop()


def start_menu(WIDTH, HEIGHT, screen, settings=None):
    if settings is None:
        settings = Settings()
    menu_loop(WIDTH, HEIGHT, screen, settings)
    return settings
