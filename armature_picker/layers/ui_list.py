from bpy.types import AnyType, Context, UILayout, UIList

from .pg import PG_PickerLayer



class LIST_PickerLayers(UIList):
    bl_idname = 'AP_UL_picker_layers'
    
    def draw_item(self, context: Context, layout: UILayout, data: AnyType, item: PG_PickerLayer, icon: int, active_data: AnyType, active_property: str, index: int = 0, flt_flag: int = 0):
        row = layout.row(align=True)
        row.prop(item, 'enabled', expand=False, text='', icon='HIDE_OFF' if item.enabled else 'HIDE_ON', emboss=False)
        row.prop(item, 'edit_name', text="", emboss=False)
