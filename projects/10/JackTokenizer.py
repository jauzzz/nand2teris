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
    XML_CONVSERSIONS = {
        '<': '&lt;',
        '>': '&gt;',
        '&': '&amp;'
    }
    
    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
    get_token = re.compile(tok_regex)

    def __init__(self, input_file):
        self.input = input_file.read()
        self.tokenizer = self.tokenize()

    def advance(self):        
        self.current_token = (self.next_token.lastgroup, self.next_token.group())        

    def hasMoreTokens(self):
        try:
            self.next_token = next(self.tokenizer)
            return True
        except:
            return False

    def tokenType(self):
        return self.current_token[0]

    def keyWord(self):
        return self.current_token[1].upper()

    def symbol(self):
        symbol = self.current_token[1]
        if symbol in self.XML_CONVSERSIONS.keys():
            symbol = self.XML_CONVSERSIONS[symbol]
        return symbol

    def identifier(self):
        return self.current_token[1]

    def intval(self):
        return self.current_token[1]

    def stringval(self):
        return self.current_token[1]

    ### Non API
    @property
    def current_token(self):
        if hasattr(self, 'current_token'):            
            return self.current_token
        else:
            raise AttributeError()

    @property
    def xml_token(self):
        typ = self.current_token[0]
        val = self.current_token[1]
        if typ == 'string':
            typ = 'stringConstant'
            val = val[1:-1]
        if typ == 'integer':
            typ = 'integerConstant'
        if val in self.XML_CONVSERSIONS.keys():
            val = self.XML_CONVSERSIONS[val]
        return '<{typ}> {val} </{typ}>\n'.format(typ=typ, val=val)

    def tokenize(self):
        input_without_comments = self.remove_comments()
        tokens = self.get_token.finditer(input_without_comments)
        return tokens

    def remove_comments(self):
        without_multiline = re.sub(self.MULTILINE_COMMENT_REGEX, ' ', self.input)
        without_inline = re.sub(self.INLINE_COMMENT_REGEX, '\n', without_multiline)
        return without_inline
