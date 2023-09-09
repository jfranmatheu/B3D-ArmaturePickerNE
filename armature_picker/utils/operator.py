

class OpsReturn:
    FINISH = {'FINISHED'}
    CANCEL = {'CANCELLED'}
    PASS = {'PASS_THROUGH'}
    RUN = {'RUNNING_MODAL'}
    UI = {'INTERFACE'}


def add_modal_handler(context, operator):
    if not context.window_manager.modal_handler_add(operator):
        return OpsReturn.CANCEL
    return OpsReturn.RUN
