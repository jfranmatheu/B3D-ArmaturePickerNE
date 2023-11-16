from armature_picker.ackit import ACK
from armature_picker.pk_editor.widgets._button_style_common import CommonTheme__Button, call_active_node_func


@ACK.Deco.PROP_GROUP.CHILD
class PG__BonePicker__Style(CommonTheme__Button):
    color: ACK.Prop.COLOR_RGBA("Background Color", (.9, .62, .14, 1.0))
    text_color: ACK.Prop.COLOR_RGBA('Text Color', (.0, .0, .0, 1.0), update=call_active_node_func('update_label'))
