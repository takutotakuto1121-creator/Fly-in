import sys
from enum import Enum
from pydantic import BaseModel, Field, ValidationError, model_validator


class ZoneType(str, Enum):
    normal = "normal"
    blocked = "blocked"
    restricted = "restricted"
    priority = "priority"


class Zone(BaseModel):
    name: str
    coordinate: tuple[int, int]
    type: ZoneType = Field(default=ZoneType.normal)
    color: str = Field(default="none")
    max_drones: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def validate_zone(self) -> "Zone":
        if "-" in self.name:
            raise ValueError(
                "The connection syntax forbids dashes in zone names"
            )
        return self


class Connection(BaseModel):
    zone1_name: str
    zone2_name: str
    max_link_capacity: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def validate_connection(self) -> "Connection":
        if "-" in self.zone1_name or "-" in self.zone2_name:
            raise ValueError(
                "The connection syntax forbids dashes in zone names."
            )
        return self


class Map(BaseModel):
    nb_drones: int
    start_hub: Zone
    end_hub: Zone
    hubs: list[Zone]
    connections: list[Connection]


class Parser:
    def __init__(self) -> None:
        self.nb_drones: int = 0
        self.start_hub: Zone | None = None
        self.end_hub: Zone | None = None
        self.hubs: list[Zone] = []
        self.connections: list[Connection] = []
        self.exist_first_line: bool = False
        self.exist_start_hub: bool = False
        self.exist_end_hub: bool = False
        self.defined_zones: set[str] = set()
        self.defined_connections: set[frozenset[str]] = set()

    def parse(self, filepath: str) -> Map:
        try:
            with open(filepath) as f:
                lines = f.readlines()
        except FileNotFoundError:
            print(f"[Error] file {filepath} not found", file=sys.stderr)
            sys.exit(1)
        except PermissionError:
            print(f"[Error] have no right to open {filepath}", file=sys.stderr)
            sys.exit(1)

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            try:
                if line == "":
                    continue
                elif line.startswith("#"):
                    continue
                elif line.startswith("nb_drones:"):
                    self._parse_nb_drones(line)
                elif line.startswith(("start_hub:", "end_hub:", "hub:")):
                    self._parse_hub(line)
                elif line.startswith("connection:"):
                    self._parse_connection(line)
                else:
                    raise ValueError("Invalid line format")
            except (ValueError, ValidationError) as e:
                print(
                    f"[Error] error at {line_num} line: {e}",
                    file=sys.stderr
                )
                sys.exit(1)

        if self.start_hub is None or self.end_hub is None:
            raise ValueError("you must implement start_hub and end_hub")

        return Map(
            nb_drones=self.nb_drones,
            start_hub=self.start_hub,
            end_hub=self.end_hub,
            hubs=self.hubs,
            connections=self.connections
        )

    def _parse_nb_drones(self, line: str) -> None:
        if self.exist_first_line:
            raise ValueError("you must implement nb_drones only 1 time")

        parts = line.split(":")
        if len(parts) != 2:
            raise ValueError("Invalid nb_drones format")
        self.nb_drones = int(parts[1].strip())
        self.exist_first_line = True

    def _parse_hub(self, line: str) -> None:
        if not self.exist_first_line:
            raise ValueError(
                "The first line defines the number of drones "
                "using nb_drones: <number>."
            )

        prefix, rest = line.split(":", 1)
        rest = rest.strip()

        meta: list[str] = []
        if "[" in rest and rest.endswith("]"):
            base, meta_str = rest.split("[", 1)
            rest = base.strip()
            meta = meta_str[:-1].split()

        parts = rest.split()
        if len(parts) != 3:
            raise ValueError("Invalid hub format")

        hub_name = parts[0]
        if hub_name in self.defined_zones:
            raise ValueError(f"Duplicate zone name: {hub_name}")
        hub_coordinate = (int(parts[1]), int(parts[2]))

        zone_exist = False
        color_exist = False
        max_drones_exist = False

        hub_type = ZoneType.normal
        hub_color = "none"
        hub_max_drones = 1

        for data in meta:
            data_parts = data.split("=")
            if len(data_parts) != 2:
                raise ValueError("Invalid zone-metadata format")
            if data_parts[0] == "zone" and not zone_exist:
                zone_exist = True
                hub_type = ZoneType(data_parts[1])
            elif data_parts[0] == "color" and not color_exist:
                color_exist = True
                hub_color = data_parts[1]
            elif data_parts[0] == "max_drones" and not max_drones_exist:
                max_drones_exist = True
                hub_max_drones = int(data_parts[1])
            else:
                raise ValueError("Invalid metadata")

        zone = Zone(
            name=hub_name,
            coordinate=hub_coordinate,
            type=hub_type,
            color=hub_color,
            max_drones=hub_max_drones
        )

        self.defined_zones.add(hub_name)

        prefix = prefix.strip()
        if prefix == "start_hub":
            if self.exist_start_hub:
                raise ValueError(
                    "implementation of start_hub must be only 1 time"
                )
            self.start_hub = zone
            self.exist_start_hub = True
        elif prefix == "end_hub":
            if self.exist_end_hub:
                raise ValueError(
                    "implementation of end_hub must be only 1 time"
                )
            self.end_hub = zone
            self.exist_end_hub = True
        elif prefix == "hub":
            self.hubs.append(zone)
        else:
            raise ValueError("hub prefix should be start_hub, end_hub or hub")

    def _parse_connection(self, line: str) -> None:
        if not self.exist_first_line:
            raise ValueError(
                "The first line defines the number of drones "
                "using nb_drones: <number>."
            )

        prefix, rest = line.split(":", 1)
        rest = rest.strip()

        meta: list[str] = []
        if "[" in rest and rest.endswith("]"):
            base, meta_str = rest.split("[", 1)
            rest = base.strip()
            meta = meta_str[:-1].split()

        connect = rest.split("-")
        if len(connect) != 2:
            raise ValueError("Invalid connection format")

        zone1 = connect[0].strip()
        zone2 = connect[1].strip()

        if zone1 not in self.defined_zones or zone2 not in self.defined_zones:
            raise ValueError("Connection uses undefined zones")

        conn_pair = frozenset([zone1, zone2])
        if conn_pair in self.defined_connections:
            raise ValueError("Duplicate connection defined")
        self.defined_connections.add(conn_pair)

        capacity = 1
        for data in meta:
            data_parts = data.split("=")
            if len(data_parts) != 2 or data_parts[0] != "max_link_capacity":
                raise ValueError("Invalid connection metadata format")
            capacity = int(data_parts[1])

        connection = Connection(
            zone1_name=zone1,
            zone2_name=zone2,
            max_link_capacity=capacity
        )

        self.connections.append(connection)
