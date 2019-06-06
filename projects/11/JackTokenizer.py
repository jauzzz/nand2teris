"""
Jack Syntactic Elements
    - white space and comments
    - symbols: () [] {} , ; = . + - * / & | ~ < >
    - reversed words
        - class, constructor, method, function // Program components
        - int, boolean, char, void // Primitive types
        - var, static, field // Variable declarations
        - let, do, if, else, while, return // Statements
        - true, false, null // constant values
        - this // object reference
    - constants
        - integer
        - string
        - boolean
    - identifiers

"""

import re


class JackTokenizer:
    " Reference: https://docs.python.org/3/library/re.html#writing-a-tokenizer "

    token_specification = [
        ('integer', r'\d+'),
        ('string', r'\"([^"]*)\"'),
        ('symbol', r'[+\-*\/\&\|\~\<\>\=\(\)\{\}\[\]\.\,\;]'),
        ('keyword',
         r'(class|constructor|method|function|int|boolean|char|void|var|static|field|let|do|if|else|while|return|true|false|null|this)'
         ),
        ('identifier', r'[A-Za-z_][A-Za-z_0-9]*'),
    ]
    INLINE_COMMENT_REGEX = re.compile(r'//.*\n')
    MULTILINE_COMMENT_REGEX = re.compile(r'/\*.*?\*/', flags=re.S)
    XML_CONVSERSIONS = {'<': '&lt;', '>': '&gt;', '&': '&amp;'}

    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
    get_token = re.compile(tok_regex)

    def __init__(self, input_file):
        token_file = open(input_file, 'r')

        self.input = token_file.read()
        self.tokenizer = self.tokenize()

        # IO handle
        token_file.close()

    def hasMoreTokens(self):
        try:
            self.next_token = next(self.tokenizer)
            return True
        except:
            return False

    def advance(self):
        self.current_token = (self.next_token.lastgroup,
                              self.next_token.group())

    def tokenType(self):
        return self.current_token[0]

    def keyWord(self):
        return self.current_token[1]

    def symbol(self):
        return self.current_token[1]

    def identifier(self):
        return self.current_token[1]

    def intVal(self):
        return self.current_token[1]

    def stringVal(self):
        return self.current_token[1][1:-1]

    # Non API
    def tokenize(self):
        format_lines = self.format_lines()
        tokens = self.get_token.finditer(format_lines)
        return tokens

    def format_lines(self):
        without_multiline = re.sub(self.MULTILINE_COMMENT_REGEX, ' ',
                                   self.input)
        without_inline = re.sub(self.INLINE_COMMENT_REGEX, '\n',
                                without_multiline)
        format_lines = without_inline
        return format_lines
