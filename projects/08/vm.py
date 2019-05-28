"""
Michine Language: manipulate a memory using a processor and a set of registers
    - Arithmetic and Logic Operations
    - Memory Access
        - Direct addressing
        - Immediate addressing
        - Indirect addressing
    - Flow of control

The VM language that we present here consists of four types of commands: 
    - arithmetic
    - memory access
    - program flow
    - subroutine calling commands

Two way to implement vm:
    - Based on stack machine
    - Based on register


---
We can find out that subroutine call is the extra part of vm language.

Cause the model of subroutine call is Recursive, follow the order of LIFO(Last in First out);
Stack is the natural LIFO model, so we determine to use stack machine to implement vm.

And what's the content of subroutine call?
    - Pass argument
    - Saving the state of the caller
    - Allocating space for the local variables of callee
    - Jump to callee
    - Return values to the caller
    - Recycling the memory space occupied by the callee
    - Reinstating the state of the caller
    - Jump to the position of caller where we left

"""

import re
import os
import sys


class Translator:
    def __init__(self, path):
        if os.path.isdir(path):
            basename = os.path.basename(path) + '.asm'
            fname = os.path.join(path, basename)
            self.writer = CodeWriter(fname)

            files = FileSet(path, 'vm')
            while files.hasMoreFiles():
                filename = files.nextFile()
                self.translate(filename)

            self.writer.save()
        elif os.path.isfile(path):
            self.writer = CodeWriter(path)
            self.translate(path)
            self.writer.save()

    def translate(self, filename):
        parser = Parser(filename)

        while parser.hasMoreCommand():
            parser.advance()
            Type = parser.commandType()
            commandType = self.writer.getCommandType(Type)

            if commandType == 'C_ARITHEMETIC':
                self.writer.writeArithmetic(Type)
            elif commandType in ['C_PUSH', 'C_POP']:
                self.writer.writePushPop(commandType, parser.arg1(),
                                         parser.arg2())
            elif commandType == 'C_LABEL':
                self.writer.writeLabel(parser.arg1())
            elif commandType == 'C_GOTO':
                self.writer.writeGoto(parser.arg1())
            elif commandType == 'C_IF':
                self.writer.writeIf(parser.arg1())
            elif commandType == 'C_FUNCTION':
                self.writer.writeFunction(parser.arg1(), parser.arg2())
            elif commandType == 'C_CALL':
                self.writer.writeCall(parser.arg1(), parser.arg2())
            elif commandType == 'C_RETURN':
                self.writer.writeReturn()
            elif commandType is None:
                raise Exception(" Unknown commandType...")


class Parser:
    def __init__(self, filename):
        self.file = open(filename, 'r')
        self.input = self.format_lines(self.file.read())
        self.index = -1
        self.length = len(self.input)
        self.file.close()

    def hasMoreCommand(self):
        return self.index < self.length - 1

    def advance(self):
        self.index += 1
        self.command = self.input[self.index].strip().split(' ')

    def commandType(self):
        return self.command[0]

    def arg1(self):
        return self.command[1]

    def arg2(self):
        if len(self.command) > 2:
            return self.command[2]
        else:
            return ''

    # Non API
    def format_lines(self, lines):
        # remove blank line and comment
        INLINE_COMMENT_REGEX = re.compile(r'//.*\n')
        without_inline = re.sub(INLINE_COMMENT_REGEX, '\n', lines)
        format_lines = [
            x.strip() for x in without_inline.splitlines() if x != ''
        ]
        return format_lines


class CodeWriter:

    COMMAND_DICT = {
        'add': 'C_ARITHEMETIC',
        'sub': 'C_ARITHEMETIC',
        'and': 'C_ARITHEMETIC',
        'or': 'C_ARITHEMETIC',
        'gt': 'C_ARITHEMETIC',
        'lt': 'C_ARITHEMETIC',
        'eq': 'C_ARITHEMETIC',
        'not': 'C_ARITHEMETIC',
        'neg': 'C_ARITHEMETIC',
        'push': 'C_PUSH',
        'pop': 'C_POP',
        'label': 'C_LABEL',
        'goto': 'C_GOTO',
        'if-goto': 'C_IF',
        'function': 'C_FUNCTION',
        'call': 'C_CALL',
        'return': 'C_RETURN',
    }
    BINARY_ARITHMETIC = {
        'add': 'M+D',
        'sub': 'M-D',
        'and': 'M&D',
        'or': 'M|D',
        'gt': 'M>D',
        'lt': 'M<D',
        'eq': 'M=D',
    }
    UNARY_ARITHMETIC = {
        'not': '!M',
        'neg': '-M',
    }
    JUMP_COMMAND = {
        'gt': 'JGT',
        'lt': 'JLT',
        'eq': 'JEQ',
    }
    ADDRESS_DICT = {
        'local': 'LCL',
        'argument': 'ARG',
        'this': 'THIS',
        'that': 'THAT',
        'pointer': 3,
        'temp': 5,
        # R13-15 are free
        'static': 16,
    }

    def __init__(self, filename):
        self.setFilename(filename)
        self.jump_count = 0
        self.call_count = 0
        self.output = self.target_file(filename)
        self.writeInit()

    def setFilename(self, filename):
        self.filename = filename.split('.vm')[0]

    def writeInit(self):
        self.write('@256')
        self.write('D=A')
        self.write('@SP')
        self.write('M=D')
        self.writeCall('Sys.init', 0)

    def writeArithmetic(self, command):
        # unary: load to A register, save to D, eg., D=!A
        # binary: load to D, load to A, do the arithmetic, eg., D=D+A
        if command in self.BINARY_ARITHMETIC.keys():
            self.pop_stack_to_D()

        self.set_stack_to_A()

        if command in self.BINARY_ARITHMETIC.keys():
            self.write('M={}'.format(self.BINARY_ARITHMETIC[command]))
        elif command in self.UNARY_ARITHMETIC.keys():
            self.write('M={}'.format(self.UNARY_ARITHMETIC[command]))
        elif command in self.JUMP_COMMAND.keys():
            # calculate the result
            # according the result, return Boolean values
            self.write('D=M-D')
            # jump
            self.write('@{}_JUMP{}'.format(self.filename, self.jump_count))
            self.write('D;{}'.format(self.JUMP_COMMAND[command]))
            # default write
            # 0 is false, 1 is true
            self.write('@SP')
            self.write('M=0')
            self.write('@{}_ENDJUMP{}'.format(self.filename, self.jump_count))
            self.write('0;JMP')
            # define jump
            self.write('({}_JUMP{})'.format(self.filename, self.jump_count))
            self.write('@SP')
            self.write('M=-1')
            self.write('({}_ENDJUMP{})'.format(self.filename, self.jump_count))
        else:
            raise Exception("Unknown command")

        self.increment_SP()

    def writePushPop(self, command, segment, index):
        # resolve address to A register
        self.resolve_address(segment, index)

        if command == 'C_PUSH':
            self.writePush(segment)
        elif command == 'C_POP':
            self.writePop(segment)
        else:
            raise Exception("Unknown segment")

    def writeLabel(self, label):
        self.write('({}${})'.format(self.filename, label))

    def writeGoto(self, label):
        self.write('@{}${}'.format(self.filename, label))

    def writeIf(self, label):
        self.pop_stack_to_D()
        self.write('@{}${}'.format(self.filename, label))
        self.write('D;JNE')

    def writeFunction(self, function, nLocals):
        self.write('({})'.format(function))
        nLocals = int(nLocals)
        while nLocals > 0:
            self.writePush('D=0')
            self.push_D_to_stack()
            nLocals -= 1

    def writeCall(self, function, nArgs):
        # Return address
        RET = '@RET.{}.{}'.format(function, self.call_count)
        self.call_count += 1

        self.write(RET)
        self.write('D=A')
        self.push_D_to_stack()

        # save caller status
        for segment in ['LCL', 'ARG', 'THIS', 'THAT']:
            self.write('@{}'.format(segment))
            self.write('D=M')
            self.push_D_to_stack()

        # Reposition of LCL
        self.write('@SP')
        self.write('D=M')
        self.write('@LCL')
        self.write('M=D')

        # Reposition of ARG
        offset = int(nArgs) + 5
        self.write('@{}'.format(offset))
        self.write('D=D-A')
        self.write('@ARG')
        self.write('M=D')

        # goto RET
        self.write('@{}'.format(function))

        # define return address
        self.write('({})'.format(RET))

    def writeReturn(self):
        FRAME = 'R13'
        RET = 'R14'

        # FRAME = LCL
        self.write('@LCL')
        self.write('D=M')
        self.write('@{}'.format(FRAME))
        self.write('M=D')

        # RET = *(FRAME - 5)
        self.write('@{}'.format(FRAME))
        self.write('D=M')
        self.write('@5')
        self.write('D=D-A')
        self.write('@{}'.format(RET))
        self.write('M=D')

        # Reposition the return value
        self.pop_stack_to_D()
        self.write('@ARG')
        self.write('A=M')
        self.write('M=D')

        # SP = ARG + 1
        self.write('@ARG')
        self.write('D=M')
        self.write('@SP')
        self.write('M=D+1')

        # Restore function scope
        offset = 1
        for segment in ["THAT", "THIS", "ARG", "LCL"]:
            self.write('@{}'.format(FRAME))
            self.write('D=M')
            self.write('@{}'.format(offset))
            self.write('D=D-A')
            self.write('A=D')
            self.write('D=M')
            self.write('@{}'.format(segment))
            self.write('M=D')
            offset += 1

        # goto RET
        self.write('@{}'.format(RET))
        self.write('A=M')
        self.write('0;JMP')

    # Non API
    def resolve_address(self, segment, index):
        base_address = self.ADDRESS_DICT.get(segment)
        if segment in ['local', 'argument', 'this', 'that']:
            self.write('@{}'.format(base_address))
            self.write('D=M')
            self.write('@{}'.format(index))
            self.write('A=A+D')
        elif segment in ['pointer', 'temp']:
            address = base_address + int(index)
            self.write('@R{}'.format(address))
        elif segment == 'constant':
            self.write('@{}'.format(index))
        elif segment == 'static':
            self.write('@{}.{}'.format(self.filename, index))
        else:
            raise Exception("Unknown segment")

    def target_file(self, filename):
        target_name = filename.replace('.vm', '.asm')
        target_file = open(target_name, 'w')
        return target_file

    def save(self):
        self.output.close()

    def write(self, s):
        self.output.write("{}\n".format(s))

    def getCommandType(self, comandType):
        return self.COMMAND_DICT.get(comandType, None)

    def push_D_to_stack(self):
        self.write('@SP')
        self.write('A=M')
        self.write('M=D')
        self.increment_SP()

    def pop_stack_to_D(self):
        self.decrement_SP()
        self.write('@SP')
        self.write('A=M')
        self.write('D=M')

    def set_stack_to_A(self):
        self.decrement_SP()
        self.write('@SP')
        self.write('A=M')

    def increment_SP(self):
        self.write('@SP')
        self.write('M=M+1')

    def decrement_SP(self):
        self.write('@SP')
        self.write('M=M-1')

    def writePush(self, segment):
        if segment == 'constant':
            self.write('D=A')
        else:
            self.write('D=M')
        self.push_D_to_stack()

    def writePop(self, segment):
        self.write('D=A')
        self.write('@R13')
        self.write('M=D')
        self.pop_stack_to_D()
        self.write('@R13')
        self.write('A=M')
        self.write('M=D')


class FileSet:
    def __init__(self, filename, file_ext):
        self.target_ext = "." + file_ext
        self.fname = os.path.splitext(filename)[0]
        self.ext = os.path.splitext(filename)[1]

        # Determine if a file or directory was supplied
        self.type_file = False
        self.type_dir = False

        if self.ext == self.target_ext:
            self.type_file = True
        else:
            self.type_dir = True

        self.fileList = []
        self.dirList = []

        # Supplied name is a file of the correct extension
        if (self.type_file):
            if (os.path.isfile(filename)):
                self.dirList = [filename]

        # Supplied name is a directory
        if (self.type_dir):
            if (os.path.isdir(self.fname)):
                self.dirList = os.listdir(self.fname)

        for filename in self.dirList:
            if (os.path.splitext(filename)[1] == self.target_ext):
                if self.type_dir:
                    filename = os.path.join(self.fname, filename)
                self.fileList.append(filename)

    def report(self):
        if (self.type_file):
            print("Processing FILE: %s" % self.fname)
        if (self.type_dir):
            print("Processing DIRECTORY: %s" % self.fname)

        print("Files: %i" % len(self.fileList))

        for filename in self.fileList:
            print("  %s" % os.path.basename(filename))

    def hasMoreFiles(self):
        if self.fileList:
            return True
        return False

    def nextFile(self):
        filename = None
        if self.fileList:
            filename = self.fileList[0]
            self.fileList.remove(filename)
        return filename

    def basename(self):
        return self.fname


if __name__ == '__main__':
    print(' Translating ... ')
    filename = sys.argv[1]
    Translator(filename)
