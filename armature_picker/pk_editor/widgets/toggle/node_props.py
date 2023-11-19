from bpy.types import Context, UILayout

from armature_picker.ops import Ops as AP_OPS
from armature_picker.ackit import ACK
from .wg_style import PG__Toggle__Style


data_path_list = []


class APNODE_Toggle_NodeProps:
    style: ACK.Prop.POINTER.CUSTOM("Style", PG__Toggle__Style)

    def get_style(self, theme) -> PG__Toggle__Style:
        if self.use_override_theme:
            return self.style
        return getattr(theme, self.wg_type)


    def update_label(self, context: Context) -> None:
        self.dirty_label = True

    tooltip: ACK.Prop.STRING(name="Tooltip", description="Tooltip Label", default="", update=update_label)

    # def get_next_data_paths(self, context: Context) -> list:
    #     global data_path_list
    #     data_path_list.clear()
    #     try:
    #         data = context.path_resolve(self.data_path, coerce=True)
    #         data_path_list = [
    #             (attr, attr, '') for attr in dir(data)
    #             if not attr.startswith(('_', 'bl', 'rna')) and isinstance(getattr(data, attr), bool)
    #         ]
    #     except ValueError:
    #         return [('NONE', 'None', ""),]
    #     return data_path_list

    def update_data_path(self, context: Context) -> None:
        # self.data_path += ('.' + self.data_path_enum)
        if self.data_path != '':
            data_path: str = self.data_path
            if data_path.endswith(']'):
                start_split = data_path.rindex('[')
                attr = data_path[start_split+2:-2] # remove ['']
                self.tooltip = attr.replace('_', ' ').title()
            else:
                self.tooltip = data_path.split('.')[-1].replace('_', ' ').title()

    data_path: ACK.Prop.STRING(default='active_object', update=update_data_path)
    # data_path_enum: ACK.Prop.ENUM(
    #     items=get_next_data_paths,
    #     update=update_data_path
    # )
