from app.tokenizer import Tokenizer
from app.tokens import TokenEnum, OpCodeEnum
from app.error_handling import CustomSyntaxError
from app.parser.instr_node import ConstInstrNode, OpInstrNode
from app.parser.cfg import CFG


class Parser:
    def __init__(self, file_name):
        self.tokenizer = Tokenizer(file_name)
        self.sym = None
        self.cfg = CFG()
        self.__next_token()

    def __next_token(self):
        self.sym = self.tokenizer.get_next()

    def __check_token(self, expected):
        if isinstance(expected, int):
            if self.sym != expected:
                raise CustomSyntaxError(message="error")
        else:
            if self.sym not in expected:
                raise CustomSyntaxError(message="error")

        if self.sym == TokenEnum.PERIOD.value:
            return
        self.__next_token()

    def parse_computation(self):
        self.__check_token(TokenEnum.MAIN.value)
        self.__check_token(TokenEnum.BEGIN.value)
        self.parse_stat_sequence()
        self.__check_token(TokenEnum.END.value)
        self.__check_token(TokenEnum.PERIOD.value)

    def parse_var_decl(self):
        pass

    def parse_assignment(self):
        self.__check_token(TokenEnum.LET.value)
        ident = self.tokenizer.id
        self.parse_designator(rhs=False)
        self.__check_token(TokenEnum.BECOMES.value)
        instr_num = self.parse_expression()
        self.cfg.curr_bb.update_var_instr_map(ident, instr_num)

    def parse_designator(self, rhs=True):
        ident = self.tokenizer.id
        self.__check_token(TokenEnum.IDENTIFIER.value)
        if rhs:
            return self.cfg.curr_bb.get_instr_num(ident)

    def parse_expression(self):
        l_instr = self.parse_term()

        while self.sym in [TokenEnum.PLUS.value, TokenEnum.MINUS.value]:
            op = self.sym
            self.__next_token()
            if op == TokenEnum.PLUS.value:
                l_instr = self.cfg.build_instr_node(OpInstrNode, OpCodeEnum.ADD.value, left=l_instr,
                                                    right=self.parse_term())
            else:
                l_instr = self.cfg.build_instr_node(OpInstrNode, OpCodeEnum.SUB.value, left=l_instr,
                                                    right=self.parse_term())
        return l_instr

    def parse_term(self):
        l_instr = self.parse_factor()
        while self.sym in [TokenEnum.TIMES.value, TokenEnum.DIV.value]:
            op = self.sym
            self.__next_token()
            if op == TokenEnum.TIMES.value:
                l_instr = self.cfg.build_instr_node(OpInstrNode, OpCodeEnum.MUL.value, left=l_instr,
                                                    right=self.parse_factor())
            else:
                l_instr = self.cfg.build_instr_node(OpInstrNode, OpCodeEnum.DIV.value, left=l_instr,
                                                    right=self.parse_factor())
        return l_instr

    def parse_number(self):
        if not self.cfg.const_bb.check_instr_exists(self.tokenizer.number):
            self.cfg.const_bb.update_var_instr_map(self.tokenizer.number, self.cfg.build_instr_node(
                ConstInstrNode, OpCodeEnum.CONST.value, bb=self.cfg.const_bb, val=self.tokenizer.number))

        self.__next_token()
        return self.cfg.const_bb.get_instr_num(self.tokenizer.number)

    def parse_factor(self):
        if self.sym == TokenEnum.NUMBER.value:
            return self.parse_number()
        else:
            return self.parse_designator()

    def parse_statement(self):
        self.parse_assignment()

    def parse_stat_sequence(self):
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
