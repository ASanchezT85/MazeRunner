import pygame
import random
import time

CELL_WALL = 1
CELL_PATH = 0
CELL_GLADER = 2
CELL_GRIEVER_ZONE = 3
CELL_OUTER_WALL = 4
CELL_GLADER_GATE = 5
CELL_GLADER_WALL = 6
CELL_EXIT_GATE = 7

class Config:
    MAZE_WIDTH = 25
    MAZE_HEIGHT = 25
    CELL_SIZE = 30
    MOVE_DELAY = 8
    GATE_CHANGE_TIME = 300
    GATE_CHANGE_PROBABILITY = 0.6
    GLADER_GATE_COUNT = 4
    MAZE_CHANGE_TIME = 500
    MAZE_CHANGE_PROBABILITY = 0.3

class Difficulty:
    EASY = {"gate_change_time": 400, "move_delay": 6, "maze_change_time": 600, "maze_change_probability": 0.2}
    MEDIUM = {"gate_change_time": 300, "move_delay": 8, "maze_change_time": 500, "maze_change_probability": 0.3}
    HARD = {"gate_change_time": 200, "move_delay": 10, "maze_change_time": 400, "maze_change_probability": 0.4}

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
        self.update_appearance()
        self.rect = self.image.get_rect(topleft=(x * cell_size, y * cell_size))
    
    def update_appearance(self):
        color = self.open_color if self.is_open else self.closed_color
        self.image.fill(color)
        pygame.draw.rect(self.image, (30, 30, 30), (0, 0, self.cell_size, self.cell_size), 1)
    
    def toggle(self):
        self.is_open = not self.is_open
        self.update_appearance()
        return self.is_open

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
        
        if self.victory:
            self.image.fill((0, 255, 0))
        else:
            self.image.fill((220, 60, 60))

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
        self.maze_change_timer = 0
        
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

    def generate_full_maze(self):
        self.maze = [[CELL_WALL for _ in range(self.width)] for _ in range(self.height)]
        
        self._create_outer_walls()
        self._create_glade()
        self._create_blue_wall_around_glade()
        self._define_valid_gate_positions()
        self._place_random_gates()
        self._generate_outer_maze()
        self._place_random_exit_gates()

    def _create_sprite_groups(self):
        # Limpiar todos los grupos de sprites
        self.wall_sprites.empty()
        self.gate_sprites.empty()
        self.exit_sprites.empty()
        self.path_sprites.empty()
        self.all_sprites.empty()
        
        # Crear sprites para cada celda del laberinto
        for y in range(self.height):
            for x in range(self.width):
                cell = self.maze[y][x]
                if cell in [CELL_WALL, CELL_OUTER_WALL, CELL_GLADER_WALL]:
                    sprite = WallSprite(x, y, self.cell_size, self.colors['wall'])
                    self.wall_sprites.add(sprite)
                    self.all_sprites.add(sprite)
                elif cell == CELL_GLADER_GATE:
                    is_open = self.glader_gates.get((x, y), False)
                    sprite = GateSprite(x, y, self.cell_size, 
                                      self.colors['glader_gate_open'],
                                      self.colors['glader_gate_closed'],
                                      is_open)
                    self.gate_sprites.add(sprite)
                    self.all_sprites.add(sprite)
                elif cell == CELL_EXIT_GATE:
                    sprite = ExitGateSprite(x, y, self.cell_size, self.colors['exit_gate'])
                    self.exit_sprites.add(sprite)
                    self.all_sprites.add(sprite)
                elif cell == CELL_GLADER:
                    sprite = WallSprite(x, y, self.cell_size, self.colors['glader'])
                    self.all_sprites.add(sprite)
                elif cell == CELL_PATH:
                    sprite = PathSprite(x, y, self.cell_size, self.colors['path'])
                    self.path_sprites.add(sprite)
                    self.all_sprites.add(sprite)

    def _create_outer_walls(self):
        for i in range(self.width):
            self.maze[0][i] = CELL_OUTER_WALL
            self.maze[self.height-1][i] = CELL_OUTER_WALL
        for i in range(self.height):
            self.maze[i][0] = CELL_OUTER_WALL
            self.maze[i][self.width-1] = CELL_OUTER_WALL

    def _create_glade(self):
        center_x, center_y = self.width // 2, self.height // 2
        for y in range(center_y-1, center_y+2):
            for x in range(center_x-1, center_x+2):
                if self._is_valid_coord(x, y):
                    self.maze[y][x] = CELL_GLADER

    def _create_blue_wall_around_glade(self):
        center_x, center_y = self.width // 2, self.height // 2
        for y in range(center_y-2, center_y+3):
            for x in range(center_x-2, center_x+3):
                if self._is_valid_coord(x, y):
                    if (y == center_y-2 or y == center_y+2 or 
                        x == center_x-2 or x == center_x+2):
                        if self.maze[y][x] != CELL_OUTER_WALL:
                            self.maze[y][x] = CELL_GLADER_WALL

    def _define_valid_gate_positions(self):
        center_x, center_y = self.width // 2, self.height // 2
        self.possible_gate_positions = []
        
        for x in range(center_x-1, center_x+2):
            self.possible_gate_positions.append((x, center_y-2))
        
        for x in range(center_x-1, center_x+2):
            self.possible_gate_positions.append((x, center_y+2))
        
        for y in range(center_y-1, center_y+2):
            self.possible_gate_positions.append((center_x-2, y))
        
        for y in range(center_y-1, center_y+2):
            self.possible_gate_positions.append((center_x+2, y))

    def _place_random_gates(self):
        self.glader_gates = {}
        
        if len(self.possible_gate_positions) < Config.GLADER_GATE_COUNT:
            chosen_positions = self.possible_gate_positions.copy()
        else:
            chosen_positions = random.sample(
                self.possible_gate_positions, 
                Config.GLADER_GATE_COUNT
            )
        
        for x, y in chosen_positions:
            if self._is_valid_coord(x, y):
                initial_state = random.choice([True, False])
                self.glader_gates[(x, y)] = initial_state
                self.maze[y][x] = CELL_GLADER_GATE

    def _generate_outer_maze(self):
        self._generate_with_depth_first()
        self._connect_glader_gates()

    def _generate_with_depth_first(self):
        stack = []
        
        for (px, py) in self.glader_gates.keys():
            start_x, start_y = self._get_gate_outer_position(px, py)
            if start_x is not None and self._is_valid_coord(start_x, start_y):
                if self.maze[start_y][start_x] == CELL_WALL:
                    self.maze[start_y][start_x] = CELL_PATH
                    stack.append((start_x, start_y))
        
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
        if px < self.width // 2:
            return px-1, py
        elif px > self.width // 2:
            return px+1, py
        elif py < self.height // 2:
            return px, py-1
        elif py > self.height // 2:
            return px, py+1
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
        
        for direction, positions in possible_positions.items():
            if positions:
                x, y = random.choice(positions)
                self.exit_gates[(x, y)] = True
                self.maze[y][x] = CELL_EXIT_GATE

    def _replace_exit_gates(self):
        for (x, y) in self.exit_gates.keys():
            if self._is_valid_coord(x, y):
                self.maze[y][x] = CELL_OUTER_WALL
        
        self.exit_gates.clear()
        self._place_random_exit_gates()
        self._create_sprite_groups()

    def _is_outer_area(self, x, y):
        center_x, center_y = self.width // 2, self.height // 2
        return (abs(x - center_x) >= 3 or abs(y - center_y) >= 3)

    def _is_valid_coord(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def _is_in_glade(self, x, y):
        center_x, center_y = self.width // 2, self.height // 2
        return (center_x-1 <= x <= center_x+1 and 
                center_y-1 <= y <= center_y+1)

    def update_player_state(self, x, y):
        new_state = self._is_in_glade(x, y)
        old_state = self.player_in_glade
        self.player_in_glade = new_state
        
        if old_state and not new_state:
            print("Player left the Glade! Maze will start changing.")
        elif not old_state and new_state:
            print("Player entered the Glade! Maze stabilizes.")
            
        return new_state

    def change_gate_states(self):
        if not self.player_in_glade:
            return
            
        changes = 0
        for sprite in self.gate_sprites:
            if random.random() > (1 - Config.GATE_CHANGE_PROBABILITY):
                sprite.toggle()
                x = sprite.rect.x // self.cell_size
                y = sprite.rect.y // self.cell_size
                self.glader_gates[(x, y)] = sprite.is_open
                changes += 1

    def change_exit_gates(self):
        if not self.player_in_glade:
            return
            
        self._replace_exit_gates()

    def change_maze_layout(self):
        if self.player_in_glade:
            return False
            
        changes = 0
        change_positions = []
        
        # Buscar celdas que pueden cambiar (solo en área exterior y que no sean especiales)
        for y in range(self.height):
            for x in range(self.width):
                if (self._is_outer_area(x, y) and 
                    self.maze[y][x] in [CELL_WALL, CELL_PATH] and
                    (x, y) not in self.exit_gates and
                    (x, y) not in self.glader_gates and
                    random.random() < self.difficulty["maze_change_probability"]):
                    
                    change_positions.append((x, y))
        
        # Aplicar cambios
        for x, y in change_positions:
            if self.maze[y][x] == CELL_WALL:
                self.maze[y][x] = CELL_PATH
            else:
                self.maze[y][x] = CELL_WALL
            changes += 1
        
        # Solo recrear los sprites si hubo cambios
        if changes > 0:
            self._create_sprite_groups()  # ¡Esta línea es crucial!
            print(f"Maze changed! {changes} cells modified")
            return True
            
        return False

    def check_exit(self, x, y):
        if (x, y) in self.exit_gates:
            self.exit_found = True
            return True
        return False

class MazeRunnerGame:
    def __init__(self, difficulty="MEDIUM"):
        if not pygame.get_init():
            pygame.init()
            
        self.difficulty = difficulty
        self.maze = MazeRunnerMaze(difficulty)
        self.screen_width = self.maze.width * self.maze.cell_size
        self.screen_height = self.maze.height * self.maze.cell_size
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption(f"Maze Runner - {difficulty} Difficulty")
        
        self.clock = pygame.time.Clock()
        self.running = True
        self.day_time = 0
        self.victory = False
        
        self.player_sprite = PlayerSprite(self.maze.width // 2, self.maze.height // 2, self.maze.cell_size)
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.maze.all_sprites)
        self.all_sprites.add(self.player_sprite)
        
        self.timer_glader_gates = 0
        self.timer_exit_gates = 0
        self.timer_maze_changes = 0
        
        self.sound_enabled = False
        self.init_sound()
        
        try:
            self.font = pygame.font.Font(None, 24)
            self.font_large = pygame.font.Font(None, 48)
        except:
            self.font = pygame.font.SysFont('Arial', 24)
            self.font_large = pygame.font.SysFont('Arial', 48)
        
        self.move_timer = 0
        self.move_delay = self.maze.difficulty["move_delay"]
        self.gate_change_time = self.maze.difficulty["gate_change_time"]
        self.maze_change_time = self.maze.difficulty["maze_change_time"]

    def init_sound(self):
        try:
            pygame.mixer.init()
            self.sound_enabled = True
        except:
            self.sound_enabled = False

    def play_sound(self, sound_type):
        if not self.sound_enabled:
            return

    def draw_game(self):
        self.screen.fill(self.maze.colors['background'])
        self.all_sprites.draw(self.screen)
        self._draw_ui()

    def _draw_ui(self):
        open_gates = sum(1 for sprite in self.maze.gate_sprites if sprite.is_open)
        glade_state = "IN THE GLADE" if self.maze.player_in_glade else "OUTSIDE - MAZE CHANGING!"
        info_text = f"Open gates: {open_gates}/{Config.GLADER_GATE_COUNT} | {glade_state}"
        instructions = "Arrows/WASD: Move | R: Restart | 1-3: Difficulty | ESC: Quit"
        
        if self.victory:
            victory_text = "VICTORY! You have escaped the maze"
            text_surface = self.font_large.render(victory_text, True, (0, 255, 0))
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
            
            instructions_surface = self.font.render(instructions, True, (200, 200, 200))
            self.screen.blit(instructions_surface, (10, self.screen_height - 30))
        except Exception as e:
            print(f"UI drawing error: {e}")

    def handle_movement(self, keys):
        if self.move_timer > 0 or self.victory:
            self.move_timer -= 1
            return
            
        current_x = self.player_sprite.grid_x
        current_y = self.player_sprite.grid_y
        new_x, new_y = current_x, current_y
        moved = False
        
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            new_y -= 1
            moved = True
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            new_y += 1
            moved = True
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            new_x -= 1
            moved = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            new_x += 1
            moved = True
        
        if moved and self._is_valid_move(new_x, new_y):
            self.player_sprite.update_position(new_x, new_y)
            self.move_timer = self.move_delay
            self.play_sound("move")
            
            self.maze.update_player_state(new_x, new_y)
            
            if self.maze.check_exit(new_x, new_y):
                self.victory = True
                self.player_sprite.victory = True
                self.play_sound("victory")

    def _is_valid_move(self, x, y):
        if not self.maze._is_valid_coord(x, y):
            return False
        
        cell = self.maze.maze[y][x]
        
        blocked_cells = {
            CELL_WALL, 
            CELL_OUTER_WALL, 
            CELL_GLADER_WALL
        }
        
        if cell in blocked_cells:
            return False
        
        if cell == CELL_GLADER_GATE:
            return self.maze.glader_gates.get((x, y), False)
        
        return True

    def update_time(self):
        self.day_time += 1
        
        if self.maze.player_in_glade and not self.victory:
            self.timer_glader_gates += 1
            if self.timer_glader_gates >= self.gate_change_time:
                self.maze.change_gate_states()
                self.timer_glader_gates = 0
                self.play_sound("gate")
            
            self.timer_exit_gates += 1
            if self.timer_exit_gates >= self.gate_change_time * 2:
                self.maze.change_exit_gates()
                self.timer_exit_gates = 0
                self.play_sound("gate")
        else:
            self.timer_maze_changes += 1
            if self.timer_maze_changes >= self.maze_change_time and not self.victory:
                if self.maze.change_maze_layout():
                    # Actualizar el grupo all_sprites después de los cambios del laberinto
                    self.all_sprites.empty()
                    self.all_sprites.add(self.maze.all_sprites)
                    self.all_sprites.add(self.player_sprite)
                    self.play_sound("maze_change")
                self.timer_maze_changes = 0

    def change_difficulty(self, difficulty):
        self.difficulty = difficulty
        self.restart_game()

    def restart_game(self):
        try:
            self.maze = MazeRunnerMaze(self.difficulty)
            self.player_sprite = PlayerSprite(self.maze.width // 2, self.maze.height // 2, self.maze.cell_size)
            self.all_sprites = pygame.sprite.Group()
            self.all_sprites.add(self.maze.all_sprites)
            self.all_sprites.add(self.player_sprite)
            self.victory = False
            self.day_time = 0
            self.timer_glader_gates = 0
            self.timer_exit_gates = 0
            self.timer_maze_changes = 0
            self.move_delay = self.maze.difficulty["move_delay"]
            self.gate_change_time = self.maze.difficulty["gate_change_time"]
            self.maze_change_time = self.maze.difficulty["maze_change_time"]
        except Exception as e:
            print(f"Restart error: {e}")

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_r and not self.victory:
                        self.restart_game()
                    elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3] and not self.victory:
                        difficulties = {pygame.K_1: "EASY", pygame.K_2: "MEDIUM", pygame.K_3: "HARD"}
                        self.change_difficulty(difficulties[event.key])
            
            keys = pygame.key.get_pressed()
            self.handle_movement(keys)
            self.update_time()
            self.player_sprite.update_animation()
            self.draw_game()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()

if __name__ == "__main__":
    try:
        game = MazeRunnerGame()
        game.run()
    except Exception as e:
        print(f"Critical error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")