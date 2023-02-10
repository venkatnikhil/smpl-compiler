from typing import Type, Union
from app.parser.instr_node import ConstInstrNode, OpInstrNode, EmptyInstrNode, SingleOpInstrNode, ZeroOpInstrNode

InstrNodeType = Union[Type[ConstInstrNode], Type[OpInstrNode], Type[EmptyInstrNode], Type[SingleOpInstrNode],
                      Type[ZeroOpInstrNode]]
InstrNodeActual = Union[ConstInstrNode, OpInstrNode, EmptyInstrNode, SingleOpInstrNode, ZeroOpInstrNode]
