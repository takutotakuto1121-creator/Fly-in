import pygame
from src import Map, Zone, Parser, Connection, MAPF


class Visualizer:
    def __init__(self) -> None:
        # マップデータ関連の初期化
        self.map: Map | None = None
        self.paths: list[list[tuple[float, float]]] = []
        self.max_turn = 0

        # 描画関連の初期化
        self.tab_size: tuple[int, int] = (1280, 80)
        self.screen_size: tuple[int, int] = (1280, 720)
        self.unit_x = 0.0
        self.unit_y = 0.0
        self.circle_radius = 0.0

        # アプリケーションの状態管理
        self.running = True
        self.state = "home"
        self.turn_count = 0
        self.index = 0

    def load_map(self, difficulty: str, filename: str) -> None:
        # 選択された難易度とファイル名からマップをロード
        filepath = f"maps/{difficulty}/{filename}"
        parser = Parser()
        self.map = parser.parse(filepath)
        mapf = MAPF(self.map)
        paths, max_turn = mapf.find_path()

        self.max_turn = max_turn

        # 座標やパスを画面用に再計算
        self.redefine_coordinates_and_get_unit()
        self.paths = self.redefine_paths(paths)
        self.circle_radius = self.define_circle_radius()

        self.turn_count = 0
        self.state = "map"

    def redefine_coordinates_and_get_unit(self) -> None:
        assert self.map is not None
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
            hub.coordinate = (new_x, new_y)  # type: ignore[assignment]

    def redefine_paths(
        self, paths: list[list[str]]
    ) -> list[list[tuple[float, float]]]:
        assert self.map is not None
        hubs = [self.map.start_hub, self.map.end_hub] + self.map.hubs
        hub_coords = {hub.name: hub.coordinate for hub in hubs}

        new_paths: list[list[tuple[float, float]]] = []
        for path in paths:
            new_path: list[tuple[float, float]] = []
            for hub in path:
                if hub in hub_coords:
                    new_path.append(hub_coords[hub])
                elif "-" in hub:
                    zone1, zone2 = hub.split("-", 1)
                    if zone1 in hub_coords and zone2 in hub_coords:
                        coord1 = hub_coords[zone1]
                        coord2 = hub_coords[zone2]
                        midpoint = (
                            (coord1[0] + coord2[0]) / 2,
                            (coord1[1] + coord2[1]) / 2
                        )
                        new_path.append(midpoint)
            new_paths.append(new_path)
        return new_paths

    def define_circle_radius(self) -> float:
        size = min([self.unit_x, self.unit_y])
        radius = size * 2 / 5
        return radius

    def draw_text_in_circle(
        self, hub: Zone, screen: pygame.Surface
    ) -> None:
        length = max(1, len(hub.name))
        font_size = max(10, int(self.circle_radius / (length * 0.17)))
        x_text = hub.coordinate[0] - self.circle_radius
        y_text = hub.coordinate[1] + self.circle_radius
        font = pygame.font.Font(None, font_size)
        text = font.render(hub.name, True, "black")
        screen.blit(text, (int(x_text), int(y_text)))

    def get_zone_coordinate(
        self, connection: Connection
    ) -> tuple[tuple[float, float], tuple[float, float]]:
        assert self.map is not None
        hubs = [self.map.start_hub, self.map.end_hub] + self.map.hubs
        result_1, result_2 = (0.0, 0.0), (0.0, 0.0)
        for hub in hubs:
            if connection.zone1_name == hub.name:
                result_1 = hub.coordinate
            elif connection.zone2_name == hub.name:
                result_2 = hub.coordinate
        return (result_1, result_2)

    def draw_lines(self, screen: pygame.Surface) -> None:
        assert self.map is not None
        for connection in self.map.connections:
            pos_1, pos_2 = self.get_zone_coordinate(connection)
            thickness = max(
                1, int(self.unit_x * 0.1 * connection.max_link_capacity)
            )
            pygame.draw.line(
                screen, "gray",
                (int(pos_1[0]), int(pos_1[1])),
                (int(pos_2[0]), int(pos_2[1])),
                thickness
            )

    def draw_circles(self, screen: pygame.Surface) -> None:
        assert self.map is not None
        hubs = [self.map.start_hub, self.map.end_hub] + self.map.hubs
        self.draw_lines(screen)
        for hub in hubs:
            center = (int(hub.coordinate[0]), int(hub.coordinate[1]))
            radius = int(self.circle_radius)
            if hub.color == "rainbow":
                pygame.draw.circle(screen, "red", center, radius)
                pygame.draw.circle(screen, "yellow", center, int(radius / 2))
                pygame.draw.circle(screen, "blue", center, int(radius / 3))
            else:
                pygame.draw.circle(screen, hub.color, center, radius)
            self.draw_text_in_circle(hub, screen)

    def draw_drone(
        self, screen: pygame.Surface, pos: tuple[float, float], num: int
    ) -> None:
        org_x, org_y = pos
        width = max(2, int(self.unit_x * 0.5))
        height = max(2, int(self.unit_y * 0.2))
        x = int(org_x - width / 2)
        y = int(org_y - height / 2)

        rect = (x, y, width, height)
        pygame.draw.ellipse(screen, "white", rect)
        pygame.draw.ellipse(screen, "black", rect, 1)

        font_size = max(10, height)
        font = pygame.font.Font(None, font_size)
        text = font.render(f"{num}", True, "black")
        text_rect = text.get_rect(center=(int(org_x), int(org_y)))
        screen.blit(text, text_rect)

    def draw_drones(self, screen: pygame.Surface, turn_count: int) -> None:
        coordinates: dict[tuple[float, float], int] = {}
        for path in self.paths:
            if not path:
                continue
            idx = min(turn_count, len(path) - 1)
            coord = path[idx]
            coordinates[coord] = coordinates.get(coord, 0) + 1
        for coord, num in coordinates.items():
            self.draw_drone(screen, coord, num)

    def draw_tabs(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(
            screen, "gray",
            (0, self.screen_size[1], self.tab_size[0], self.tab_size[1])
        )
        font_size = int(self.tab_size[1] / 2)
        font = pygame.font.Font(None, font_size)
        text1 = font.render("<- / ->: Slow down / Advance time", True, "black")
        text2 = font.render("esc: Return to the home screen", True, "black")
        screen.blit(text1, (0, self.screen_size[1]))
        screen.blit(text2, (0, self.screen_size[1] + font_size))

    def get_map_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                self.turn_count = min(self.max_turn, self.turn_count + 1)
            elif event.key == pygame.K_LEFT:
                self.turn_count = max(0, self.turn_count - 1)
            elif event.key == pygame.K_ESCAPE:
                self.state = "home"
                self.index = 0

    def draw_home_texts(
        self, screen: pygame.Surface, candidates: list[str]
    ) -> None:
        center_x = self.screen_size[0] / 2
        font_size = self.screen_size[1] * 0.2
        font = pygame.font.Font(None, int(font_size))

        title = font.render("Fly-in", True, "blue")
        title_rect = title.get_rect(center=(int(center_x), int(font_size / 2)))
        screen.blit(title, title_rect)

        for index, name in enumerate(candidates):
            text = font.render(name, True, "black")
            text_rect = text.get_rect(center=(
                int(center_x), int(font_size / 2) + font_size * (index + 1)
            ))
            screen.blit(text, text_rect)

    def draw_selections(self, screen: pygame.Surface) -> None:
        font_size = self.screen_size[1] * 0.2
        rect = (
            0, int(font_size) * (self.index + 1),
            self.screen_size[0], font_size
        )
        pygame.draw.rect(screen, "gray", rect)

    def draw_home_tab(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(
            screen, "gray",
            (0, self.screen_size[1], self.tab_size[0], self.tab_size[1])
        )
        font_size = int(self.tab_size[1] / 2)
        font = pygame.font.Font(None, font_size)
        text1 = font.render("<- / -> : Change selection", True, "black")
        text2 = font.render("Enter: Select the map", True, "black")
        screen.blit(text1, (0, self.screen_size[1]))
        screen.blit(text2, (0, self.screen_size[1] + font_size))

    def draw_screen(self, screen: pygame.Surface) -> None:
        screen.fill("white")

        if self.state in ("home", "easy", "medium", "hard", "challenger"):
            if self.state == "home":
                candidates = ["easy", "medium", "hard", "challenger"]
            elif self.state == "easy":
                candidates = [
                    "01_linear_path.txt",
                    "02_simple_fork.txt",
                    "03_basic_capacity.txt"
                ]
            elif self.state == "medium":
                candidates = [
                    "01_dead_end_trap.txt",
                    "02_circular_loop.txt",
                    "03_priority_puzzle.txt"
                ]
            elif self.state == "hard":
                candidates = [
                    "01_maze_nightmare.txt",
                    "02_capacity_hell.txt",
                    "03_ultimate_challenge.txt"
                ]
            elif self.state == "challenger":
                candidates = ["01_the_impossible_dream.txt"]

            self.draw_selections(screen)
            self.draw_home_texts(screen, candidates)
            self.draw_home_tab(screen)

        elif self.state == "map":
            if self.map:
                self.draw_circles(screen)
                self.draw_drones(screen, self.turn_count)
                self.draw_tabs(screen)

        pygame.display.flip()

    def get_home_event(
        self, event: pygame.event.Event, candidates: list[str]
    ) -> None:
        length = len(candidates)
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                self.index = min(length - 1, self.index + 1)
            elif event.key in (pygame.K_LEFT, pygame.K_UP):
                self.index = max(0, self.index - 1)
            elif event.key == pygame.K_RETURN:
                selected = candidates[self.index]
                if selected.endswith(".txt"):
                    self.load_map(self.state, selected)
                else:
                    self.state = selected
                self.index = 0
            elif event.key == pygame.K_ESCAPE:
                if self.state == "home":
                    return
                else:
                    self.state = "home"
                    self.index = 0

    def get_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False

        if self.state in ("home", "easy", "medium", "hard", "challenger"):
            if self.state == "home":
                candidates = ["easy", "medium", "hard", "challenger"]
            elif self.state == "easy":
                candidates = [
                    "01_linear_path.txt",
                    "02_simple_fork.txt",
                    "03_basic_capacity.txt"
                ]
            elif self.state == "medium":
                candidates = [
                    "01_dead_end_trap.txt",
                    "02_circular_loop.txt",
                    "03_priority_puzzle.txt"
                ]
            elif self.state == "hard":
                candidates = [
                    "01_maze_nightmare.txt",
                    "02_capacity_hell.txt",
                    "03_ultimate_challenge.txt"
                ]
            elif self.state == "challenger":
                candidates = ["01_the_impossible_dream.txt"]
            self.get_home_event(event, candidates)

        elif self.state == "map":
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
    visualizer = Visualizer()
    visualizer.visualize()
