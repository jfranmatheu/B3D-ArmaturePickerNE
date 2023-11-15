# /ops.py
# Code automatically generated!
from enum import Enum, auto

from armature_picker.ackit._auto_code_gen.ops import OpTypeEnum

__all__ = ["Ops",]




class Ops(OpTypeEnum, Enum):
	LoadCustomShapeFromGeometry = auto()
	AsignActiveBoneToBonePicker = auto()
	CenterView = auto()
	LoadImageForActiveNode = auto()


''' Usage example:
from addon_module.ops import Ops
Ops.LoadCustomShapeFromGeometry() # directly run execute the operator.
Ops.LoadCustomShapeFromGeometry.operator.run_invoke() # access to the operator class and run invoke the operator.
'''