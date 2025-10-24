import pygame
import random
import time
from collections import deque

# ----- CELDAS / TIPOS -----
CELL_WALL = 1
CELL_PATH = 0
CELL_GLADER = 2
CELL_GRIEVER_ZONE = 3  # reservado/etiqueta
CELL_OUTER_WALL = 4
CELL_GLADER_GATE = 5
CELL_GLADER_WALL = 6
CELL_EXIT_GATE = 7

# ----- CONFIGURACIÓN BASE -----
class Config:
    MAZE_WIDTH = 25
    MAZE_HEIGHT = 25
    CELL_SIZE = 30
    GATE_CHANGE_PROBABILITY = 0.6
    GLADER_GATE_COUNT = 4
    DAY_LENGTH_MS = 20_000  # ciclo día/noche

# ----- DIFICULTADES -----
class Difficulty:
    EASY   = {
        "gate_change_time_ms": 4000,
        "move_delay_ms": 120,
        "maze_change_time_ms": 6000,
        "maze_change_probability": 0.20,
        "gate_change_probability": 0.50,
        "grievers": 1,
        "griever_step_ms": 260,
    }
    MEDIUM = {
        "gate_change_time_ms": 3000,
        "move_delay_ms": 140,
        "maze_change_time_ms": 5000,
        "maze_change_probability": 0.30,
        "gate_change_probability": 0.60,
        "grievers": 2,
        "griever_step_ms": 230,
    }
    HARD   = {
        "gate_change_time_ms": 2000,
        "move_delay_ms": 160,
        "maze_change_time_ms": 4000,
        "maze_change_probability": 0.40,
        "gate_change_probability": 0.70,
        "grievers": 3,
        "griever_step_ms": 200,
    }

# ----- SPRITES -----
class WallSprite(pygame.sprite.Sprite):
    def __init__(self, x, y, cell_size, color):
        super().__init__()
        self.image = pygame.Surface((cell_size, cell_size))
        self.image.fill(color)
        pygame.draw.rect(self.image, (30, 30, 30), (0, 0, cell_size, cell_size), 1)
        self.rect = self.image.get_rect(topleft=(x * cell_size, y * cell_size))
        self.grid_x = x
        self.grid_y = y
        self.type = "wall"

class GateSprite(pygame.sprite.Sprite):
    def __init__(self, x, y, cell_size, open_color, closed_color, is_open=True):
        super().__init__()
        self.cell_size = cell_size
        self.open_color = open_color
        self.closed_color = closed_color
        self.is_open = is_open
        self.type = "gate"
        self.grid_x = x
        self.grid_y = y
        self.image = pygame.Surface((cell_size, cell_size))
        self.rect = self.image.get_rect(topleft=(x * cell_size, y * cell_size))
        self.pulse_timer = 0
        self.update_appearance()

    def update_appearance(self):
        color = self.open_color if self.is_open else self.closed_color
        self.image.fill(color)
        pygame.draw.rect(self.image, (30, 30, 30), (0, 0, self.cell_size, self.cell_size), 1)

    def toggle(self):
        self.is_open = not self.is_open
        self.pulse_timer = 180
        self.update_appearance()
        return self.is_open

    def update(self, dt_ms: int):
        if self.pulse_timer > 0:
            self.pulse_timer -= dt_ms
            pygame.draw.rect(self.image, (255, 255, 255), (2, 2, self.cell_size - 4, self.cell_size - 4), 1)
        else:
            self.update_appearance()

class ExitGateSprite(pygame.sprite.Sprite):
    def __init__(self, x, y, cell_size, color):
        super().__init__()
        self.image = pygame.Surface((cell_size, cell_size))
        self.image.fill(color)
        pygame.draw.rect(self.image, (30, 30, 30), (0, 0, cell_size, cell_size), 1)
        self.rect = self.image.get_rect(topleft=(x * cell_size, y * cell_size))
        self.grid_x = x
        self.grid_y = y
        self.type = "exit"

class PathSprite(pygame.sprite.Sprite):
    def __init__(self, x, y, cell_size, color):
        super().__init__()
        self.image = pygame.Surface((cell_size, cell_size))
        self.image.fill(color)
        pygame.draw.rect(self.image, (30, 30, 30), (0, 0, cell_size, cell_size), 1)
        self.rect = self.image.get_rect(topleft=(x * cell_size, y * cell_size))
        self.grid_x = x
        self.grid_y = y
        self.type = "path"

class PlayerSprite(pygame.sprite.Sprite):
    def __init__(self, x, y, cell_size):
        super().__init__()
        self.cell_size = cell_size
        self.grid_x = x
        self.grid_y = y
        self.target_x = x * cell_size
        self.target_y = y * cell_size
        self.image = pygame.Surface((cell_size - 10, cell_size - 10))
        self.image.fill((220, 60, 60))
        self.rect = self.image.get_rect(center=(self.target_x + cell_size//2, self.target_y + cell_size//2))
        self.type = "player"
        self.victory = False

    def update_position(self, x, y):
        self.grid_x = x
        self.grid_y = y
        self.target_x = x * self.cell_size
        self.target_y = y * self.cell_size

    def update_animation(self):
        current_x, current_y = self.rect.center
        if abs(self.target_x + self.cell_size//2 - current_x) > 1 or abs(self.target_y + self.cell_size//2 - current_y) > 1:
            new_x = current_x + (self.target_x + self.cell_size//2 - current_x) * 0.3
            new_y = current_y + (self.target_y + self.cell_size//2 - current_y) * 0.3
            self.rect.center = (new_x, new_y)
        else:
            self.rect.center = (self.target_x + self.cell_size//2, self.target_y + self.cell_size//2)
        self.image.fill((0, 255, 0) if self.victory else (220, 60, 60))

class GrieverSprite(pygame.sprite.Sprite):
    def __init__(self, x, y, cell_size):
        super().__init__()
        self.cell_size = cell_size
        self.grid_x = x
        self.grid_y = y
        self.image = pygame.Surface((cell_size - 8, cell_size - 8))
        self.image.fill((240, 170, 40))
        self.rect = self.image.get_rect(center=(x*cell_size + cell_size//2, y*cell_size + cell_size//2))
        self.type = "griever"

    def update_position(self, x, y):
        self.grid_x = x
        self.grid_y = y
        self.rect.center = (x*self.cell_size + self.cell_size//2, y*self.cell_size + self.cell_size//2)

# ----- LABERINTO -----
class MazeRunnerMaze:
    def __init__(self, difficulty="MEDIUM"):
        self.width = Config.MAZE_WIDTH
        self.height = Config.MAZE_HEIGHT
        self.cell_size = Config.CELL_SIZE
        self.difficulty = getattr(Difficulty, difficulty)
        self.maze = None
        self.glader_gates = {}
        self.exit_gates = {}
        self.exit_found = False
        self.possible_gate_positions = []
        self.player_in_glade = True

        self.colors = {
            'wall': (40, 40, 60),
            'path': (180, 180, 200),
            'glader': (80, 140, 80),
            'glader_gate_open': (80, 200, 80),
            'glader_gate_closed': (40, 40, 60),
            'exit_gate': (255, 215, 0),
            'griever_zone': (120, 80, 60),
            'outer_wall': (40, 40, 60),
            'glader_wall': (40, 40, 60),
            'background': (15, 15, 25)
        }

        self.wall_sprites = pygame.sprite.Group()
        self.gate_sprites = pygame.sprite.Group()
        self.exit_sprites = pygame.sprite.Group()
        self.path_sprites = pygame.sprite.Group()
        self.all_sprites = pygame.sprite.Group()

        self.generate_full_maze()
        self._create_sprite_groups()

    # --- Generación inicial ---
    def generate_full_maze(self):
        self.maze = [[CELL_WALL for _ in range(self.width)] for _ in range(self.height)]
        self._create_outer_walls()
        self._create_glade()
        self._create_blue_wall_around_glade()
        self._define_valid_gate_positions()
        self._place_random_gates()
        self._generate_outer_maze()
        self._place_random_exit_gates()
        self._ensure_exit_connectivity()

    def _create_sprite_groups(self):
        self.wall_sprites.empty()
        self.gate_sprites.empty()
        self.exit_sprites.empty()
        self.path_sprites.empty()
        self.all_sprites.empty()

        for y in range(self.height):
            for x in range(self.width):
                cell = self.maze[y][x]
                if cell in [CELL_WALL, CELL_OUTER_WALL, CELL_GLADER_WALL]:
                    sprite = WallSprite(x, y, self.cell_size, self.colors['wall'])
                    self.wall_sprites.add(sprite); self.all_sprites.add(sprite)
                elif cell == CELL_GLADER_GATE:
                    is_open = self.glader_gates.get((x, y), False)
                    sprite = GateSprite(x, y, self.cell_size,
                                        self.colors['glader_gate_open'],
                                        self.colors['glader_gate_closed'],
                                        is_open)
                    self.gate_sprites.add(sprite); self.all_sprites.add(sprite)
                elif cell == CELL_EXIT_GATE:
                    sprite = ExitGateSprite(x, y, self.cell_size, self.colors['exit_gate'])
                    self.exit_sprites.add(sprite); self.all_sprites.add(sprite)
                elif cell == CELL_GLADER:
                    sprite = WallSprite(x, y, self.cell_size, self.colors['glader'])
                    self.all_sprites.add(sprite)
                elif cell == CELL_PATH:
                    sprite = PathSprite(x, y, self.cell_size, self.colors['path'])
                    self.path_sprites.add(sprite); self.all_sprites.add(sprite)

    def _create_outer_walls(self):
        for i in range(self.width):
            self.maze[0][i] = CELL_OUTER_WALL
            self.maze[self.height-1][i] = CELL_OUTER_WALL
        for i in range(self.height):
            self.maze[i][0] = CELL_OUTER_WALL
            self.maze[i][self.width-1] = CELL_OUTER_WALL

    def _create_glade(self):
        cx, cy = self.width // 2, self.height // 2
        for y in range(cy-1, cy+2):
            for x in range(cx-1, cx+2):
                if self._is_valid_coord(x, y):
                    self.maze[y][x] = CELL_GLADER

    def _create_blue_wall_around_glade(self):
        cx, cy = self.width // 2, self.height // 2
        for y in range(cy-2, cy+3):
            for x in range(cx-2, cx+3):
                if self._is_valid_coord(x, y):
                    if (y == cy-2 or y == cy+2 or x == cx-2 or x == cx+2):
                        if self.maze[y][x] != CELL_OUTER_WALL:
                            self.maze[y][x] = CELL_GLADER_WALL

    def _define_valid_gate_positions(self):
        cx, cy = self.width // 2, self.height // 2
        self.possible_gate_positions = []
        for x in range(cx-1, cx+2):
            self.possible_gate_positions.append((x, cy-2))
            self.possible_gate_positions.append((x, cy+2))
        for y in range(cy-1, cy+2):
            self.possible_gate_positions.append((cx-2, y))
            self.possible_gate_positions.append((cx+2, y))

    def _place_random_gates(self):
        self.glader_gates = {}
        if len(self.possible_gate_positions) < Config.GLADER_GATE_COUNT:
            chosen_positions = self.possible_gate_positions.copy()
        else:
            chosen_positions = random.sample(self.possible_gate_positions, Config.GLADER_GATE_COUNT)
        for x, y in chosen_positions:
            if self._is_valid_coord(x, y):
                self.glader_gates[(x, y)] = random.choice([True, False])
                self.maze[y][x] = CELL_GLADER_GATE

    def _generate_outer_maze(self):
        self._generate_with_depth_first()
        self._connect_glader_gates()

    def _generate_with_depth_first(self):
        stack = []
        for (px, py) in self.glader_gates.keys():
            sx, sy = self._get_gate_outer_position(px, py)
            if sx is not None and self._is_valid_coord(sx, sy):
                if self.maze[sy][sx] == CELL_WALL:
                    self.maze[sy][sx] = CELL_PATH
                    stack.append((sx, sy))
        while stack:
            x, y = stack[-1]
            neighbors = self._get_unvisited_neighbors(x, y)
            if neighbors:
                dx, dy = random.choice(neighbors)
                self.maze[y + dy//2][x + dx//2] = CELL_PATH
                self.maze[y + dy][x + dx] = CELL_PATH
                stack.append((x + dx, y + dy))
            else:
                stack.pop()

    def _get_gate_outer_position(self, px, py):
        cx, cy = self.width // 2, self.height // 2
        if px < cx: return px-1, py
        if px > cx: return px+1, py
        if py < cy: return px, py-1
        if py > cy: return px, py+1
        return None, None

    def _get_unvisited_neighbors(self, x, y):
        neighbors = []
        for dx, dy in [(0, 2), (2, 0), (0, -2), (-2, 0)]:
            nx, ny = x + dx, y + dy
            if (self._is_valid_coord(nx, ny) and
                self.maze[ny][nx] == CELL_WALL and
                self._is_outer_area(nx, ny)):
                neighbors.append((dx, dy))
        return neighbors

    def _connect_glader_gates(self):
        for (px, py) in self.glader_gates.keys():
            cx, cy = self._get_gate_outer_position(px, py)
            if cx is not None and self._is_valid_coord(cx, cy):
                if self.maze[cy][cx] == CELL_WALL:
                    self.maze[cy][cx] = CELL_PATH

    def _place_random_exit_gates(self):
        self.exit_gates = {}
        possible_positions = {
            'north': [(x, 0) for x in range(1, self.width-1)],
            'south': [(x, self.height-1) for x in range(1, self.width-1)],
            'west': [(0, y) for y in range(1, self.height-1)],
            'east': [(self.width-1, y) for y in range(1, self.height-1)]
        }
        for positions in possible_positions.values():
            if positions:
                x, y = random.choice(positions)
                self.exit_gates[(x, y)] = True
                self.maze[y][x] = CELL_EXIT_GATE

    def _ensure_exit_connectivity(self):
        q = deque(); seen = set()
        for x in range(self.width):
            for y in [1, self.height - 2]:
                if self.maze[y][x] == CELL_PATH:
                    q.append((x, y)); seen.add((x, y))
        for y in range(self.height):
            for x in [1, self.width - 2]:
                if self.maze[y][x] == CELL_PATH:
                    q.append((x, y)); seen.add((x, y))
        while q:
            x, y = q.popleft()
            for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                nx, ny = x + dx, y + dy
                if self._is_valid_coord(nx, ny) and (nx, ny) not in seen:
                    if self.maze[ny][nx] in (CELL_PATH, CELL_EXIT_GATE):
                        seen.add((nx, ny)); q.append((nx, ny))
        replaced = False
        for (ex, ey) in list(self.exit_gates.keys()):
            if (ex, ey) not in seen:
                if self._is_valid_coord(ex, ey):
                    self.maze[ey][ex] = CELL_OUTER_WALL
                del self.exit_gates[(ex, ey)]
                replaced = True
        if replaced or not self.exit_gates:
            self._place_random_exit_gates()

    # --- Utilidades de estado ---
    def _is_outer_area(self, x, y):
        cx, cy = self.width // 2, self.height // 2
        return (abs(x - cx) >= 3 or abs(y - cy) >= 3)

    def _is_valid_coord(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def _is_in_glade(self, x, y):
        cx, cy = self.width // 2, self.height // 2
        return (cx-1 <= x <= cx+1 and cy-1 <= y <= cy+1)

    def update_player_state(self, x, y):
        new_state = self._is_in_glade(x, y)
        old_state = self.player_in_glade
        self.player_in_glade = new_state
        if old_state and not new_state:
            print("Player left the Glade! Maze will start changing.")
        elif not old_state and new_state:
            print("Player entered the Glade! Maze stabilizes.")
        return new_state

    # --- Cambios dinámicos ---
    def change_gate_states(self, prob=None):
        if not self.player_in_glade:
            return
        if prob is None:
            prob = self.difficulty.get("gate_change_probability", Config.GATE_CHANGE_PROBABILITY)
        for sprite in self.gate_sprites:
            if random.random() < prob:
                sprite.toggle()
                x = sprite.rect.x // self.cell_size
                y = sprite.rect.y // self.cell_size
                self.glader_gates[(x, y)] = sprite.is_open

    def change_exit_gates(self):
        if not self.player_in_glade:
            return
        for (x, y) in self.exit_gates.keys():
            if self._is_valid_coord(x, y):
                self.maze[y][x] = CELL_OUTER_WALL
        self.exit_gates.clear()
        self._place_random_exit_gates()
        self._create_sprite_groups()

    def change_maze_layout(self):
        if self.player_in_glade:
            return False
        changes = 0
        prob = self.difficulty["maze_change_probability"]
        change_positions = []
        for y in range(self.height):
            for x in range(self.width):
                if (self._is_outer_area(x, y) and
                    self.maze[y][x] in [CELL_WALL, CELL_PATH] and
                    (x, y) not in self.exit_gates and
                    (x, y) not in self.glader_gates and
                    random.random() < prob):
                    change_positions.append((x, y))
        for x, y in change_positions:
            self.maze[y][x] = CELL_PATH if self.maze[y][x] == CELL_WALL else CELL_WALL
            changes += 1
        if changes > 0:
            self._create_sprite_groups()
            print(f"Maze changed! {changes} cells modified")
            return True
        return False

    def check_exit(self, x, y):
        # Victoria si estás sobre la salida
        if (x, y) in self.exit_gates:
            self.exit_found = True
            return True
        # ...o si estás en la casilla interior contigua a una salida en el borde
        if x == 1 and (0, y) in self.exit_gates: return True
        if x == self.width-2 and (self.width-1, y) in self.exit_gates: return True
        if y == 1 and (x, 0) in self.exit_gates: return True
        if y == self.height-2 and (x, self.height-1) in self.exit_gates: return True
        return False

# ----- JUEGO -----
class MazeRunnerGame:
    def __init__(self, difficulty="MEDIUM", seed: int | None = None):
        if not pygame.get_init():
            pygame.init()
        if seed is not None:
            random.seed(seed)

        self.difficulty = difficulty
        self.maze = MazeRunnerMaze(difficulty)
        self.screen_width = self.maze.width * self.maze.cell_size
        self.screen_height = self.maze.height * self.maze.cell_size
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption(f"Maze Runner - {difficulty} Difficulty")

        self.clock = pygame.time.Clock()
        self.running = True
        self.victory = False
        self.defeat = False

        self.player_sprite = PlayerSprite(self.maze.width // 2, self.maze.height // 2, self.maze.cell_size)
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.maze.all_sprites)
        self.all_sprites.add(self.player_sprite)

        # Grievers
        self.grievers = pygame.sprite.Group()
        self._spawn_grievers()

        # Timers en ms
        d = self.maze.difficulty
        self.gate_change_time_ms = d["gate_change_time_ms"]
        self.maze_change_time_ms = d["maze_change_time_ms"]
        self.move_delay_ms = d["move_delay_ms"]
        self.gate_change_probability = d.get("gate_change_probability", Config.GATE_CHANGE_PROBABILITY)

        self.timer_glader_gates_ms = 0
        self.timer_exit_gates_ms = 0
        self.timer_maze_changes_ms = 0
        self.move_cooldown_ms = 0
        self.day_time_ms = 0

        self.griever_step_ms = d["griever_step_ms"]
        self.griever_timer_ms = 0

        self.sound_enabled = False
        self.init_sound()

        try:
            self.font = pygame.font.Font(None, 24)
            self.font_large = pygame.font.Font(None, 48)
        except:
            self.font = pygame.font.SysFont('Arial', 24)
            self.font_large = pygame.font.SysFont('Arial', 48)

    def _spawn_grievers(self):
        count = self.maze.difficulty["grievers"]
        attempts = 0
        while len(self.grievers) < count and attempts < 500:
            attempts += 1
            x = random.randint(1, self.maze.width-2)
            y = random.randint(1, self.maze.height-2)
            if not self.maze._is_outer_area(x, y):  # sólo área exterior
                continue
            if self.maze.maze[y][x] != CELL_PATH:
                continue
            if abs(x - self.player_sprite.grid_x) + abs(y - self.player_sprite.grid_y) < 6:
                continue
            g = GrieverSprite(x, y, self.maze.cell_size)
            self.grievers.add(g)
            self.all_sprites.add(g)

    def init_sound(self):
        try:
            pygame.mixer.init()
            self.sound_enabled = True
        except:
            self.sound_enabled = False

    def play_sound(self, sound_type):
        if not self.sound_enabled:
            return

    # --- DIBUJADO ---
    def draw_game(self, dt_ms: int):
        self.screen.fill(self.maze.colors['background'])
        for g in self.maze.gate_sprites:
            g.update(dt_ms)
        self.all_sprites.draw(self.screen)
        self._draw_day_night_overlay()
        self._draw_ui()

    def _draw_day_night_overlay(self):
        phase = (self.day_time_ms % Config.DAY_LENGTH_MS) / Config.DAY_LENGTH_MS
        if phase <= 0.5:
            alpha = int(120 * (phase / 0.5))
        else:
            alpha = int(120 * (1 - (phase - 0.5) / 0.5))
        alpha = 120 - alpha
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, max(0, min(120, alpha))))
        self.screen.blit(overlay, (0, 0))

    def _draw_ui(self):
        open_gates = sum(1 for sprite in self.maze.gate_sprites if sprite.is_open)
        glade_state = "IN THE GLADE" if self.maze.player_in_glade else "OUTSIDE - MAZE CHANGING!"
        info_text = f"Open gates: {open_gates}/{Config.GLADER_GATE_COUNT} | {glade_state}"
        instructions = "Arrows/WASD: Move | R: Restart | 1-3: Difficulty | ESC: Quit | F: Seed"

        if self.victory:
            victory_text = "VICTORY! You escaped"
            text_surface = self.font_large.render(victory_text, True, (0, 255, 0))
            text_rect = text_surface.get_rect(center=(self.screen_width//2, self.screen_height//2))
            self.screen.blit(text_surface, text_rect)
        if self.defeat:
            defeat_text = "CAUGHT BY A GRIEVER!"
            text_surface = self.font_large.render(defeat_text, True, (255, 80, 80))
            text_rect = text_surface.get_rect(center=(self.screen_width//2, self.screen_height//2))
            self.screen.blit(text_surface, text_rect)

        try:
            text_surface = self.font.render(info_text, True, (255, 255, 255))
            self.screen.blit(text_surface, (10, 10))

            difficulty_text = f"Difficulty: {self.difficulty}"
            diff_surface = self.font.render(difficulty_text, True, (200, 200, 100))
            self.screen.blit(diff_surface, (10, 40))

            maze_state = "Maze: STABLE" if self.maze.player_in_glade else "Maze: CHANGING!"
            maze_surface = self.font.render(maze_state, True, (100, 200, 255) if self.maze.player_in_glade else (255, 100, 100))
            self.screen.blit(maze_surface, (10, 70))

            gate_in = max(0, (self.gate_change_time_ms - self.timer_glader_gates_ms) // 100) / 10
            exit_in = max(0, ((self.gate_change_time_ms * 2) - self.timer_exit_gates_ms) // 100) / 10
            maze_in = max(0, (self.maze_change_time_ms - self.timer_maze_changes_ms) // 100) / 10

            self.screen.blit(self.font.render(f"Gate change in: {gate_in:.1f}s", True, (180, 220, 255)), (10, 100))
            self.screen.blit(self.font.render(f"Exit relocate in: {exit_in:.1f}s", True, (220, 200, 150)), (10, 122))
            self.screen.blit(self.font.render(f"Next maze morph in: {maze_in:.1f}s (outside only)", True, (220, 160, 160)), (10, 144))

            self.screen.blit(self.font.render(instructions, True, (200, 200, 200)), (10, self.screen_height - 30))
        except Exception as e:
            print(f"UI drawing error: {e}")

    # --- INPUT / MOVIMIENTO ---
    def handle_movement(self, keys, dt_ms: int):
        if self.victory or self.defeat:
            return
        if self.move_cooldown_ms > 0:
            self.move_cooldown_ms -= dt_ms
            return

        cx = self.player_sprite.grid_x
        cy = self.player_sprite.grid_y
        nx, ny = cx, cy
        moved = False

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            ny -= 1; moved = True
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            ny += 1; moved = True
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            nx -= 1; moved = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            nx += 1; moved = True

        if moved and self._is_valid_move(nx, ny):
            self.player_sprite.update_position(nx, ny)
            self.move_cooldown_ms = self.move_delay_ms
            self.play_sound("move")

            self.maze.update_player_state(nx, ny)
            if self.maze.check_exit(nx, ny):
                self.victory = True
                self.player_sprite.victory = True
                self.play_sound("victory")

    def _is_valid_move(self, x, y):
        if not self.maze._is_valid_coord(x, y):
            return False
        cell = self.maze.maze[y][x]
        blocked_cells = {CELL_WALL, CELL_OUTER_WALL, CELL_GLADER_WALL}
        if cell in blocked_cells:
            return False
        if cell == CELL_GLADER_GATE:
            return self.maze.glader_gates.get((x, y), False)
        return True

    # --- TIEMPO / REGLAS ---
    def update_time(self, dt_ms: int):
        self.day_time_ms += dt_ms

        if self.maze.player_in_glade and not (self.victory or self.defeat):
            self.timer_glader_gates_ms += dt_ms
            if self.timer_glader_gates_ms >= self.gate_change_time_ms:
                self.maze.change_gate_states(self.gate_change_probability)
                self.timer_glader_gates_ms = 0
                self.play_sound("gate")

            self.timer_exit_gates_ms += dt_ms
            if self.timer_exit_gates_ms >= self.gate_change_time_ms * 2:
                self.maze.change_exit_gates()
                self.timer_exit_gates_ms = 0
                self.play_sound("gate")
        else:
            self.timer_maze_changes_ms += dt_ms
            if self.timer_maze_changes_ms >= self.maze_change_time_ms and not (self.victory or self.defeat):
                if self.maze.change_maze_layout():
                    self.all_sprites.empty()
                    self.all_sprites.add(self.maze.all_sprites)
                    self.all_sprites.add(self.player_sprite)
                    self.all_sprites.add(self.grievers)  # re-draw grievers
                    self.play_sound("maze_change")
                self.timer_maze_changes_ms = 0

        # Grievers: patrulla (idle) si estás en el Glade, persiguen si estás fuera
        self.griever_timer_ms += dt_ms
        if self.griever_timer_ms >= self.griever_step_ms and not (self.victory or self.defeat):
            self._update_grievers()
            self.griever_timer_ms = 0

    # --- GRIEVERS AI ---
    def _tile_is_passable_for_griever(self, x, y):
        if not self.maze._is_valid_coord(x, y):
            return False
        cell = self.maze.maze[y][x]
        if cell in (CELL_WALL, CELL_OUTER_WALL, CELL_GLADER_WALL):
            return False
        if cell == CELL_GLADER:  # no entran al Glade
            return False
        if cell == CELL_GLADER_GATE and not self.maze.glader_gates.get((x, y), False):
            return False
        return True  # PATH, open gates, EXIT ok

    def _next_step_bfs(self, start, goal):
        if start == goal:
            return start
        q = deque([start])
        parent = {start: None}
        while q:
            x, y = q.popleft()
            for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                nx, ny = x+dx, y+dy
                if (nx, ny) not in parent and self._tile_is_passable_for_griever(nx, ny):
                    parent[(nx, ny)] = (x, y)
                    if (nx, ny) == goal:
                        # reconstruir 1er paso
                        cur = (nx, ny)
                        while parent[cur] != start:
                            cur = parent[cur]
                        return cur
                    q.append((nx, ny))
        return start  # sin camino

    def _update_grievers(self):
        player_pos = (self.player_sprite.grid_x, self.player_sprite.grid_y)
        for g in self.grievers:
            if self.maze.player_in_glade:
                # patrulla simple: intenta moverse al azar dentro del área exterior
                dirs = [(1,0),(-1,0),(0,1),(0,-1)]
                random.shuffle(dirs)
                moved = False
                for dx, dy in dirs:
                    nx, ny = g.grid_x + dx, g.grid_y + dy
                    if self._tile_is_passable_for_griever(nx, ny) and self.maze._is_outer_area(nx, ny):
                        g.update_position(nx, ny); moved = True; break
                if not moved:
                    pass
            else:
                step = self._next_step_bfs((g.grid_x, g.grid_y), player_pos)
                g.update_position(step[0], step[1])

            # Colisión con jugador
            if (g.grid_x, g.grid_y) == player_pos and not self.victory:
                self.defeat = True

    def change_difficulty(self, difficulty):
        self.difficulty = difficulty
        self.restart_game()

    def restart_game(self, seed: int | None = None):
        try:
            if seed is not None:
                random.seed(seed)
            self.maze = MazeRunnerMaze(self.difficulty)
            self.player_sprite = PlayerSprite(self.maze.width // 2, self.maze.height // 2, self.maze.cell_size)
            self.all_sprites = pygame.sprite.Group()
            self.all_sprites.add(self.maze.all_sprites)
            self.all_sprites.add(self.player_sprite)
            self.victory = False
            self.defeat = False

            d = self.maze.difficulty
            self.gate_change_time_ms = d["gate_change_time_ms"]
            self.maze_change_time_ms = d["maze_change_time_ms"]
            self.move_delay_ms = d["move_delay_ms"]
            self.gate_change_probability = d.get("gate_change_probability", Config.GATE_CHANGE_PROBABILITY)

            self.timer_glader_gates_ms = 0
            self.timer_exit_gates_ms = 0
            self.timer_maze_changes_ms = 0
            self.move_cooldown_ms = 0
            self.day_time_ms = 0

            self.grievers.empty()
            self._spawn_grievers()
            self.all_sprites.add(self.grievers)
            self.griever_step_ms = d["griever_step_ms"]
            self.griever_timer_ms = 0
        except Exception as e:
            print(f"Restart error: {e}")

    # ----- LOOP PRINCIPAL -----
    def run(self):
        seed_to_apply = None
        while self.running:
            dt_ms = self.clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_r and not self.victory:
                        self.restart_game(seed_to_apply)
                    elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3] and not self.victory:
                        difficulties = {pygame.K_1: "EASY", pygame.K_2: "MEDIUM", pygame.K_3: "HARD"}
                        self.change_difficulty(difficulties[event.key])
                    elif event.key == pygame.K_f:
                        seed_to_apply = int(time.time())
                        print(f"[Seed] Using seed: {seed_to_apply}. Press R to restart with this seed.")

            keys = pygame.key.get_pressed()
            self.handle_movement(keys, dt_ms)
            self.update_time(dt_ms)
            self.player_sprite.update_animation()
            self.draw_game(dt_ms)
            pygame.display.flip()
        pygame.quit()

# ----- ENTRYPOINT -----
if __name__ == "__main__":
    try:
        # game = MazeRunnerGame(difficulty="MEDIUM", seed=12345)
        game = MazeRunnerGame(difficulty="MEDIUM")
        game.run()
    except Exception as e:
        print(f"Critical error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
