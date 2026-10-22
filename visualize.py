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

    def visualize(self) -> None:
        pygame.init()
        size = (self.screen_size[0], self.screen_size[1] + self.tab_size[1])
        screen = pygame.display.set_mode(size)
        pygame.display.set_caption("Fly-in")
        clock = pygame.time.Clock()
        turn_count = 0
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RIGHT:
                        turn_count = min(self.max_turn, turn_count + 1)
                    elif event.key == pygame.K_LEFT:
                        turn_count = max(0, turn_count - 1)

            screen.fill("white")
            self.draw_circles(screen)
            self.draw_drones(screen, turn_count)
            self.draw_tabs(screen)
            pygame.display.flip()
            clock.tick(60)

        pygame.quit()


if __name__ == "__main__":
    parser = Parser()
    map = parser.parse("maps/hard/03_ultimate_challenge.txt")
    mapf = MAPF(map)
    paths, t = mapf.find_path()
    visualizer = Visualizer(map, paths, t)
    visualizer.visualize()
