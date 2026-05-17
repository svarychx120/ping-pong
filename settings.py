import pygame

# ── Palette ──────────────────────────────────────────────────────────────────
NEON_CYAN   = (0,   255, 240)
NEON_PINK   = (255,  20, 147)
NEON_ORANGE = (255, 140,   0)
DARK_BG     = (6,    4,  20)
WHITE       = (255, 255, 255)
DIM_WHITE   = (160, 160, 190)


class Settings:
    def __init__(self):
        self.music_enabled = True
        self.volume = 0.5
        self.host = "localhost"
        self.port = "8081"


# ── Music helpers ─────────────────────────────────────────────────────────────
def toggle_music(settings):
    settings.music_enabled = not settings.music_enabled
    if settings.music_enabled:
        pygame.mixer.music.set_volume(settings.volume)
        pygame.mixer.music.play(-1)
    else:
        pygame.mixer.music.stop()


# ── Settings loop ─────────────────────────────────────────────────────────────
def settings_loop(screen, screen_width, screen_height, settings: Settings):
    def load_font(size, bold=False):
        for name in ["fonts/Orbitron-Bold.ttf", "fonts/orbitron.ttf"]:
            try:
                return pygame.font.Font(name, size)
            except:
                pass
        return pygame.font.SysFont("Arial", size, bold=bold)

    font_title = load_font(40, bold=True)
    font_item  = load_font(26, bold=True)
    font_hint  = load_font(16)

    try:
        choice_snd = pygame.mixer.Sound('sounds/Menu Choice.mp3')
    except:
        choice_snd = None

    clock_obj = pygame.time.Clock()

    while True:
        dt = clock_obj.tick(60) / 1000.0

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); exit()
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN:
                    toggle_music(settings)
                    if choice_snd: choice_snd.play()
                elif ev.key == pygame.K_ESCAPE:
                    return

        # ── Draw
        screen.fill(DARK_BG)

        # Title
        title_surf = font_title.render("НАЛАШТУВАННЯ", True, NEON_CYAN)
        tx = screen_width // 2 - title_surf.get_width() // 2
        screen.blit(title_surf, (tx, 60))

        # Music toggle box
        box_w, box_h = 300, 80
        box_x = screen_width // 2 - box_w // 2
        box_y = screen_height // 2 - box_h // 2
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)

        # Box background
        pygame.draw.rect(screen, (20, 15, 40), box_rect, border_radius=8)
        # Box border
        pygame.draw.rect(screen, NEON_PINK, box_rect, width=2, border_radius=8)

        # Music label
        music_label = font_item.render("Музика", True, NEON_PINK)
        screen.blit(music_label, (box_x + 20, box_y + 15))

        # Status text
        status_text = "ВКЛ" if settings.music_enabled else "ВИМКЛ"
        status_surf = font_item.render(status_text, True, NEON_CYAN)
        screen.blit(status_surf, (box_x + box_w - status_surf.get_width() - 20, box_y + 15))

        # Hint
        hint = font_hint.render("ENTER  перемикання     ESC  назад", True, (80, 80, 120))
        screen.blit(hint, (screen_width // 2 - hint.get_width() // 2,
                           screen_height - 40))

        pygame.display.flip()

