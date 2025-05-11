import pygame
import random
import time
from queue import Queue, PriorityQueue
from collections import deque
import math

pygame.init()

WIDTH, HEIGHT = 800, 600
CELL_SIZE = 20
GRID_WIDTH = 35
GRID_HEIGHT = 25
DELAY = 0.05

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
PINK = (255, 192, 203)
DARK_GRAY = (50, 50, 50)
LIGHT_GRAY = (220, 220, 220)
BACKGROUND = (240, 240, 245)

TEAMS = {
    "Dijkstra": (220, 50, 50),
    "A*": (50, 180, 50),
    "BFS": (50, 50, 220), 
    "DFS": (220, 180, 50)
}

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Algorithm Maze Race")
font = pygame.font.SysFont("Arial", 16)
big_font = pygame.font.SysFont("Arial", 24, bold=True)
title_font = pygame.font.SysFont("Arial", 32, bold=True)


grid_info = {}

def generate_maze():
    maze = [[1 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    
    def carve_passages(x, y):
        maze[y][x] = 0
        
        directions = [(2, 0), (0, 2), (-2, 0), (0, -2)]
        random.shuffle(directions)
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            
            if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT and maze[ny][nx] == 1:
                maze[y + dy//2][x + dx//2] = 0
                carve_passages(nx, ny)
    
    start_x = random.randrange(0, GRID_WIDTH, 2)
    start_y = random.randrange(0, GRID_HEIGHT, 2)
    if start_x >= GRID_WIDTH: start_x = GRID_WIDTH - 1
    if start_y >= GRID_HEIGHT: start_y = GRID_HEIGHT - 1
    
    carve_passages(start_x, start_y)
    
    maze[1][1] = 0
    maze[GRID_HEIGHT-2][GRID_WIDTH-2] = 0
    
    for _ in range(GRID_WIDTH * GRID_HEIGHT // 10):
        x = random.randint(1, GRID_WIDTH - 2)
        y = random.randint(1, GRID_HEIGHT - 2)
        maze[y][x] = 0

    
    global grid_info
    grid_info = {}
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            grid_info[(x, y)] = {
                'visitors': [],          
                'in_path': [],           
                'visit_times': {}        
            }
    
    return maze

class Pathfinder:
    def __init__(self, maze, start, end, name, color):
        self.maze = maze
        self.start = start
        self.end = end
        self.name = name
        self.color = color
        self.path = []
        self.visited = set()
        self.recently_visited = []
        self.finished = False
        self.finish_time = 0
        self.steps = 0
        self.current_pos = start
        self.came_from = {}
        self.trail_max_length = 10
        self.pulse_timer = 0
        self.algorithm_time = 0  

    def is_valid(self, pos):
        x, y = pos
        return (0 <= x < GRID_WIDTH and 
                0 <= y < GRID_HEIGHT and 
                self.maze[y][x] == 0 and 
                pos not in self.visited)

    def get_neighbors(self, pos):
        x, y = pos
        neighbors = []
        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
            nx, ny = x + dx, y + dy
            new_pos = (nx, ny)
            if self.is_valid(new_pos):
                neighbors.append(new_pos)
        return neighbors

    def heuristic(self, pos):
        return abs(pos[0] - self.end[0]) + abs(pos[1] - self.end[1])

    def update(self):
        if self.finished:
            return
        
        self.steps += 1
        self.algorithm_time += 1
        self.algorithm_step()
        
        if self.current_pos not in self.recently_visited and self.current_pos is not None:
            self.recently_visited.append(self.current_pos)
            if len(self.recently_visited) > self.trail_max_length:
                self.recently_visited.pop(0)
        
        if self.current_pos and self.current_pos not in self.visited:
            self.visited.add(self.current_pos)
            
            if self.current_pos not in grid_info:
                grid_info[self.current_pos] = {'visitors': [], 'in_path': [], 'visit_times': {}}
                
            if self.name not in grid_info[self.current_pos]['visitors']:
                grid_info[self.current_pos]['visitors'].append(self.name)
                grid_info[self.current_pos]['visit_times'][self.name] = self.algorithm_time
        
        if self.current_pos == self.end:
            self.finished = True
            self.finish_time = time.time()
            
            self.path = []
            current = self.end
            while current in self.came_from:
                self.path.append(current)
                current = self.came_from[current]
            self.path.append(self.start)
            self.path.reverse()
            
            
            for pos in self.path:
                if pos not in grid_info:
                    grid_info[pos] = {'visitors': [], 'in_path': [], 'visit_times': {}}
                if self.name not in grid_info[pos]['in_path']:
                    grid_info[pos]['in_path'].append(self.name)
        
        self.pulse_timer = (self.pulse_timer + 0.1) % (2 * math.pi)

    def draw(self, screen):
        
        
        
        if not self.finished:
            pulse = (math.sin(self.pulse_timer) + 1) / 2
            
            
            if self.current_pos:
                x, y = self.current_pos
                bright_color = (
                    min(255, int(self.color[0] + (255 - self.color[0]) * pulse * 0.7)),
                    min(255, int(self.color[1] + (255 - self.color[1]) * pulse * 0.7)),
                    min(255, int(self.color[2] + (255 - self.color[2]) * pulse * 0.7))
                )
                
                glow_size = int(CELL_SIZE * (1 + pulse * 0.5))
                glow_rect = pygame.Rect(
                    x * CELL_SIZE + CELL_SIZE//2 - glow_size//2,
                    y * CELL_SIZE + CELL_SIZE//2 - glow_size//2,
                    glow_size, glow_size
                )
                glow_surface = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
                
                glow_color = (*self.color, int(100 * (1 - pulse)))
                pygame.draw.rect(glow_surface, glow_color, (0, 0, glow_size, glow_size), border_radius=glow_size//3)
                screen.blit(glow_surface, glow_rect)

class DijkstraPathfinder(Pathfinder):
    def __init__(self, maze, start, end, name, color):
        super().__init__(maze, start, end, name, color)
        self.queue = PriorityQueue()
        self.queue.put((0, start))
        self.distance = {start: 0}
        self.came_from = {}

    def algorithm_step(self):
        if self.queue.empty():
            return
        
        current_distance, current = self.queue.get()
        
        if current == self.end:
            self.current_pos = current
            return
        
        if current in self.visited:
            return
        
        self.current_pos = current
        
        for neighbor in self.get_neighbors(current):
            new_distance = self.distance[current] + 1
            
            if neighbor not in self.distance or new_distance < self.distance[neighbor]:
                self.distance[neighbor] = new_distance
                self.came_from[neighbor] = current
                self.queue.put((new_distance, neighbor))

class AStarPathfinder(Pathfinder):
    def __init__(self, maze, start, end, name, color):
        super().__init__(maze, start, end, name, color)
        self.queue = PriorityQueue()
        self.queue.put((self.heuristic(start), 0, start))
        self.g_score = {start: 0}
        self.came_from = {}

    def algorithm_step(self):
        if self.queue.empty():
            return
        
        _, current_g, current = self.queue.get()
        
        if current == self.end:
            self.current_pos = current
            return
        
        if current in self.visited:
            return
        
        self.current_pos = current
        
        for neighbor in self.get_neighbors(current):
            tentative_g = self.g_score[current] + 1
            
            if neighbor not in self.g_score or tentative_g < self.g_score[neighbor]:
                self.came_from[neighbor] = current
                self.g_score[neighbor] = tentative_g
                f_score = tentative_g + self.heuristic(neighbor)
                self.queue.put((f_score, tentative_g, neighbor))

class BFSPathfinder(Pathfinder):
    def __init__(self, maze, start, end, name, color):
        super().__init__(maze, start, end, name, color)
        self.queue = deque([start])
        self.visited.add(start)
        self.came_from = {}

    def algorithm_step(self):
        if not self.queue:
            return
        
        current = self.queue.popleft()
        self.current_pos = current
        
        if current == self.end:
            return
        
        for neighbor in self.get_neighbors(current):
            if neighbor not in self.visited:
                self.queue.append(neighbor)
                self.visited.add(neighbor)
                self.came_from[neighbor] = current

class DFSPathfinder(Pathfinder):
    def __init__(self, maze, start, end, name, color):
        super().__init__(maze, start, end, name, color)
        self.stack = [start]
        self.came_from = {}

    def algorithm_step(self):
        if not self.stack:
            return
        
        current = self.stack.pop()
        
        if current in self.visited:
            return
        
        self.current_pos = current
        
        if current == self.end:
            return
        
        for neighbor in self.get_neighbors(current):
            if neighbor not in self.visited:
                self.stack.append(neighbor)
                self.came_from[neighbor] = current

def draw_maze(screen, maze):
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            if maze[y][x] == 1:
                pygame.draw.rect(screen, DARK_GRAY, rect)
                pygame.draw.rect(screen, BLACK, rect, 1)
            else:
                pygame.draw.rect(screen, WHITE, rect)
                pygame.draw.rect(screen, LIGHT_GRAY, rect, 1)

def draw_grid_cells(screen, pathfinders):
    
    for pos, info in grid_info.items():
        if not info['visitors']:
            continue
            
        x, y = pos
        cell_rect = pygame.Rect(x * CELL_SIZE + 1, y * CELL_SIZE + 1, CELL_SIZE - 2, CELL_SIZE - 2)

        
        if len(info['visitors']) > 1:
            
            sorted_visitors = sorted(info['visitors'], key=lambda n: info['visit_times'].get(n, 0))
            
            
            segment_width = (CELL_SIZE - 2) / len(sorted_visitors)
            for i, name in enumerate(sorted_visitors):
                team_color = None
                for p in pathfinders:
                    if p.name == name:
                        team_color = p.color
                        break
                
                if team_color:
                    segment_rect = pygame.Rect(
                        x * CELL_SIZE + 1 + i * segment_width, 
                        y * CELL_SIZE + 1, 
                        segment_width, 
                        CELL_SIZE - 2
                    )
                    
                    
                    fade_color = (
                        int(team_color[0] * 0.8),
                        int(team_color[1] * 0.8),
                        int(team_color[2] * 0.8)
                    )
                    pygame.draw.rect(screen, fade_color, segment_rect)
        else:
            
            team_name = info['visitors'][0]
            team_color = None
            for p in pathfinders:
                if p.name == team_name:
                    team_color = p.color
                    break
                    
            if team_color:
                fade_color = (
                    int(team_color[0] * 0.7),
                    int(team_color[1] * 0.7),
                    int(team_color[2] * 0.7)
                )
                pygame.draw.rect(screen, fade_color, cell_rect)

    
    
    for pathfinder in pathfinders:
        if pathfinder.finished and pathfinder.path:
            path_width = max(3, CELL_SIZE // 4)
            
            for i in range(len(pathfinder.path) - 1):
                x1, y1 = pathfinder.path[i]
                x2, y2 = pathfinder.path[i + 1]
                
                start_pos = (
                    x1 * CELL_SIZE + CELL_SIZE // 2,
                    y1 * CELL_SIZE + CELL_SIZE // 2
                )
                end_pos = (
                    x2 * CELL_SIZE + CELL_SIZE // 2,
                    y2 * CELL_SIZE + CELL_SIZE // 2
                )
                
                pygame.draw.line(screen, pathfinder.color, start_pos, end_pos, path_width)
                
                
                pygame.draw.circle(screen, pathfinder.color, start_pos, path_width // 2 + 1)
                pygame.draw.circle(screen, pathfinder.color, end_pos, path_width // 2 + 1)

def draw_leaderboard(screen, pathfinders):
    leaderboard = sorted(pathfinders, key=lambda p: (not p.finished, p.finish_time if p.finished else float('inf')))
    
    panel_width, panel_height = 180, 170
    panel_x, panel_y = WIDTH - panel_width - 10, 10
    
    panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    pygame.draw.rect(panel_surface, (255, 255, 255, 220), (0, 0, panel_width, panel_height), border_radius=10)
    pygame.draw.rect(panel_surface, (100, 100, 100, 100), (0, 0, panel_width, panel_height), 2, border_radius=10)
    screen.blit(panel_surface, (panel_x, panel_y))
    
    title = big_font.render("LEADERBOARD", True, DARK_GRAY)
    title_shadow = big_font.render("LEADERBOARD", True, (200, 200, 200))
    screen.blit(title_shadow, (panel_x + 21, panel_y + 16))
    screen.blit(title, (panel_x + 20, panel_y + 15))
    
    for i, pathfinder in enumerate(leaderboard):
        rank = i + 1
        color_rect = pygame.Rect(panel_x + 15, panel_y + 50 + i * 25, 15, 15)
        pygame.draw.rect(screen, pathfinder.color, color_rect, border_radius=3)
        
        if pathfinder.finished:
            text = f"{rank}. {pathfinder.name} - {pathfinder.steps} steps"
        else:
            text = f"   {pathfinder.name} - Running..."
        
        text_surface = font.render(text, True, DARK_GRAY)
        screen.blit(text_surface, (panel_x + 40, panel_y + 48 + i * 25))

def draw_start_end(screen, start, end):
    start_x, start_y = start
    end_x, end_y = end
    
    start_color = (20, 200, 95)
    end_color = (200, 50, 50)
    
    pulse = (math.sin(time.time() * 3) + 1) / 2
    
    for pos, color in [(start, start_color), (end, end_color)]:
        x, y = pos
        
        glow_size = int(CELL_SIZE * (1.5 + pulse * 0.5))
        glow_rect = pygame.Rect(
            x * CELL_SIZE + CELL_SIZE//2 - glow_size//2,
            y * CELL_SIZE + CELL_SIZE//2 - glow_size//2,
            glow_size, glow_size
        )
        glow_surface = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        
        glow_alpha = int(100 * (1 - pulse * 0.5))
        glow_color = (*color, glow_alpha)
        pygame.draw.rect(glow_surface, glow_color, (0, 0, glow_size, glow_size), border_radius=glow_size//2)
        screen.blit(glow_surface, glow_rect)
        
        inner_rect = pygame.Rect(
            x * CELL_SIZE + 2, 
            y * CELL_SIZE + 2, 
            CELL_SIZE - 4, 
            CELL_SIZE - 4
        )
        pygame.draw.rect(screen, color, inner_rect, border_radius=4)

def draw_title(screen):
    
    title_width = 190
    title_height = 50
    title_x = WIDTH - title_width - 10
    title_y = HEIGHT - title_height - 50
    
    title_bg = pygame.Surface((title_width, title_height), pygame.SRCALPHA)
    pygame.draw.rect(title_bg, (255, 255, 255, 200), (0, 0, title_width, title_height), border_radius=10)
    screen.blit(title_bg, (title_x, title_y))
    
    title = title_font.render("MAZE RACE", True, DARK_GRAY)
    screen.blit(title, (title_x + 10, title_y + 8))

def draw_instructions(screen):
    instr_bg = pygame.Surface((250, 30), pygame.SRCALPHA)
    pygame.draw.rect(instr_bg, (255, 255, 255, 200), (0, 0, 250, 30), border_radius=8)
    
    
    instr_x = WIDTH - 260
    instr_y = HEIGHT - 40
    
    screen.blit(instr_bg, (instr_x, instr_y))
    
    instr = font.render("Press 'R' to generate a new maze", True, DARK_GRAY)
    screen.blit(instr, (instr_x + 10, instr_y + 5))

def main():
    maze = generate_maze()
    
    start = (1, 1)
    end = (GRID_WIDTH - 2, GRID_HEIGHT - 2)
    
    pathfinders = [
        DijkstraPathfinder(maze, start, end, "Dijkstra", TEAMS["Dijkstra"]),
        AStarPathfinder(maze, start, end, "A*", TEAMS["A*"]),
        BFSPathfinder(maze, start, end, "BFS", TEAMS["BFS"]),
        DFSPathfinder(maze, start, end, "DFS", TEAMS["DFS"])
    ]
    
    running = True
    clock = pygame.time.Clock()
    last_update = time.time()
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    main()
                    return
        
        current_time = time.time()
        if current_time - last_update > DELAY:
            for pathfinder in pathfinders:
                pathfinder.update()
            last_update = current_time
        
        screen.fill(BACKGROUND)
        draw_maze(screen, maze)
        draw_grid_cells(screen, pathfinders)
        
        for pathfinder in pathfinders:
            pathfinder.draw(screen)
        
        draw_start_end(screen, start, end)
        draw_title(screen)
        draw_leaderboard(screen, pathfinders)
        draw_instructions(screen)
        
        all_finished = all(p.finished for p in pathfinders)
        
        pygame.display.flip()
        clock.tick(60)
        
        if all_finished:
            time.sleep(3)

if __name__ == "__main__":
    main()
    pygame.quit()