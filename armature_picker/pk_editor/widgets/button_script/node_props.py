from bpy.props import PointerProperty
from bpy.types import Text, Context, UILayout, Operator, NodeTree
from bpy import ops as BPY_OPS
import bpy
from rna_prop_ui import rna_idprop_quote_path

from armature_picker.utils.ui_layout import draw_section
from armature_picker.ackit import ACK
from armature_picker.ops import Ops as AP_OPS
from .wg_style import PG__ButtonScript__Style
from .._button_common import APNODE_Button_Common
from .ops import AP_OT_create_open_wg_button_script



valid_modules = {
    'view3d', 'pose', 'object', 'armature',
}

op_modules = [
    (op_mod_name, op_mod_name.title(), '') for op_mod_name in dir(BPY_OPS) if op_mod_name in valid_modules
]
op_modules_search = [op_mod[0] for op_mod in op_modules]

def get_op_item_enum(op_id: str, op: Operator):
    return (op_id, op.bl_label if hasattr(op, 'bl_label') else op_id.replace('_', ' ').title(), op.bl_description if hasattr(op, 'bl_description') else '')

op_module_ids_enum = {
    op_mod_name: [
        get_op_item_enum(op_id, getattr(getattr(BPY_OPS, op_mod_name), op_id)) for op_id in dir(getattr(BPY_OPS, op_mod_name))
    ]
    for op_mod_name in dir(BPY_OPS) if op_mod_name in valid_modules
}

def get_op_label(op_id: str, op: Operator):
    return op.bl_label if hasattr(op, 'bl_label') else op_id.replace('_', ' ').title()

op_module_ids_search = {
    op_mod_name: {
        get_op_label(op_id, getattr(getattr(BPY_OPS, op_mod_name), op_id).get_rna_type()): op_id for op_id in dir(getattr(BPY_OPS, op_mod_name))
    }
    for op_mod_name in dir(BPY_OPS) if op_mod_name in valid_modules
}


@ACK.Deco.PROP_GROUP.CHILD
class OperatorPropertiesIdnames:
    name: ACK.Prop.STRING()
    op_idname: ACK.Prop.STRING()
    temp_idname: ACK.Prop.STRING()


class APNODE_ButtonScript_NodeProps(APNODE_Button_Common):
    def get_style(self, theme) -> PG__ButtonScript__Style:
        if self.use_override_theme:
            return self.style
        return getattr(theme, self.wg_type)
    style: PointerProperty(name="Style", type=PG__ButtonScript__Style)


    # SCRIPT --------------------------------------------------------------------------------
    script_text: PointerProperty(name="Script", description="Script Text Datablock", type=Text)


    # OPERATOR ------------------------------------------------------------------------------
    def update_op_idname(self, context: Context) -> None:
        if op_module := getattr(BPY_OPS, self.op_module):
            if self.op_id != '':
                if operator := getattr(op_module, self.op_id, None):
                    self.invalid_command = False
                    self.operator = operator.get_rna_type()
                    self.label = self.op_action
                    self.update_op_props()
                    return
        self.label = 'Invalid Operator'
        self.invalid_command = True

    def search_ops_modules(button, _context, edit_text: str) -> tuple:
        if not edit_text:
            return op_modules_search
        _edit_text = edit_text.lower()
        startswith = []
        contains = []
        for name in op_modules_search:
            _name = name.lower()
            if _name.startswith(_edit_text):
                startswith.append(name)
            elif _edit_text in _name:
                contains.append(name)
        return startswith + contains

    def search_ops_idname_paths(button, _context, edit_text: str) -> tuple:
        ops_ids= op_module_ids_search[button.op_module]
        if not edit_text:
            return ops_ids
        _edit_text = edit_text.lower()
        startswith = []
        contains = []
        for name in ops_ids:
            _name = name.lower()
            if _name.startswith(_edit_text):
                startswith.append(name)
            elif _edit_text in _name:
                contains.append(name)
        return startswith + contains

    button_type: ACK.Prop.ENUM(
        name='Button Type',
        items=(
            ('SCRIPT', 'Script', "Executes an script file"),
            ('OPERATOR', 'Operator', "Executes an operator"),
        ),
        default='SCRIPT',
    )
    operator: ACK.Type.OPS.ACTION = None
    invalid_command: ACK.Prop.BOOL(default=False)
    op_module: ACK.Prop.ENUM(
        name="Operator Module",
        items=op_modules,
        update=update_op_idname
        # search=search_ops_modules
    )
    @property
    def op_id(self) -> str:
        if self.op_action == '':
            return ''
        return op_module_ids_search[self.op_module][self.op_action]

    op_action: ACK.Prop.STRING(
        name="Operator Action",
        # items=lambda wg, _ctx: op_module_ids[wg.op_module],
        # update=update_op_idname
        search=search_ops_idname_paths,
        update=update_op_idname
    )
    op_props_idnames: ACK.Prop.COLLECTION(OperatorPropertiesIdnames)

    def cleanup_temp_op_props(self):
        if not self.op_props_idnames:
            return
        for prop in self.op_props_idnames:
            # print("removing temp operator property...", prop.op_idname, prop.temp_idname)
            if prop.temp_idname and hasattr(bpy.types.WindowManager, prop.temp_idname):
                exec('del bpy.types.WindowManager.' + prop.temp_idname, globals())
            custom_prop_idname = 'op@' + prop.op_idname
            if custom_prop_idname in self:
                del self[custom_prop_idname]
        self.op_props_idnames.clear()
        self.set_state('INIT_OP_PROPS', False)

    def update_op_prop(self, context: Context, op_prop: OperatorPropertiesIdnames) -> None:
        self['op@' + op_prop.op_idname] = getattr(context.window_manager, op_prop.temp_idname)

    def update_op_props(self) -> None:
        # Cleanup previous operator properties...
        #for output in reversed(self.outputs):
        #    if output.name == 'Operator':
        #        continue
        #    self.outputs.remove(output)
        self.cleanup_temp_op_props()

        op = self.get_op()
        if op is None:
            return

        _id = self.uuid[:4] + self.uuid[-4:]
        for prop_id, op_prop in op.properties.items():
            if prop_id == 'rna_type':
                continue
            if prop_id.startswith('_'):
                continue
            prop = self.op_props_idnames.add()
            prop.name = op_prop.name
            prop.op_idname = prop_id
            prop.temp_idname = 'temp__' + _id + '_' + prop_id

            # print("New operator prop:", prop_id, prop.temp_idname)

            shared_props = dict(name=op_prop.name, description=op_prop.description, default=op_prop.default, options=set(),
                                update=lambda node_tree, ctx: self.update_op_prop(ctx, prop))

            if op_prop.is_skip_save:
                shared_props['options'].add('SKIP_SAVE')

            if isinstance(op_prop, (bpy.types.IntProperty, bpy.types.FloatProperty)):
                shared_props['min'] = op_prop.hard_min
                shared_props['soft_min'] = op_prop.soft_min
                shared_props['max'] = op_prop.hard_max
                shared_props['soft_max'] = op_prop.soft_max
                shared_props['subtype'] = op_prop.subtype

            if isinstance(op_prop, (bpy.types.IntProperty, bpy.types.FloatProperty, bpy.types.BoolProperty)):
                if op_prop.is_array:
                    shared_props['size'] = op_prop.array_length
                    shared_props['default'] = op_prop.default_array

            if isinstance(op_prop, bpy.types.StringProperty):
                ppt = ACK.Prop.STRING(subtype=op_prop.subtype, **shared_props)
            elif isinstance(op_prop, bpy.types.EnumProperty):
                items = tuple(
                    (item.identifier, item.name, item.description)
                    for item in op_prop.enum_items
                )
                # TODO: support options flags.
                if op_prop.is_enum_flag:
                    del shared_props['default']
                    shared_props['options'].add('ENUM_FLAG')
                ppt = ACK.Prop.ENUM(items=items, **shared_props)
            elif isinstance(op_prop, bpy.types.IntProperty):
                if op_prop.is_array:
                    ppt = ACK.Prop.INT_VECTOR(**shared_props)
                else:
                    ppt = ACK.Prop.INT(**shared_props)
            elif isinstance(op_prop, bpy.types.FloatProperty):
                if op_prop.is_array:
                    ppt = ACK.Prop.FLOAT_VECTOR(**shared_props)
                else:
                    ppt = ACK.Prop.FLOAT(**shared_props)
            elif isinstance(op_prop, bpy.types.BoolProperty):
                if op_prop.is_array:
                    ppt = ACK.Prop.BOOL_VECTOR(**shared_props)
                else:
                    ppt = ACK.Prop.BOOL(**shared_props)
            else:
                print("NONE")
                continue

            # print("runtime register prop:", prop.temp_idname, ppt)
            ACK.Helper.PROP_RUNTIME(bpy.types.WindowManager, prop.temp_idname, ppt)
            self['op@' + prop_id] = shared_props['default']
        
        self.set_state('INIT_OP_PROPS', True)


    def get_op(self, rna: bool = True) -> Operator:
        if self.operator is not None and rna:
            return self.operator
        try:
            operator_idname = 'bpy.ops.' + self.op_module + '.' + self.op_id
            op: Operator = eval(operator_idname)
            if rna:
                op = op.get_rna_type()
        except Exception as e:
            print("BAD OPERATOR:", e)
            return
        return op

    def get_op_props(self, context: Context) -> dict:
        if self.get_state('INIT_OP_PROPS', False):
            wm = context.window_manager
            return {
                op_prop.op_idname: getattr(wm, op_prop.temp_idname) for op_prop in self.op_props_idnames
            }
        else:
            return {
                op_prop.op_idname: self['op@' + op_prop.op_idname] for op_prop in self.op_props_idnames
            }


    # UI -----------------------------------------------------------------------------------

    def draw_wg_props(self, context: Context, layout: UILayout) -> None:
        # layout.prop(self, 'script_text', icon='TEXT')
        super().draw_wg_props(context, layout)
        if self.button_type == 'SCRIPT':
            layout.scale_y = 1.5
            layout.operator(AP_OT_create_open_wg_button_script.bl_idname,
                            text="Open Script" if self.script_text is not None else "Create Script",
                            icon='TEXT')

    def draw_ui__edit(self, context: Context, layout: UILayout) -> None:
        if self.button_type == 'OPERATOR':
            if AP_OPS.PickLayoutButton.operator.is_modal_running: # GLOBALS.get_addon_global_value('IS_PICKING_DATAPATH', False):
                box = layout.box()
                col = box.column(align=True)
                col.label(text='', icon='INFO')
                col.alert = True
                col.label(text='Right Click a Button')

            else:
                col = layout.column(align=True)
                _row = col.row(align=True)
                AP_OPS.PickLayoutButton.draw_in_layout(_row, label='Pick Operator from UI', icon='EYEDROPPER')
                col.separator()
                col.label(text="Operator", icon='SCRIPTPLUGINS')
                col.scale_y = 1.4
                col.use_property_split = False
                if self.invalid_command:
                    col.alert = True
                col.prop(self, 'op_module', text='Context')
                col.prop(self, 'op_action', text='Action')
                if self.invalid_command:
                    col.alert = False
                
                if len(self.op_props_idnames) != 0:
                    props_are_initialized = self.get_state('INIT_OP_PROPS', False)
                    content = draw_section(layout, 'Operator Properties', icon='PROPERTIES', align_content=not props_are_initialized)
                    if props_are_initialized:
                        wm = context.window_manager
                        for op_prop in self.op_props_idnames:
                            content.prop(wm, op_prop.temp_idname)
                    else:
                        content.enabled = False
                        for op_prop in self.op_props_idnames:
                            content.prop(self, rna_idprop_quote_path('op@' + op_prop.op_idname), text=op_prop.name)
