from bpy.types import AnyType, PropertyGroup, UILayout, Context, UIList
from bpy.props import FloatVectorProperty, BoolProperty, CollectionProperty, StringProperty, EnumProperty, IntProperty, PointerProperty

from ._base import StyleBase
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



class PG_ArmaturePicker_ColorTag(PropertyGroup):
    name: StringProperty(
        name="Tag Name",
        default='Tag Name',
        update=lambda self, ctx: color_tags.clear()
    )
    color: FloatVectorProperty(
        name="Color",
        description="Color of the button",
        default=(.05, .51, .95, 1.0),
        size=4,
        min=0.0,
        max=1.0,
        subtype='COLOR',
        # update=lambda self, ctx: color_tags.clear()
    )


class PG_ArmaturePickerTheme__BonePickerGeo(StyleBase, PropertyGroup):
    color_tag_0: PointerProperty(type=PG_ArmaturePicker_ColorTag)
    color_tag_1: PointerProperty(type=PG_ArmaturePicker_ColorTag)
    color_tag_2: PointerProperty(type=PG_ArmaturePicker_ColorTag)
    color_tag_3: PointerProperty(type=PG_ArmaturePicker_ColorTag)
    color_tag_4: PointerProperty(type=PG_ArmaturePicker_ColorTag)
    color_tag_5: PointerProperty(type=PG_ArmaturePicker_ColorTag)
    color_tag_6: PointerProperty(type=PG_ArmaturePicker_ColorTag)
    color_tag_7: PointerProperty(type=PG_ArmaturePicker_ColorTag)
    color_tag_8: PointerProperty(type=PG_ArmaturePicker_ColorTag)
    color_tag_9: PointerProperty(type=PG_ArmaturePicker_ColorTag)
    
    initialized: BoolProperty()
    
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


class PG__BonePickerGeo__Style(StyleBase, PropertyGroup):
    def get_color_tags(self, context: Context) -> tuple:
        if len(color_tags) == 0:
            prefs = context.preferences.addons[__main_package__].preferences
            th__bone_picker_geo = prefs.active_theme.bone_picker_geo
            for i in range(10):
                color_tag_prop_name = 'color_tag_' + str(i)
                color_tag = getattr(th__bone_picker_geo, color_tag_prop_name)
                color_tags.append((color_tag_prop_name, color_tag.name, ''))
        return color_tags

    color_tag: EnumProperty(
        name="Color Tag",
        items=get_color_tags
    )

    def get_color(self, theme_style: PG_ArmaturePickerTheme__BonePickerGeo) -> tuple:
        theme_style.ensure_color_tags()
        if color_tag := getattr(theme_style, self.color_tag, None):
            return color_tag.color
        return (1, 1, 1, 1)

    def draw(node, layout: UILayout, in_prefs_space: bool = False) -> None:
        row = layout.row(align=True)
        row.prop(node, 'color_tag')
