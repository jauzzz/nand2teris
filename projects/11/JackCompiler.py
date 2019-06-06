import os

from JackTokenizer import JackTokenizer
from VMWriter import VMWriter
from CompilationEngine import CompilationEngine


class JackCompiler:
    """
    The analyzer program operates on a given source, 
    where source is either a file name of the form Xxx.jack or a directory name containing one or more such files. 

    For each source Xxx.jack file, the analyzer goes through the following logic:
    1. Create a JackTokenizer from the Xxx.jack input file.
    2. Create an output file called Xxx.xml and prepare it for writing.
    3. Use the CompilationEngine to compile the input JackTokenizer into the output file.

    """

    XML_CONVSERSIONS = {'<': '&lt;', '>': '&gt;', '&': '&amp;'}

    def __init__(self, path):
        self.path = path

        if os.path.isdir(path):
            fileset = self.getFileList(path)
            for f in fileset:
                self.compile(f)
        elif os.path.isfile(path):
            self.compile(path)
        else:
            raise Exception("Unknown path {}".format(path))

    def compile(self, path):
        token_file_name = self.create_token(path)
        self.compile_jack(path, token_file_name)

    def create_token(self, path):
        token_file_name = path.replace('.jack', '.token.xml')
        token_file = open(token_file_name, 'w')
        tokenizer = JackTokenizer(path)

        token_file.write('<tokens>\n')
        while tokenizer.hasMoreTokens():
            tokenizer.advance()
            token_file.write(self.xml_token(tokenizer.current_token))

        token_file.write('</tokens>\n')
        token_file.close()

        return token_file_name

    def compile_jack(self, path, token_file_name):
        tokenizer = JackTokenizer(path)
        vm_writer = VMWriter(path)

        engine = CompilationEngine(tokenizer, vm_writer)
        engine.compileClass()

    def xml_token(self, token):
        typ = token[0]
        val = token[1]
        if typ == 'string':
            typ = 'stringConstant'
            val = val[1:-1]
        if typ == 'integer':
            typ = 'integerConstant'
        if val in self.XML_CONVSERSIONS.keys():
            val = self.XML_CONVSERSIONS[val]
        return '<{typ}> {val} </{typ}>\n'.format(typ=typ, val=val)

    def getFileList(self, path):
        fileset = []
        for i in os.listdir(path):
            if os.path.splitext(i)[1] == '.jack':
                fileset.append(i)
        filelist = [os.path.join(path, i) for i in fileset]
        return filelist
