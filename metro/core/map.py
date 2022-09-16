from metro.core.system import System


class Map:
    def __init__(self):
        self.names: dict[str, str] = {}
        self.systems: dict[str, System] = {}
        self.local_languages: list[str] = []

    def get_system_by_id(self, system_id: str) -> System:
        return self.systems[system_id]

    def set_names(self, names: dict[str, str]) -> None:
        self.names = names

    def get_local_languages(self) -> list[str]:
        return self.local_languages

    def get_systems(self):
        return self.systems.values()
