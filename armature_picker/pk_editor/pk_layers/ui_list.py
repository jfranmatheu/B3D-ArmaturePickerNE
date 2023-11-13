from bpy.types import AnyType, Context, UILayout, UIList

from .pg import PG_PickerLayer



class LIST_PickerLayers(UIList):
    bl_idname = 'AP_UL_picker_layers'
    
    def draw_item(self, context: Context, layout: UILayout, data: AnyType, item: PG_PickerLayer, icon: int, active_data: AnyType, active_property: str, index: int = 0, flt_flag: int = 0):
        row = layout.row(align=True)
        row.prop(item, 'color_icon', emboss=False, icon_only=True)
        row.prop(item, 'name', text="", emboss=False)
        row.prop(item, 'use_pin', text='', icon='PINNED' if item.use_pin else 'UNPINNED')
