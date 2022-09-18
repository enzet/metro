import logging
from dataclasses import dataclass, field, fields
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from metro.core import data
from metro.core.line import Line
from metro.core.named import Named
from metro.core.serialization import deserialize, is_null, serialize, TIME_FORMAT

__author__ = "Sergey Vartanov"
__email__ = "me@enzet.ru"


@dataclass
class Station(Named):
    """Transport station."""

    id_: str
    open_time: Optional[datetime] = None
    altitude: Optional[float] = None
    height: Optional[float] = None
    structure_type: Optional["StationStructure"] = None
    geo_position: Optional[tuple[float, float]] = None
    caption: Optional[str] = None
    connections: list["Connection"] = field(default_factory=list)
    status: dict[str, str] = field(default_factory=dict)
    platform_length: Optional[float] = None
    site_links: dict[str, str] = field(default_factory=dict)
    wikidata_id: Optional[int] = None
    line: Optional[Line] = None

    def deserialize(self, structure: dict[str, Any], lines: dict[str, Line]) -> "Station":
        """Deserialize station from structure."""
        assert structure["id"] == self.id_

        for key, value in structure.items():
            if key == "connections":
                continue
            elif key == "line":
                self.line = lines[value]
            elif key == "open_time":
                self.open_time = datetime.strptime(value, TIME_FORMAT)
            else:
                self.__setattr__(key, deserialize(structure[key]))

        return self

    def serialize(self) -> dict[str, Any]:
        """Serialize station to structure."""
        structure = {"id": self.id_}

        for key in [x.name for x in fields(Station)]:
            value = self.__getattribute__(key)
            if key == "line":
                structure[key] = value.id_
            elif not is_null(value):
                structure[key] = serialize(value)

        return structure

    def short_id(self) -> str:
        return self.id_.split("/")[1]

    def get_save_id(self) -> str:
        return self.id_.replace("/", "___")

    def get_caption(self, language) -> str:
        text: str = "unknown"
        if self.id_:
            text = self.id_[self.id_.find("/") + 1 :]
        for postfix in "", "_tr", "_un":
            if self.has_name(language + postfix):
                text = self.get_name(language + postfix)
        return data.extract_station_name(text, language)

    def get_connections(self, connection_type: "ConnectionType" = None) -> list["Connection"]:
        return [x for x in self.connections if connection_type is None or x.type_ == connection_type]

    def get_connection(self, other: "Station") -> Optional["Connection"]:
        connections: list[Connection] = [x for x in self.connections if x.to_ == other]
        return connections[0] if connections else None

    def check_height_and_structure(self) -> None:
        if self.structure_type:
            self.structure_type.check_height(self.altitude, self.id_)

    def recompute(self) -> None:
        """Assume ground station altitude."""
        if self.structure_type and self.altitude is None:
            if StationStructure.is_ground(self.structure_type):
                self.altitude = 2

    def is_terminus(self) -> bool:
        """Should we draw this station as terminus."""
        if self.is_transition():
            return False
        count: int = 0
        count_for_hidden: int = 0
        connection: Connection
        for connection in self.connections:
            if connection.type_ == ConnectionType.NEXT:
                to_: Station = connection.to_
                if to_.is_hidden():
                    count_for_hidden += 1
                else:
                    count += 1
        return (count + count_for_hidden <= 1) if self.is_hidden() else count <= 1

    def is_transition(self) -> bool:
        """If this station is as transition station."""
        return any(x.type_ == ConnectionType.TRANSITION for x in self.connections)

    def add_connection(self, other_station: "Station", type_: "ConnectionType", status: dict = None) -> None:
        """Add connection from this station to another."""
        connection: Connection
        for connection in self.connections:
            if connection.to_ == other_station:
                if not connection.type_ == type_:
                    logging.warning("change connection type")
                    connection.type_ = type_
                return
        connection = Connection(other_station, type_, status)
        self.connections.append(connection)

    def remove_connection(self, other_station: "Station") -> int:
        """
        Remove connection from this station to another.

        :returns number of connections removed
        """
        removed = 0
        new_structure = []
        connection: Connection
        for connection in self.connections:
            if connection.to_ != other_station:
                new_structure.append(connection)
            else:
                removed += 1
        self.connections = new_structure
        return removed

    # Status.

    def is_hidden(self) -> bool:
        """If station is not currently in operation."""
        return self.status["type"] in [ObjectStatus.CLOSED, ObjectStatus.UNDER_CONSTRUCTION, ObjectStatus.PLANNED]


class ConnectionType(Enum):
    NEXT = "next"
    TRANSITION = "transition"
    SAME = "same"


@dataclass
class Connection:

    to_: Optional[Station]
    type_: ConnectionType
    status: dict = None

    def is_hidden(self) -> bool:
        return self.status and self.status["type"] in ["closed", "under_construction", "planned"]

    @classmethod
    def deserialize(cls, structure, stations: dict[str, Station]) -> "Connection":
        return cls(
            stations[structure["to"]],
            ConnectionType(structure["type"]),
            structure["status"] if "status" in structure else None,
        )

    def serialize(self):
        return {"to": self.to_.id_, "type": self.type_.value} | ({"status": self.status} if self.status else {})


class ObjectStatus(Enum):
    """Current status of object: station, transition, line, system, etc."""

    OPEN = 0
    CLOSED = 1
    UNDER_CONSTRUCTION = 2
    PLANNED = 3


class StationStructure(Enum):
    """Type of station structure."""

    UNKNOWN = 0
    UNDERGROUND = 1
    OVERGROUND = 2
    GROUND = 3
    GROUND_COVERED = 4
    DEEP_PYLON = 5
    DEEP_PYLON_SHORT = 6
    DEEP_PYLON_2 = 7
    DEEP_PYLON_3 = 8
    DEEP_COLUMN = 9
    DEEP_COLUMN_3 = 10
    DEEP_COLUMN_WALL = 11
    DEEP_CLOSED = 12
    DEEP_VAULT_1 = 13
    SHALLOW_COLUMN = 14
    SHALLOW_COLUMN_2 = 15
    SHALLOW_COLUMN_3 = 16
    SHALLOW_VAULT_1 = 17
    SHALLOW_COLUMN_0 = 18
    GROUND_OPEN = 19
    GROUND_CLOSED = 20

    def check_height(self, height: float, station_id: str) -> None:
        """
        Check station structure and depth and print warning if there is inconsistency.

        :param height: station height.
        :param station_id: stations identifier.
        """
        if self.is_ground() and height < 0 or self.is_deep() and height >= -6 or self.is_shallow() and height < -15:
            logging.warning(f"station {station_id} is {self.name} but height is {height}")

    def is_ground(self) -> bool:
        return self.name[:6] == "GROUND"

    def is_deep(self) -> bool:
        return self.name[:4] == "DEEP"

    def is_shallow(self) -> bool:
        return self.name[:7] == "SHALLOW"
