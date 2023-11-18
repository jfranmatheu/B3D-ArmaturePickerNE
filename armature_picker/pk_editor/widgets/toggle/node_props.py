from bpy.types import Text, Context, UILayout

from armature_picker.ackit import ACK
from .wg_style import PG__Toggle__Style

data_path_list = []
class APNODE_Toggle_NodeProps:
    style: ACK.Prop.POINTER.CUSTOM("Style", PG__Toggle__Style)

    tooltip: ACK.Prop.STRING(name="Tooltip", description="Tooltip Label", default="")

    def get_next_data_paths(self, context: Context) -> list:
        global data_path_list
        data_path_list.clear()
        try:
            data = context.path_resolve(self.data_path, coerce=True)
            data_path_list = [
                (attr, attr, '') for attr in dir(data)
                if not attr.startswith(('_', 'bl', 'rna')) and isinstance(getattr(data, attr), bool)
            ]
        except ValueError:
            return [('NONE', 'None', ""),]
        return data_path_list

    def update_data_path(self, context: Context) -> None:
        self.data_path += ('.' + self.data_path_enum)

    data_path: ACK.Prop.STRING(default='active_object')
    data_path_enum: ACK.Prop.ENUM(
        items=get_next_data_paths,
        update=update_data_path
    )

    def draw_wg_props(self, context: Context, layout: UILayout) -> None:
        layout.prop(self, 'tooltip')

        layout.label(text=self.data_path)
        flow = layout.column(align=True)
        for segment in self.data_path.split('.'):
            row = flow.split(align=True, factor=.9)
            row.box().label(text=segment)
            row.box().label(text='', icon='DOT')
        flow.prop(self, 'data_path_enum')
