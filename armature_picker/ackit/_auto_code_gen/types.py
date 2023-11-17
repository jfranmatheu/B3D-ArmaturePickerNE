from string import Template
from collections import defaultdict

import bpy
from bpy.types import AnyType, PropertyGroup, BlenderRNA
from bpy.props import _PropertyDeferred


class RootPropertyGroup:
    bpy_type: AnyType
    prop_name: str
    original_idname: str
    data_path: str
    bl_rna: BlenderRNA


coll_class_wrapper_template = Template("""
class ${class_name}_Collection:
\tdef __getitem__(coll, index: int) -> '${class_name}': pass
\tdef add(coll) -> '${class_name}': pass
\tdef remove(coll, item_index: int) -> None: pass
\tdef clear(coll) -> None: pass
""")

pg_class_wrapper_template = Template("""
class ${class_name}:${comment}
${property_defs}
""")

pg_class_get_data_template = Template("""
\t@classmethod
\tdef get_data(cls: '${class_name}', context: Context) -> '${class_name}':
\t\treturn context.${pg_data_path}
""")

example_typing_template = Template("""
\n\n# EXAMPLE ++++++++++++++++++++++++++++++++++++++++++++++++++\n'''
from ${addon_module_name} import types as ${addon_module_name}_types

# Your property_group variable will have the correct typing. :-)
property_group = ${addon_module_name}_types.${pg_name}.get_data(context)
property = property_group.${prop_name}
print(property)
'''\n""")


def prop_type_to_py_type(prop) -> str:
    if isinstance(prop, _PropertyDeferred):
        bpy_prop_name = prop.function.__name__
        is_array = 'Vector' in bpy_prop_name
    else:
        # print(dir(prop))
        bpy_prop_name = type(prop).__name__
        is_array = hasattr(prop, 'is_array') and prop.is_array

    if 'Float' in bpy_prop_name:
        return 'tuple[float]' if is_array else 'float'
    if 'Int' in bpy_prop_name:
        return 'tuple[int]' if is_array else 'int'
    if 'Bool' in bpy_prop_name:
        return 'tuple[bool]' if is_array else 'bool'
    if 'String' in bpy_prop_name or 'Enum' in bpy_prop_name:
        return 'str'
    if 'Pointer' in bpy_prop_name:
        if isinstance(prop, _PropertyDeferred):
            return f'{prop.keywords["type"].__name__}'
        else:
            if hasattr(prop.fixed_type, 'original_idname'):
                return prop.fixed_type.original_idname
            # print(prop.type, prop.fixed_type.name)
            return 'bpy.types.' + prop.fixed_type.name
    if 'Collection' in bpy_prop_name:
        if isinstance(prop, _PropertyDeferred):
            return f'{prop.keywords["type"].__name__}_Collection'
        else:
            #print(prop, prop.fixed_type, dir(prop.fixed_type), prop.fixed_type.original_idname)
            return f'{prop.fixed_type.original_idname}_Collection' # f'list[{prop.fixed_type.original_idname}]'
    return 'None'


def codegen__types_py(types_filepath: str | None = None) -> None:
    """Generates the Typing for PropertyGroup types.

    Args:
        types_filepath (str): path relative to the addon source where to write your types.py file. Defaults to '/types.py' (source root).
    """
    # Get PropertyGroup classes in the proper order.
    from .._register._register import BlenderTypes
    pg_classes = BlenderTypes.PropertyGroup.get_classes()
    if pg_classes == []:
        # SAD. No PropertyGroup classes to process... :-(
        return

    from .._loader import get_ordered_pg_classes_to_register
    pg_sorted_classes: list[PropertyGroup] = get_ordered_pg_classes_to_register(pg_classes)


    # Search for PropertyGroup used as CollectionProperty inside other PropertyGroup class.
    classes_used_as_collection = []
    for pg in pg_sorted_classes:
        for prop_idname, prop in pg.bl_rna.properties.items():
            if prop_idname in {'rna_type', 'name'}:
                continue
            if 'Collection' not in type(prop).__name__:
                continue
            classes_used_as_collection.append(prop.fixed_type.original_idname)


    # WRITE TO FILE. ---------------------------
    from .._globals import GLOBALS
    if types_filepath is None:
        types_filepath = GLOBALS.CodeGen.TYPES
    output_path = GLOBALS.ADDON_SOURCE_PATH / types_filepath
    addon_module_name = GLOBALS.ADDON_MODULE

    with output_path.open('w') as f:
        f.write('""" File generated automatically by ackit (Addon Creator Kit). """\n')
        # f.write('import bpy\n')#from {addon_module_name}.addon_utils.prop import PGType\n\n')

        from .._register.reg_helpers.help_property import to_register_properties
        import_bpy_types = {'Context'}
        for bpy_type, props_wrappers in to_register_properties.items():
            import_bpy_types.add(bpy_type.__name__)
            for prop_wrapper in props_wrappers:
                if isinstance(prop_wrapper.property, _PropertyDeferred):
                    prop_type = prop_type_to_py_type(prop_wrapper.property)
                    # print(prop_type, prop_type.__name__)
                    if hasattr(bpy.types, prop_type):
                        import_bpy_types.add(prop_type)

        f.write(f'from bpy.types import {", ".join(import_bpy_types)}\n\n')

        if len(classes_used_as_collection) != 0:
            f.write('\n""" Util classes to have CollectionProperty types typing: """')
            # Write the CollectionProperty classes we found with a nice template.
            for coll_cls_name in classes_used_as_collection:
                f.write(
                    coll_class_wrapper_template.substitute(
                        class_name=coll_cls_name,
                    )
                )

        # Just to store some PropertyGroup to use for the example code.
        example_pg_prop = None

        # For the Data Enumerator utility.
        root_pg_classes: list[RootPropertyGroup] = []

        # Write to file the property groups.
        f.write('\n""" Addon-Defined PropertyGroup: """')
        for pg in pg_sorted_classes:
            # print(pg, pg.bl_rna.properties)
            # is_root = pg.is_root
            is_root: bool = hasattr(pg, 'is_root') and pg.is_root
            f.write(
                pg_class_wrapper_template.substitute(
                    class_name=pg.original_idname,
                    comment=f'\n\t# Root PG, attached to bpy.types.{pg.bpy_type.__name__}' if is_root else '',
                    property_defs='\n'.join([
                        f'\t{prop_idname}: {prop_type_to_py_type(prop)}'
                            for prop_idname, prop in pg.bl_rna.properties.items() # pg.__annotations__.items()
                            if prop_idname not in {'rna_type'}
                            #if isinstance(prop, _PropertyDeferred) and prop_idname not in {'rna_type'}
                    ]),

                )
            )

            # If it's a root PropertyGroup, we need to add a get_path() class method
            # to it to get the corresponding data with typing!.
            if is_root:
                pg: RootPropertyGroup
                f.write(
                    pg_class_get_data_template.substitute(
                        class_name=pg.original_idname,
                        pg_data_path=pg.data_path,
                    )
                )
                if example_pg_prop is None:
                    for prop_idname in pg.bl_rna.properties.keys():
                        if prop_idname not in {'rna_type', 'name'}:
                            example_pg_prop = (pg, prop_idname)
                            break

                root_pg_classes.append(pg)

        # Write the extended bpy type classes.
        # pack root PG types by its root bpy_type.
        # pg_types_per_bpy_type: dict[AnyType, list[RootPropertyGroup]] = defaultdict(list)
        # for root_pg_cls in root_pg_classes:
        #     pg_types_per_bpy_type[root_pg_cls.bpy_type].append(root_pg_cls)
        # for bpy_type, pg_types in pg_types_per_bpy_type.items():
        #     f.write(f'\n\nclass {bpy_type.__name__}:')
        #     for pg_type in pg_types:
        #         f.write(f'\n\t{pg_type.prop_name}: {pg_type.original_idname}')

        f.write("\n\n# ++++++++++++++++++++++++++++++++++++++++++++++++++\n")
        f.write('""" Extended bpy.types classes by the addon: """')
        for bpy_type, props_wrappers in to_register_properties.items():
            f.write(f'\n\nclass Ext{bpy_type.__name__}({bpy_type.__name__}):')
            for prop_wrapper in props_wrappers:
                # print(prop_wrapper.property, prop_type_to_py_type(prop_wrapper.property))
                f.write(f'\n\t{prop_wrapper.prop_name}: {prop_type_to_py_type(prop_wrapper.property)}')
        
        if to_register_properties:
            f.write('\n\nclass ExtTypes:')
            for bpy_type in to_register_properties.keys():
                f.write(f'\n\t{bpy_type.__name__} = Ext{bpy_type.__name__}')

        # Write the Data enumerator.
        f.write("\n\n# ++++++++++++++++++++++++++++++++++++++++++++++++++\n")
        f.write('""" Root PropertyGroups (linked directly to any bpy.types): """\n')
        f.write('class RootPG:')
        if len(root_pg_classes) == 0:
            f.write(f'\n\tpass')
        else:
            for root_pg_cls in root_pg_classes:
                f.write(f'\n\t{root_pg_cls.original_idname} = {root_pg_cls.original_idname}.get_data')

        # Write example code.
        f.write("\n\n# ++++++++++++++++++++++++++++++++++++++++++++++++++\n")
        if example_pg_prop is not None:
            pg, prop_idname = example_pg_prop
            f.write(
                example_typing_template.substitute(
                    addon_module_name=addon_module_name,
                    pg_name=pg.original_idname,
                    prop_name=prop_idname
                )
            )
