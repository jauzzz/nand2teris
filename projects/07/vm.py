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
    - pass argument
    - save return address
    - save the status of caller
    - jump to callee

"""

import re
import sys


class Translator:
    def __init__(self, filename):
        self.filename = filename
        self.translate()

    def translate(self):
        parser = Parser(self.filename)
        writer = CodeWriter(self.filename)

        while parser.hasMoreCommand():
            parser.advance()
            Type = parser.commandType()
            commandType = writer.getCommandType(Type)

            if commandType == 'C_ARITHEMETIC':
                writer.writeArithmetic(Type)
            elif commandType in ['C_PUSH', 'C_POP']:
                writer.writePushPop(commandType, parser.arg1(), parser.arg2())
            elif commandType is None:
                raise Exception(" Unknown commandType...")

        # IO handle
        writer.save()


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
        self.output = self.target_file(filename)

    def setFilename(self, filename):
        self.function_name = filename.split('.vm')[0]

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
            self.write('@{}_JUMP{}'.format(self.function_name,
                                           self.jump_count))
            self.write('D;{}'.format(self.JUMP_COMMAND[command]))
            # default write
            # 0 is false, 1 is true
            self.write('@SP')
            self.write('M=0')
            self.write('@{}_ENDJUMP{}'.format(self.function_name,
                                              self.jump_count))
            self.write('0;JMP')
            # define jump
            self.write('({}_JUMP{})'.format(self.function_name,
                                            self.jump_count))
            self.write('@SP')
            self.write('M=-1')
            self.write('({}_ENDJUMP{})'.format(self.function_name,
                                               self.jump_count))
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
            self.write('@{}.{}'.format(self.function_name, index))
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


if __name__ == '__main__':
    print(' Translating ... ')
    filename = sys.argv[1]
    Translator(filename)
