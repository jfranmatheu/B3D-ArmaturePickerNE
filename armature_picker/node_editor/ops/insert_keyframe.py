from bpy.types import Context, Menu


keyset = (
    'Location',
    'Rotation',
    'Scale',
    'Available'
)


class MT_insert_keyframe(Menu):
    bl_idname = 'AP_MT_insert_keyframe'
    bl_label = "Insert Keyframe"
    
    def draw(self, context: Context):
        layout = self.layout
        pie = layout.menu_pie()
        # Pie order: west, east, south, north, north-west, north-east, south-west, south-east
        for key in keyset:
            pie.operator('anim.keyframe_insert_by_name', text=key).type = key
