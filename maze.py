import pygame
import random
import time

# Constants for cell types
CELL_WALL = 1
CELL_PATH = 0
CELL_GLADER = 2
CELL_GRIEVER_ZONE = 3
CELL_OUTER_WALL = 4
CELL_GLADER_GATE = 5
CELL_GLADER_WALL = 6
CELL_EXIT_GATE = 7

class Config:
    """Centralized game configuration"""
    MAZE_WIDTH = 25
    MAZE_HEIGHT = 25
    CELL_SIZE = 30
    MOVE_DELAY = 8
    GATE_CHANGE_TIME = 300
    GATE_CHANGE_PROBABILITY = 0.6
    GLADER_GATE_COUNT = 4

class MazeRunnerMaze:
    def __init__(self):
        self.width = Config.MAZE_WIDTH
        self.height = Config.MAZE_HEIGHT
        self.cell_size = Config.CELL_SIZE
        self.maze = None
        self.glader_gates = {}  # Gates around the Glade
        self.exit_gates = {}    # Exit/victory gates
        self.exit_found = False
        self.possible_gate_positions = []  # Valid positions for gates
        self.player_in_glade = True  # Track if player is in the Glade
        
        # Updated colors
        self.colors = {
            'wall': (40, 40, 60),
            'path': (180, 180, 200),
            'glader': (80, 140, 80),  # Green for the 3x3 Glade
            'glader_gate_open': (80, 200, 80),
            'glader_gate_closed': (40, 40, 60),  # Red when closed
            'exit_gate': (255, 215, 0),  # Gold for exits
            'griever_zone': (120, 80, 60),
            'outer_wall': (40, 40, 60),  # Blue for outer walls
            'glader_wall': (40, 40, 60),  # Blue for walls around the Glade
            'background': (15, 15, 25)
        }
        
        self.generate_full_maze()
    
    def generate_full_maze(self):
        """Generates the maze according to the new design"""
        # Initialize everything as walls
        self.maze = [[CELL_WALL for _ in range(self.width)] for _ in range(self.height)]
        
        # 1. Create outer walls FIRST
        self._create_outer_walls()
        
        # 2. THE GLADE (3x3 in the center)
        self._create_glade()
        
        # 3. BLUE WALL around the Glade (5x5)
        self._create_blue_wall_around_glade()
        
        # 4. DEFINE valid positions for gates (no corners)
        self._define_valid_gate_positions()
        
        # 5. PLACE initial gates in the blue wall
        self._place_random_gates()
        
        # 6. GENERATE outer maze
        self._generate_outer_maze()
        
        # 7. EXIT GATES in the blue outer walls (RANDOM)
        self._place_random_exit_gates()
        
        print("Maze generated: 3x3 Glade + Blue Wall + Valid Gates")
    
    def _create_outer_walls(self):
        """Creates the BLUE outer walls first"""
        for i in range(self.width):
            self.maze[0][i] = CELL_OUTER_WALL  # North blue wall
            self.maze[self.height-1][i] = CELL_OUTER_WALL  # South blue wall
        for i in range(self.height):
            self.maze[i][0] = CELL_OUTER_WALL  # West blue wall
            self.maze[i][self.width-1] = CELL_OUTER_WALL  # East blue wall
    
    def _create_glade(self):
        """Creates the 3x3 Glade in the exact center"""
        center_x, center_y = self.width // 2, self.height // 2
        
        # Centered 3x3 Glade
        for y in range(center_y-1, center_y+2):
            for x in range(center_x-1, center_x+2):
                if self._is_valid_coord(x, y):
                    self.maze[y][x] = CELL_GLADER
    
    def _create_blue_wall_around_glade(self):
        """Creates an immediate BLUE wall around the Glade (5x5)"""
        center_x, center_y = self.width // 2, self.height // 2
        
        # Blue wall around the Glade (5x5)
        for y in range(center_y-2, center_y+3):
            for x in range(center_x-2, center_x+3):
                if self._is_valid_coord(x, y):
                    # Only put wall on the perimeter of the 5x5
                    if (y == center_y-2 or y == center_y+2 or 
                        x == center_x-2 or x == center_x+2):
                        # Don't overwrite outer walls
                        if self.maze[y][x] != CELL_OUTER_WALL:
                            self.maze[y][x] = CELL_GLADER_WALL
    
    def _define_valid_gate_positions(self):
        """Defines valid positions for gates (no corners)"""
        center_x, center_y = self.width // 2, self.height // 2
        
        self.possible_gate_positions = []
        
        # North (y = center_y-2) - exclude corners
        for x in range(center_x-1, center_x+2):  # Only center, no corners
            self.possible_gate_positions.append((x, center_y-2))
        
        # South (y = center_y+2) - exclude corners
        for x in range(center_x-1, center_x+2):  # Only center, no corners
            self.possible_gate_positions.append((x, center_y+2))
        
        # West (x = center_x-2) - exclude corners
        for y in range(center_y-1, center_y+2):  # Only center, no corners
            self.possible_gate_positions.append((center_x-2, y))
        
        # East (x = center_x+2) - exclude corners
        for y in range(center_y-1, center_y+2):  # Only center, no corners
            self.possible_gate_positions.append((center_x+2, y))
        
        print(f"Valid positions for gates: {len(self.possible_gate_positions)}")
    
    def _place_random_gates(self):
        """Places gates in RANDOM valid positions (no corners)"""
        # Clear previous gates
        self.glader_gates = {}
        
        # Check that there are enough valid positions
        if len(self.possible_gate_positions) < Config.GLADER_GATE_COUNT:
            print(f"Warning: Only {len(self.possible_gate_positions)} valid positions, using all available")
            chosen_positions = self.possible_gate_positions.copy()
        else:
            # Choose different random positions
            chosen_positions = random.sample(
                self.possible_gate_positions, 
                Config.GLADER_GATE_COUNT
            )
        
        for x, y in chosen_positions:
            if self._is_valid_coord(x, y):
                # Start some gates open, others closed
                initial_state = random.choice([True, False])
                self.glader_gates[(x, y)] = initial_state
                self.maze[y][x] = CELL_GLADER_GATE
        
        print(f"Gates placed in valid positions: {len(chosen_positions)}")
    
    def _generate_outer_maze(self):
        """Generates the maze outside the Glade area"""
        # Use maze algorithm
        self._generate_with_depth_first()
        
        # Ensure connections from Glade gates
        self._connect_glader_gates()
    
    def _generate_with_depth_first(self):
        """Generates maze using Depth-First Search"""
        stack = []
        
        # Start points from Glade gates
        for (px, py) in self.glader_gates.keys():
            start_x, start_y = self._get_gate_outer_position(px, py)
            if start_x is not None and self._is_valid_coord(start_x, start_y):
                if self.maze[start_y][start_x] == CELL_WALL:
                    self.maze[start_y][start_x] = CELL_PATH
                    stack.append((start_x, start_y))
        
        while stack:
            x, y = stack[-1]
            
            # Find unvisited neighbors (only straight moves)
            neighbors = self._get_unvisited_neighbors(x, y)
            
            if neighbors:
                dx, dy = random.choice(neighbors)
                # Remove wall between cells
                self.maze[y + dy//2][x + dx//2] = CELL_PATH
                self.maze[y + dy][x + dx] = CELL_PATH
                stack.append((x + dx, y + dy))
            else:
                stack.pop()
    
    def _get_gate_outer_position(self, px, py):
        """Gets the immediate outer position of a gate"""
        if px < self.width // 2:  # West
            return px-1, py
        elif px > self.width // 2:  # East
            return px+1, py
        elif py < self.height // 2:  # North
            return px, py-1
        elif py > self.height // 2:  # South
            return px, py+1
        return None, None
    
    def _get_unvisited_neighbors(self, x, y):
        """Gets unvisited neighbors for the DFS algorithm"""
        neighbors = []
        for dx, dy in [(0, 2), (2, 0), (0, -2), (-2, 0)]:  # Only vertical/horizontal
            nx, ny = x + dx, y + dy
            if (self._is_valid_coord(nx, ny) and 
                self.maze[ny][nx] == CELL_WALL and
                self._is_outer_area(nx, ny)):
                neighbors.append((dx, dy))
        return neighbors
    
    def _connect_glader_gates(self):
        """Ensures that Glade gates are connected to the outer maze"""
        for (px, py) in self.glader_gates.keys():
            cx, cy = self._get_gate_outer_position(px, py)
            if cx is not None and self._is_valid_coord(cx, cy):
                if self.maze[cy][cx] == CELL_WALL:
                    self.maze[cy][cx] = CELL_PATH
    
    def _place_random_exit_gates(self):
        """Places 4 exit/victory gates in RANDOM positions on the outer walls"""
        # Clear previous exit gates
        self.exit_gates = {}
        
        # Define possible positions for each wall (excluding corners)
        possible_positions = {
            'north': [(x, 0) for x in range(1, self.width-1)],
            'south': [(x, self.height-1) for x in range(1, self.width-1)],
            'west': [(0, y) for y in range(1, self.height-1)],
            'east': [(self.width-1, y) for y in range(1, self.height-1)]
        }
        
        # Choose a random position for each direction
        for direction, positions in possible_positions.items():
            if positions:  # Ensure there are available positions
                x, y = random.choice(positions)
                self.exit_gates[(x, y)] = True
                # IMPORTANT: Overwrite the outer wall with the exit gate
                self.maze[y][x] = CELL_EXIT_GATE
                print(f"Exit gate {direction} placed at: ({x}, {y})")
    
    def _replace_exit_gates(self):
        """Re-places the exit gates in new random positions"""
        print("Re-placing exit gates!")
        
        # Remove previous exit gates from the maze
        for (x, y) in self.exit_gates.keys():
            if self._is_valid_coord(x, y):
                self.maze[y][x] = CELL_OUTER_WALL
        
        # Place new exit gates in random positions
        self._place_random_exit_gates()
    
    def _is_outer_area(self, x, y):
        """Checks if the coordinate is outside the Glade area"""
        center_x, center_y = self.width // 2, self.height // 2
        # It's outside the 5x5 Glade + wall area
        return (abs(x - center_x) >= 3 or abs(y - center_y) >= 3)
    
    def _is_valid_coord(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height
    
    def _is_in_glade(self, x, y):
        """Checks if the player is in the Glade (central 3x3)"""
        center_x, center_y = self.width // 2, self.height // 2
        return (center_x-1 <= x <= center_x+1 and 
                center_y-1 <= y <= center_y+1)
    
    def update_player_state(self, x, y):
        """Updates the player's state and handles gate changes"""
        new_state = self._is_in_glade(x, y)
        
        # If the player just entered the Glade
        if new_state and not self.player_in_glade:
            print("Player entered the Glade! Gates will start changing.")
        
        # If the player just left the Glade
        elif not new_state and self.player_in_glade:
            print("Player left the Glade! Gates stabilize.")
        
        self.player_in_glade = new_state
        return new_state
    
    def change_gate_states(self):
        """Changes the STATE (open/closed) of existing gates ONLY if the player is in the Glade"""
        if not self.player_in_glade:
            return  # Don't change gates if player is not in the Glade
            
        print("Changing gate states!")
        
        changes = 0
        for pos in list(self.glader_gates.keys()):
            # Configurable probability to change state
            if random.random() > (1 - Config.GATE_CHANGE_PROBABILITY):
                self.glader_gates[pos] = not self.glader_gates[pos]
                changes += 1
        
        if changes > 0:
            print(f"{changes} gates changed state!")
        else:
            print("Gates remain the same")
    
    def change_exit_gates(self):
        """Changes the position of the exit gates ONLY if the player is in the Glade"""
        if not self.player_in_glade:
            return  # Don't change exit gates if player is not in the Glade
            
        print("Changing exit gate positions!")
        self._replace_exit_gates()
    
    def check_exit(self, x, y):
        """Checks if the player reached an exit"""
        if (x, y) in self.exit_gates:
            self.exit_found = True
            return True
        return False

class MazeRunnerGame:
    def __init__(self):
        if not pygame.get_init():
            pygame.init()
            
        self.maze = MazeRunnerMaze()
        self.screen_width = self.maze.width * self.maze.cell_size
        self.screen_height = self.maze.height * self.maze.cell_size
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Maze Runner - Blue Walls + Dynamic Gates")
        
        self.clock = pygame.time.Clock()
        self.running = True
        self.day_time = 0
        self.victory = False
        
        # Static surface for optimization
        self.maze_surface = None
        self.need_redraw_maze = True
        
        # Separate timers for different events
        self.timer_glader_gates = 0
        self.timer_exit_gates = 0
        
        try:
            self.font = pygame.font.Font(None, 24)
            self.font_large = pygame.font.Font(None, 48)
        except:
            self.font = pygame.font.SysFont('Arial', 24)
            self.font_large = pygame.font.SysFont('Arial', 48)
        
        # Player in the center of the Glade
        self.player_x = self.maze.width // 2
        self.player_y = self.maze.height // 2
        
        self.move_timer = 0
        self.move_delay = Config.MOVE_DELAY
    
    def _create_maze_surface(self):
        """Creates the static maze surface for optimization"""
        surface = pygame.Surface((self.screen_width, self.screen_height))
        surface.fill(self.maze.colors['background'])
        
        for y in range(self.maze.height):
            for x in range(self.maze.width):
                rect = pygame.Rect(
                    x * self.maze.cell_size,
                    y * self.maze.cell_size,
                    self.maze.cell_size,
                    self.maze.cell_size
                )
                
                cell = self.maze.maze[y][x]
                color = self._get_cell_color(cell, x, y)
                pygame.draw.rect(surface, color, rect)
                pygame.draw.rect(surface, (30, 30, 30), rect, 1)
        
        return surface
    
    def _get_cell_color(self, cell_type, x, y):
        """Gets the color for a cell type"""
        if cell_type == CELL_WALL:
            return self.maze.colors['wall']
        elif cell_type == CELL_GLADER:
            return self.maze.colors['glader']
        elif cell_type == CELL_GRIEVER_ZONE:
            return self.maze.colors['griever_zone']
        elif cell_type == CELL_OUTER_WALL:
            return self.maze.colors['outer_wall']
        elif cell_type == CELL_GLADER_GATE:
            # Glade gates have dynamic color depending on state
            if self.maze.glader_gates.get((x, y), False):
                return self.maze.colors['glader_gate_open']
            else:
                return self.maze.colors['glader_gate_closed']
        elif cell_type == CELL_GLADER_WALL:
            return self.maze.colors['glader_wall']
        elif cell_type == CELL_EXIT_GATE:
            return self.maze.colors['exit_gate']
        else:  # CELL_PATH
            return self.maze.colors['path']
    
    def draw_maze(self):
        """Draws the full maze in an optimized way"""
        # Create static surface if it doesn't exist or needs update
        if self.maze_surface is None or self.need_redraw_maze:
            self.maze_surface = self._create_maze_surface()
            self.need_redraw_maze = False
        
        # Draw static maze
        self.screen.blit(self.maze_surface, (0, 0))
        
        # Draw dynamic elements (gates that change)
        self._draw_dynamic_gates()
        
        # Draw player
        self._draw_player()
        
        # Draw user interface
        self._draw_ui()
    
    def _draw_dynamic_gates(self):
        """Draws the gates that can change state"""
        for (x, y), is_open in self.maze.glader_gates.items():
            rect = pygame.Rect(
                x * self.maze.cell_size,
                y * self.maze.cell_size,
                self.maze.cell_size,
                self.maze.cell_size
            )
            color = (self.maze.colors['glader_gate_open'] 
                    if is_open 
                    else self.maze.colors['glader_gate_closed'])
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, (30, 30, 30), rect, 1)
    
    def _draw_player(self):
        """Draws the player at the current position"""
        player_rect = pygame.Rect(
            self.player_x * self.maze.cell_size + 5,
            self.player_y * self.maze.cell_size + 5,
            self.maze.cell_size - 10,
            self.maze.cell_size - 10
        )
        player_color = (0, 255, 0) if self.victory else (220, 60, 60)
        pygame.draw.rect(self.screen, player_color, player_rect)
    
    def _draw_ui(self):
        """Draws the user interface"""
        open_gates = sum(1 for state in self.maze.glader_gates.values() if state)
        glade_state = "IN THE GLADE" if self.maze.player_in_glade else "OUTSIDE THE GLADE"
        info_text = f"Open gates: {open_gates}/{Config.GLADER_GATE_COUNT} | {glade_state}"
        instructions = "Arrows/WASD: Move | R: Restart | ESC: Quit"
        
        if self.victory:
            victory_text = "VICTORY! You have escaped the maze"
            text_surface = self.font_large.render(victory_text, True, (0, 255, 0))
            text_rect = text_surface.get_rect(center=(self.screen_width//2, self.screen_height//2))
            self.screen.blit(text_surface, text_rect)
        
        try:
            text_surface = self.font.render(info_text, True, (255, 255, 255))
            self.screen.blit(text_surface, (10, 10))
            
            instructions_surface = self.font.render(instructions, True, (200, 200, 200))
            self.screen.blit(instructions_surface, (10, self.screen_height - 30))
        except Exception as e:
            print(f"Error drawing UI: {e}")
    
    def handle_movement(self, keys):
        """Handles player movement (only straight)"""
        if self.move_timer > 0 or self.victory:
            self.move_timer -= 1
            return
            
        new_x, new_y = self.player_x, self.player_y
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
            self.player_x, self.player_y = new_x, new_y
            self.move_timer = self.move_delay
            
            # Update player state (if in the Glade or not)
            self.maze.update_player_state(new_x, new_y)
            
            # Check if reached an exit
            if self.maze.check_exit(new_x, new_y):
                self.victory = True
                print("VICTORY!!! You have found the exit of the maze")
    
    def _is_valid_move(self, x, y):
        """Checks if the move is valid (only vertical/horizontal)"""
        if not self.maze._is_valid_coord(x, y):
            return False
        
        cell = self.maze.maze[y][x]
        
        # Explicit list of blocked cells
        blocked_cells = [CELL_WALL, CELL_OUTER_WALL, CELL_GLADER_WALL]
        if cell in blocked_cells:
            return False
        
        # Glade gate requires open state
        if cell == CELL_GLADER_GATE:
            return self.maze.glader_gates.get((x, y), False)
        
        # Exit gates (7) CAN always be passed
        return True
    
    def update_time(self):
        """Updates the cycle and changes gate states"""
        self.day_time += 1
        
        # Only update gates if the player is in the Glade
        if self.maze.player_in_glade and not self.victory:
            # Change STATE of Glade gates every certain time
            self.timer_glader_gates += 1
            if self.timer_glader_gates >= Config.GATE_CHANGE_TIME:
                self.maze.change_gate_states()
                self.timer_glader_gates = 0
                self.need_redraw_maze = True
            
            # Change POSITION of exit gates less frequently
            self.timer_exit_gates += 1
            if self.timer_exit_gates >= Config.GATE_CHANGE_TIME * 2:  # Slower
                self.maze.change_exit_gates()
                self.timer_exit_gates = 0
                self.need_redraw_maze = True
    
    def restart_game(self):
        """Restarts the game to its initial state"""
        try:
            self.maze = MazeRunnerMaze()
            self.player_x = self.maze.width // 2
            self.player_y = self.maze.height // 2
            self.victory = False
            self.day_time = 0
            self.timer_glader_gates = 0
            self.timer_exit_gates = 0
            self.need_redraw_maze = True
            print("Game restarted")
        except Exception as e:
            print(f"Error restarting the game: {e}")
    
    def run(self):
        """Main game loop"""
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_r and not self.victory:
                        self.restart_game()
            
            keys = pygame.key.get_pressed()
            self.handle_movement(keys)
            self.update_time()
            self.draw_maze()
            
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