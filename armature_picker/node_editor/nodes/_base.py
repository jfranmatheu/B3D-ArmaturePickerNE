from bpy.types import Node, UILayout, NodeTree
from bpy.props import StringProperty, BoolProperty
from mathutils import Vector

from uuid import uuid4


# BUG-FIX: AttributeError: Writing to ID classes in this context is not allowed
_dirty_cache: dict[str, bool] = {}


def set_dirty_state(uuid: str, state: bool) -> None:
    _dirty_cache[uuid] = state


# Mix-in class for all custom nodes in this tree type.
# Defines a poll function to enable instantiation.
class AP_Node:
    uuid: StringProperty(name="UUID", default='')
    # dirty: BoolProperty(default=True, options={'HIDDEN'})
    
    @property
    def node_tree(self) -> NodeTree:
        return self.id_data

    @property
    def dirty(self) -> bool:
        return _dirty_cache.get(self.uuid, False)

    @dirty.setter
    def dirty(self, state: bool) -> bool:
        _dirty_cache[self.uuid] = state

    @classmethod
    def poll(cls, ntree):
        return ntree.bl_idname == 'AP_NODETREE'

    def init(self, context):
        self.name = self.uuid = uuid4().hex
        self.dirty = True
        self.mute = True
        self.hide = True
        print("New node ", self)

    # Copy function to initialize a copied node from an existing one.
    def copy(self, node):
        self.uuid = uuid4().hex
        self.dirty = True
        print("Copying from node ", node)

    # Free function to clean up on removal.
    def free(self):
        print("Removing node ", self, ", Goodbye!")

    def draw(self, context, scale: float, active: bool) -> None:
        pass

    def _draw(self, context, scale: float, active: bool) -> None:
        self.draw(context, scale, active)
        if self.dirty:
            set_dirty_state(self.uuid, False)

    def draw_section(self, layout: UILayout, title: str, icon: str = 'NONE', align_content: bool = False) -> UILayout:
        section = layout.column(align=True)
        header = section.box().row(align=True)
        header.label(text=title, icon=icon)
        content = section.box().column(align=align_content)
        return content
