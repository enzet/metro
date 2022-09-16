import logging
from typing import Any, Dict, Optional

from metro.core.named import Named

__author__ = "Sergey Vartanov"
__email__ = "me@enzet.ru"


class Line(Named):
    """
    Transport route.

    The definition of the line depend on transport system.
    """

    def __init__(self, id_: str) -> None:
        super().__init__()

        self.id_: str = id_
        self.style_designator: str = "default"
        self.color: Optional[str] = None
        self.index: Optional[float] = None

    def from_structure(self, structure: Dict[str, Any]) -> "Line":
        """
        Deserialize transport route from structure.

        :param structure: transport route initial structure
        """
        for key in structure:
            value = structure[key]
            if key == "id":
                assert self.id_ == value
            elif key == "color":
                self.color = value
            elif key == "style":
                self.style_designator = value
            elif key == "index":
                self.index = value
            elif key == "names":
                self.set_names(value)
            else:
                logging.warning("ignored key " + key + " for line")

        return self

    def to_structure(self) -> Dict[str, Any]:
        """
        Serialize transport route to structure.

        :returns transport route final structure
        """
        structure = {"id": self.id_}
        if self.color:
            structure["color"] = self.color
        if self.index is not None:
            structure["index"] = self.index
        if self.names:
            structure["names"] = self.names
        return structure

    def get_id(self) -> str:
        return self.id_

    # Index.

    def has_index(self) -> bool:
        return self.index is not None

    def get_index(self) -> Optional[float]:
        """
        Return index if this transport route has one. Index is a float that is used to sort routes. E.g. we can use 1
        for "Line 1", 10 for "Route 10", and 5.1 for "Line 5A".
        """
        return self.index

    # Color.

    def has_color(self) -> bool:
        return self.color is not None

    def get_color(self) -> Optional[str]:
        return self.color

    def set_color(self, color: str) -> None:
        self.color = color

    # Style designator.

    def get_style_designator(self) -> str:
        return self.style_designator
