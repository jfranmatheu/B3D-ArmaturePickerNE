# We're doing this as a HACK because of a Blender BUG: https://projects.blender.org/blender/blender/issues/98598
# Instead of using the Gizmo.draw to draw this...

import bpy
from bpy.types import SpaceNodeEditor, Context
from mathutils import Vector

from armature_picker.gpu import draw
from armature_picker.icons import Icons
from armature_picker.utils.geometry import calculate_scale_to_fit_box_in_box


draw_handler = None


def draw_fallback_wrong_mode(context: Context) -> None:
    ui_scale = context.preferences.system.ui_scale
    draw.rectangle(
        None, None,
        Vector((0, 0)), Vector((context.region.width, context.region.height)), 0,
        color=(0.25, 0.1, 0.1, .2),
    )
    icon = Icons.ICONS8.HUMAN_BONES
    gputex = icon.gputex
    if not gputex:
        return
    size = icon.image_size
    # aspect_ratio = size[1] / size[0]
    wanted_dimensions, scale = calculate_scale_to_fit_box_in_box((context.region.width, context.region.height), size)
    # w = int(min(int(context.region.width * 0.5), 128) * scale * aspect_ratio)
    # h = w * aspect_ratio
    w, h = wanted_dimensions
    w = min(w, size[0] * 2 * ui_scale)
    h = min(h, size[1] * 2 * ui_scale)

    ipos = Vector((context.region.width * 0.5 - w * 0.5, context.region.height * 0.5 - h * 0.5))
    draw.image(
        None, None,
        ipos, Vector((w, h)), 0,
        image=gputex
    )
    # draw.text(
    #     Vector((ipos.x + w - 25, ipos.y + h)),
    #     "Let's pose!",
    #     int(16 * ui_scale),
    #     (0.0, 0.0),
    #     width=int(context.region.width * 0.9),
    #     color=(.8, .3, .75, 1.0)
    # )
    draw.text(
        Vector((context.region.width * 0.5, ipos.y - h * 0.5)), # Vector((context.region.width * 0.5, context.region.height - 40)), #
        "Let's pose!",
        24,
        (0.5, 1.0),
        width=int(context.region.width * 0.9),
    )


def draw_fallback_wrong_object_type(context: Context) -> None:
    ui_scale = context.preferences.system.ui_scale
    draw.rectangle(
        None, None,
        Vector((0, 0)), Vector((context.region.width, context.region.height)), 0,
        color=(0.25, 0.1, 0.1, .2),
    )
    icon = Icons.ICONS8.HUMAN_BONES
    gputex = icon.gputex
    if not gputex:
        return
    size = icon.image_size
    # aspect_ratio = size[1] / size[0]
    wanted_dimensions, scale = calculate_scale_to_fit_box_in_box((context.region.width, context.region.height), size)
    # w = int(min(int(context.region.width * 0.5), 128) * scale * aspect_ratio)
    # h = w * aspect_ratio
    w, h = wanted_dimensions
    w = min(w, size[0] * 2 * ui_scale)
    h = min(h, size[1] * 2 * ui_scale)

    ipos = Vector((context.region.width * 0.5 - w * 0.5, context.region.height * 0.5 - h * 0.5))
    draw.image(
        None, None,
        ipos, Vector((w, h)), 0,
        image=gputex
    )
    draw.text(
        Vector((context.region.width * 0.5, ipos.y - h * 0.5)), # Vector((context.region.width * 0.5, context.region.height - 40)), #
        "Armature Object should be Active!",
        24,
        (0.5, 1.0),
        width=int(context.region.width * 0.9),
    )


def draw_callback() -> None:
    context= bpy.context
    if context.space_data.node_tree is None:
        return
    if context.space_data.tree_type != 'AP_NODETREE':
        return
    if context.active_object is None:
        return
    if context.active_object.type not in {'ARMATURE'}:
        draw_fallback_wrong_object_type(context)
        return
    if context.active_object.mode != 'POSE':
        draw_fallback_wrong_mode(context)
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
