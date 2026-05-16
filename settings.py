from pygame import *

WHITE = (255, 255, 255)
PURPLE = (142, 36, 108)
BLUE = (85, 118, 201)
ORANGE = (225, 108, 68)
GRAY = (30, 30, 30)

class Settings:
    def __init__(self):
        self.music_enabled = True
        self.volume = 0.5
        self.host = "localhost"
        self.port = "8081"

# --- МУЗИЧНІ ФУНКЦІЇ ---
def apply_volume(settings):
    mixer.music.set_volume(settings.volume)

def toggle_music(settings):
    settings.music_enabled = not settings.music_enabled
    if settings.music_enabled:
        mixer.music.set_volume(settings.volume)
        mixer.music.play(-1)
    else:
        mixer.music.stop()

def increase_volume(settings):
    settings.volume = max(0, min(1, settings.volume + 0.05))
    apply_volume(settings)

def decrease_volume(settings):
    settings.volume = max(0, min(1, settings.volume - 0.05))
    apply_volume(settings)

class SettingsItem:
    def __init__(self, label, kind, rect, get_value, set_value=None, set_value_up=None, set_value_down=None):
        self.label = label
        self.kind = kind  # 'slider', 'toggle', 'text', 'action'
        self.rect = rect
        self.get_value = get_value
        self.set_value = set_value
        self.set_value_up = set_value_up
        self.set_value_down = set_value_down
        self.editing = False

    def draw(self, screen, font, selected):
        bg_color = ORANGE if selected else PURPLE if self.kind != 'slider' else BLUE
        draw.rect(screen, bg_color, self.rect,
                  border_top_left_radius=20 if self.label == "Гучність" else 0,
                  border_top_right_radius=20 if self.label == "Гучність" else 0,
                  border_bottom_left_radius=20 if self.label == "Назад" else 0,
                  border_bottom_right_radius=20 if self.label == "Назад" else 0)
        value = self.get_value()
        text = f"{self.label}: {value}" if self.kind != "toggle" else f"{self.label}: {'Так' if value else 'Ні'}"
        label_surface = font.render(text, True, WHITE)
        screen.blit(label_surface, label_surface.get_rect(center=self.rect.center))

def settings_loop(screen, screen_width, screen_height, settings: Settings):
    font_obj = font.SysFont("Arial", 36)
    gap = 10
    button_height = 70
    button_width = 500
    center_x = (screen_width - button_width) // 2
    total_height = 5 * button_height + 4 * gap
    start_y = (screen_height - total_height) // 2
    input_buffer = {"host": settings.host, "port": settings.port}
    editing_field = None
    # --- ЕЛЕМЕНТИ МЕНЮ ---
    items = [
        SettingsItem(
            "Гучність", "slider",
            Rect(center_x, start_y + 0 * (button_height + gap), button_width, button_height),
            get_value=lambda: f"{int(settings.volume * 100)}%",
            set_value_up=lambda: increase_volume(settings),
            set_value_down=lambda: decrease_volume(settings)
        ),
        SettingsItem(
            "Музика", "toggle",
            Rect(center_x, start_y + 1 * (button_height + gap), button_width, button_height),
            get_value=lambda: settings.music_enabled,
            set_value=lambda: toggle_music(settings)
        ),
        SettingsItem(
            "Host", "text",
            Rect(center_x, start_y + 2 * (button_height + gap), button_width, button_height),
            get_value=lambda: input_buffer["host"],
            set_value=None
        ),
        SettingsItem(
            "Port", "text",
            Rect(center_x, start_y + 3 * (button_height + gap), button_width, button_height),
            get_value=lambda: input_buffer["port"],
            set_value=None
        ),
        SettingsItem(
            "Назад", "action",
            Rect(center_x, start_y + 4 * (button_height + gap), button_width, button_height),
            get_value=lambda: "",
            set_value=None
        )
    ]
    selected = 0
    clock_obj = time.Clock()
    MENU_CHOICE_SOUND = mixer.Sound('sounds/Menu Choice.mp3')
    while True:
        screen.fill(GRAY)
        for ev in event.get():
            if ev.type == QUIT:
                quit()
                exit()
            elif ev.type == KEYDOWN:
                current = items[selected]
                if editing_field:
                    if ev.key == K_RETURN:
                        editing_field.editing = False
                        editing_field = None
                    elif ev.key == K_BACKSPACE:
                        buf = input_buffer[editing_field.label.lower()]
                        input_buffer[editing_field.label.lower()] = buf[:-1]
                    elif ev.unicode:
                        buf = input_buffer[editing_field.label.lower()]
                        input_buffer[editing_field.label.lower()] = buf + ev.unicode
                else:
                    if ev.key == K_DOWN:
                        selected = (selected + 1) % len(items)
                        MENU_CHOICE_SOUND.play()
                    elif ev.key == K_UP:
                        selected = (selected - 1) % len(items)
                        MENU_CHOICE_SOUND.play()
                    elif ev.key == K_LEFT and current.kind == "slider" and current.set_value_down:
                        current.set_value_down()
                        MENU_CHOICE_SOUND.play()
                    elif ev.key == K_RIGHT and current.kind == "slider" and current.set_value_up:
                        current.set_value_up()
                        MENU_CHOICE_SOUND.play()
                    elif ev.key == K_RETURN:
                        if current.kind == "toggle" and current.set_value:
                            current.set_value()
                        elif current.kind == "text":
                            current.editing = True
                            editing_field = current
                        elif current.label == "Назад":
                            settings.host = input_buffer["host"]
                            settings.port = input_buffer["port"]
                            return
        for i, item in enumerate(items):
            item.draw(screen, font_obj, selected == i or item.editing)
        display.flip()
        clock_obj.tick(60)
