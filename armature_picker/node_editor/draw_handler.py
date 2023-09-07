# We're doing this as a HACK because of a Blender BUG: https://projects.blender.org/blender/blender/issues/98598
# Instead of using the Gizmo.draw to draw this...

import bpy
from bpy.types import SpaceNodeEditor


draw_handler = None


def draw_callback():
    context= bpy.context
    if context.space_data.node_tree is None:
        return
    if context.space_data.tree_type != 'AP_NODETREE':
        return
    context.space_data.node_tree._draw(context)


def register():
    global draw_handler
    draw_handler = SpaceNodeEditor.draw_handler_add(draw_callback, (), 'WINDOW', 'POST_PIXEL')


def unregister():
    global draw_handler
    if draw_handler is not None:
        SpaceNodeEditor.draw_handler_remove(draw_handler, 'WINDOW')
        draw_handler = None
