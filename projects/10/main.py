import sys
from JackAnalyzer import JackAnalyzer


if __name__ == '__main__':
    # input is a filename or a directory
    path = sys.argv[1]
    JackAnalyzer(path)
