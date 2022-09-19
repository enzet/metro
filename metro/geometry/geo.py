from typing import Dict, Optional

import numpy as np

__author__ = "Sergey Vartanov"
__email__ = "me@enzet.ru"


class Position:
    """Geographical position: longitude, latitude, and altitude."""

    def __init__(self, longitude: float = None, latitude: float = None, altitude: float = None):
        self.longitude: Optional[float] = longitude
        self.latitude: Optional[float] = latitude
        self.altitude: Optional[float] = altitude

    def __eq__(self, other: "Position") -> bool:
        if self.latitude is None or self.longitude is None or other.latitude is None or self.longitude is None:
            return False
        return np.equal(self.longitude, other.longitude) and np.equal(self.latitude, other.latitude)

    def from_structure(self, structure: dict) -> "Position":
        """Deserialize from structure."""
        self.longitude = structure["longitude"]
        self.latitude = structure["latitude"]
        if "altitude" in structure and structure["altitude"] is not None:
            self.altitude = structure["altitude"]
        return self

    def to_structure(self) -> Dict[str, float]:
        """Serialize to structure."""
        structure = {"longitude": self.longitude, "latitude": self.latitude}
        if self.altitude is not None:
            structure["altitude"] = self.altitude
        return structure
