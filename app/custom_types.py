from typing import Type, Union
from app.parser.instr_node import ConstInstrNode, OpInstrNode, EmptyInstrNode, SingleOpInstrNode


InstrNodeType = Union[Type[ConstInstrNode], Type[OpInstrNode], Type[EmptyInstrNode], Type[SingleOpInstrNode]]
InstrNodeActual = Union[ConstInstrNode, OpInstrNode, EmptyInstrNode, SingleOpInstrNode]
