import bpy
from bpy.types import Context


def get_view3d_context(context: Context) -> dict | None:
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'WINDOW':
                    return {
                        'window': context.window,
                        'area': area,
                        'region': region
                    }
    return None


def view3d_set_mode(context: Context, mode: str) -> None:
    view3d_ctx = get_view3d_context(context)
    if view3d_ctx is None:
        return
    with context.temp_override(**view3d_ctx):
        bpy.ops.object.mode_set(mode=mode)
