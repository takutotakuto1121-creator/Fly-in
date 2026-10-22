import pygame
from src import Map, Zone, Parser, Connection, MAPF


class Visualizer:
    def __init__(self, map: Map, paths: list[list[tuple[int, int]]], max_turn: int) -> None:
        self.map = map
        self.max_turn = max_turn
        self.tab_size: tuple[int, int] = (1280, 80)
        self.screen_size: tuple[int, int] = (1280, 720)
        self.redefine_coordinates_and_get_unit()
        self.paths = self.redefine_paths(paths)
        self.circle_radius = self.define_circle_radius()
        self.running = True
        self.state = "map"
        self.turn_count = 0
        self.index = 0

    def redefine_coordinates_and_get_unit(self) -> None:
        x_screen, y_screen = self.screen_size

        hubs = [self.map.start_hub, self.map.end_hub] + self.map.hubs
        x_coordinates = [hub.coordinate[0] for hub in hubs]
        y_coordinates = [hub.coordinate[1] for hub in hubs]

        x_max, x_min = max(x_coordinates), min(x_coordinates)
        y_max, y_min = max(y_coordinates), min(y_coordinates)

        x_size = x_max - x_min + 2
        y_size = y_max - y_min + 2

        # 座標の1単位
        self.unit_x = x_screen / x_size
        self.unit_y = y_screen / y_size

        for hub in hubs:
            orig_x, orig_y = hub.coordinate
            new_x = (orig_x - x_min + 1) * self.unit_x
            new_y = (orig_y - y_min + 1) * self.unit_y
            hub.coordinate = (new_x, new_y)

    def redefine_paths(self, paths: list[list[str]]) -> list[list[tuple[int, int]]]:
        hubs = [self.map.start_hub, self.map.end_hub] + self.map.hubs
        hub_coords = {hub.name: hub.coordinate for hub in hubs}
        
        new_paths: list[list[tuple[int, int]]] = []
        for path in paths:
            new_path: list[tuple[int, int]] = []
            for hub in path:
                new_path.append(hub_coords[hub])
            new_paths.append(new_path)
        return new_paths

    def define_circle_radius(self) -> float:
        size = min([self.unit_x, self.unit_y])
        radius = size * 2 / 5
        return radius

    def draw_text_in_circle(self, hub, screen) -> None:
        length = max(1, len(hub.name))
        font_size = self.circle_radius / (length * 0.17)
        x_text = hub.coordinate[0] - self.circle_radius
        y_text = hub.coordinate[1] + self.circle_radius
        font = pygame.font.Font(None, int(font_size))
        text = font.render(hub.name, True, "black")
        screen.blit(text, (x_text, y_text))

    def get_zone_coordinate(self, connection: Connection) -> tuple[tuple[float, float], tuple[float, float]]:
        hubs = [self.map.start_hub, self.map.end_hub] + self.map.hubs
        for hub in hubs:
            if connection.zone1_name == hub.name:
                result_1 = hub.coordinate
            elif connection.zone2_name == hub.name:
                result_2 = hub.coordinate
        return (result_1, result_2)

    def draw_lines(self, screen) -> None:
        # pygame.draw.line(screen, "gray", (pos: tuple), (pos), hutosa)
        for connection in self.map.connections:
            pos_1, pos_2 = self.get_zone_coordinate(connection)
            thickness = self.unit_x * 0.1 * connection.max_link_capacity
            thickness = max(1, int(thickness))
            pygame.draw.line(screen, "gray", pos_1, pos_2, thickness)

    def draw_circles(self, screen) -> None:
        hubs = [self.map.start_hub, self.map.end_hub] + self.map.hubs

        self.draw_lines(screen)

        for hub in hubs:
            pygame.draw.circle(screen, hub.color, hub.coordinate, self.circle_radius)
            self.draw_text_in_circle(hub, screen)

    def draw_drone(self, screen, pos: tuple[int, int], num: int) -> None:
        x, y = pos
        org_x, org_y = x, y
        width = self.unit_x * 0.5
        height = self.unit_y * 0.2
        x -= width // 2
        y -= height // 2
        pygame.draw.ellipse(screen, "white", (x, y, width, height))
        pygame.draw.ellipse(screen, "black", (x, y, width, height), 3)

        font_size = height
        font = pygame.font.Font(None, int(font_size))
        text = font.render(f"{num}", True, "black")
        text_rect = text.get_rect(center=(org_x, org_y))
        screen.blit(text, text_rect)

    def draw_drones(self, screen, turn_count: int) -> None:
        coordinates: dict[tuple[int, int], int] = {}
        for path in self.paths:
            if not path:
                continue
            idx = min(turn_count, len(path) - 1)
            coord = path[idx]
            coordinates[coord] = coordinates.get(coord, 0) + 1
        for coord, num in coordinates.items():
            self.draw_drone(screen, coord, num)

    def draw_tabs(self, screen) -> None:
        pygame.draw.rect(screen, "gray", (0, self.screen_size[1], self.tab_size[0], self.tab_size[1]))
        font_size = self.tab_size[1] / 2
        font = pygame.font.Font(None, int(font_size))
        text1 = font.render("<- / ->: Slow down / Advance time", True, "black")
        text2 = font.render("esc: Return to the home screen", True, "black")
        screen.blit(text1, (0, self.screen_size[1]))
        screen.blit(text2, (0, self.screen_size[1] + font_size))

    def get_map_event(self, event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                self.turn_count = min(self.max_turn, self.turn_count + 1)
            elif event.key == pygame.K_LEFT:
                self.turn_count = max(0, self.turn_count - 1)
            elif event.key == pygame.K_ESCAPE:
                self.state = "home"

    def draw_home_texts(self, screen, candidates) -> None:
        center_x = self.screen_size[0] / 2
        font_size = self.unit_y * 0.9
        font = pygame.font.Font(None, int(font_size))

        title = font.render("Fly-in", True, "blue")
        title_rect = title.get_rect(center=(int(center_x), int(font_size / 2)))
        screen.blit(title, title_rect)

        for index, name in enumerate(candidates):
            text = font.render(name, True, "black")
            text_rect = text.get_rect(center=(int(center_x), int(font_size / 2) + font_size * (index + 1)))
            screen.blit(text, text_rect)

    def draw_selections(self, screen) -> None:
        font_size = self.unit_y * 0.9
        pygame.draw.rect(screen, "gray", (0, font_size * (self.index + 1), self.screen_size[0], font_size))

    def draw_home_tab(self, screen) -> None:
        pygame.draw.rect(screen, "gray", (0, self.screen_size[1], self.tab_size[0], self.tab_size[1]))
        font_size = self.tab_size[1] / 2
        font = pygame.font.Font(None, int(font_size))
        text1 = font.render("<- / -> : Change selection", True, "black")
        text2 = font.render("Enter: Select the map", True, "black")
        screen.blit(text1, (0, self.screen_size[1]))
        screen.blit(text2, (0, self.screen_size[1] + font_size))

    def draw_screen(self, screen) -> None:
        screen.fill("white")

        if self.state in ("home", "easy", "medium", "hard", "challenger"):
            if self.state == "home":
                candidates = ["easy", "medium", "hard", "challenger"]
            elif self.state == "easy":
                candidates = ["01_linear_path.txt", "02_simple_fork.txt", "03_basic_capacity.txt"]
            elif self.state == "medium":
                candidates = ["01_dead_end_trap.txt", "02_circular_loop.txt", "03_priority_puzzle.txt"]
            elif self.state == "hard":
                candidates = ["01_maze_nightmare.txt", "02_capacity_hell.txt", "03_ultimate_challenge.txt"]
            elif self.state == "challenger":
                candidates = ["01_the_impossible_dream.txt"] 

            self.draw_selections(screen)
            self.draw_home_texts(screen, candidates)
            self.draw_home_tab(screen)
            
        elif self.state == "map":
            screen.fill("white")
            self.draw_circles(screen)
            self.draw_drones(screen, self.turn_count)
            self.draw_tabs(screen)
            
        pygame.display.flip()

    def get_home_event(self, event, candidates) -> None:
        length = len(candidates)
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                self.index = min(length, self.index + 1)
            elif event.key in (pygame.K_LEFT, pygame.K_UP):
                self.index = max(0, self.index - 1)
            elif event.key == pygame.K_RETURN:
                self.state = candidates[self.index]
                self.index = 0
            elif event.key == pygame.K_ESCAPE:
                if self.state == "home":
                    return
                else:
                    self.state = "home"
                    self.index = 0

    def get_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        
        if self.state in ("home", "easy", "medium", "hard", "challenger"):
            if self.state == "home":
                candidates = ["easy", "medium", "hard", "challenger"]
            elif self.state == "easy":
                candidates = ["01_linear_path.txt", "02_simple_fork.txt", "03_basic_capacity.txt"]
            elif self.state == "medium":
                candidates = ["01_dead_end_trap.txt", "02_circular_loop.txt", "03_priority_puzzle.txt"]
            elif self.state == "hard":
                candidates = ["01_maze_nightmare.txt", "02_capacity_hell.txt", "03_ultimate_challenge.txt"]
            elif self.state == "challenger":
                candidates = ["01_the_impossible_dream.txt"] 
            self.get_home_event(event, candidates)

        if self.state == "map":
            self.get_map_event(event)

    def visualize(self) -> None:
        pygame.init()
        size = (self.screen_size[0], self.screen_size[1] + self.tab_size[1])
        screen = pygame.display.set_mode(size)
        pygame.display.set_caption("Fly-in")
        clock = pygame.time.Clock()

        while self.running:
            for event in pygame.event.get():
                self.get_event(event)

            self.draw_screen(screen)
            clock.tick(60)

        pygame.quit()


if __name__ == "__main__":
    parser = Parser()
    map = parser.parse("maps/hard/03_ultimate_challenge.txt")
    mapf = MAPF(map)
    paths, t = mapf.find_path()
    visualizer = Visualizer(map, paths, t)
    visualizer.visualize()
