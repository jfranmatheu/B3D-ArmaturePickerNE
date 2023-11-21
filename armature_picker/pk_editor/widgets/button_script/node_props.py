from bpy.props import PointerProperty
from bpy.types import Text, Context, UILayout
from bpy import ops as BPY_OPS

from armature_picker.ackit import ACK
from armature_picker.ops import Ops as AP_OPS
from .wg_style import PG__ButtonScript__Style
from .._button_common import APNODE_Button_Common
from .ops import AP_OT_create_open_wg_button_script


class APNODE_ButtonScript_NodeProps(APNODE_Button_Common):
    def get_style(self, theme) -> PG__ButtonScript__Style:
        if self.use_override_theme:
            return self.style
        return getattr(theme, self.wg_type)
    style: PointerProperty(name="Style", type=PG__ButtonScript__Style)


    def update_op_idname(self, context: Context) -> None:
        if self.op_idname == '':
            self.invalid_command = True
            return
        if '.' not in self.op_idname:
            self.invalid_command = True
            return
        split = self.op_idname.split('.')
        if len(split) != 2:
            self.invalid_command = True
            return
        module, idname = split
        if op_module := getattr(BPY_OPS, module):
            if operator := getattr(op_module, idname, None):
                self.invalid_command = False
                self.operator = operator
                return
        self.invalid_command = True

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
    op_idname: ACK.Prop.STRING(name='Operator', default='render.render', update=update_op_idname)
    script_text: PointerProperty(name="Script", description="Script Text Datablock", type=Text)


    def draw_wg_props(self, context: Context, layout: UILayout) -> None:
        # layout.prop(self, 'script_text', icon='TEXT')
        if self.button_type == 'SCRIPT':
            layout.scale_y = 1.5
            layout.operator(AP_OT_create_open_wg_button_script.bl_idname,
                            text="Open Script" if self.script_text is not None else "Create Script",
                            icon='TEXT')
        elif self.button_type == 'OPERATOR':
            if AP_OPS.PickLayoutButton.operator.is_modal_running: # GLOBALS.get_addon_global_value('IS_PICKING_DATAPATH', False):
                box = layout.box()
                col = box.column(align=True)
                col.label(text='', icon='INFO')
                col.alert = True
                col.label(text='Right Click a Button')

            else:
                col = layout.column(align=True)
                col.label(text="Operator Idname")
                row = col.row(align=True)
                row.scale_y = 1.5
                row.use_property_split = False
                if self.invalid_command:
                    row.alert = True
                row.prop(self, 'op_idname', text='')
                if self.invalid_command:
                    row.alert = False
                _row = row.row(align=True)
                _row.ui_units_x = 1.5
                AP_OPS.PickLayoutButton.draw_in_layout(_row, label=' ', icon='EYEDROPPER') # Pick Operator
