import math
import time
from collections import deque
from src import Map, Zone

Node = tuple[str, str, int]


class Edge:
    def __init__(self, to_node: Node, cap: float, is_forward: bool):
        self.to: Node = to_node
        self.cap: float = cap
        self.rev: Edge
        self.is_forward: bool = is_forward


class MAPF:
    def __init__(self, map: Map, timeout: float = 10.0) -> None:
        self.map = map
        self.timeout = timeout
        self.graph: dict[Node, list[Edge]] = {}

    def add_edge(
        self, from_node: Node, to_node: Node, cap: float
    ) -> None:
        if from_node not in self.graph:
            self.graph[from_node] = []
        if to_node not in self.graph:
            self.graph[to_node] = []

        forward_edge = Edge(to_node, cap, True)
        reverse_edge = Edge(from_node, 0, False)
        forward_edge.rev = reverse_edge
        reverse_edge.rev = forward_edge

        self.graph[from_node].append(forward_edge)
        self.graph[to_node].append(reverse_edge)

    def is_zonetype(self, name: str, type: str) -> bool:
        all_zones: list[Zone] = (
            [self.map.start_hub, self.map.end_hub] + self.map.hubs
        )
        for zone in all_zones:
            if zone.name == name:
                if zone.type == type:
                    return True
                else:
                    return False
        return False

    def expand_time(self, t: int) -> None:
        all_zones: list[Zone] = (
            [self.map.start_hub, self.map.end_hub] + self.map.hubs
        )

        for zone in all_zones:
            hub_names = (self.map.start_hub.name, self.map.end_hub.name)
            cap = math.inf if zone.name in hub_names else zone.max_drones
            self.add_edge(
                (zone.name, "in", t + 1), (zone.name, "out", t + 1), cap
            )
            self.add_edge(
                (zone.name, "out", t), (zone.name, "in", t + 1), cap
            )

        for connection in self.map.connections:
            zone1 = connection.zone1_name
            zone2 = connection.zone2_name
            max_link_capacity = connection.max_link_capacity

            if (
                self.is_zonetype(zone1, "blocked")
                or self.is_zonetype(zone2, "blocked")
            ):
                continue

            if self.is_zonetype(zone2, "restricted"):
                dummy = f"{zone1}-{zone2}"
                self.add_edge(
                    (zone1, "out", t), (dummy, "in", t + 1),
                    max_link_capacity
                )
                self.add_edge(
                    (dummy, "in", t + 1), (dummy, "out", t + 1),
                    max_link_capacity
                )
                if t > 0:
                    self.add_edge(
                        (dummy, "out", t), (zone2, "in", t + 1),
                        max_link_capacity
                    )

            else:
                self.add_edge(
                    (zone1, "out", t), (zone2, "in", t + 1),
                    max_link_capacity
                )

            if self.is_zonetype(zone1, "restricted"):
                dummy = f"{zone2}-{zone1}"
                self.add_edge(
                    (zone2, "out", t), (dummy, "in", t + 1),
                    max_link_capacity
                )
                self.add_edge(
                    (dummy, "in", t + 1), (dummy, "out", t + 1),
                    max_link_capacity
                )
                if t > 0:
                    self.add_edge(
                        (dummy, "out", t), (zone1, "in", t + 1),
                        max_link_capacity
                    )

            else:
                self.add_edge(
                    (zone2, "out", t), (zone1, "in", t + 1),
                    max_link_capacity
                )

    def bfs(
        self, start_node: Node, end_node: Node
    ) -> dict[Node, Edge] | None:
        parent_edge: dict[Node, Edge] = {}
        queue = deque([start_node])

        while queue:
            current = queue.popleft()

            if current == end_node:
                return parent_edge

            for edge in self.graph.get(current, []):
                if (
                    edge.cap > 0
                    and edge.to not in parent_edge
                    and edge.to != start_node
                ):
                    if self.is_zonetype(edge.to[0], "priority"):
                        parent_edge[edge.to] = edge
                        queue.append(edge.to)

            for edge in self.graph.get(current, []):
                if (
                    edge.cap > 0
                    and edge.to not in parent_edge
                    and edge.to != start_node
                ):
                    parent_edge[edge.to] = edge
                    queue.append(edge.to)

        return None

    def extract_paths(self, t: int) -> list[list[str]]:
        paths = []
        for _ in range(self.map.nb_drones):
            current_node = (self.map.start_hub.name, "out", 0)
            drone_path = [self.map.start_hub.name]

            while (
                current_node[0] != self.map.end_hub.name
                and current_node[2] != t
            ):
                for edge in self.graph.get(current_node, []):
                    if edge.rev.cap > 0 and edge.is_forward:

                        edge.rev.cap -= 1
                        next_node = edge.to

                        if next_node[2] > current_node[2]:
                            drone_path.append(next_node[0])

                        current_node = next_node
                        break

            paths.append(drone_path)

        return paths

    def find_path(self) -> tuple[list[list[str]], int]:
        self.add_edge(
            (self.map.start_hub.name, "in", 0),
            (self.map.start_hub.name, "out", 0),
            math.inf
        )

        t = 0
        total_flow = 0
        parents_list = []
        deadline = time.monotonic() + self.timeout

        while total_flow < self.map.nb_drones:
            if time.monotonic() > deadline:
                raise TimeoutError(
                    f"No path to the goal found within {self.timeout}s "
                    f"(the goal may be unreachable)"
                )
            self.expand_time(t)
            t += 1

            target_node = (self.map.end_hub.name, "out", t)
            start_node = (self.map.start_hub.name, "in", 0)

            while total_flow < self.map.nb_drones:
                parents = self.bfs(start_node, target_node)

                if not parents:
                    break

                parents_list.append(parents)
                current = target_node
                while current != start_node:
                    edge = parents[current]
                    edge.cap -= 1
                    edge.rev.cap += 1
                    current = edge.rev.to

                total_flow += 1

        paths = self.extract_paths(t)
        return (paths, t)

    def print_logs(self, paths: list[list[str]], max_t: int) -> None:
        for t in range(1, max_t + 1):
            turn_move = []
            for drone_id, path in enumerate(paths):
                if t >= len(path):
                    continue
                prev_pos = path[t - 1]
                curr_pos = path[t]
                if curr_pos != prev_pos:
                    turn_move.append(f"D{drone_id + 1}-{curr_pos}")

            if turn_move:
                print(" ".join(turn_move))
