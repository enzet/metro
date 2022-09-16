import logging
from typing import Any, Optional

from metro.core.line import Line
from metro.core.named import Named
from metro.core.station import Station, ConnectionType

__author__ = "Sergey Vartanov"
__email__ = "me@enzet.ru"

DEFAULT_STYLE_ID = "normal"


class System(Named):
    """Transport system."""

    def __init__(self, id_: str):
        super().__init__()

        self.id_: str = id_
        self.stations: list[Station] = []
        self.lines: list[Line] = []
        self.lookup_station_id: dict[str, Station] = {}
        self.style_id: Optional[str] = None
        self.line_width: Optional[float] = None
        self.point_length: Optional[float] = None

    def from_structure(self, structure: dict[str, Any]):
        """
        Deserialize transport system from structure.
        """
        if "lines" in structure:
            line: dict[str, Any]
            for line in structure["lines"]:
                self.lines.append(Line(line["id"]).from_structure(line))

        if "stations" in structure:
            station_structure: dict[str, Any]
            for station_structure in structure["stations"]:
                if "id" in station_structure:
                    station_id = station_structure["id"]
                    station = Station(station_id).from_structure(station_structure)
                    if "line" in station_structure:
                        station.set_line(self.get_line_by_id(station_structure["line"]))
                    self.stations.append(station)
                else:
                    logging.error("no station ID found")

            station_structure: dict[str, Any]
            for station_structure in structure["stations"]:
                if "connections" in station_structure:
                    station = self.get_station_by_id(station_structure["id"])
                    for connection_structure in station_structure["connections"]:
                        other_station = self.get_station_by_id(connection_structure["to"])
                        status = None
                        if "status" in connection_structure:
                            status = connection_structure["status"]
                        station.add_connection(
                            other_station, ConnectionType(1).from_str(connection_structure["type"]), status
                        )

        for key in structure:
            value = structure[key]

            if key == "id":
                self.id_ = value

            elif key == "line_width":
                self.line_width = value

            elif key == "names":
                self.set_names(value)

            elif key not in ["lines", "stations"]:
                logging.warning("ignored key " + key + " for system")

    def to_structure(self) -> dict[str, Any]:
        """
        Serialize transport system to structure.
        """
        structure = {"id": self.id_, "stations": [], "lines": []}

        for station in self.stations:  # type: Station
            structure["stations"].append(station.to_structure())

        for line in self.lines:  # type: Line
            structure["lines"].append(line.to_structure())

        if self.line_width is not None:
            structure["line_width"] = self.line_width

        return structure

    def get_id(self):
        return self.id_

    # Style

    def get_style_id(self) -> str:
        if self.style_id:
            return self.style_id
        return DEFAULT_STYLE_ID

    def has_line_width(self) -> bool:
        return self.line_width is not None

    def get_line_width(self) -> Optional[float]:
        return self.line_width

    def has_point_length(self) -> bool:
        return self.point_length is not None

    def get_point_length(self) -> Optional[float]:
        return self.point_length

    # Station.

    def get_stations(self) -> list[Station]:
        return self.stations

    def get_station_by_id(self, station_id: str) -> Optional[Station]:
        station: Station
        for station in self.stations:
            if station.get_id() == station_id:
                return station
        return None

    def get_stations_by_short_id(self, station_short_id) -> list[Station]:
        result = []
        station: Station
        for station in self.stations:
            if (station.short_id == station_short_id) or (station.id_ and station.id_.endswith("/" + station_short_id)):
                result.append(station)
        return result

    def get_station_by_wikidata_id(self, station_wikidata_id) -> Optional[Station]:
        station: Station
        for station in self.stations:
            if station.wikidata_id == station_wikidata_id:
                return station
        return None

    def get_station_by_line_and_wid(self, line_id, station_wikidata_id) -> Optional[Station]:
        station: Station
        for station in self.stations:
            if station.wikidata_id == station_wikidata_id and station.get_line_id() == line_id:
                return station
        return None

    def get_stations_by_name(self, name: str, language: str) -> list[Station]:
        result = []
        station: Station
        for station in self.stations:
            if station.has_name(language) and station.get_caption(language) == name:
                result.append(station)
        return result

    def get_stations_by_line(self, line: Line) -> list[Station]:
        result = []
        station: Station
        for station in self.stations:
            if station.has_line() and station.get_line() == line:
                result.append(station)
        return result

    def add_station(self, station: Station) -> None:
        assert self.get_station_by_id(station.get_id()) is None, station.get_id()
        self.stations.append(station)

    def remove_station(self, station: Station) -> None:
        self.stations.remove(station)

    # Line.

    def get_line_by_id(self, line_id) -> Line:
        """Get transport system line using its unique ID."""
        line: Line
        for line in self.lines:
            if line.id_ == line_id:
                return line

    def get_lines(self):
        """Get all lines of transport system."""
        return self.lines

    def add_line(self, line: Line) -> None:
        """
        Add new line to transport system.

        :param line: line to add.
        """
        # if self.get_line_by_id(line.id_):
        #     raise Exception("there is a line with such ID " + line.id_)
        self.lines.append(line)

    def has_line(self, line: Line) -> bool:
        return line in self.lines

    def remove_line(self, line: Line) -> None:
        self.lines.remove(line)

    def __repr__(self) -> str:
        return self.id_ + "[" + str(len(self.stations)) + ", " + str(len(self.lines)) + "]"

    def get_lines_number(self) -> float:
        return len(self.lines)

    def get_stations_number(self) -> float:
        return len(self.stations)

    def has_transitions(self) -> bool:
        """If there is at least one transition station."""
        return any(station.is_transition() for station in self.stations)

    def get_station_unique_names(self, language: str) -> set[str]:
        unique_names: set[str] = set()
        for station in self.stations:
            unique_names.add(station.get_caption(language))
        return unique_names

    def get_depth_bounds(self) -> tuple[float, float]:
        if not len(self.stations):
            raise Exception()

        bounds: tuple[float, float] = (self.stations[0].get_height(),) * 2
        for station in self.stations:
            height: float = station.get_height()
            bounds = (min(bounds[0], height), max(bounds[1], height))
        return bounds
