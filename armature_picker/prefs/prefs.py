from bpy.types import AddonPreferences, Context
from bpy.props import CollectionProperty, IntProperty, PointerProperty, EnumProperty

from ..ackit._globals import __main_package__
from .themes import PG_ArmaturePickerTheme
from .settings import PG_ArmaturePicker_WidgetSettings
from ..utils.ui_layout import draw_section_h, draw_section
from ..utils.node_editor import get_armature_picker_editor


class ArmaturePickerPreferences(AddonPreferences):
    bl_idname = __main_package__


    # ----------------------------------------------------------------
    # THEMES
    # ----------------------------------------------------------------

    def update_active_theme(self, context: Context) -> None:
        if area := get_armature_picker_editor(context, ret_area=True):
            node_editor = area.spaces[0]
            node_tree = node_editor.node_tree
            if node_tree is None:
                return
            for node in node_tree.nodes:
                node.dirty = True
                node.dirty_label = True
            area.tag_redraw()

    def get_themes(self, context: Context) -> tuple:
        if (self.user_themes) == 0:
            return (('DEFAULT', "Default", ""),)
        else:
            return (('DEFAULT', "Default", ""), *[(th.name, th.name, '') for th in self.user_themes])

    default_theme: PointerProperty(type=PG_ArmaturePickerTheme)
    user_themes: CollectionProperty(type=PG_ArmaturePickerTheme)
    active_theme_id: EnumProperty(
        name="Active Theme",
        items=get_themes,
        update=update_active_theme
    )

    @property
    def active_theme(self) -> PG_ArmaturePickerTheme:
        if self.active_theme_id == 'DEFAULT':
            return self.default_theme
        return self.user_themes[self.active_theme_id]


    # ----------------------------------------------------------------
    # WIDGET SETTINGS
    # ----------------------------------------------------------------

    wg_settings: PointerProperty(type=PG_ArmaturePicker_WidgetSettings)

    def draw(self, context: Context) -> None:
        wg_settings_section = draw_section(self.layout, 'Widget Settings', icon='COLOR')
        self.wg_settings.draw(wg_settings_section)

        themes_header, theme_section = draw_section_h(self.layout, 'Themes', icon='COLOR')
        themes_header.scale_y = 1.5
        themes_header.prop(self, 'active_theme_id', text='')
        actions = themes_header.row(align=True)
        actions.scale_x = 1.5
        actions.operator('armature_picker.new_theme', icon='ADD', text='')
        if self.active_theme_id != 'DEFAULT':
            actions.alert = True
            actions.operator('armature_picker.remove_theme', icon='REMOVE', text='')
        theme = self.active_theme
        theme.draw(theme_section)
