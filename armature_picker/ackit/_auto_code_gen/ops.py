'''
    OPS.PY GENERATION
'''

from collections import defaultdict
from string import Template


from .._globals import GLOBALS

# ----------------------------------------------------------------
# IMPORT CODE.

from .._register.reg_types.ops import Operator
from .._register import BlenderTypes


ot_original_name_relation: dict[str, Operator] = {}


class OpTypeEnum:
    @property
    def operator(self) -> Operator:
        return ot_original_name_relation[self.name]

    def run(self, **operator_properties: dict) -> None:
        self.operator.run(**operator_properties)

    def run_invoke(self, **operator_properties: dict) -> None:
        self.operator.run_invoke(**operator_properties)

    def draw_in_layout(self, layout, label: str | None = None, op_props: dict | None = None, **draw_kwargs):
        return self.operator.draw_in_layout(layout, label, op_props=op_props, **draw_kwargs)

    def __call__(self, *args, **kwargs) -> None:
        return self.operator.run_invoke(*args, **kwargs)


def register():
    for cls in BlenderTypes.Operator.get_classes():
        ot_original_name_relation[cls.original_name] = cls

def unregister():
    ot_original_name_relation.clear()



# ----------------------------------------------------------------


def codegen__ops_py() -> None:
    from .._register import BlenderTypes

    def prop_type_to_py_type(prop) -> tuple:
        bpy_prop_name = prop.function.__name__
        default = prop.keywords.get('default', None)
        is_vector = 'Vector' in bpy_prop_name
        value = default
        type_str = 'None'
        if 'Float' in bpy_prop_name:
            type_str = 'float'
            if default is None: value = 0.0
        if 'Int' in bpy_prop_name:
            type_str = 'int'
            if default is None: value = 0
        if 'Bool' in bpy_prop_name:
            type_str = 'bool'
            if default is None: value = False
        if is_vector:
            if default:
                value = tuple(value)
                size = len(value)
            else:
                size = prop.keywords.get('size', 3)
                value = tuple([value]*size)
            type_str = 'tuple[%s]' % (', '.join([type_str for i in range(size)])[:-2])
        if 'String' in bpy_prop_name:
            type_str = 'str'
            if default is None: value = ''
        return type_str, value
        if 'Pointer' in bpy_prop_name:
            # print(prop.type, prop.fixed_type.name)
            return 'bpy.types.' + prop.fixed_type.name
        if 'Collection' in bpy_prop_name:
            #print(prop, prop.fixed_type, dir(prop.fixed_type), prop.fixed_type.original_idname)
            return f'list' # [{prop.fixed_type.original_idname}]'
        return 'None'

    ops_py_filepath = GLOBALS.ADDON_SOURCE_PATH / 'ops.py'
    code_per_ops_subtype: dict[str, str] = defaultdict(str)
    example_op = None
    #properties_per_ot = defaultdict(list)
    with ops_py_filepath.open('w', encoding='utf-8') as f:
        f.write("# /ops.py\n# Code automatically generated!\n")
        f.write('from enum import Enum, auto\n\n')
        f.write(f'from {__package__}.ops import OpTypeEnum\n\n')
        f.write('__all__ = ["Ops",]\n\n\n')
        #for ori_name, ot_cls in ot_original_name_relation.items():
        #    op_subtype: str = ot_cls.bl_idname.split('.')[0]
        #    code_per_ops_subtype[op_subtype] += f'\t\t{ori_name} = auto()\n'
        #    if example_op is None:
        #        example_op = f'Ops.{op_subtype}.{ori_name}'
            #for prop_name, prop in ot_cls.original_class.__annotations__.items():
            #    type_str, value = prop_type_to_py_type(prop)
            #    properties_per_ot[ot_cls.original_name].append((prop_name, type_str, value))
        '''
        for ot_name, ot_props in properties_per_ot.items():
            f.write(f'class {ot_name}:')
            f.write
            for (prop_name, type_str, value) in ot_props:
                f.write(f'{prop_name}: {type_str} = {value}')

            #for (prop_name, type_str, value) in ot_props:
            #    f.write(f'\t{prop_name}: {type_str}\n')
            f.write('\n')
        '''

        f.write('\n\nclass Ops(OpTypeEnum, Enum):\n')
        #for subtype_name, code in code_per_ops_subtype.items():
        #    f.write(f'\tclass {subtype_name}(OpTypeEnum, Enum):\n')
        #    f.write(code)
        for ot_cls in BlenderTypes.Operator.get_classes():
            ori_name: str = ot_cls.original_name
            f.write(f'\t{ori_name} = auto()\n')
            if example_op is None:
                example_op = f'Ops.{ori_name}'

        f.write(f"""\n\n''' Usage example:
from addon_module.ops import Ops
{example_op}() # directly run execute the operator.
{example_op}.operator.run_invoke() # access to the operator class and run invoke the operator.
'''""")
