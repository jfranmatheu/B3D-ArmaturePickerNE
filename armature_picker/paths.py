from pathlib import Path as _Path
from enum import Enum


src_path = _Path(__file__).parent


class Paths(Enum):
    SRC = src_path
    LIB = src_path / 'lib'
    LIB_SHADERS = LIB / 'shaders'
    LIB_IMAGES = LIB / 'images'

    def __call__(self, *paths, as_path: bool = False):
        if paths:
            return self.value.joinpath(*paths) if as_path else str(self.value.joinpath(*paths))
        return self.value if as_path else str(self.value)
