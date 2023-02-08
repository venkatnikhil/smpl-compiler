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
                line, col = self.tokenizer.get_curr_pos()
                raise CustomSyntaxError(expected=f"{Tokenizer.id2string(expected)}",
                                        found=f"{Tokenizer.id2string(self.sym)}", at=f"line: {line}, col: {col}")
        else:
            if self.sym not in expected:  # does not match **any** of the expected tokens
                line, col = self.tokenizer.get_curr_pos()
                raise CustomSyntaxError(expected=f"{list(map(Tokenizer.id2string, expected))}",
                                        found=f"{Tokenizer.id2string(self.sym)}", at=f"line: {line}, col: {col}")

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
                line, col = self.tokenizer.get_curr_pos()
                raise CustomSyntaxError(message=f"'{Tokenizer.id2string(self.tokenizer.id)}' declared more than once "
                                                f"at line: {line}, col: {col}!")
            self.cfg.declared_vars.add(self.tokenizer.id)
        self.__check_token(TokenEnum.SEMI.value)

    def parse_assignment(self) -> None:
        self.__check_token(TokenEnum.LET.value)
        ident: int = self.tokenizer.id
        self.parse_designator(rhs=False)
        self.__check_token(TokenEnum.BECOMES.value)
        instr_num: int = self.parse_expression()
        self.cfg.update_var_instr_map(self.cfg.curr_bb, ident, instr_num, True)

    def parse_identifier(self) -> int:
        if self.tokenizer.id not in self.cfg.declared_vars:
            line, col = self.tokenizer.get_curr_pos()
            raise CustomSyntaxError(message=f"'{Tokenizer.id2string(self.tokenizer.id)}' not declared but used at line: "
                                            f"{line}, col: {col}!")
        self.__check_token(TokenEnum.IDENTIFIER.value)
        return self.tokenizer.id

    def parse_designator(self, rhs: bool = True) -> Optional[int]:
        ident = self.parse_identifier()
        if rhs:  # get instr num only when it is on RHS
            instr_num: int = self.cfg.get_var_instr_num(self.cfg.curr_bb, ident, set())
            phi_instr_num: Optional[int] = self.cfg.create_phi(ident, instr_num, assignment=False)
            return phi_instr_num if phi_instr_num else instr_num

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
            self.cfg.update_var_instr_map(self.cfg.const_bb, self.tokenizer.number,
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
        # creating if relation and branch instructions
        self.__check_token(TokenEnum.IF.value)
        br_instr: int = self.parse_relation()

        # creating then, else, and join blocks
        if_bb: int = self.cfg.curr_bb.bb_num
        then_bb: int = self.cfg.create_bb([if_bb])
        else_bb: int = self.cfg.create_bb([if_bb])
        join_bb: int = self.cfg.create_bb([])

        # updating phi_scope before start of if
        self.cfg.add_phi_scope(join_bb, TokenEnum.IF.value)

        # creating then block instructions
        self.__check_token(TokenEnum.THEN.value)
        self.cfg.curr_bb = self.cfg.get_bb(then_bb)
        self.parse_stat_sequence()
        l_parent: int = self.cfg.curr_bb.bb_num
        self.cfg.update_successors(l_parent, [join_bb])

        # creating else block instructions
        self.cfg.curr_bb = self.cfg.get_bb(else_bb)
        if self.sym == TokenEnum.ELSE.value:
            self.__next_token()
            self.parse_stat_sequence()
        r_parent: int = self.cfg.curr_bb.bb_num
        self.cfg.update_successors(r_parent, [join_bb])

        # updating the branch instruction from if relation to start of else
        self.cfg.update_instr(br_instr, {"right": else_bb})

        # creating join block instructions
        self.__check_token(TokenEnum.FI.value)
        self.cfg.curr_bb = self.cfg.get_bb(join_bb)
        self.cfg.update_predecessors(join_bb, [l_parent, r_parent])
        self.cfg.update_dom_predecessors(join_bb, [if_bb])
        self.cfg.resolve_phi(join_bb)

        # adding branch instruction at the end of then block to start join block
        self.cfg.build_instr_node(SingleOpInstrNode, OpCodeEnum.BRA.value, l_parent, left=join_bb)

        # updating phi scope at the end of if
        self.cfg.remove_phi_scope()

    def parse_while(self) -> None:
        self.__check_token(TokenEnum.WHILE.value)

        # create while, do and join blocks
        while_bb: int = self.cfg.create_bb([self.cfg.curr_bb.bb_num])
        do_bb: int = self.cfg.create_bb([while_bb])
        follow_bb: int = self.cfg.create_bb([while_bb])

        # updating phi_scope before start of while
        self.cfg.add_phi_scope(while_bb, TokenEnum.WHILE.value)

        # creating while block instructions
        self.cfg.curr_bb = self.cfg.get_bb(while_bb)
        br_instr: int = self.parse_relation()

        # creating do block instructions
        self.__check_token(TokenEnum.DO.value)
        self.cfg.curr_bb = self.cfg.get_bb(do_bb)
        self.parse_stat_sequence()
        r_parent: int = self.cfg.curr_bb.bb_num

        self.cfg.update_predecessors(while_bb, [r_parent])
        self.cfg.update_successors(r_parent, [while_bb])
        self.cfg.build_instr_node(SingleOpInstrNode, OpCodeEnum.BRA.value, do_bb, left=while_bb)

        # updating phi scope at the end of while
        self.cfg.remove_phi_scope()

        # end while parsing
        self.__check_token(TokenEnum.OD.value)
        self.cfg.curr_bb = self.cfg.get_bb(follow_bb)

        # updating the branch instruction from while relation to start of follow
        self.cfg.update_instr(br_instr, {"right": follow_bb})

        self.cfg.resolve_phi(while_bb)

    def parse_statement(self) -> None:
        if self.sym == TokenEnum.LET.value:
            self.parse_assignment()
        elif self.sym == TokenEnum.IF.value:
            self.parse_if()
        elif self.sym == TokenEnum.WHILE.value:
            self.parse_while()

    def parse_stat_sequence(self) -> None:
        self.parse_statement()
        if self.sym == TokenEnum.SEMI.value:
            self.__next_token()
            if self.sym not in [TokenEnum.FI.value, TokenEnum.ELSE.value, TokenEnum.END.value, TokenEnum.OD.value]:
                self.parse_stat_sequence()
