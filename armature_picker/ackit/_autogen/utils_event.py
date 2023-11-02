import bpy
from bpy.types import Event, View2D, Context
from mathutils import Vector, Matrix
from string import Template
from pathlib import Path


global_vars_code_snippet = """
class Event:
    type: str
    value: str
    shift: bool
    ctrl: bool
    alt: bool


EVENT_TYPE = 'NONE'
EVENT_VALUE = 'NONE'
EVENT_MODIFIERS = { # Ctrl, Shift, Alt states.
    'ctrl':     False,
    'shift':    False,
    'alt':      False
} 

def set_global_event(event: Event):
    global EVENT_TYPE
    global EVENT_VALUE
    global EVENT_MODIFIERS
    EVENT_TYPE = event.type
    EVENT_VALUE = event.value
    EVENT_MODIFIERS['alt'] = event.alt
    EVENT_MODIFIERS['ctrl'] = event.ctrl
    EVENT_MODIFIERS['shift'] = event.shift

def get_global_event() -> tuple[str, str]:
    global EVENT_TYPE
    global EVENT_VALUE
    return EVENT_TYPE, EVENT_VALUE
"""

event_check_property_template = Template(
"""
    _${event}: str = '${event}'
    @property
    def ${event}(self) -> bool: global ${global_name}; return ${global_name} == '${event}'
"""
)


gevent_code_snippet = """

isEventValue = _isEventValue()
isEventType  = _isEventType()


class GEvent:
    TYPE = _isEventType
    VALUE = _isEventValue

    @staticmethod
    def check(event_type: str, event_value: str, shift: bool = None, alt: bool = None, ctrl: bool = None) -> bool:
        global EVENT_TYPE
        global EVENT_VALUE
        global EVENT_MODIFIERS
        if shift is not None and EVENT_MODIFIERS['shift'] != shift:
            return False
        if alt is not None and EVENT_MODIFIERS['alt'] != alt:
            return False
        if ctrl is not None and EVENT_MODIFIERS['ctrl'] != ctrl:
            return False
        return event_type == EVENT_TYPE and event_value == EVENT_VALUE

isEvent = GEvent.check
"""


out_event_enums_path = Path(__file__).parent / 'output' / 'event_enums.py'
out_event_globals_path = Path(__file__).parent / 'output' / 'event_globals.py'


def init():
    if out_event_enums_path.exists() and out_event_globals_path.exists():
        return

    event_types = bpy.types.Event.bl_rna.properties['type'].enum_items
    event_values = bpy.types.Event.bl_rna.properties['value'].enum_items
    
    with out_event_enums_path.open('w') as f:
        # ENUMS...
        f.write("\n\nclass EventValue:\n")

        for event_value in event_values:
            v = event_value.identifier
            f.write(f"    {v} = '{v}'\n")

        f.write("\n\nclass EventType:\n")

        for event_type in event_types:
            v = event_type.identifier
            f.write(f"    {v} = '{v}'\n")

    with out_event_globals_path.open('w') as f:
        f.write(global_vars_code_snippet)

        # GLOBALS...
        f.write("\n\nclass _isEventValue:")

        for event_value in event_values:
            f.write(event_check_property_template.substitute(
                global_name='EVENT_VALUE',
                event=event_value.identifier
            ))

        f.write("\n\nclass _isEventType:")

        for event_type in event_types:
            f.write(event_check_property_template.substitute(
                global_name='EVENT_TYPE',
                event=event_type.identifier
            ))

        f.write(gevent_code_snippet)
