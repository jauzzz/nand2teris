import os
import re


class JackTokenizer:

    token_specification = [
        ('integer', r'\d+'),
        ('string', r'\"([^"]*)\"'),
        ('keyword', r'(class|constructor|method|function|int|boolean|char|void|var|static|field|let|do|if|else|while|return|true|false|null|this)'),
        ('symbol', r'[+\-*\/\&\|\~\<\>\=\(\)\{\}\[\]\.\,\;]'),
        ('identifier', r'[A-Za-z_][A-Za-z_0-9]*'),
    ]
    INLINE_COMMENT_REGEX    = re.compile(r'//.*\n')
    MULTILINE_COMMENT_REGEX = re.compile(r'/\*.*?\*/', flags=re.S)

    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
    get_token = re.compile(tok_regex)

    def __init__(self, input_file):
        self.input = input_file.read()
        self.tokens = self.tokenize()
        self.next_token = ''
        self.advance()
        
        input_file.close()

    def advance(self):
        self.current_token = self.next_token

        try:
            ele = next(self.tokens)
            self.next_token = (ele.lastgroup, ele.group())
        except:
            self.next_token = False

    def hasMoreTokens(self):
        return self.next_token

    def tokenType(self):
        return self.current_token[0]

    def keyWord(self):
        return self.current_token[1].upper()

    def symbol(self):
        return self.current_token[1]

    def identifier(self):
        return self.current_token[1]

    def intval(self):
        return self.current_token[1]

    def stringval(self):
        return self.current_token[1]

    # Private
    def tokenize(self):
        input_without_comments = self.remove_comments()
        tokens = self.get_token.finditer(input_without_comments)
        return tokens

    def remove_comments(self):
        without_multiline = re.sub(self.MULTILINE_COMMENT_REGEX, ' ', self.input)
        without_inline = re.sub(self.INLINE_COMMENT_REGEX, '\n', without_multiline)
        return without_inline
