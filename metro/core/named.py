"""
Map Machine.

Author: Sergey Vartanov (me@enzet.ru)
"""
import logging
from typing import Dict, Optional

__author__ = "Sergey Vartanov"
__email__ = "me@enzet.ru"


class Named:
    def __init__(self) -> None:
        self.names: Dict[str, str] = {}

    def set_name(self, language: str, name: str, ignore_rewrite: bool = True) -> None:
        if language in self.names and not ignore_rewrite and self.names[language] != name:
            logging.warning("rewrite name: " + self.names[language] + " -> " + name)
        self.names[language] = name

    def set_names(self, names: Dict[str, str], ignore_rewrite: bool = True) -> None:
        language: str
        for language in names:
            self.set_name(language, names[language], ignore_rewrite)

    def has_name(self, language: str) -> bool:
        return language in self.names or "int" in self.names

    def get_name(self, language: str) -> Optional[str]:
        if language in self.names:
            return self.names[language]
        if "int" in self.names:
            return self.names["int"]
        return None
