from typing import Type, Union
from app.parser.instr_node import ConstInstrNode, OpInstrNode, EmptyInstrNode


InstrNodeType = Union[Type[ConstInstrNode], Type[OpInstrNode], Type[EmptyInstrNode]]
InstrNodeActual = Union[ConstInstrNode, OpInstrNode, EmptyInstrNode]
