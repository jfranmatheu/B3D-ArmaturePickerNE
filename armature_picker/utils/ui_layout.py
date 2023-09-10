from bpy.types import UILayout


def draw_section(layout: UILayout, title: str, icon: str = 'NONE', align_content: bool = False) -> UILayout:
        section = layout.column(align=True)
        header = section.box().row(align=True)
        header.label(text=title, icon=icon)
        content = section.box().column(align=align_content)
        content.use_property_split = True
        content.use_property_decorate = False
        return content

def draw_section_h(layout: UILayout, title: str, icon: str = 'NONE', align_content: bool = False) -> UILayout:
        section = layout.column(align=True)
        header = section.box().row(align=True)
        header.label(text=title, icon=icon)
        content = section.box().column(align=align_content)
        content.use_property_split = True
        content.use_property_decorate = False
        return header, content
