"""
Code Generation:
    - Data Translation
        - Symbol table
        - Handle variables
        - Handle arrays
        - Handle objects
    - Command Translation
        - Evaluating expressions
        - Flow control

"""

import re
from SymbolTable import SymbolTable


class CompilationEngine:
    " Gets its input from a JackTokenizer and emits its parsed structure into output.  "

    CONVERT_KIND = {
        'ARG': 'ARG',
        'STATIC': 'STATIC',
        'VAR': 'LOCAL',
        'FIELD': 'THIS'
    }

    ARITHMETIC = {
        '+': 'ADD',
        '-': 'SUB',
        '=': 'EQ',
        '>': 'GT',
        '<': 'LT',
        '&': 'AND',
        '|': 'OR'
    }

    ARITHMETIC_UNARY = {'-': 'NEG', '~': 'NOT'}

    if_index = 0
    while_index = 0

    def __init__(self, input_file, output_file):
        self.tokenizer = input_file
        self.vm_writer = output_file
        self.symbol_table = SymbolTable()
        # cause tokenizer advance is irreversible
        # need a buffer to save token which need to use more than one time
        self.buffer = []

    # class className '{' classVarDec*, subroutineDec* '}'
    def compileClass(self):
        self.get_token()
        self.class_name = self.get_token()
        self.get_token()

        while self.is_class_var_dec():
            self.compileClassVarDec()  # classVarDec*

        while self.is_subroutine_dec():
            self.compileSubroutine()  # subroutineDec*

        self.vm_writer.close()

    # ('static' | 'field') type varName(',' varName)* ';'
    def compileClassVarDec(self):
        kind = self.get_token()
        type = self.get_token()
        name = self.get_token()
        self.symbol_table.define(name, type, kind)

        while self.peek() != ';':
            self.get_token()
            name = self.get_token()
            self.symbol_table.define(name, type, kind)

        self.get_token()

    # subroutineDec: ('constructor' | 'function' | 'method') ('void' | type) subroutineName '(' parameterList ')' subroutineBody
    # subroutineBody: '{' varDec* statements '}'
    def compileSubroutine(self):
        subroutine_kind = self.get_token()
        subroutine_type = self.get_token()
        subroutine_name = self.get_token()
        self.symbol_table.startSubroutine()

        if subroutine_kind == 'method':
            self.symbol_table.define('instance', self.class_name, 'ARG')

        self.get_token()
        self.compileParameterList()
        self.get_token()
        self.get_token()

        while self.peek() == 'var':
            self.compileVarDec()

        function_name = '{}.{}'.format(self.class_name, subroutine_name)
        nLocals = self.symbol_table.varCount('VAR')
        self.vm_writer.writeFunction(function_name, nLocals)

        if subroutine_kind == 'constructor':
            # collect field number
            field_num = self.symbol_table.varCount('FIELD')
            self.vm_writer.writePush('CONST', field_num)
            self.vm_writer.writeCall('Memory.alloc', 1)
            self.vm_writer.writePop('POINTER', 0)
        elif subroutine_kind == 'method':
            self.vm_writer.writePush('ARG', 0)
            self.vm_writer.writePop('POINTER', 0)

        self.compileStatements()
        self.get_token()

    # ( (type varName) (',' type varName)*)?
    def compileParameterList(self):
        if self.peek() != ')':
            varType = self.get_token()
            varName = self.get_token()
            self.symbol_table.define(varName, varType, 'ARG')

        while self.peek() != ')':
            self.get_token()
            varType = self.get_token()
            varName = self.get_token()
            self.symbol_table.define(varName, varType, 'ARG')

    # 'var' type varName (',' varName)* ';'
    def compileVarDec(self):
        self.get_token()
        varType = self.get_token()
        varName = self.get_token()

        self.symbol_table.define(varName, varType, 'VAR')

        while self.peek() != ';':
            self.get_token()
            varName = self.get_token()
            self.symbol_table.define(varName, varType, 'VAR')

        self.get_token()

    # letStatement | ifStatement | whileStatement | doStatement | returnStatement
    def compileStatements(self):
        while self.is_statement():
            token = self.get_token()

            if 'let' == token:
                self.compileLet()
            elif 'if' == token:
                self.compileIf()
            elif 'while' == token:
                self.compileWhile()
            elif 'do' == token:
                self.compileDo()
            elif 'return' == token:
                self.compileReturn()

    # 'do' subroutineCall ';'
    # subroutineCall: subroutineName '(' expressionList ')' | ( className | varName) '.' subroutineName '(' expressionList ')'
    def compileDo(self):
        self.compile_subroutine_call()
        self.vm_writer.writePop('TEMP', 0)
        self.get_token()

    # 'let' varName ('[' expression ']')? '=' expression ';'
    def compileLet(self):
        varName = self.get_token()
        varKind = self.CONVERT_KIND[self.symbol_table.kindOf(varName)]
        varIndex = self.symbol_table.indexOf(varName)

        if self.peek() == '[':
            self.get_token()
            self.compileExpression()
            self.get_token()

            self.vm_writer.writePush(varKind, varIndex)
            self.vm_writer.writeArithmetic('ADD')

            self.get_token()
            self.compileExpression()
            self.get_token()

            self.vm_writer.writePop('TEMP', 0)
            self.vm_writer.writePop('POINTER', 1)
            self.vm_writer.writePush('TEMP', 0)
            self.vm_writer.writePop('THAT', 0)

        else:
            self.get_token()
            self.compileExpression()
            self.get_token()

            self.vm_writer.writePop(varKind, varIndex)

    # 'while' '(' expression ')' '{' statements '}'
    def compileWhile(self):
        while_index = self.while_index
        self.while_index += 1

        self.vm_writer.writeLabel('WHILE_EXP{}'.format(while_index))
        self.get_token()
        self.compileExpression()
        self.vm_writer.writeArithmetic('NOT')
        self.get_token()
        self.get_token()
        self.vm_writer.writeIf('WHILE_END{}'.format(while_index))
        self.compileStatements()
        self.vm_writer.writeGoto('WHILE_EXP{}'.format(while_index))
        self.vm_writer.writeLabel('WHILE_END{}'.format(while_index))
        self.get_token()

    # 'return' expression? ';'
    def compileReturn(self):
        if self.peek() != ';':
            self.compileExpression()
        else:
            self.vm_writer.writePush('CONST', 0)

        self.vm_writer.writeReturn()
        self.get_token()

    # 'if' '(' expression ')' '{' statements '}' ( 'else' '{' statements '}' )?
    def compileIf(self):
        if_index = self.if_index
        self.if_index += 1

        self.get_token()
        self.compileExpression()
        self.get_token()

        self.get_token()
        self.vm_writer.writeIf('IF_TRUE{}'.format(if_index))
        self.vm_writer.writeGoto('IF_FALSE{}'.format(if_index))
        self.vm_writer.writeLabel('IF_TRUE{}'.format(if_index))
        self.compileStatements()
        self.vm_writer.writeGoto('IF_END{}'.format(if_index))
        self.get_token()

        self.vm_writer.writeLabel('IF_FALSE{}'.format(if_index))
        if self.peek() == 'else':
            self.get_token()
            self.get_token()
            self.compileStatements()
            self.get_token()

        self.vm_writer.writeLabel('IF_END{}'.format(if_index))

    # term (op term)*
    def compileExpression(self):
        self.compileTerm()

        while self.is_op():
            op = self.get_token()
            self.compileTerm()

            if op in self.ARITHMETIC.keys():
                self.vm_writer.writeArithmetic(self.ARITHMETIC[op])
            elif op == '*':
                self.vm_writer.writeCall('Math.multiply', 2)
            elif op == '/':
                self.vm_writer.writeCall('Math.divide', 2)

    # integerConstant | stringConstant | keywordConstant | varName |
    # varName '[' expression ']' | subroutineCall | '(' expression ')' | unaryOp term
    def compileTerm(self):
        if self.is_unary_op_term():
            unary_op = self.get_token()
            self.compileTerm()
            self.vm_writer.writeArithmetic(self.ARITHMETIC_UNARY[unary_op])

        elif self.peek() == '(':
            self.get_token()
            self.compileExpression()
            self.get_token()

        elif self.peek_type() == 'integer':
            self.vm_writer.writePush('CONST', self.get_token())

        elif self.peek_type() == 'string':
            self.compile_string()

        # true、false、null、this
        elif self.peek_type() == 'keyword':
            self.compile_keyword()

        else:
            # varName '[' expression ']'
            if self.is_array():
                array_var = self.get_token()
                self.get_token()
                self.compileExpression()
                self.get_token()

                array_kind = self.symbol_table.kindOf(array_var)
                array_index = self.symbol_table.indexOf(array_var)
                self.vm_writer.writePush(self.CONVERT_KIND[array_kind],
                                         array_index)
                self.vm_writer.writeArithmetic('ADD')
                self.vm_writer.writePop('POINTER', 1)
                self.vm_writer.writePush('THAT', 0)

            # subroutineCall: subroutineName '(' expressionList ')' | ( className | varName) '.' subroutineName '(' expressionList ')'
            elif self.is_subroutine_call():
                self.compile_subroutine_call()

            # varName
            else:
                varName = self.get_token()
                varKind = self.CONVERT_KIND[self.symbol_table.kindOf(varName)]
                varIndex = self.symbol_table.indexOf(varName)
                self.vm_writer.writePush(varKind, varIndex)

    # (expression (',' expression)* )?
    def compileExpressionList(self):
        number_args = 0

        if self.peek() != ')':
            number_args += 1
            self.compileExpression()

        while self.peek() != ')':
            number_args += 1
            self.get_token()
            self.compileExpression()

        return number_args

    # Non API
    def compile_keyword(self):
        keyword = self.get_token()
        if keyword == 'this':
            self.vm_writer.writePush('POINTER', 0)
        else:
            self.vm_writer.writePush('CONST', 0)

            if keyword == 'true':
                self.vm_writer.writeArithmetic('NOT')

    def compile_subroutine_call(self):
        identifier = self.get_token()
        number_args = 0

        if self.peek() == '.':
            self.get_token()
            subroutine_name = self.get_token()
            subroutine_type = self.symbol_table.typeOf(identifier)

            if subroutine_type is not None:
                # instance
                instance_kind = self.symbol_table.kindOf(identifier)
                instance_type = self.symbol_table.typeOf(identifier)
                instance_index = self.symbol_table.indexOf(identifier)
                self.vm_writer.writePush(self.CONVERT_KIND[instance_kind],
                                         instance_index)

                function_name = '{}.{}'.format(instance_type, subroutine_name)
                number_args += 1

            else:
                # class
                class_name = identifier
                function_name = '{}.{}'.format(class_name, subroutine_name)

        elif self.peek() == '(':
            subroutine_name = identifier
            function_name = '{}.{}'.format(self.class_name, subroutine_name)
            number_args += 1
            self.vm_writer.writePush('POINTER', 0)

        self.get_token()
        number_args += self.compileExpressionList()
        self.get_token()
        self.vm_writer.writeCall(function_name, number_args)

    def compile_string(self):
        string = self.get_token()
        self.vm_writer.writePush('CONST', len(string))
        self.vm_writer.writeCall('String.new', 1)
        for char in string:
            self.vm_writer.writePush('CONST', ord(char))
            self.vm_writer.writeCall('String.appendChar', 2)

    def is_subroutine_call(self):
        token = self.get_token()
        subroutine_call = self.peek() in ['.', '(']
        self.unget_token(token)
        return subroutine_call

    def is_array(self):
        token = self.get_token()
        array = self.peek() == '['
        self.unget_token(token)
        return array

    def is_class_var_dec(self):
        return self.peek() in ['static', 'field']

    def is_subroutine_dec(self):
        return self.peek() in ['constructor', 'function', 'method']

    def is_statement(self):
        return self.peek() in ['let', 'if', 'while', 'do', 'return']

    def is_op(self):
        return self.peek() in ['+', '-', '*', '/', '&', '|', '<', '>', '=']

    def is_unary_op_term(self):
        return self.peek() in ['~', '-']

    def peek(self):
        return self.peek_info()[0]

    def peek_type(self):
        return self.peek_info()[1]

    def peek_info(self):
        token_info = self.get_token_info()
        self.unget_token_info(token_info)
        return token_info

    def get_token(self):
        return self.get_token_info()[0]

    def get_token_info(self):
        if self.buffer:
            return self.buffer.pop(0)
        else:
            return self.get_next_token()

    def unget_token(self, token):
        self.unget_token_info((token, 'UNKNOWN'))

    def unget_token_info(self, token):
        self.buffer.insert(0, token)

    def get_next_token(self):
        if self.tokenizer.hasMoreTokens():
            self.tokenizer.advance()

            if self.tokenizer.tokenType() == 'keyword':
                return (self.tokenizer.keyWord().lower(), self.tokenizer.tokenType())
            elif self.tokenizer.tokenType() == 'symbol':
                return (self.tokenizer.symbol(), self.tokenizer.tokenType())
            elif self.tokenizer.tokenType() == 'identifier':
                return (self.tokenizer.identifier(), self.tokenizer.tokenType())
            elif self.tokenizer.tokenType() == 'integer':
                return (self.tokenizer.intVal(), self.tokenizer.tokenType())
            elif self.tokenizer.tokenType() == 'string':
                return (self.tokenizer.stringVal(), self.tokenizer.tokenType())
