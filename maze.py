import pygame  # Importa la librería pygame para gráficos y entrada de usuario
import random  # Importa la librería random para operaciones aleatorias
import time    # Importa la librería time para manejo de tiempo

# Constantes para los tipos de celdas del laberinto
CELL_WALL = 1           # Celda de muro
CELL_PATH = 0           # Celda de camino
CELL_GLADER = 2         # Celda del claro central (Glade)
CELL_GRIEVER_ZONE = 3   # Celda de zona de Griever (enemigo)
CELL_OUTER_WALL = 4     # Celda de muro exterior azul
CELL_GLADER_GATE = 5    # Celda de puerta del Glade
CELL_GLADER_WALL = 6    # Celda de muro azul alrededor del Glade
CELL_EXIT_GATE = 7      # Celda de puerta de salida (victoria)

class Config:
    """Configuración centralizada del juego"""
    MAZE_WIDTH = 25              # Ancho del laberinto en celdas
    MAZE_HEIGHT = 25             # Alto del laberinto en celdas
    CELL_SIZE = 30               # Tamaño de cada celda en píxeles
    MOVE_DELAY = 8               # Retardo de movimiento del jugador
    GATE_CHANGE_TIME = 300       # Tiempo para cambiar el estado de las puertas
    GATE_CHANGE_PROBABILITY = 0.6 # Probabilidad de que una puerta cambie de estado
    GLADER_GATE_COUNT = 4        # Número de puertas alrededor del Glade

class MazeRunnerMaze:
    def __init__(self):
        self.width = Config.MAZE_WIDTH  # Ancho del laberinto
        self.height = Config.MAZE_HEIGHT  # Alto del laberinto
        self.cell_size = Config.CELL_SIZE  # Tamaño de celda
        self.maze = None  # Matriz del laberinto
        self.glader_gates = {}  # Diccionario de puertas del Glade y su estado (abierta/cerrada)
        self.exit_gates = {}    # Diccionario de puertas de salida
        self.exit_found = False  # Indica si se encontró la salida
        self.possible_gate_positions = []  # Lista de posiciones válidas para puertas del Glade
        self.player_in_glade = True  # Indica si el jugador está en el Glade
        
        # Diccionario de colores para cada tipo de celda
        self.colors = {
            'wall': (40, 40, 60),                # Color de muro
            'path': (180, 180, 200),             # Color de camino
            'glader': (80, 140, 80),             # Verde para el Glade 3x3
            'glader_gate_open': (80, 200, 80),   # Verde claro para puerta abierta
            'glader_gate_closed': (40, 40, 60),  # Azul oscuro para puerta cerrada
            'exit_gate': (255, 215, 0),          # Dorado para puertas de salida
            'griever_zone': (120, 80, 60),       # Color para zona de Griever
            'outer_wall': (40, 40, 60),          # Azul para muros exteriores
            'glader_wall': (40, 40, 60),         # Azul para muros alrededor del Glade
            'background': (15, 15, 25)           # Color de fondo
        }
        
        self.generate_full_maze()  # Genera el laberinto completo al inicializar
    
    def generate_full_maze(self):
        """Genera el laberinto según el diseño especificado"""
        self.maze = [[CELL_WALL for _ in range(self.width)] for _ in range(self.height)]  # Inicializa todo como muro
        
        self._create_outer_walls()            # 1. Crea los muros exteriores primero
        self._create_glade()                  # 2. Crea el Glade (3x3 en el centro)
        self._create_blue_wall_around_glade() # 3. Crea el muro azul alrededor del Glade (5x5)
        self._define_valid_gate_positions()   # 4. Define posiciones válidas para puertas (sin esquinas)
        self._place_random_gates()            # 5. Coloca puertas aleatorias en el muro azul
        self._generate_outer_maze()           # 6. Genera el laberinto exterior
        self._place_random_exit_gates()       # 7. Coloca puertas de salida aleatorias en los muros exteriores
        
        print("Maze generated: 3x3 Glade + Blue Wall + Valid Gates")  # Mensaje de depuración
    
    def _create_outer_walls(self):
        """Crea los muros exteriores azules primero"""
        for i in range(self.width):  # Recorre columnas
            self.maze[0][i] = CELL_OUTER_WALL  # Muro norte
            self.maze[self.height-1][i] = CELL_OUTER_WALL  # Muro sur
        for i in range(self.height):  # Recorre filas
            self.maze[i][0] = CELL_OUTER_WALL  # Muro oeste
            self.maze[i][self.width-1] = CELL_OUTER_WALL  # Muro este
    
    def _create_glade(self):
        """Crea el Glade 3x3 en el centro exacto"""
        center_x, center_y = self.width // 2, self.height // 2  # Calcula el centro
        
        for y in range(center_y-1, center_y+2):  # Recorre filas del Glade
            for x in range(center_x-1, center_x+2):  # Recorre columnas del Glade
                if self._is_valid_coord(x, y):  # Verifica que la coordenada sea válida
                    self.maze[y][x] = CELL_GLADER  # Asigna celda de Glade
    
    def _create_blue_wall_around_glade(self):
        """Crea un muro azul inmediato alrededor del Glade (5x5)"""
        center_x, center_y = self.width // 2, self.height // 2  # Centro del laberinto
        
        for y in range(center_y-2, center_y+3):  # Recorre filas del área 5x5
            for x in range(center_x-2, center_x+3):  # Recorre columnas del área 5x5
                if self._is_valid_coord(x, y):  # Verifica coordenada válida
                    # Solo coloca muro en el perímetro del 5x5
                    if (y == center_y-2 or y == center_y+2 or 
                        x == center_x-2 or x == center_x+2):
                        # No sobrescribe muros exteriores
                        if self.maze[y][x] != CELL_OUTER_WALL:
                            self.maze[y][x] = CELL_GLADER_WALL  # Asigna muro azul
    
    def _define_valid_gate_positions(self):
        """Define posiciones válidas para puertas (sin esquinas)"""
        center_x, center_y = self.width // 2, self.height // 2  # Centro
        
        self.possible_gate_positions = []  # Reinicia la lista
        
        # Norte (y = center_y-2), sin esquinas
        for x in range(center_x-1, center_x+2):
            self.possible_gate_positions.append((x, center_y-2))
        
        # Sur (y = center_y+2), sin esquinas
        for x in range(center_x-1, center_x+2):
            self.possible_gate_positions.append((x, center_y+2))
        
        # Oeste (x = center_x-2), sin esquinas
        for y in range(center_y-1, center_y+2):
            self.possible_gate_positions.append((center_x-2, y))
        
        # Este (x = center_x+2), sin esquinas
        for y in range(center_y-1, center_y+2):
            self.possible_gate_positions.append((center_x+2, y))
        
        print(f"Valid positions for gates: {len(self.possible_gate_positions)}")  # Muestra cuántas posiciones válidas hay
    
    def _place_random_gates(self):
        """Coloca puertas en posiciones válidas aleatorias (sin esquinas)"""
        self.glader_gates = {}  # Limpia puertas anteriores
        
        # Verifica si hay suficientes posiciones válidas
        if len(self.possible_gate_positions) < Config.GLADER_GATE_COUNT:
            print(f"Warning: Only {len(self.possible_gate_positions)} valid positions, using all available")
            chosen_positions = self.possible_gate_positions.copy()  # Usa todas las disponibles
        else:
            # Elige posiciones aleatorias distintas
            chosen_positions = random.sample(
                self.possible_gate_positions, 
                Config.GLADER_GATE_COUNT
            )
        
        for x, y in chosen_positions:  # Para cada posición elegida
            if self._is_valid_coord(x, y):  # Verifica coordenada válida
                initial_state = random.choice([True, False])  # Estado inicial aleatorio (abierta/cerrada)
                self.glader_gates[(x, y)] = initial_state  # Asigna estado a la puerta
                self.maze[y][x] = CELL_GLADER_GATE  # Marca la celda como puerta
        
        print(f"Gates placed in valid positions: {len(chosen_positions)}")  # Muestra cuántas puertas se colocaron
    
    def _generate_outer_maze(self):
        """Genera el laberinto fuera del área del Glade"""
        self._generate_with_depth_first()  # Usa algoritmo DFS para generar el laberinto
        self._connect_glader_gates()       # Asegura conexiones desde las puertas del Glade
    
    def _generate_with_depth_first(self):
        """Genera el laberinto usando búsqueda en profundidad (DFS)"""
        stack = []  # Pila para el algoritmo DFS
        
        # Puntos de inicio: las puertas del Glade
        for (px, py) in self.glader_gates.keys():
            start_x, start_y = self._get_gate_outer_position(px, py)  # Obtiene la posición exterior inmediata a la puerta
            if start_x is not None and self._is_valid_coord(start_x, start_y):
                if self.maze[start_y][start_x] == CELL_WALL:  # Si es muro
                    self.maze[start_y][start_x] = CELL_PATH   # Lo convierte en camino
                    stack.append((start_x, start_y))          # Lo agrega a la pila
        
        while stack:  # Mientras haya celdas en la pila
            x, y = stack[-1]  # Toma la celda actual
            
            neighbors = self._get_unvisited_neighbors(x, y)  # Busca vecinos no visitados
            
            if neighbors:  # Si hay vecinos disponibles
                dx, dy = random.choice(neighbors)  # Elige uno al azar
                self.maze[y + dy//2][x + dx//2] = CELL_PATH  # Elimina el muro intermedio
                self.maze[y + dy][x + dx] = CELL_PATH        # Marca el vecino como camino
                stack.append((x + dx, y + dy))               # Agrega el vecino a la pila
            else:
                stack.pop()  # Retrocede si no hay vecinos
    
    def _get_gate_outer_position(self, px, py):
        """Obtiene la posición exterior inmediata a una puerta"""
        if px < self.width // 2:      # Si la puerta está al oeste
            return px-1, py
        elif px > self.width // 2:    # Si la puerta está al este
            return px+1, py
        elif py < self.height // 2:   # Si la puerta está al norte
            return px, py-1
        elif py > self.height // 2:   # Si la puerta está al sur
            return px, py+1
        return None, None  # Si no es ninguna de las anteriores
    
    def _get_unvisited_neighbors(self, x, y):
        """Obtiene vecinos no visitados para el algoritmo DFS"""
        neighbors = []  # Lista de vecinos válidos
        for dx, dy in [(0, 2), (2, 0), (0, -2), (-2, 0)]:  # Solo movimientos rectos
            nx, ny = x + dx, y + dy  # Calcula la posición del vecino
            if (self._is_valid_coord(nx, ny) and 
                self.maze[ny][nx] == CELL_WALL and
                self._is_outer_area(nx, ny)):
                neighbors.append((dx, dy))  # Agrega vecino si es válido
        return neighbors  # Devuelve la lista de vecinos
    
    def _connect_glader_gates(self):
        """Asegura que las puertas del Glade estén conectadas al laberinto exterior"""
        for (px, py) in self.glader_gates.keys():  # Para cada puerta
            cx, cy = self._get_gate_outer_position(px, py)  # Obtiene la celda exterior
            if cx is not None and self._is_valid_coord(cx, cy):
                if self.maze[cy][cx] == CELL_WALL:  # Si es muro
                    self.maze[cy][cx] = CELL_PATH   # Lo convierte en camino
    
    def _place_random_exit_gates(self):
        """Coloca 4 puertas de salida en posiciones aleatorias de los muros exteriores"""
        self.exit_gates = {}  # Limpia puertas de salida anteriores
        
        # Define posiciones posibles para cada muro (sin esquinas)
        possible_positions = {
            'north': [(x, 0) for x in range(1, self.width-1)],
            'south': [(x, self.height-1) for x in range(1, self.width-1)],
            'west': [(0, y) for y in range(1, self.height-1)],
            'east': [(self.width-1, y) for y in range(1, self.height-1)]
        }
        
        # Elige una posición aleatoria para cada dirección
        for direction, positions in possible_positions.items():
            if positions:  # Si hay posiciones disponibles
                x, y = random.choice(positions)  # Elige una al azar
                self.exit_gates[(x, y)] = True   # Marca la puerta de salida
                self.maze[y][x] = CELL_EXIT_GATE # Sobrescribe el muro exterior con la puerta de salida
                print(f"Exit gate {direction} placed at: ({x}, {y})")  # Mensaje de depuración
    
    def _replace_exit_gates(self):
        """Recoloca las puertas de salida en nuevas posiciones aleatorias"""
        print("Re-placing exit gates!")  # Mensaje de depuración
        
        # Elimina las puertas de salida anteriores del laberinto
        for (x, y) in self.exit_gates.keys():
            if self._is_valid_coord(x, y):
                self.maze[y][x] = CELL_OUTER_WALL  # Restaura el muro exterior
        
        self._place_random_exit_gates()  # Coloca nuevas puertas de salida
    
    def _is_outer_area(self, x, y):
        """Verifica si la coordenada está fuera del área del Glade"""
        center_x, center_y = self.width // 2, self.height // 2  # Centro
        # Está fuera del área 5x5 del Glade y su muro
        return (abs(x - center_x) >= 3 or abs(y - center_y) >= 3)
    
    def _is_valid_coord(self, x, y):
        """Verifica si la coordenada está dentro de los límites del laberinto"""
        return 0 <= x < self.width and 0 <= y < self.height
    
    def _is_in_glade(self, x, y):
        """Verifica si el jugador está en el Glade (3x3 central)"""
        center_x, center_y = self.width // 2, self.height // 2  # Centro
        return (center_x-1 <= x <= center_x+1 and 
                center_y-1 <= y <= center_y+1)
    
    def update_player_state(self, x, y):
        """Actualiza el estado del jugador y gestiona cambios de puertas"""
        new_state = self._is_in_glade(x, y)  # Determina si el jugador está en el Glade
        
        if new_state and not self.player_in_glade:  # Si acaba de entrar al Glade
            print("Player entered the Glade! Gates will start changing.")
        elif not new_state and self.player_in_glade:  # Si acaba de salir del Glade
            print("Player left the Glade! Gates stabilize.")
        
        self.player_in_glade = new_state  # Actualiza el estado
        return new_state  # Devuelve el nuevo estado
    
    def change_gate_states(self):
        """Cambia el estado (abierta/cerrada) de las puertas solo si el jugador está en el Glade"""
        if not self.player_in_glade:
            return  # No cambia puertas si el jugador no está en el Glade
            
        print("Changing gate states!")  # Mensaje de depuración
        
        changes = 0  # Contador de cambios
        for pos in list(self.glader_gates.keys()):
            # Probabilidad configurable de cambiar el estado
            if random.random() > (1 - Config.GATE_CHANGE_PROBABILITY):
                self.glader_gates[pos] = not self.glader_gates[pos]  # Invierte el estado
                changes += 1  # Incrementa el contador
        
        if changes > 0:
            print(f"{changes} gates changed state!")  # Muestra cuántas puertas cambiaron
        else:
            print("Gates remain the same")  # No hubo cambios
    
    def change_exit_gates(self):
        """Cambia la posición de las puertas de salida solo si el jugador está en el Glade"""
        if not self.player_in_glade:
            return  # No cambia puertas de salida si el jugador no está en el Glade
            
        print("Changing exit gate positions!")  # Mensaje de depuración
        self._replace_exit_gates()  # Recoloca las puertas de salida
    
    def check_exit(self, x, y):
        """Verifica si el jugador llegó a una salida"""
        if (x, y) in self.exit_gates:  # Si la posición es una puerta de salida
            self.exit_found = True     # Marca que se encontró la salida
            return True                # Devuelve True
        return False                   # Si no, devuelve False

class MazeRunnerGame:
    def __init__(self):
        if not pygame.get_init():  # Si pygame no está inicializado
            pygame.init()          # Inicializa pygame
            
        self.maze = MazeRunnerMaze()  # Crea el laberinto
        self.screen_width = self.maze.width * self.maze.cell_size  # Calcula el ancho de la ventana
        self.screen_height = self.maze.height * self.maze.cell_size  # Calcula el alto de la ventana
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))  # Crea la ventana
        pygame.display.set_caption("Maze Runner - Blue Walls + Dynamic Gates")  # Título de la ventana
        
        self.clock = pygame.time.Clock()  # Reloj para controlar FPS
        self.running = True               # Bandera de ejecución del juego
        self.day_time = 0                 # Contador de tiempo/ciclos
        self.victory = False              # Indica si el jugador ganó
        
        self.maze_surface = None          # Superficie estática para optimización
        self.need_redraw_maze = True      # Bandera para redibujar el laberinto
        
        self.timer_glader_gates = 0       # Temporizador para puertas del Glade
        self.timer_exit_gates = 0         # Temporizador para puertas de salida
        
        try:
            self.font = pygame.font.Font(None, 24)        # Fuente para texto normal
            self.font_large = pygame.font.Font(None, 48)  # Fuente para texto grande
        except:
            self.font = pygame.font.SysFont('Arial', 24)        # Fuente alternativa
            self.font_large = pygame.font.SysFont('Arial', 48)  # Fuente alternativa grande
        
        self.player_x = self.maze.width // 2  # Posición inicial del jugador (centro)
        self.player_y = self.maze.height // 2
        
        self.move_timer = 0                   # Temporizador de movimiento
        self.move_delay = Config.MOVE_DELAY   # Retardo de movimiento
    
    def _create_maze_surface(self):
        """Crea la superficie estática del laberinto para optimización"""
        surface = pygame.Surface((self.screen_width, self.screen_height))  # Crea la superficie
        surface.fill(self.maze.colors['background'])  # Rellena con el color de fondo
        
        for y in range(self.maze.height):  # Recorre filas
            for x in range(self.maze.width):  # Recorre columnas
                rect = pygame.Rect(
                    x * self.maze.cell_size,
                    y * self.maze.cell_size,
                    self.maze.cell_size,
                    self.maze.cell_size
                )  # Define el rectángulo de la celda
                
                cell = self.maze.maze[y][x]  # Obtiene el tipo de celda
                color = self._get_cell_color(cell, x, y)  # Obtiene el color correspondiente
                pygame.draw.rect(surface, color, rect)    # Dibuja la celda
                pygame.draw.rect(surface, (30, 30, 30), rect, 1)  # Dibuja el borde de la celda
        
        return surface  # Devuelve la superficie generada
    
    def _get_cell_color(self, cell_type, x, y):
        """Obtiene el color para un tipo de celda"""
        if cell_type == CELL_WALL:
            return self.maze.colors['wall']
        elif cell_type == CELL_GLADER:
            return self.maze.colors['glader']
        elif cell_type == CELL_GRIEVER_ZONE:
            return self.maze.colors['griever_zone']
        elif cell_type == CELL_OUTER_WALL:
            return self.maze.colors['outer_wall']
        elif cell_type == CELL_GLADER_GATE:
            # Las puertas del Glade tienen color dinámico según su estado
            if self.maze.glader_gates.get((x, y), False):
                return self.maze.colors['glader_gate_open']
            else:
                return self.maze.colors['glader_gate_closed']
        elif cell_type == CELL_GLADER_WALL:
            return self.maze.colors['glader_wall']
        elif cell_type == CELL_EXIT_GATE:
            return self.maze.colors['exit_gate']
        else:  # Por defecto, camino
            return self.maze.colors['path']
    
    def draw_maze(self):
        """Dibuja el laberinto completo de forma optimizada"""
        if self.maze_surface is None or self.need_redraw_maze:  # Si no existe o necesita actualización
            self.maze_surface = self._create_maze_surface()      # Crea la superficie estática
            self.need_redraw_maze = False                        # Ya no necesita redibujar
        
        self.screen.blit(self.maze_surface, (0, 0))  # Dibuja la superficie estática
        
        self._draw_dynamic_gates()  # Dibuja las puertas dinámicas
        self._draw_player()         # Dibuja al jugador
        self._draw_ui()             # Dibuja la interfaz de usuario
    
    def _draw_dynamic_gates(self):
        """Dibuja las puertas que pueden cambiar de estado"""
        for (x, y), is_open in self.maze.glader_gates.items():  # Para cada puerta
            rect = pygame.Rect(
                x * self.maze.cell_size,
                y * self.maze.cell_size,
                self.maze.cell_size,
                self.maze.cell_size
            )  # Rectángulo de la puerta
            color = (self.maze.colors['glader_gate_open'] 
                    if is_open 
                    else self.maze.colors['glader_gate_closed'])  # Color según estado
            pygame.draw.rect(self.screen, color, rect)  # Dibuja la puerta
            pygame.draw.rect(self.screen, (30, 30, 30), rect, 1)  # Dibuja el borde
    
    def _draw_player(self):
        """Dibuja al jugador en la posición actual"""
        player_rect = pygame.Rect(
            self.player_x * self.maze.cell_size + 5,
            self.player_y * self.maze.cell_size + 5,
            self.maze.cell_size - 10,
            self.maze.cell_size - 10
        )  # Rectángulo del jugador (más pequeño que la celda)
        player_color = (0, 255, 0) if self.victory else (220, 60, 60)  # Verde si ganó, rojo si no
        pygame.draw.rect(self.screen, player_color, player_rect)  # Dibuja al jugador
    
    def _draw_ui(self):
        """Dibuja la interfaz de usuario"""
        open_gates = sum(1 for state in self.maze.glader_gates.values() if state)  # Cuenta puertas abiertas
        glade_state = "IN THE GLADE" if self.maze.player_in_glade else "OUTSIDE THE GLADE"  # Estado del jugador
        info_text = f"Open gates: {open_gates}/{Config.GLADER_GATE_COUNT} | {glade_state}"  # Texto informativo
        instructions = "Arrows/WASD: Move | R: Restart | ESC: Quit"  # Instrucciones
        
        if self.victory:  # Si el jugador ganó
            victory_text = "VICTORY! You have escaped the maze"  # Mensaje de victoria
            text_surface = self.font_large.render(victory_text, True, (0, 255, 0))  # Renderiza el texto
            text_rect = text_surface.get_rect(center=(self.screen_width//2, self.screen_height//2))  # Centra el texto
            self.screen.blit(text_surface, text_rect)  # Dibuja el texto
        
        try:
            text_surface = self.font.render(info_text, True, (255, 255, 255))  # Renderiza info
            self.screen.blit(text_surface, (10, 10))  # Dibuja info
            
            instructions_surface = self.font.render(instructions, True, (200, 200, 200))  # Renderiza instrucciones
            self.screen.blit(instructions_surface, (10, self.screen_height - 30))  # Dibuja instrucciones
        except Exception as e:
            print(f"Error drawing UI: {e}")  # Muestra error si ocurre
    
    def handle_movement(self, keys):
        """Gestiona el movimiento del jugador (solo recto)"""
        if self.move_timer > 0 or self.victory:  # Si está en retardo o ya ganó
            self.move_timer -= 1
            return
            
        new_x, new_y = self.player_x, self.player_y  # Posición tentativa
        moved = False  # Bandera de movimiento
        
        if keys[pygame.K_UP] or keys[pygame.K_w]:  # Arriba
            new_y -= 1
            moved = True
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:  # Abajo
            new_y += 1
            moved = True
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:  # Izquierda
            new_x -= 1
            moved = True
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:  # Derecha
            new_x += 1
            moved = True
        
        if moved and self._is_valid_move(new_x, new_y):  # Si se movió y es válido
            self.player_x, self.player_y = new_x, new_y  # Actualiza posición
            self.move_timer = self.move_delay            # Reinicia retardo
            
            self.maze.update_player_state(new_x, new_y)  # Actualiza estado del jugador
            
            if self.maze.check_exit(new_x, new_y):       # Si llegó a la salida
                self.victory = True
                print("VICTORY!!! You have found the exit of the maze")  # Mensaje de victoria
    
    def _is_valid_move(self, x, y):
        """Verifica si el movimiento es válido (solo vertical/horizontal)"""
        if not self.maze._is_valid_coord(x, y):  # Si está fuera de los límites
            return False
        
        cell = self.maze.maze[y][x]  # Tipo de celda destino
        
        blocked_cells = [CELL_WALL, CELL_OUTER_WALL, CELL_GLADER_WALL]  # Celdas bloqueadas
        if cell in blocked_cells:  # Si es una celda bloqueada
            return False
        
        if cell == CELL_GLADER_GATE:  # Si es una puerta del Glade
            return self.maze.glader_gates.get((x, y), False)  # Solo si está abierta
        
        return True  # Por defecto, movimiento permitido
    
    def update_time(self):
        """Actualiza el ciclo y cambia el estado de las puertas"""
        self.day_time += 1  # Incrementa el tiempo
        
        if self.maze.player_in_glade and not self.victory:  # Solo si el jugador está en el Glade y no ha ganado
            self.timer_glader_gates += 1  # Incrementa temporizador de puertas
            if self.timer_glader_gates >= Config.GATE_CHANGE_TIME:  # Si es tiempo de cambiar puertas
                self.maze.change_gate_states()  # Cambia el estado de las puertas
                self.timer_glader_gates = 0    # Reinicia temporizador
                self.need_redraw_maze = True   # Marca para redibujar
            
            self.timer_exit_gates += 1  # Incrementa temporizador de puertas de salida
            if self.timer_exit_gates >= Config.GATE_CHANGE_TIME * 2:  # Si es tiempo de cambiar puertas de salida
                self.maze.change_exit_gates()  # Cambia las puertas de salida
                self.timer_exit_gates = 0      # Reinicia temporizador
                self.need_redraw_maze = True   # Marca para redibujar
    
    def restart_game(self):
        """Reinicia el juego a su estado inicial"""
        try:
            self.maze = MazeRunnerMaze()  # Crea un nuevo laberinto
            self.player_x = self.maze.width // 2  # Posición inicial del jugador
            self.player_y = self.maze.height // 2
            self.victory = False           # Reinicia victoria
            self.day_time = 0              # Reinicia tiempo
            self.timer_glader_gates = 0    # Reinicia temporizador de puertas
            self.timer_exit_gates = 0      # Reinicia temporizador de puertas de salida
            self.need_redraw_maze = True   # Marca para redibujar
            print("Game restarted")        # Mensaje de depuración
        except Exception as e:
            print(f"Error restarting the game: {e}")  # Muestra error si ocurre
    
    def run(self):
        """Bucle principal del juego"""
        while self.running:  # Mientras el juego esté activo
            for event in pygame.event.get():  # Procesa eventos
                if event.type == pygame.QUIT:  # Si se cierra la ventana
                    self.running = False
                elif event.type == pygame.KEYDOWN:  # Si se presiona una tecla
                    if event.key == pygame.K_ESCAPE:  # Tecla ESC para salir
                        self.running = False
                    elif event.key == pygame.K_r and not self.victory:  # Tecla R para reiniciar
                        self.restart_game()
            
            keys = pygame.key.get_pressed()  # Obtiene el estado de las teclas
            self.handle_movement(keys)       # Gestiona el movimiento del jugador
            self.update_time()               # Actualiza el tiempo y puertas
            self.draw_maze()                 # Dibuja el laberinto y UI
            
            pygame.display.flip()            # Actualiza la pantalla
            self.clock.tick(60)              # Limita a 60 FPS
        
        pygame.quit()  # Sale de pygame al terminar el juego

if __name__ == "__main__":
    try:
        game = MazeRunnerGame()  # Crea el juego
        game.run()               # Ejecuta el bucle principal
    except Exception as e:
        print(f"Critical error: {e}")  # Muestra error crítico si ocurre
        import traceback
        traceback.print_exc()          # Imprime el traceback del error
        input("Press Enter to exit...")  # Espera entrada antes de salir