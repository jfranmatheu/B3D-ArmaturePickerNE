from bpy.types import Panel, Menu

from typing import Union

from ..override_cache import set_cls_attribute


def ui_override(bl_ui_class: Union[Panel, Menu],
                attr_name: str,
                poll: callable):
    ''' This is a Decorator. Use it over Blender UI built-in classes of Panel, Menu... type. '''
    def decorator(fun):
        setattr(fun, 'poll', poll)
        # setattr(fun, 'old', get_attr_from_cache(bl_ui_class, attr_name, None))
        def wrapper(_self, _context): # *args, **kwargs):
            print(_self, _context)
            if not fun.poll(_context):
                if fun.old is not None:
                    fun.old(_self, _context)
            else:
                fun(_self, _context)
        setattr(fun, 'old', set_cls_attribute(bl_ui_class, attr_name, wrapper))
        return wrapper
    # cache_cls_attributes(bl_ui_class)
    return decorator
