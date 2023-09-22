'''
### Node Categories ###
# Node categories are a python system for automatically
# extending the Add menu, toolbar panels and search operator.
# For more examples see scripts/startup/nodeitems_builtins.py

import nodeitems_utils
from nodeitems_utils import NodeCategory, NodeItem

from armature_picker.node_editor.poll import poll_check

# our own base class with an appropriate poll function,
# so the categories only show up in our own tree type


class AP_NodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context):
        return poll_check(context, use_active_object=False)


# all categories in a list
node_categories = [
    # identifier, label, items list
    AP_NodeCategory('AP_NODECAT_BUTTONS', "Buttons", items=[
        # our basic node
        NodeItem("AP_NODE_bone_picker"),
    ]),
]


def register():
    nodeitems_utils.register_node_categories('AP_NODES', node_categories)


def unregister():
    nodeitems_utils.unregister_node_categories('AP_NODES')
'''
