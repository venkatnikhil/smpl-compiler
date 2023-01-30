from typing import Type, Union
from app.parser.instr_node import ConstInstrNode, OpInstrNode


InstrNodeType = Union[Type[ConstInstrNode], Type[OpInstrNode]]
InstrNodeActual = Union[ConstInstrNode, OpInstrNode]
