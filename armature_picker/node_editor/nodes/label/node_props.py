from bpy.types import Context, UILayout, Armature
from bpy.props import StringProperty, IntProperty, FloatProperty, BoolProperty, FloatVectorProperty, EnumProperty
from blf import size as set_text_size, dimensions as get_text_dimensions



class APNODE_Label_NodeProps:

    # UPDATE FUNCTIONS
    # ----------------------------------------------------------------
    def update_label(self, context: Context) -> None:
        set_text_size(0, self.text_size)
        self.dimensions = get_text_dimensions(0, 'X' if self.text == '' else self.text)

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

    def draw_buttons_ext(self, context: Context, layout: UILayout) -> None:
        layout.prop(self, 'text')
