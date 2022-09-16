import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import numpy as np

from metro.core import data
from metro.core.line import Line
from metro.core.named import Named
from metro.geometry.geo import Position

__author__ = "Sergey Vartanov"
__email__ = "me@enzet.ru"

TIME_FORMAT = "%Y.%m.%d %H:%M:%S"


class Station(Named):
    """
    Transport station.
    """

    illegal_keys = [
        "id",
        "map",
        "geo",
        "textcoordinates",
        "text_parts",
        "open_time",
        "depth",
        "structure_type",
        "align",
        "line",
    ]

    def __init__(self, id_: str) -> None:
        super().__init__()
        assert "/" in id_
        self.id_: str = id_
        self.short_id: Optional[str] = None
        self.open_time: Optional[datetime] = None
        self.height: Optional[float] = None
        self.structure_type: Optional[StationStructure] = None
        self.text_coordinates: dict[int, np.ndarray] = {}
        self.align: Optional[str] = None
        self.position: Optional[Optional[np.ndarray]] = None
        self.geo_position: Optional[Position] = None
        self.caption: Optional[str] = None
        self.connections: list[Connection] = []
        self.status: dict[str, str] = {"type": None}
        self.caption_direction: Optional[np.ndarray] = None
        self.tick_vector: Optional[np.ndarray] = None
        self.right_shift: float = 0
        self.platform_length: Optional[Optional[float]] = None
        self.site_links: dict[str, str] = {}
        self.wikidata_id: Optional[int] = None
        self.line: Optional[Line] = None

    def __repr__(self) -> str:
        if self.id_ is not None:
            return "<" + self.id_ + ">"
        return "<unknown station>"

    def from_structure(self, structure: dict[str, Any]) -> "Station":
        """
        Deserialize station from structure.

        :param structure: input structure.
        """
        for key in structure:  # type: str
            value = structure[key]

            if key == "id":
                assert value == self.id_
            elif key == "open_time":
                self.open_time = datetime.strptime(structure["open_time"], TIME_FORMAT)
            elif key == "height":
                self.height = value
            elif key == "structure_type":
                self.structure_type = value
            elif key == "textcoordinates":
                for from_word in value:  # type: str
                    self.text_coordinates[int(from_word)] = value[from_word]
            elif key == "align":
                self.align = value
            elif key == "right_shift":
                self.right_shift = value
            elif key == "names":
                self.set_names(value)
            elif key == "geo":
                self.set_geo_position(Position().from_structure(value))
            elif key == "position":
                self.set_position(np.array(value))
            elif key == "site_links":
                self.site_links = value
            elif key == "tick_vector":
                self.tick_vector = np.array(value)
            else:
                logging.warning("ignored key " + key + " in station structure")

        return self

    def to_structure(self) -> dict[str, Any]:
        """
        Serialize station to structure.
        """
        structure = {"id": self.id_}
        if self.open_time:
            structure["open_time"] = self.open_time.strftime(TIME_FORMAT)
        if self.height is not None:
            structure["depth"] = self.height
        if self.structure_type:
            structure["structure_type"] = self.structure_type
        if self.text_coordinates:
            structure["textcoordinates"] = self.text_coordinates
        if self.line is not None:
            structure["line"] = self.line.get_id()
        if self.geo_position is not None:
            structure["geo"] = self.geo_position.to_structure()
        if self.position is not None:
            structure["position"] = self.position.to_short()
        if self.names:
            structure["names"] = self.names
        if self.height is not None:
            structure["height"] = self.height
        if self.right_shift is not None:
            structure["right_shirt"] = self.right_shift
        if self.connections:
            connection_structure = []
            for connection in self.connections:  # type: Connection
                connection_structure.append(connection.to_structure())
            structure["connections"] = connection_structure
        if self.site_links:
            structure["site_links"] = self.site_links
        if self.tick_vector is not None:
            structure["tick_vector"] = self.tick_vector.to_short()
        return structure

    def get_id(self) -> str:
        return self.id_

    def get_save_id(self) -> str:
        return self.id_.replace("/", "___")

    # Position.

    def has_position(self) -> bool:
        return self.position is not None

    def get_position(self) -> Optional[np.ndarray]:
        return self.position

    def set_position(self, position: np.ndarray) -> None:
        assert position is not None
        self.position = position

    # Geo position.

    def has_geo_position(self) -> bool:
        return self.geo_position is not None

    def get_geo_position(self) -> Optional[Position]:
        return self.geo_position

    def set_geo_position(self, geo_position: Position) -> None:
        assert isinstance(geo_position, Position)
        self.geo_position = geo_position

    # Direction.

    def has_tick_vector(self) -> bool:
        return self.tick_vector is not None

    def get_tick_vector(self) -> np.ndarray:
        if self.tick_vector:
            return self.tick_vector
        return np.array((1, 0))

    def has_caption_direction(self) -> bool:
        return self.caption_direction is not None or self.tick_vector is not None

    def get_caption_direction(self):
        if self.caption_direction is not None:
            return self.caption_direction
        if self.tick_vector is not None:
            return self.tick_vector
        return np.array((1, 0))

    def set_tick_vector(self, direction: np.ndarray) -> None:
        self.tick_vector = direction

    def set_caption_direction(self, direction: np.ndarray) -> None:
        self.caption_direction = direction

    # Names.

    def set_name(self, language: str, name: str, ignore_rewrite: bool = True) -> None:
        super().set_name(language, name, ignore_rewrite)

    def set_names(self, names: dict[str, str], ignore_rewrite: bool = True) -> None:
        super().set_names(names, ignore_rewrite)

    def get_caption(self, language) -> str:
        text = "unknown"
        if self.id_:
            text = self.id_[self.id_.find("/") + 1 :]
        if self.has_name(language):
            text = self.get_name(language)
        elif self.has_name(language + "_tr"):
            text = self.get_name(language + "_tr")
        elif self.has_name(language + "_un"):
            text = self.get_name(language + "_un")
        return data.extract_station_name(text, language)

    # Text coordinates.

    def has_text_coordinates(self) -> bool:
        return len(self.text_coordinates) != 0

    def get_text_coordinates_indices(self) -> list[int]:
        return list(self.text_coordinates.keys())

    def get_text_coordinates(self, word_number: int) -> Optional[np.ndarray]:
        position_list = self.text_coordinates[word_number]
        return np.array(position_list) if position_list else None

    def set_text_coordinates(self, word_number: int, position: Optional[np.ndarray]) -> None:
        self.text_coordinates[word_number] = position if position else None

    def get_caption_parts(self, language: str) -> dict[int, str]:
        parts = {}
        if language == "ja":
            words = self.get_caption(language).replace("-", "- ").split("・")
        else:
            words = self.get_caption(language).replace("-", "- ").split(" ")
        indices = list(sorted(self.text_coordinates.keys()))
        indices2 = indices + [len(words) + 1]
        for k, i in enumerate(indices):
            word = ""
            ii = i
            while i < indices2[k + 1]:
                if i <= len(words):
                    word += words[i - 1] + ("" if words[i - 1][-1:] == "-" else " ")
                i += 1
            parts[ii] = word
        return parts

    # Align.

    def has_align(self) -> bool:
        return self.align is not None

    def get_align(self) -> str:
        return self.align

    def set_align(self, align: str) -> None:
        self.align = align

    # Line.

    def has_line(self) -> bool:
        return self.line is not None

    def get_line(self) -> Optional[Line]:
        return self.line

    def set_line(self, line: Line) -> None:
        self.line = line

    # Connection.

    def get_connections(self, connection_type: "ConnectionType" = None) -> list["Connection"]:
        connections = []
        connection: Connection
        for connection in self.connections:
            if connection_type is None or connection.of_type(connection_type):
                connections.append(connection)
        return connections

    def get_connection_type(self, other: "Station") -> Optional["ConnectionType"]:
        connection: Connection
        for connection in self.connections:
            if connection.get_to() == other:
                return connection.get_type()
        return None

    def get_connection(self, other: "Station") -> Optional["Connection"]:
        connection: Connection
        for connection in self.connections:
            if connection.get_to() == other:
                return connection
        return None

    # Shift.

    def get_right_shift(self) -> float:
        return self.right_shift

    def set_right_shift(self, right_shift: float) -> None:
        self.right_shift = right_shift

    # Platform.

    def add_platform(self, paltform_name: str) -> None:
        self.platforms.append(paltform_name)

    # Open time.

    def has_open_time(self) -> bool:
        return self.open_time is not None

    def get_open_time(self) -> datetime:
        return self.open_time

    def set_open_time(self, open_time: datetime) -> None:
        if not isinstance(open_time, datetime):
            logging.error(str(open_time) + " is not datetime")
            raise Exception
        self.open_time = open_time

    def set_close_time(self, close_time: datetime) -> None:
        # TODO: implement
        pass

    # Depth and height.

    def has_height(self) -> bool:
        return self.height is not None

    def get_height(self) -> Optional[float]:
        return self.height

    def set_height(self, height: float) -> None:
        """
        :param height: station height in meters or depth (negative value)
        """
        self.height = height
        self.check_height_and_structure()

    def check_height_and_structure(self) -> None:
        if self.structure_type:
            self.structure_type.check_height(self.height, self.id_)

    def recompute(self) -> None:
        if self.structure_type and self.height is None:
            if StationStructure.is_ground(self.structure_type):
                self.height = 2

    # Structure type.

    def set_structure_type(self, structure_type: "StationStructure") -> None:
        self.structure_type = structure_type

    # Methods.

    def get_shifted_position(self, shift_size: float) -> np.ndarray:
        return self.get_position() + shift_size * self.get_right_shift() * self.get_tick_vector()

    def is_terminus(self) -> bool:
        """
        Should we draw this station as terminus.
        """
        for connection in self.connections:  # type: Connection
            if connection.is_transition():
                return False
        count = 0
        count_for_hidden = 0
        for connection in self.connections:  # type: Connection
            if connection.is_next():
                to_ = connection.get_to()  # type: Station
                if to_.is_hidden():
                    count_for_hidden += 1
                else:
                    count += 1
        if self.is_hidden():
            if count + count_for_hidden > 1:
                return False
            else:
                return True
        else:
            if count > 1:
                return False
            else:
                return True

    def is_transition(self) -> bool:
        """
        If this station is as transition station.
        """
        is_transition: bool = False
        connection: Connection
        for connection in self.connections:
            if connection.is_transition():
                is_transition = True
        return is_transition

    def add_connection(self, other_station: "Station", type_: "ConnectionType", status: dict = None) -> None:
        """
        Add connection from this station to another.
        """
        if not isinstance(other_station, Station):
            raise TypeError("other station is of type " + str(type(other_station)))

        connection: Connection
        for connection in self.connections:
            if connection.get_to() == other_station:
                if not connection.of_type(type_):
                    logging.warning("change connection type")
                    connection.set_type(type_)
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
            if connection.get_to() != other_station:
                new_structure.append(connection)
            else:
                removed += 1
        self.connections = new_structure
        return removed

    # Status.

    def set_status(self, status: dict[str, "ObjectStatus"]) -> None:
        self.status = status

    def is_hidden(self) -> bool:
        """
        If station is not currently in operation.
        """
        if self.status["type"] in [ObjectStatus.CLOSED, ObjectStatus.UNDER_CONSTRUCTION, ObjectStatus.PLANNED]:
            return True
        return False

    # Site links

    def add_site_link(self, key: str, link: str) -> None:
        self.site_links[key] = link

    def has_wikipedia_page_name(self, language: str) -> bool:
        return (language + "wiki") in self.site_links

    def get_wikipedia_page_name(self, language: str) -> str:
        return self.site_links[language + "wiki"]

    # Platform

    def set_platform_length(self, length: float):
        self.platform_length = length


class ConnectionType(Enum):
    NEXT = 1
    TRANSITION = 2
    SAME = 3

    def __str__(self):
        if self == self.NEXT:
            return "next"
        if self == self.TRANSITION:
            return "transition"
        if self == self.SAME:
            return "same"

    def from_str(self, text: str):
        if text == "next":
            return self.NEXT
        if text == "transition":
            return self.TRANSITION
        if text == "same":
            return self.SAME


@dataclass
class Connection:

    to_: Station
    type_: ConnectionType
    status: dict = None

    def of_type(self, type_: ConnectionType) -> bool:
        return self.type_ == type_

    def set_type(self, type_: ConnectionType) -> None:
        self.type_ = type_

    def get_type(self) -> ConnectionType:
        return self.type_

    def get_to(self) -> Station:
        return self.to_

    def is_next(self) -> bool:
        return self.type_ == ConnectionType.NEXT

    def is_transition(self) -> bool:
        return self.type_ == ConnectionType.TRANSITION

    def has_status(self) -> bool:
        return self.status is not None

    def is_hide(self) -> bool:
        if self.status and self.status["type"] in ["closed", "under_construction", "planned"]:
            return True
        return False

    def get_status(self) -> dict[str, str]:
        return self.status

    def to_structure(self):
        return {"to": self.to_.get_id(), "type": str(self.type_)}


class ObjectStatus(Enum):
    """
    Current status of object: station, transition, line, system, etc.
    """

    OPEN = 0
    CLOSED = 1
    UNDER_CONSTRUCTION = 2
    PLANNED = 3


class StationStructure(Enum):
    """
    Type of station structure.
    """

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
            logging.warning("station " + station_id + " is " + self.name + " but height is " + str(height))

    def is_ground(self) -> bool:
        return self.name[:6] == "GROUND"

    def is_deep(self) -> bool:
        return self.name[:4] == "DEEP"

    def is_shallow(self) -> bool:
        return self.name[:7] == "SHALLOW"
