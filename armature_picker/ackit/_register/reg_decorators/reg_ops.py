# OPERATOR DECORATORS.
from bpy_extras.io_utils import ExportHelper, ImportHelper
from bpy.props import StringProperty


def ops_io(helper_cls, file_formats: tuple[str]):
    def decorator(deco_cls):
        derivated_helper_cls = type(
            deco_cls.__name__ + '_IOHelper',
            (deco_cls, helper_cls),
            {
                '__annotations__': {
                    'filter_glob': StringProperty(
                        default='*.' + ';*.'.join([file_format.lower() for file_format in file_formats]),
                        options={'HIDDEN'}
                    )
                }
            }
        )
        return derivated_helper_cls
    return decorator


class OpsDecorators:
    IMPORT = lambda *file_formats: ops_io(ImportHelper, file_formats)
    EXPORT = lambda *file_formats: ops_io(ExportHelper, file_formats)
