from app.tokenizer import Tokenizer
from app.tokens import TokenEnum, OpCodeEnum, RELOP_TOKEN_OPCODE
from app.error_handling import CustomSyntaxError
from app.parser.instr_node import ConstInstrNode, OpInstrNode, SingleOpInstrNode
from app.parser.cfg import CFG
from typing import Optional, Union


class Parser:
    def __init__(self, file_name: str) -> None:
        self.tokenizer: Tokenizer = Tokenizer(file_name)
        self.sym: Optional[int] = None  # holds current token
        self.cfg: CFG = CFG()
        self.__next_token()

    def __next_token(self) -> None:
        # get the next token
        self.sym = self.tokenizer.get_next()

    def __check_token(self, expected: Union[int, set[int]]) -> None:
        # check if the current token matches the expected token; raise error otherwise
        if isinstance(expected, int):
            if self.sym != expected:  # does not match specific token
                raise CustomSyntaxError(message="error")
        else:
            if self.sym not in expected:  # does not match **any** of the expected tokens
                raise CustomSyntaxError(message="error")

        if self.sym == TokenEnum.EOF.value:  # end of input, simply return
            return
        self.__next_token()  # move onto next token

    def parse_computation(self) -> None:
        self.__check_token(TokenEnum.MAIN.value)
        if self.sym == TokenEnum.VAR.value:
            self.parse_var_decl()
        self.__check_token(TokenEnum.BEGIN.value)
        self.parse_stat_sequence()
        self.__check_token(TokenEnum.END.value)
        self.__check_token(TokenEnum.PERIOD.value)
        self.__check_token(TokenEnum.EOF.value)
        self.cfg.update_branch_instrs()

    def parse_var_decl(self) -> None:
        self.__check_token(TokenEnum.VAR.value)
        self.__check_token(TokenEnum.IDENTIFIER.value)
        self.cfg.declared_vars.add(self.tokenizer.id)
        while self.sym == TokenEnum.COMMA.value:
            self.__next_token()
            self.__check_token(TokenEnum.IDENTIFIER.value)
            if self.tokenizer.id in self.cfg.declared_vars:
                raise CustomSyntaxError(message=f"'{Tokenizer.id2string(self.tokenizer.id)}' declared more than once.")
            self.cfg.declared_vars.add(self.tokenizer.id)
        self.__check_token(TokenEnum.SEMI.value)

    def parse_assignment(self) -> None:
        self.__check_token(TokenEnum.LET.value)
        ident: int = self.tokenizer.id
        self.parse_designator(rhs=False)
        self.__check_token(TokenEnum.BECOMES.value)
        instr_num: int = self.parse_expression()
        self.cfg.curr_bb.update_var_instr_map(ident, instr_num)

    def parse_identifier(self) -> int:
        if self.tokenizer.id not in self.cfg.declared_vars:
            raise CustomSyntaxError(message=f"'{Tokenizer.id2string(self.tokenizer.id)}' not declared!")
        self.__check_token(TokenEnum.IDENTIFIER.value)
        return self.tokenizer.id

    def parse_designator(self, rhs: bool = True) -> Optional[int]:
        ident = self.parse_identifier()
        if rhs:  # get instr num only when it is on RHS
            return self.cfg.get_var_instr_num(self.cfg.curr_bb, ident, set())

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
                                                                             bb=self.cfg.const_bb.bb_num,
                                                                             val=self.tokenizer.number))

        self.__next_token()
        return self.cfg.const_bb.get_var_instr_num(self.tokenizer.number)

    def parse_factor(self) -> Optional[int]:
        if self.sym == TokenEnum.NUMBER.value:
            return self.parse_number()
        elif self.sym == TokenEnum.OPEN_PAREN.value:
            self.__next_token()
            instr_num: int = self.parse_expression()
            self.__check_token(TokenEnum.CLOSE_PAREN.value)
            return instr_num
        else:
            return self.parse_designator()

    def parse_relop(self) -> OpCodeEnum:
        op: int = self.sym
        self.__check_token(set(RELOP_TOKEN_OPCODE.keys()))
        return RELOP_TOKEN_OPCODE[op]  # check which branch instr

    def parse_relation(self) -> int:
        l_instr: int = self.parse_expression()
        opcode: OpCodeEnum = self.parse_relop()
        r_instr: int = self.parse_expression()
        cmp_instr: int = self.cfg.build_instr_node(OpInstrNode, OpCodeEnum.CMP.value, left=l_instr, right=r_instr)
        br_instr: int = self.cfg.build_instr_node(OpInstrNode, opcode, left=cmp_instr, right=None)
        return br_instr

    def parse_if(self) -> None:
        self.__check_token(TokenEnum.IF.value)
        br_instr: int = self.parse_relation()
        self.__check_token(TokenEnum.THEN.value)
        if_bb: int = self.cfg.curr_bb.bb_num
        then_bb: int = self.cfg.create_bb([if_bb])
        self.parse_stat_sequence()
        l_parent: int = self.cfg.curr_bb.bb_num
        else_bb: int = self.cfg.create_bb([if_bb])
        if self.sym == TokenEnum.ELSE.value:
            self.__next_token()
            self.parse_stat_sequence()
        r_parent: int = self.cfg.curr_bb.bb_num
        self.cfg.update_instr(br_instr, {"right": self.cfg.get_bb(else_bb).get_first_instr_num()})
        self.__check_token(TokenEnum.FI.value)
        join_bb: int = self.cfg.create_bb([l_parent, r_parent], [if_bb])
        # self.cfg.build_instr_node(SingleOpInstrNode, OpCodeEnum.BRA.value, l_parent,
        #                           left=self.cfg.get_bb(join_bb).get_first_instr_num())
        self.cfg.build_instr_node(SingleOpInstrNode, OpCodeEnum.BRA.value, l_parent,
                                  left=join_bb)

    def parse_statement(self) -> None:
        if self.sym == TokenEnum.LET.value:
            self.parse_assignment()
        elif self.sym == TokenEnum.IF.value:
            self.parse_if()

    def parse_stat_sequence(self) -> None:
        self.parse_statement()
        if self.sym == TokenEnum.SEMI.value:
            self.__next_token()
            if self.sym not in [TokenEnum.FI.value, TokenEnum.ELSE.value, TokenEnum.END.value, TokenEnum.OD.value]:
                self.parse_stat_sequence()
