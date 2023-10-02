import addon_utils
from bl_ui.space_userpref import USERPREF_PT_addons, USERPREF_PT_navigation_bar, USERPREF_HT_header
from bpy.app.translations import (
    pgettext_iface as iface_,
    pgettext_tip as tip_,
)
import bpy
from bpy.types import Context, UILayout, AddonPreferences
from bpy.props import BoolProperty

import os
from collections import defaultdict

from .ui_addon_options import BETTERPREFS_MT_addon_options, BETTERPREFS_OT_show_addon_options
from .op_show_betterprefs import BETTERPREFS_OT_toggle_betterprefs


from ... import __package__
b3d_version = (*bpy.app.version[:2], 0)


_active_module_name: str = None

def get_active_module() -> None or str:
    global _active_module_name
    return _active_module_name

def get_addon_prefs(context: Context) -> AddonPreferences:
    if addon := context.preferences.addons.get(__package__, None):
        return addon.preferences


def toggle_addon_prefs(context: Context, module_name: str, enable: bool) -> None:
    global _active_module_name
    if enable:
        _active_module_name = module_name
    else:
        _active_module_name = None


# ----------------------------------------------------------------

def draw_error_labels(self: USERPREF_PT_addons, layout: UILayout) -> None:
    # set in addon_utils.modules_refresh()
    if addon_utils.error_duplicates:
        box = layout.box()
        row = box.row()
        row.label(text="Multiple add-ons with the same name found!")
        row.label(icon='ERROR')
        box.label(text="Delete one of each pair to resolve:")
        for (addon_name, addon_file, addon_path) in addon_utils.error_duplicates:
            box.separator()
            sub_col = box.column(align=True)
            sub_col.label(text=addon_name + ":")
            sub_col.label(text="    " + addon_file)
            sub_col.label(text="    " + addon_path)

    if addon_utils.error_encoding:
        self.draw_error(
            layout,
            "One or more addons do not have UTF-8 encoding\n"
            "(see console for details)",
        )


def draw_header(context: Context, layout: UILayout) -> None:
    wm = context.window_manager
    prefs = context.preferences

    split = layout.split(factor=0.6)

    row = split.row()
    row.prop(wm, "addon_support", expand=True)

    row = split.row(align=True)
    row.operator("preferences.addon_install", icon='IMPORT', text="Install...")
    row.operator("preferences.addon_refresh", icon='FILE_REFRESH', text="Refresh")

    row = layout.row()
    row.prop(prefs.view, "show_addons_enabled_only")
    row.prop(wm, "addon_filter", text="")
    row.prop(wm, "addon_search", text="", icon='VIEWZOOM')


# ----------------------------------------------------------------


def main__draw_navigation_bar(self: USERPREF_PT_navigation_bar, context: Context) -> None:
    global _active_module_name
    if _active_module_name is None:
        # print(self, context)
        USERPREF_PT_navigation_bar.old_draw(self, context)
        return

    layout: UILayout = self.layout
    addon_prefs = context.preferences.addons[_active_module_name].preferences
    col = layout.column()
    col.scale_x = 1.5
    col.scale_y = 1.5
    col.prop(addon_prefs, 'better_tabs', expand=True)


def main__draw_header(self: USERPREF_HT_header, context: Context) -> None:
    global _active_module_name
    if _active_module_name is None:
        # print(self, context)
        USERPREF_HT_header.old_draw(self, context)
        return

    layout: UILayout = self.layout
    op = layout.operator(BETTERPREFS_OT_toggle_betterprefs.bl_idname, text="Exit", icon='LOOP_BACK')
    op.module = _active_module_name
    op.enable = False


def main__draw_addon_prefs(self: USERPREF_PT_addons, context: Context):
    layout: UILayout = self.layout

    global _active_module_name
    if _active_module_name is not None:
        return

    addon_user_dirs = tuple(
        p for p in (
            *[os.path.join(pref_p, "addons") for pref_p in bpy.utils.script_paths_pref()],
            bpy.utils.user_resource('SCRIPTS', path="addons"),
        )
        if p
    )

    # collect the categories that can be filtered on
    addons = [
        (mod, addon_utils.module_bl_info(mod))
        for mod in addon_utils.modules(refresh=False)
    ]

    draw_header(context, layout)

    col = layout.column()

    draw_error_labels(self, col)

    wm = context.window_manager
    prefs = context.preferences
    used_ext = {ext.module for ext in prefs.addons}
    prefs_addons = prefs.addons

    show_enabled_only = prefs.view.show_addons_enabled_only
    filter = wm.addon_filter
    search = wm.addon_search.lower()
    support = wm.addon_support

    # initialized on demand
    user_addon_paths = []

    for mod, info in addons:
        module_name = mod.__name__

        is_enabled = module_name in used_ext

        if info["support"] not in support:
            continue

        # check if addon should be visible with current filters
        is_visible = (
            (filter == "All") or
            (filter == info["category"]) or
            (filter == "User" and (mod.__file__.startswith(addon_user_dirs)))
        )
        if show_enabled_only:
            is_visible = is_visible and is_enabled

        if not is_visible:
            continue

        if search and not (
                (search in info["name"].lower() or
                    search in iface_(info["name"]).lower()) or
                (info["author"] and (search in info["author"].lower())) or
                ((filter == "All") and (search in info["category"].lower() or
                                        search in iface_(info["category"]).lower()))
        ):
            continue

        user_addon = USERPREF_PT_addons.is_user_addon(mod, user_addon_paths)
        addon_prefs = prefs_addons.get(module_name, None)
        if addon_prefs:
            addon_prefs = addon_prefs.preferences
        use_better_prefs = user_addon and addon_prefs is not None and hasattr(addon_prefs, 'better_tabs')

        if use_better_prefs:
            draw_better_addon(self, context, col, mod, info, is_enabled=is_enabled)
        else:
            draw_addon(self, context, col, prefs, mod, info, is_enabled=is_enabled, user_addon=user_addon)

        if filter in {"All", "Enabled"}:
            draw_missing_addons(col, addons, used_ext)


def draw_better_addon(self: USERPREF_PT_addons, context: Context, layout: UILayout, mod, info: dict, is_enabled: bool):
    wrong_b3d_version = b3d_version != (*info["blender"][:2], 0)

    module_name = mod.__name__

    # Addon UI Code
    colbox = layout.column(align=True)
    row_box = colbox.row(align=True)

    if info["warning"] or wrong_b3d_version:
        box = row_box.box()
        row = box.row(align=True)
        row.alert = wrong_b3d_version
        row.label(icon='ERROR')

    box = row_box.box()
    row = box.row(align=True)

    row.operator(
        "preferences.addon_disable" if is_enabled else "preferences.addon_enable",
        icon='CHECKBOX_HLT' if is_enabled else 'CHECKBOX_DEHLT', text="",
        emboss=False,
    ).module = module_name

    name = f'{iface_(info["name"])}  -  {".".join(str(x) for x in info["version"])}'
    row.label(text=name)

    if info["doc_url"] or info.get("tracker_url"):
        sub = row.row(align=True)
        if info["doc_url"]:
            sub.operator("wm.url_open", text="", text_ctxt="Documentation", icon='HELP').url = info["doc_url"]
        if info.get("tracker_url"):
            sub.operator("wm.url_open", text="", text_ctxt="Report a Bug", icon='URL').url = info["tracker_url"]

    box = row_box.box()
    box.alignment = 'RIGHT'
    row = box.row(align=True)
    row.emboss = 'PULLDOWN_MENU'
    row.scale_x = 1.1

    op = row.operator(BETTERPREFS_OT_toggle_betterprefs.bl_idname, text="", icon='PROPERTIES')
    op.module = module_name
    op.enable = True
    row = row.row(align=True)
    row.scale_x = 0.9
    op = row.operator(BETTERPREFS_OT_show_addon_options.bl_idname, text='', icon='DOWNARROW_HLT')
    op.module_name = module_name
    op.addon_name = info['name']


def draw_addon(self: USERPREF_PT_addons, context: Context, layout: UILayout, prefs, mod: str, info: dict, is_enabled: bool, user_addon: bool):
    module_name = mod.__name__

    # Addon UI Code
    col_box = layout.column()
    box = col_box.box()
    colsub = box.column()
    row = colsub.row(align=True)

    row.operator(
        "preferences.addon_expand",
        icon='DISCLOSURE_TRI_DOWN' if info["show_expanded"] else 'DISCLOSURE_TRI_RIGHT',
        emboss=False,
    ).module = module_name

    row.operator(
        "preferences.addon_disable" if is_enabled else "preferences.addon_enable",
        icon='CHECKBOX_HLT' if is_enabled else 'CHECKBOX_DEHLT', text="",
        emboss=False,
    ).module = module_name

    sub = row.row()
    sub.active = is_enabled
    sub.label(text=iface_("%s: %s") % (iface_(info["category"]), iface_(info["name"])))

    if info["warning"]:
        sub.label(icon='ERROR')

    # icon showing support level.
    sub.label(icon=self._support_icon_mapping.get(info["support"], 'QUESTION'))

    # Expanded UI (only if additional info is available)
    if info["show_expanded"]:
        if info["description"]:
            split = colsub.row().split(factor=0.15)
            split.label(text="Description:")
            split.label(text=tip_(info["description"]))
        if info["location"]:
            split = colsub.row().split(factor=0.15)
            split.label(text="Location:")
            split.label(text=tip_(info["location"]))
        if mod:
            split = colsub.row().split(factor=0.15)
            split.label(text="File:")
            split.label(text=mod.__file__, translate=False)
        if info["author"]:
            split = colsub.row().split(factor=0.15)
            split.label(text="Author:")
            split.label(text=info["author"], translate=False)
        if info["version"]:
            split = colsub.row().split(factor=0.15)
            split.label(text="Version:")
            split.label(text=".".join(str(x) for x in info["version"]), translate=False)
        if info["warning"]:
            split = colsub.row().split(factor=0.15)
            split.label(text="Warning:")
            split.label(text="  " + info["warning"], icon='ERROR')

        if info["doc_url"] or info.get("tracker_url"):
            split = colsub.row().split(factor=0.15)
            split.label(text="Internet:")
            sub = split.row()
            if info["doc_url"]:
                sub.operator(
                    "wm.url_open", text="Documentation", icon='HELP',
                ).url = info["doc_url"]
            # Only add "Report a Bug" button if tracker_url is set
            # or the add-on is bundled (use official tracker then).
            if info.get("tracker_url"):
                sub.operator(
                    "wm.url_open", text="Report a Bug", icon='URL',
                ).url = info["tracker_url"]
            elif not user_addon:
                addon_info = (
                    "Name: %s %s\n"
                    "Author: %s\n"
                ) % (info["name"], str(info["version"]), info["author"])
                props = sub.operator(
                    "wm.url_open_preset", text="Report a Bug", icon='URL',
                )
                props.type = 'BUG_ADDON'
                props.id = addon_info

        if user_addon:
            split = colsub.row().split(factor=0.15)
            split.label(text="User:")
            split.operator(
                "preferences.addon_remove", text="Remove", icon='CANCEL',
            ).module = mod.__name__

        # Show addon user preferences
        if not is_enabled:
            return

        addon_preferences = prefs.addons[module_name].preferences
        if addon_preferences is not None:
            draw = getattr(addon_preferences, "draw", None)
            if draw is not None:
                addon_preferences_class = type(addon_preferences)
                box_prefs = col_box.box()
                box_prefs.label(text="Preferences:")
                addon_preferences_class.layout = box_prefs
                try:
                    draw(context)
                except:
                    import traceback
                    traceback.print_exc()
                    box_prefs.label(text="Error (see console)", icon='ERROR')
                del addon_preferences_class.layout


def draw_missing_addons(layout: UILayout, addons: list, used_ext: set) -> None:
    # Append missing scripts
    # First collect scripts that are used but have no script file.
    module_names = {mod.__name__ for mod, info in addons}
    missing_modules = {ext for ext in used_ext if ext not in module_names}

    if not missing_modules:
        return

    layout.column().separator()
    layout.column().label(text="Missing script files")

    module_names = {mod.__name__ for mod, info in addons}
    for module_name in sorted(missing_modules):
        is_enabled = module_name in used_ext
        # Addon UI Code
        box = layout.column().box()
        colsub = box.column()
        row = colsub.row(align=True)

        row.label(text="", icon='ERROR')

        if is_enabled:
            row.operator(
                "preferences.addon_disable", icon='CHECKBOX_HLT', text="", emboss=False,
            ).module = module_name

        row.label(text=module_name, translate=False)


# ----------------------------------------------------------------

_overrided_cls_attributes = defaultdict(set)
_backup_cls_attributes = {}


def override_cls_attr(cls, attr: str, new_value):
    # Check if was overridden by another addon.
    old_attr = 'old_' + attr
    if hasattr(cls, old_attr):
        # SKIP!
        return False

    # Backup cls attributes.
    if cls not in _backup_cls_attributes:
        _backup_cls_attributes[cls] = cls.__dict__.copy()

    # Add new overrided cls attr.
    _overrided_cls_attributes[cls].add(attr)

    # Add reference to old (to override) cls attr.
    if hasattr(cls, attr):
        setattr(cls, old_attr, _backup_cls_attributes[cls][attr])

    # Override cls attr.
    setattr(cls, attr, new_value)

    return True


def revert_override():
    for cls, overrided_attributes in _overrided_cls_attributes.items():
        cls_backup = _backup_cls_attributes[cls]
        for attr in overrided_attributes:
            old_attr = 'old_' + attr
            if hasattr(cls, old_attr):
                delattr(cls, old_attr)
                setattr(cls, attr, cls_backup[attr])
            else:
                if hasattr(cls, attr):
                    delattr(cls, attr)

        del _backup_cls_attributes[cls]

    _backup_cls_attributes.clear()
    _overrided_cls_attributes.clear()


def get_backup_cls_attribute(cls, attr: str):
    return _backup_cls_attributes[cls][attr]


def recover_cls_attribute(cls, attr):
    cls_backup = _backup_cls_attributes[cls]
    old_attr = 'old_' + attr
    if hasattr(cls, old_attr):
        delattr(cls, old_attr)
        setattr(cls, attr, cls_backup[attr])
    else:
        if hasattr(cls, attr):
            delattr(cls, attr)

    _overrided_cls_attributes[cls].remove(attr)
    if len(_overrided_cls_attributes[cls]) == 0:
        del _overrided_cls_attributes[cls]
        del _backup_cls_attributes[cls]


# ----------------------------------------------------------------

def register():
    # override_cls_attr(PREFERENCES_OT_addon_remove, 'execute', addon_remove)
    if override_cls_attr(USERPREF_PT_addons, 'draw', main__draw_addon_prefs):
        USERPREF_PT_addons.better_modules = {__package__}

        override_cls_attr(USERPREF_PT_navigation_bar, 'draw', main__draw_navigation_bar)
        override_cls_attr(USERPREF_HT_header, 'draw', main__draw_header)
    else:
        USERPREF_PT_addons.better_modules.add(__package__)

    AddonPreferences.show_better_preferences = BoolProperty()


def unregister():
    USERPREF_PT_addons.better_modules.remove(__package__)
    if len(USERPREF_PT_addons.better_modules) == 0:
        recover_cls_attribute(USERPREF_PT_addons, 'draw')
        del USERPREF_PT_addons.better_modules

        recover_cls_attribute(USERPREF_PT_navigation_bar, 'draw')
        recover_cls_attribute(USERPREF_HT_header, 'draw')

    # revert_override()
    _backup_cls_attributes.clear()
    _overrided_cls_attributes.clear()
