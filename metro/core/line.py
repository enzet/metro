from dataclasses import dataclass, fields
from typing import Any, Optional

from metro.core.named import Named

__author__ = "Sergey Vartanov"
__email__ = "me@enzet.ru"

from metro.core.serialization import is_null, deserialize, serialize


@dataclass
class Line(Named):
    """
    Transport route.

    The definition of line may depend on transport system.
    """

    id_: str
    color: Optional[str] = None

    # Return index if this transport route has one. Index is a float that is used to sort routes. E.g. we can use 1 for
    # "Line 1", 10 for "Route 10", and 5.1 for "Line 5A".
    index: Optional[float] = None

    def deserialize(self, structure: dict[str, Any]) -> "Line":
        """Deserialize transport route from structure."""
        for key in [x.name for x in fields(Line)]:
            if key in structure:
                self.__setattr__(key, deserialize(structure[key]))

        return self

    def serialize(self) -> dict[str, Any]:
        """Serialize transport route to structure."""
        structure: dict[str, Any] = {"id": self.id_}

        for key in [x.name for x in fields(Line)]:
            value = self.__getattribute__(key)
            if not is_null(value):
                structure[key] = serialize(value)

        return structure
