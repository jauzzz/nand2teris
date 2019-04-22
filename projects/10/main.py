import sys
import os

from JackTokenizer import JackTokenizer
from CompileEngine import CompileEngine


def main(path):
    token_file_name = create_token(path)
    compile_jack(path, token_file_name)


def create_token(path):
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


def compile_jack(path, token_file_name):
    jack_file_name = path.replace('.jack', '.jack.xml')
    jack_file = open(jack_file_name, 'w')
    token_file = open(token_file_name, 'r')

    engine = CompileEngine(token_file, jack_file)
    engine.compileClass()

    jack_file.close()


if __name__ == '__main__':
    # input is a filename or a directory
    path = sys.argv[1]

    if os.path.isdir(path):
        pass
    elif os.path.isfile(path):
        main(path)
    else:
        raise Exception("Unknown path {}".format(path))
