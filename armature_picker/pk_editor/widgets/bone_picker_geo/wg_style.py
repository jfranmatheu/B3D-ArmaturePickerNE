from bpy.types import UILayout, Context

from armature_picker.ackit import ACK
from .._base_wg_style import StyleBase
from armature_picker.ackit._globals import __main_package__


'''
NOTE: BonePickerGeo Styles are special...
- We need to define different style-sets for these widgets, so that we can have different tags to set custom colors. atm just a hard-coded 10 colors.
- Will always use the preferences theme style and the self widget style. (a combination of the two)
- Will take the color from the prefs theme style based on the selected tag (stored in the widget self-style class).
'''


default_color_tags = (
    ('Default', (0.969, 0.223, 0.07, 1.0)),
    ('Spine', (0.961, 0.969, 0.235, 1.0)),
    ('Head', (0.365, 0.969, 0.235, 1.0)),
    ('Leg R', (0.235, 0.655, 0.969, 1.0)),
    ('Leg L', (0.969, 0.282, 0.235, 1.0)),
    ('Arm R', (0.235, 0.655, 0.969, 1.0)),
    ('Arm L', (0.969, 0.282, 0.235, 1.0)),
    ('Facial', (0.51, 0.11, 0.969, 1.0)),
    ('Facial R', (0.235, 0.843, 0.969, 1.0)),
    ('Facial L', (0.969, 0.235, 0.439, 1.0)),
)

color_tags = []



@ACK.Deco.PROP_GROUP.CHILD
class PG_ArmaturePicker_ColorTag:
    name: ACK.Prop.STRING(
        name="Tag Name",
        default='Tag Name',
        update=lambda self, ctx: color_tags.clear()
    )
    color: ACK.Prop.COLOR_RGBA("Color", (.05, .51, .95, 1.0))


@ACK.Deco.PROP_GROUP.CHILD
class PG__BonePickerGeo__Style(StyleBase):
    color_tag_0: ACK.Prop.POINTER.CUSTOM('Color Tag 1', PG_ArmaturePicker_ColorTag)
    color_tag_1: ACK.Prop.POINTER.CUSTOM('Color Tag 2', PG_ArmaturePicker_ColorTag)
    color_tag_2: ACK.Prop.POINTER.CUSTOM('Color Tag 3', PG_ArmaturePicker_ColorTag)
    color_tag_3: ACK.Prop.POINTER.CUSTOM('Color Tag 4', PG_ArmaturePicker_ColorTag)
    color_tag_4: ACK.Prop.POINTER.CUSTOM('Color Tag 5', PG_ArmaturePicker_ColorTag)
    color_tag_5: ACK.Prop.POINTER.CUSTOM('Color Tag 6', PG_ArmaturePicker_ColorTag)
    color_tag_6: ACK.Prop.POINTER.CUSTOM('Color Tag 7', PG_ArmaturePicker_ColorTag)
    color_tag_7: ACK.Prop.POINTER.CUSTOM('Color Tag 8', PG_ArmaturePicker_ColorTag)
    color_tag_8: ACK.Prop.POINTER.CUSTOM('Color Tag 9', PG_ArmaturePicker_ColorTag)
    color_tag_9: ACK.Prop.POINTER.CUSTOM('Color Tag 10', PG_ArmaturePicker_ColorTag)

    initialized: ACK.Prop.BOOL()

    def ensure_color_tags(self):
        if not self.initialized:
            for idx, (tag_name, tag_color) in enumerate(default_color_tags):
                color_tag = getattr(self, 'color_tag_' + str(idx))
                setattr(color_tag, 'name', tag_name)
                setattr(color_tag, 'color', tag_color)
            self.initialized = True

    def draw(self, layout: UILayout, in_prefs_space: bool) -> None:
        if not in_prefs_space:
            return
        self.ensure_color_tags()
        col = layout.column()
        col.label(text='Color Tags')
        col.use_property_split = False
        for i in range(10):
            color_tag = getattr(self, 'color_tag_' + str(i))
            row = col.row(align=True, heading='    %i' % (i + 1))
            row.prop(color_tag, 'name', text='')
            row.prop(color_tag, 'color', text='')


@ACK.Deco.PROP_GROUP.CHILD
class PG__BonePickerGeo__LocalStyle:
    def get_color_tags(self, context: Context) -> tuple:
        if len(color_tags) == 0:
            prefs = context.preferences.addons[__main_package__].preferences
            th__bone_picker_geo = prefs.active_theme.bone_picker_geo
            for i in range(10):
                color_tag_prop_name = 'color_tag_' + str(i)
                color_tag = getattr(th__bone_picker_geo, color_tag_prop_name)
                color_tags.append((color_tag_prop_name, color_tag.name, ''))
        return color_tags

    def update_color(self, context: Context) -> None:
        context.area.tag_redraw()

    use_object_color: ACK.Prop.BOOL(name="Color from Mesh", description="Use color from source mesh", default=False, update=update_color)
    color_tag: ACK.Prop.ENUM(
        name="Color Tag",
        items=get_color_tags,
        update=update_color
    )

    def get_color(self, theme_style: PG__BonePickerGeo__Style) -> tuple:
        theme_style.ensure_color_tags()
        if color_tag := getattr(theme_style, self.color_tag, None):
            return color_tag.color
        return (1, 1, 1, 1)

    def draw(node, layout: UILayout, in_prefs_space: bool = False) -> None:
        layout.prop(node, 'use_object_color')
        row = layout.row(align=True)
        row.enabled = not node.use_object_color
        row.prop(node, 'color_tag')
