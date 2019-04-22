import re


class CompileEngine:

    def __init__(self, input_file, output_file):
        self.input = input_file
        self.output = output_file
        self.indent = 0
        self.indent_level = 4

        self.advance() # skip <class>
        self.advance() # initial current token

    # class className '{' classVarDec*, subroutineDec* '}'
    def compileClass(self):
        self.write_open_tag('class')

        self.write_token()
        self.write_token()
        self.write_token()

        while self.isClassVarDec():
            self.compileClassVarDec()

        while self.isSubroutineDec():
            self.compileSubroutine()

        self.write_token()

        self.write_close_tag('class')

    def isClassVarDec(self):
        return 'static' in self.current or 'field' in self.current

    # ('static' | 'field') type varName(',' varName)* ';'
    def compileClassVarDec(self):
        self.write_open_tag('classVarDec')

        self.write_token()
        self.write_token()
        self.write_token()

        while ',' in self.current:
            self.write_token()
            self.write_token()

        self.write_token()

        self.write_close_tag('classVarDec')

    def isSubroutineDec(self):
        return 'constructor' in self.current or 'function' in self.current or 'method' in self.current

    # ('constructor' | 'function' | 'method') ('void' | type) subroutineName '(' parameterList ')' subroutineBody
    def compileSubroutine(self):
        self.write_open_tag('subroutineDec')

        self.write_token()
        self.write_token()
        self.write_token()
        self.write_token()
        self.compileParameterList()
        self.write_token()
        
        # subroutineBody
        # '{' varDec* statements '}'
        self.write_open_tag('subroutineBody')

        self.write_token()
        while self.isVarDec():
            self.compileVarDec()
        
        self.compileStatements()
        self.write_token()
        self.write_close_tag('subroutineBody')
        self.write_close_tag('subroutineDec')

    # ((type varName) (',' type varName)*)?
    def compileParameterList(self):
        self.write_open_tag('parameterList')

        while ')' not in self.current:
            self.write_token()

        self.write_close_tag('parameterList')        

    def isVarDec(self):
        return 'var' in self.current or 'field' in self.current

    # 'var' type varName (',' varName)* ';'
    def compileVarDec(self):
        self.write_open_tag('varDec')

        while ';' not in self.current:
            self.write_token()
        self.write_token()

        self.write_close_tag('varDec')

    def isStatements(self):
        return 'let' in self.current or 'if' in self.current or 'while' in self.current or \
            'do' in self.current or 'return' in self.current

    def compileStatements(self):
        self.write_open_tag('statements')

        while self.isStatements():
            if 'let' in self.current:
                self.compileLet()
            elif 'if' in self.current:
                self.compileIf()
            elif 'while' in self.current:
                self.compileWhile()
            elif 'do' in self.current:
                self.compileDo()
            elif 'return' in self.current:
                self.compileReturn()
            else:
                raise Exception("Unknown Statements {}".format(self.current))

        self.write_close_tag('statements')


    # 'let' varName ('[' expression ']')? '=' expression ';'
    def compileLet(self):
        self.write_open_tag('letStatement')

        self.write_token()
        self.write_token()
        if '[' in self.current:
            self.write_token()
            self.compileExpression()
            self.write_token()

        self.write_token()
        self.compileExpression()
        self.write_token()

        self.write_close_tag('letStatement')

    # 'if' '(' expression ')' '{' statements '}' ('else' '{' statements '}')?
    def compileIf(self):
        self.write_open_tag('ifStatement')

        self.write_token()
        self.write_token()
        self.compileExpression()
        self.write_token()
        self.write_token()
        self.compileStatements()
        self.write_token()

        if 'else' in self.current:
            self.write_token()
            self.write_token()
            self.compileStatements()
            self.write_token()

        self.write_close_tag('ifStatement')

    # 'while' '(' expression ')' '{' statements '}'
    def compileWhile(self):
        self.write_open_tag('whileStatement')

        self.write_token()
        self.write_token()
        self.compileExpression()
        self.write_token()
        self.write_token()
        self.compileStatements()
        self.write_token()

        self.write_close_tag('whileStatement')

    # do subroutinCall ';'
    def compileDo(self):
        self.write_open_tag('doStatement')

        self.write_token()
        self.compileSubroutineCall()
        self.write_token()

        self.write_close_tag('doStatement')

    # 'return' expression? ';'
    def compileReturn(self):
        self.write_open_tag('returnStatement')

        self.write_token()
        if ';' not in self.current:
            self.compileExpression()
        self.write_token()

        self.write_close_tag('returnStatement')

    def is_op(self):
        return re.search(r'> (\+|-|\*|/|&amp;|\||&lt;|&gt;|=) <', self.current)

    # term (op term)*
    def compileExpression(self):
        self.write_open_tag('expression')

        self.compileTerm()
        while self.is_op():
            self.write_token()
            self.compileTerm()

        self.write_close_tag('expression')

    # (expression (',' expression)*)?
    def compileExpressionList(self):
        self.write_open_tag('expressionList')

        if ')' not in self.current:
            self.compileExpression()

        while ')' not in self.current:
            self.write_token()
            self.compileExpression()
        
        self.write_close_tag('expressionList')

    # integerConstant | stringConstant | keywordConstant | varName | varName '[' expression ']' | 
    # subroutineCall | '(' expression ')' | unaryOp term
    def compileTerm(self):
        self.write_open_tag('term')

        if self.is_unary_op_term():
            self.write_token()
            self.compileTerm()

        elif '(' in self.current:
            self.write_token()
            self.compileExpression()
            self.write_token()

        else:
            self.write_token()

            # subroutineCall
            if '.' in self.current:
                self.write_token()
                self.write_token()
                self.write_token()
                self.compileExpressionList()
                self.write_token()

            # '(' expression ')'
            elif '(' in self.current:
                self.write_token()
                self.compileExpression()
                self.write_token()

            elif '[' in self.current:
                self.write_token()
                self.compileExpression()
                self.write_token()

        self.write_close_tag('term')        

    def is_unary_op_term(self):
        return re.search(r'> (-|~) <', self.current)

    # subroutineName '(' expressionList ')' | (className | varName) '.' subroutineName '(' expressionList ')'
    def compileSubroutineCall(self):
        # no tag
        self.write_token()
        if '.' in self.current:
            self.write_token()
            self.write_token()
        self.write_token()
        self.compileExpressionList()
        self.write_token()

    ### Non API
    def advance(self):
        self.current = self.input.readline()

    def write_token(self):
        # write and move, so need to call advance to initial calling
        self.write('{}{}'.format(' '*self.indent, self.current))
        self.advance()

    def write(self, s):
        self.output.write(s)

    def write_open_tag(self, tag):
        self.write("{}<{}>\n".format(' '*self.indent, tag))
        self.indent_increment()

    def write_close_tag(self, tag):
        self.indent_decrement()
        self.write("{}</{}>\n".format(' '*self.indent, tag))

    def indent_increment(self):
        self.indent += self.indent_level

    def indent_decrement(self):
        self.indent -= self.indent_level
