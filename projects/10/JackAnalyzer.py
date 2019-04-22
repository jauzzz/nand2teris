import os

from JackTokenizer import JackTokenizer
from CompileEngine import CompileEngine


class JackAnalyzer:

    def __init__(self, path):
        self.path = path

        if os.path.isdir(path):
            fileset = self.getFileList(path)
            for f in fileset:
                self.analyze(f)
        elif os.path.isfile(path):
            self.analyze(path)
        else:
            raise Exception("Unknown path {}".format(path))

    def analyze(self, path):
        token_file_name = self.create_token(path)
        self.compile_jack(path, token_file_name)

    def create_token(self, path):
        token_file_name = path.replace('.jack', '.token.xml')
        token_file = open(token_file_name, 'w')
        source_file = open(path, 'r')
        tokenizer = JackTokenizer(source_file)

        token_file.write('<tokens>\n')
        
        while tokenizer.hasMoreTokens():
            tokenizer.advance()
            token_file.write(tokenizer.xml_token)

        token_file.write('</tokens>\n')
        token_file.close()

        return token_file_name

    def compile_jack(self, path, token_file_name):
        jack_file_name = path.replace('.jack', '.jack.xml')
        jack_file = open(jack_file_name, 'w')
        token_file = open(token_file_name, 'r')

        engine = CompileEngine(token_file, jack_file)
        engine.compileClass()

        jack_file.close()

    def getFileList(self, path):
        fileset = []
        for i in os.listdir(path):
            if os.path.splitext(i)[1] == '.jack':
                fileset.append(i)    
        filelist = [os.path.join(path, i) for i in fileset]
        return filelist
