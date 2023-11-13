from bpy.types import UILayout, Context


def use_active_node(func) -> None:
    def wrapper(any, context: Context):
        if context.area.type == 'PREFERENCES':
            return
        return func(context.space_data.node_tree.nodes.active, context)
    return wrapper


def call_active_node_func(func_name: str) -> None:
    def wrapper(node, context: Context):
        return getattr(node, func_name)(context)
    return use_active_node(wrapper)


class StyleBase:
    wg_type: str

    def draw(self, layout: UILayout, in_prefs_space: bool) -> None:
        pass
