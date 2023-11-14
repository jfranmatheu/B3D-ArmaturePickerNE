from bpy.types import PropertyGroup
from bpy.props import FloatVectorProperty

from armature_picker.pk_editor.widgets._button_style_common import CommonTheme__Button, call_active_node_func


class PG__ButtonScript__Style(CommonTheme__Button, PropertyGroup):
    color: FloatVectorProperty(
        name="Background Color",
        description="Background Color of the button",
        default=(.09, .1, .11, 1.0),
        size=4,
        min=0.0,
        max=1.0,
        subtype='COLOR'
    )

    text_color: FloatVectorProperty(
        name='Text Color',
        description="Label text color",
        default=(.9, .9, .9, 1.0),
        size=4,
        min=0.0,
        max=1.0,
        subtype='COLOR',
        update=call_active_node_func('update_label')
    )
