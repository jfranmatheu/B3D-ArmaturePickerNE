import bpy
from bpy.types import bpy_struct

from ..._globals import GLOBALS
from ...debug import print_debug
from ....utils.classes import get_subclasses_recursive

import re


class BaseType(object):
    original_name: str

    @classmethod
    def __subclasses_recursive__(cls):
        return get_subclasses_recursive(cls, only_outermost=True)
        direct = cls.__subclasses__()
        indirect = []
        for subclass in direct:
            indirect.extend(subclass.__subclasses_recursive__())
        return direct + indirect

    @classmethod
    def tag_register(cls, bpy_type: type | str, type_key: str | None, *subtypes, **kwargs):
        if isinstance(bpy_type, str):
            bpy_type = getattr(bpy.types, bpy_type)
        print_debug(f"--> Tag-Register class '{cls.__name__}' of type '{bpy_type.__name__} --> Package: {cls.__module__}'")

        keywords = re.findall('[A-Z][^A-Z]*', cls.__name__)
        idname: str = '_'.join([word.lower() for word in keywords])

        # Modify/Extend original class.
        if type_key is not None:
            cls_name = f'{GLOBALS.ADDON_MODULE.upper()}_{type_key}_{idname}'

            cls.bl_label = cls.label if hasattr(cls, 'label') else ' '.join(keywords)
            if hasattr(cls, 'tooltip'):
                cls.bl_description = cls.tooltip
            if bpy_type == bpy.types.Operator:
                cls.bl_idname = GLOBALS.ADDON_MODULE.lower() + '.' + idname
            elif bpy_type in {bpy.types.Menu, bpy.types.Panel}:
                cls.bl_idname = cls_name

            kwargs['original_name'] = cls.__name__
        else:
            if bpy_type == bpy.types.AddonPreferences:
                cls_name = f'{GLOBALS.ADDON_MODULE.upper()}_AddonPreferences'
            else:
                cls_name = cls.__name__ # f'{GLOBALS.ADDON_MODULE.upper()}_{idname}'

        # Create new Blender type to be registered.
        new_cls = type(
            cls_name,
            (cls, *subtypes, bpy_type),
            kwargs
        )
        from .._register import BlenderTypes
        getattr(BlenderTypes, bpy_type.__name__).add_class(new_cls)
        return new_cls


def init():
    for subcls in BaseType.__subclasses_recursive__():
        if 'types' in subcls.__module__:
           # SKIP: IF THE SUBCLASS IS INSIDE THE addon_utils module or inside any folder called 'types'.
           continue
        subcls.tag_register()
