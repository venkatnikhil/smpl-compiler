from typing import Type, Union
from app.parser.instr_node import *

InstrNodeType = Union[Type[ConstInstrNode], Type[OpInstrNode], Type[EmptyInstrNode], Type[SingleOpInstrNode],
                      Type[ZeroOpInstrNode], Type[AddrInstrNode]]
InstrNodeActual = Union[ConstInstrNode, OpInstrNode, EmptyInstrNode, SingleOpInstrNode, ZeroOpInstrNode, AddrInstrNode]
