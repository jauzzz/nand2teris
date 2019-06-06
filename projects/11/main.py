import sys
from JackCompiler import JackCompiler

if __name__ == '__main__':
    print(' Analyzing ... ')
    filename = sys.argv[1]
    JackCompiler(filename)
