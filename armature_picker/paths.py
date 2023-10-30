from pathlib import Path as _Path
from enum import Enum
import bpy
from os.path import join, dirname
import pathlib
from enum import Enum


b3d_user_path = bpy.utils.resource_path('USER')
b3d_config_path = join(b3d_user_path, "config")

b3d_appdata_path = dirname(bpy.utils.resource_path('USER'))
app_dir = pathlib.Path(b3d_appdata_path) / "addon_data" / __package__

src_path = _Path(__file__).parent


class Paths(Enum):
    SRC = src_path
    LIB = src_path / 'lib'
    LIB_SHADERS = LIB / 'shaders'
    LIB_IMAGES = LIB / 'images'
    LIB_TEMPLATES = LIB / 'templates'

    def __call__(self, *paths, as_path: bool = False):
        if paths:
            return self.value.joinpath(*paths) if as_path else str(self.value.joinpath(*paths))
        return self.value if as_path else str(self.value)
