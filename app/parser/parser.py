from app.tokenizer import Tokenizer
from app.tokens import TokenEnum, OpCodeEnum
from app.error_handling import CustomSyntaxError
from app.parser.instr_node import ConstInstrNode, OpInstrNode
from app.parser.cfg import CFG
from typing import Optional


class Parser:
    def __init__(self, file_name: str) -> None:
        self.tokenizer: Tokenizer = Tokenizer(file_name)
        self.sym: Optional[int] = None  # holds current token
        self.cfg: CFG = CFG()
        self.__next_token()

    def __next_token(self) -> None:
        # get the next token
        self.sym = self.tokenizer.get_next()

    def __check_token(self, expected: int) -> None:
        # check if the current token matches the expected token; raise error otherwise
        if isinstance(expected, int):
            if self.sym != expected:  # does not match specific token
                raise CustomSyntaxError(message="error")
        else:
            if self.sym not in expected:  # does not match **any** of the expected tokens
                raise CustomSyntaxError(message="error")

        if self.sym == TokenEnum.PERIOD.value:  # end of input, simply return
            return
        self.__next_token()  # move onto next token

    def parse_computation(self) -> None:
        self.__check_token(TokenEnum.MAIN.value)
        self.__check_token(TokenEnum.BEGIN.value)
        self.parse_stat_sequence()
        self.__check_token(TokenEnum.END.value)
        self.__check_token(TokenEnum.PERIOD.value)

    def parse_var_decl(self) -> None:
        pass

    def parse_assignment(self) -> None:
        self.__check_token(TokenEnum.LET.value)
        ident: int = self.tokenizer.id
        self.parse_designator(rhs=False)
        self.__check_token(TokenEnum.BECOMES.value)
        instr_num: int = self.parse_expression()
        self.cfg.curr_bb.update_var_instr_map(ident, instr_num)  # TODO: fix this

    def parse_designator(self, rhs: bool = True) -> Optional[int]:
        ident = self.tokenizer.id
        self.__check_token(TokenEnum.IDENTIFIER.value)
        if rhs:  # get instr num only when it is on RHS
            return self.cfg.curr_bb.get_instr_num(ident)  # TODO: fix this

    def parse_expression(self) -> int:
        l_instr: int = self.parse_term()

        while self.sym in [TokenEnum.PLUS.value, TokenEnum.MINUS.value]:
            op: int = self.sym
            self.__next_token()
            if op == TokenEnum.PLUS.value:
                l_instr = self.cfg.build_instr_node(OpInstrNode, OpCodeEnum.ADD.value, left=l_instr,
                                                    right=self.parse_term())
            else:
                l_instr = self.cfg.build_instr_node(OpInstrNode, OpCodeEnum.SUB.value, left=l_instr,
                                                    right=self.parse_term())
        return l_instr

    def parse_term(self) -> int:
        l_instr: int = self.parse_factor()
        while self.sym in [TokenEnum.TIMES.value, TokenEnum.DIV.value]:
            op: int = self.sym
            self.__next_token()
            if op == TokenEnum.TIMES.value:
                l_instr = self.cfg.build_instr_node(OpInstrNode, OpCodeEnum.MUL.value, left=l_instr,
                                                    right=self.parse_factor())
            else:
                l_instr = self.cfg.build_instr_node(OpInstrNode, OpCodeEnum.DIV.value, left=l_instr,
                                                    right=self.parse_factor())
        return l_instr

    def parse_number(self) -> int:
        if not self.cfg.const_bb.check_instr_exists(self.tokenizer.number):
            self.cfg.const_bb.update_var_instr_map(self.tokenizer.number,
                                                   self.cfg.build_instr_node(ConstInstrNode, OpCodeEnum.CONST.value,
                                                                             bb=self.cfg.const_bb,
                                                                             val=self.tokenizer.number))

        self.__next_token()
        return self.cfg.const_bb.get_instr_num(self.tokenizer.number)

    def parse_factor(self) -> Optional[int]:
        if self.sym == TokenEnum.NUMBER.value:
            return self.parse_number()
        else:
            return self.parse_designator()

    def parse_statement(self) -> None:
        self.parse_assignment()

    def parse_stat_sequence(self) -> None:
        self.parse_statement()
        if self.sym == TokenEnum.SEMI.value:
            self.__next_token()
            while self.sym != TokenEnum.END.value:
                self.parse_statement()
                if self.sym == TokenEnum.SEMI.value:
                    self.__next_token()
                elif self.sym == TokenEnum.END.value:
                    return
                else:
                    raise CustomSyntaxError(message="error")
