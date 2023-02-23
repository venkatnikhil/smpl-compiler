from app.tokenizer import Tokenizer
from app.tokens import TokenEnum, RELOP_TOKEN_OPCODE
from app.custom_types import InstrNodeType
from app.error_handling import CustomSyntaxError
from app.parser.instr_node import *
from app.parser.cfg import CFG
from typing import Optional, Union


DATATYPE_SIZE = 4
BASE_INSTR_NUM = 1


class Parser:
    def __init__(self, file_name: str) -> None:
        self.tokenizer: Tokenizer = Tokenizer(file_name)
        self.sym: Optional[int] = None  # holds current token
        self.cfg: CFG = CFG()
        self.cfg_map: dict[int, CFG] = {0: self.cfg}
        self.func_param_map: dict[int, int] = {TokenEnum.READ.value: 0, TokenEnum.WRITE.value: 1,
                                               TokenEnum.WRITE_NL.value: 0}
        self._return_func: set[int] = set()
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

    def is_declared(self) -> bool:
        if self.tokenizer.id in self.cfg.declared_vars:
            line, col = self.tokenizer.get_curr_pos()
            raise CustomSyntaxError(
                message=f"'{Tokenizer.id2string(self.tokenizer.id)}' declared more than once "
                        f"at line: {line}, col: {col}!")
        return False

    def build_param_instr(self, param_num: int) -> None:
        instr_num: int = self.cfg.build_instr_node(SingleOpInstrNode, OpCodeEnum.PARAM.value, self.cfg.const_bb.bb_num,
                                                   left=param_num)
        self.cfg.update_var_instr_map(self.cfg.const_bb, self.tokenizer.id, instr_num)

    def parse_func_params(self) -> int:
        param_count: int = 0
        self.__next_token()
        if not self.is_declared():
            param_count += 1
            self.cfg.declared_vars.add(self.tokenizer.id)
            self.build_param_instr(param_count)
        while self.sym == TokenEnum.COMMA.value:
            self.__next_token()
            self.__check_token(TokenEnum.IDENTIFIER.value)
            if not self.is_declared():
                param_count += 1
                self.cfg.declared_vars.add(self.tokenizer.id)
                self.build_param_instr(param_count)
        return param_count

    def parse_formal_param(self) -> int:
        self.__check_token(TokenEnum.OPEN_PAREN.value)
        param_count: int = 0
        if self.sym == TokenEnum.IDENTIFIER.value:
            param_count = self.parse_func_params()
        self.__check_token(TokenEnum.CLOSE_PAREN.value)
        return param_count

    def parse_func_body(self) -> None:
        while self.sym == TokenEnum.VAR.value or self.sym == TokenEnum.ARR.value:
            self.parse_var_decl()

        self.__check_token(TokenEnum.BEGIN.value)
        if self.sym != TokenEnum.END.value:
            self.parse_stat_sequence()
        self.__check_token(TokenEnum.END.value)

    def parse_function(self) -> None:
        func_cfg: CFG = CFG()

        is_void: bool = False
        if self.sym == TokenEnum.VOID.value:
            is_void = True
            self.__next_token()
        self.__check_token(TokenEnum.FUNC.value)
        self.__check_token(TokenEnum.IDENTIFIER.value)
        func_name: int = self.tokenizer.id
        self.cfg_map[func_name] = func_cfg
        self.cfg = func_cfg
        if not is_void:
            self._return_func.add(func_name)
        param_num: int = self.parse_formal_param()
        self.func_param_map[func_name] = param_num
        self.__check_token(TokenEnum.SEMI.value)
        self.parse_func_body()
        self.__check_token(TokenEnum.SEMI.value)

        self.cfg = self.cfg_map[0]

    def parse_computation(self) -> None:
        self.__check_token(TokenEnum.MAIN.value)
        while self.sym == TokenEnum.VAR.value or self.sym == TokenEnum.ARR.value:
            self.parse_var_decl()
        while self.sym == TokenEnum.FUNC.value or self.sym == TokenEnum.VOID.value:
            self.parse_function()
        self.__check_token(TokenEnum.BEGIN.value)
        self.parse_stat_sequence()
        self.__check_token(TokenEnum.END.value)
        self.__check_token(TokenEnum.PERIOD.value)
        self.__check_token(TokenEnum.EOF.value)
        self.cfg.update_branch_instrs()
        self.cfg.build_instr_node(ZeroOpInstrNode, OpCodeEnum.END.value)

    def parse_type_decl(self) -> Optional[list[int]]:
        if self.sym == TokenEnum.VAR.value:
            self.__next_token()
            return

        dim: list[int] = []
        self.__check_token(TokenEnum.ARR.value)
        self.__check_token(TokenEnum.OPEN_BRACKET.value)
        dim.append(self.parse_number())
        self.__check_token(TokenEnum.CLOSE_BRACKET.value)

        while self.sym == TokenEnum.OPEN_BRACKET.value:
            self.__next_token()
            dim.append(self.parse_number())
            self.__check_token(TokenEnum.CLOSE_BRACKET.value)

        return dim

    def parse_var_decl(self) -> None:
        dim: Optional[list[int]] = self.parse_type_decl()
        self.__check_token(TokenEnum.IDENTIFIER.value)
        self.cfg.declared_vars.add(self.tokenizer.id)
        if dim is not None:
            instr_num: int = self.cfg.build_instr_node(AddrInstrNode, OpCodeEnum.CONST.value,
                                                       bb=self.cfg.const_bb.bb_num,
                                                       val=f"{Tokenizer.id2string(self.tokenizer.id)}_addr")
            self.cfg.arr_map[self.tokenizer.id] = [instr_num, dim]

        while self.sym == TokenEnum.COMMA.value:
            self.__next_token()
            self.__check_token(TokenEnum.IDENTIFIER.value)

            if self.tokenizer.id in self.cfg.declared_vars:
                line, col = self.tokenizer.get_curr_pos()
                raise CustomSyntaxError(
                    message=f"'{Tokenizer.id2string(self.tokenizer.id)}' declared more than once "
                            f"at line: {line}, col: {col}!")
            self.cfg.declared_vars.add(self.tokenizer.id)

            if dim is not None:
                instr_num: int = self.cfg.build_instr_node(AddrInstrNode, OpCodeEnum.CONST.value,
                                                           bb=self.cfg.const_bb.bb_num,
                                                           val=f"{Tokenizer.id2string(self.tokenizer.id)}_addr")
                self.cfg.arr_map[self.tokenizer.id] = [instr_num, dim]
        self.__check_token(TokenEnum.SEMI.value)

    def parse_assignment(self) -> None:
        self.__check_token(TokenEnum.LET.value)
        ident: int = self.tokenizer.id
        adda_instr_num: int = self.parse_designator(rhs=False)
        self.__check_token(TokenEnum.BECOMES.value)
        instr_num: int = self.parse_expression()
        if adda_instr_num is not None:
            self.cfg.build_instr_node(OpInstrNode, opcode=OpCodeEnum.STORE.value, left=adda_instr_num,
                                      right=instr_num)
        else:
            self.cfg.update_var_instr_map(self.cfg.curr_bb, ident, instr_num)

    def parse_identifier(self) -> int:
        if self.tokenizer.id not in self.cfg.declared_vars and self.tokenizer.id not in self.func_param_map.keys():
            line, col = self.tokenizer.get_curr_pos()
            raise CustomSyntaxError(message=f"'{Tokenizer.id2string(self.tokenizer.id)}' not declared but used at line: "
                                            f"{line}, col: {col}!")
        self.__check_token(TokenEnum.IDENTIFIER.value)
        return self.tokenizer.id

    def __build_arr_instrs(self, ident: int, dim_instr_ops: list[int], rhs: bool) -> int:
        assert len(dim_instr_ops) == len(self.cfg.arr_map[ident][1]), "array dimensions do not match"
        self.cfg.create_kill_instr(self.cfg.arr_map[ident][0], 1 - rhs)
        cur_off: int = dim_instr_ops[0]
        for i in range(1, len(dim_instr_ops)):
            cur_off = self.cfg.build_instr_node(OpInstrNode, opcode=OpCodeEnum.MUL.value, left=cur_off,
                                                right=self.cfg.arr_map[ident][1][i])
            cur_off = self.cfg.build_instr_node(OpInstrNode, opcode=OpCodeEnum.ADD.value, left=cur_off,
                                                right=dim_instr_ops[i])
        if not self.cfg.const_bb.check_instr_exists(DATATYPE_SIZE):
            self.cfg.update_var_instr_map(self.cfg.const_bb, DATATYPE_SIZE, self.cfg.build_instr_node(
                ConstInstrNode, OpCodeEnum.CONST.value, bb=self.cfg.const_bb.bb_num, val=DATATYPE_SIZE))

        offset_instr: int = self.cfg.build_instr_node(OpInstrNode, opcode=OpCodeEnum.MUL.value, left=cur_off,
                                                      right=self.cfg.const_bb.get_var_instr_num(DATATYPE_SIZE))

        arr_addr: int = self.cfg.build_instr_node(OpInstrNode, opcode=OpCodeEnum.ADD.value, left=BASE_INSTR_NUM,
                                                  right=self.cfg.arr_map[ident][0])

        cur_addr: int = self.cfg.build_instr_node(OpInstrNode, opcode=OpCodeEnum.ADDA.value, left=offset_instr,
                                                  right=arr_addr)

        if rhs:
            return self.cfg.build_instr_node(SingleOpInstrNode, opcode=OpCodeEnum.LOAD.value, left=cur_addr)

        return cur_addr

    def parse_designator(self, rhs: bool = True) -> Optional[int]:
        ident = self.parse_identifier()
        if ident in self.cfg.arr_map:
            if self.sym != TokenEnum.OPEN_BRACKET.value:  # TODO: fix multi-dimensional array parsing
                raise CustomSyntaxError(message=f"missing [] for array")
            dim_instr_ops: list[int] = []
            while self.sym == TokenEnum.OPEN_BRACKET.value:
                self.__next_token()
                dim_instr_ops.append(self.parse_expression())
                self.__check_token(TokenEnum.CLOSE_BRACKET.value)

            return self.__build_arr_instrs(ident, dim_instr_ops, rhs)

        if rhs:  # get instr num only when it is on RHS
            instr_num: int = self.cfg.get_var_instr_num(self.cfg.curr_bb, ident, set())
            phi_instr_num: Optional[int] = self.cfg.create_phi_instr(ident, assignment=False)
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
        elif self.sym == TokenEnum.CALL.value:
            return self.parse_function_call()
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
        self.cfg.curr_bb = self.cfg.get_bb_from_bb_num(then_bb)
        self.parse_stat_sequence()
        l_parent: int = self.cfg.curr_bb.bb_num
        self.cfg.update_successors(l_parent, [join_bb])

        # creating else block instructions
        self.cfg.curr_bb = self.cfg.get_bb_from_bb_num(else_bb)
        if self.sym == TokenEnum.ELSE.value:
            self.__next_token()
            self.parse_stat_sequence()
        r_parent: int = self.cfg.curr_bb.bb_num
        self.cfg.update_successors(r_parent, [join_bb])

        # updating the branch instruction from if relation to start of else
        self.cfg.update_instr(br_instr, {"right": else_bb})

        # creating join block instructions
        self.__check_token(TokenEnum.FI.value)
        self.cfg.curr_bb = self.cfg.get_bb_from_bb_num(join_bb)
        self.cfg.update_predecessors(join_bb, [l_parent, r_parent])
        self.cfg.update_dom_predecessors(join_bb, [if_bb])
        self.cfg.resolve_phi(join_bb)
        self.cfg.resolve_kill(join_bb)

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
        self.cfg.curr_bb = self.cfg.get_bb_from_bb_num(while_bb)
        br_instr: int = self.parse_relation()

        # creating do block instructions
        self.__check_token(TokenEnum.DO.value)
        self.cfg.curr_bb = self.cfg.get_bb_from_bb_num(do_bb)
        self.parse_stat_sequence()
        r_parent: int = self.cfg.curr_bb.bb_num

        self.cfg.update_predecessors(while_bb, [r_parent])
        self.cfg.update_successors(r_parent, [while_bb])
        self.cfg.build_instr_node(SingleOpInstrNode, OpCodeEnum.BRA.value, r_parent, left=while_bb)

        # updating phi scope at the end of while
        self.cfg.remove_phi_scope()

        # end while parsing
        self.__check_token(TokenEnum.OD.value)
        self.cfg.curr_bb = self.cfg.get_bb_from_bb_num(follow_bb)

        # updating the branch instruction from while relation to start of follow
        self.cfg.update_instr(br_instr, {"right": follow_bb})

        self.cfg.resolve_phi(while_bb)
        self.cfg.resolve_kill(while_bb)

    def parse_function_call(self, rhs=True) -> int:
        self.__check_token(TokenEnum.CALL.value)

        if self.sym in [TokenEnum.READ.value, TokenEnum.WRITE.value, TokenEnum.WRITE_NL.value]:
            func_name: int = self.sym
            self.__next_token()
        else:
            func_name: int = self.parse_identifier()

        func_param: list[int] = []
        if self.sym == TokenEnum.OPEN_PAREN.value:
            self.__next_token()
            while self.sym != TokenEnum.CLOSE_PAREN.value:
                func_param.append(self.parse_expression())
                if self.sym != TokenEnum.CLOSE_PAREN.value:
                    self.__check_token(TokenEnum.COMMA.value)
            self.__next_token()

        if len(func_param) != self.func_param_map[func_name]:
            raise CustomSyntaxError(message=f"Expected {self.func_param_map[func_name]} parameters, "
                                            f"found {len(func_param)}")

        if func_name in [TokenEnum.READ.value, TokenEnum.WRITE.value, TokenEnum.WRITE_NL.value]:
            return self.call_pre_defined_funct(func_name, func_param)

        for param in func_param:
            self.cfg.build_instr_node(SingleOpInstrNode, opcode=OpCodeEnum.PARAM.value, left=param)

        if rhs and func_name not in self._return_func:
            raise CustomSyntaxError(message="Cannot assign value of void function!")
        elif not rhs and func_name in self._return_func:
            raise CustomSyntaxError(message="Cannot call a non-void function as a statement!")
        return self.cfg.build_instr_node(SingleOpInstrNode, opcode=OpCodeEnum.CALL.value, left=func_name)

    def call_pre_defined_funct(self, func_name: int, func_param: list[int]) -> int:
        if func_name == TokenEnum.READ.value:
            instr_num: int = self.cfg.build_instr_node(ZeroOpInstrNode, OpCodeEnum.READ.value, self.cfg.curr_bb.bb_num)
        elif func_name == TokenEnum.WRITE.value:
            instr_num: int = self.cfg.build_instr_node(SingleOpInstrNode, OpCodeEnum.WRITE.value,
                                                       self.cfg.curr_bb.bb_num, left=func_param[0])
        else:
            instr_num: int = self.cfg.build_instr_node(ZeroOpInstrNode, OpCodeEnum.WRITE_NL.value,
                                                       self.cfg.curr_bb.bb_num)
        return instr_num

    def parse_return(self) -> None:
        self.__check_token(TokenEnum.RETURN.value)

        if self.sym not in {TokenEnum.SEMI.value, TokenEnum.END.value}:
            return_val: int = self.parse_expression()
            self.cfg.build_instr_node(SingleOpInstrNode, OpCodeEnum.RETURN.value, left=return_val)
        else:
            self.cfg.build_instr_node(ZeroOpInstrNode, OpCodeEnum.RETURN.value)

    def parse_statement(self) -> None:
        if self.sym == TokenEnum.LET.value:
            self.parse_assignment()
        elif self.sym == TokenEnum.IF.value:
            self.parse_if()
        elif self.sym == TokenEnum.WHILE.value:
            self.parse_while()
        elif self.sym == TokenEnum.CALL.value:
            self.parse_function_call(rhs=False)
        else:
            self.parse_return()

    def parse_stat_sequence(self) -> None:
        self.parse_statement()
        if self.sym == TokenEnum.SEMI.value:
            self.__next_token()
            if self.sym not in [TokenEnum.FI.value, TokenEnum.ELSE.value, TokenEnum.END.value, TokenEnum.OD.value]:
                self.parse_stat_sequence()

    def debug(self) -> None:
        def __fmt_arr_map() -> dict[str, str]:
            temp = dict()

            for var, val in self.cfg.arr_map.items():
                temp[Tokenizer.id2string(var)] = f"{val}"

            return temp
        print(__fmt_arr_map())
        self.cfg.debug()
