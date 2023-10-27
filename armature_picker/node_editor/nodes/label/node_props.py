from bpy.types import Context, UILayout, Armature
from bpy.props import StringProperty, IntProperty, PointerProperty, BoolProperty
from blf import size as set_text_size, dimensions as get_text_dimensions

from armature_picker.prefs.styles import Label_Style


class APNODE_Label_NodeProps:
    def get_style(self, theme) -> Label_Style:
        if self.use_override_theme:
            return self.style
        return getattr(theme, self.wg_type)

    style: PointerProperty(name="Style", type=Label_Style)

    # UPDATE FUNCTIONS
    # ----------------------------------------------------------------
    def update_label(self, context: Context) -> None:
        set_text_size(0, self.text_size)
        self.rect_transform.dimensions = [int(v) for v in get_text_dimensions(0, 'X' if self.text == '' else self.text)]

        self.dirty_label = True
        self.update_graphics(context)


    # BUTTON PROPERTIES
    # ----------------------------------------------------------------

    text: StringProperty(
        name="Text",
        default='Super Cool Label',
        description="Label Text",
        update=update_label,
        options={'TEXTEDIT_UPDATE'}
    )
    
    text_size: IntProperty(
        name='Text Size',
        description="Label text size",
        default=24,
        min=10,
        update=update_label
    )

    def draw_wg_props(self, context: Context, layout: UILayout) -> None:
        layout.prop(self, 'text')
        layout.prop(self, 'text_size')
