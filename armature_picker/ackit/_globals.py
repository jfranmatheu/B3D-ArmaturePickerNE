import bpy
import sys
from pathlib import Path

from .. import __package__ as __main_package__#, bl_info


class GLOBALS:
    PYTHON_PATH = sys.executable

    BLENDER_VERSION = bpy.app.version
    IN_BACKGROUND = bpy.app.background

    ADDON_MODULE = __main_package__
    ADDON_SOURCE_PATH = Path(__file__).parent.parent
    #ADDON_NAME = bl_info['name']
    #ADDON_VERSION = bl_info['version']
    #SUPPORTED_BLENDER_VERSION = bl_info['blender']
    ICONS_PATH = ADDON_SOURCE_PATH / 'lib' / 'icons'

    IN_DEVELOPMENT = hasattr(sys, 'gettrace') and sys.gettrace() is not None # Just a nice HACK! ;-)
    IN_PRODUCTION  = not IN_DEVELOPMENT


    class CodeGen:
        TYPES = 'types.py'
        ICONS = 'icons.py'
        OPS = 'ops.py'
