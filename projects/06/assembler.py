"""
Michine Language: manipulate a memory using a processor and a set of registers
    - Arithmetic and Logic Operations
    - Memory Access
        - Direct addressing
        - Immediate addressing
        - Indirect addressing
    - Flow of control

Machine Language Specification:
    - A instruction (0vvv vvvv vvvv vvvv)
        - load constant (immediate addressing)
        - sets pointer to A register (indirect addressing)
        - sets pc (jump)
    - C instruction (111a c1c2c3c4 c5c6d1d2 d3j1j2j3)
        - ac1c2c3c4c5c6: what to compute?
        - d1d2d3: where to store the computed value?
        - j1j2j3: what to do next?

Assembly Language Specification:
    - Instructions
    - Symbols
        - Variables
        - Labels
    - Constants

Assembler: Assembly language --> Machine Language 
- Map Assembly instructions to machine instructions
- Map Symbols to actual memory address

"""

import re
import sys


class Assembler:
    """
    We need a two-pass assembler that reads code twice:
    - The first pass, builds the symbol table
    - The second pass, generate code

    """

    def __init__(self, filename):
        " Require a absolute path. "
        self.filename = filename
        self.symbols = Symbol()

        # output
        self.target = filename.replace('.asm', '.jack')
        self.output = open(self.target, 'w')

        # two pass assemble
        self.set_label()
        self.assemble()

        # IO handle
        self.output.close()

    def write(self, s):
        self.output.write(s)

    def set_label(self):
        # TODO: Is there a possibility that label and variable use the same address?
        line_num = 0
        parser = Parser(self.filename)

        while parser.hasMoreCommands():
            parser.advance()
            if parser.commandType() == 'L_COMMAND':
                symbol = parser.symbol()
                self.symbols.addEntry(symbol, line_num)
            else:
                line_num += 1

    def assemble(self):
        parser = Parser(self.filename)

        while parser.hasMoreCommands():
            parser.advance()
            if parser.commandType() == 'A_COMMAND':
                symbol = parser.symbol()
                # number or symbol
                if symbol.isdigit():
                    address = self.int_to_hex(symbol)
                elif self.symbols.contains(symbol):
                    address = self.int_to_hex(
                        self.symbols.GetAddress(parser.symbol()))
                else:
                    address = self.int_to_hex(self.symbols.next)
                    self.symbols.addEntry(symbol, self.symbols.next)
                    self.symbols.next += 1
                self.write('{}{}\n'.format(Code.A_COMMAND_PREFIX, address))
            elif parser.commandType() == 'C_COMMAND':
                dest = Code.dest(parser.dest())
                comp = Code.comp(parser.comp())
                jump = Code.jump(parser.jump())
                self.write('{}{}{}{}\n'.format(Code.C_COMMAND_PREFIX, comp,
                                               dest, jump))

    def int_to_hex(self, value):
        return bin(int(value))[2:].zfill(15)


class Parser:
    def __init__(self, filename):
        self.file = open(filename, 'r')
        self.input = self.format_lines(self.file.read())
        self.index = -1
        self.length = len(self.input)
        self.file.close()

    def hasMoreCommands(self):
        return self.index < self.length - 1

    def advance(self):
        self.index += 1
        self.command = self.input[self.index].strip()

    def commandType(self):
        if '@' in self.command:
            return 'A_COMMAND'
        elif '=' in self.command or ';' in self.command:
            return 'C_COMMAND'
        elif '(' in self.command and ')' in self.command:
            return 'L_COMMAND'

    def symbol(self):
        if self.commandType() == 'A_COMMAND':
            return self.command.split('@')[1]
        elif self.commandType() == 'L_COMMAND':
            return self.command[1:-1]

    def dest(self):
        if '=' in self.command:
            return self.command.split('=')[0]
        else:
            return ''

    def comp(self):
        # dest=comp;jump
        # the dest or jump fields may be empty
        remove_jump = self.command.split(';')[0]
        comp = remove_jump.split('=')[-1]
        return comp

    def jump(self):
        if ';' in self.command:
            return self.command.split(';')[-1]
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


class Code:

    A_COMMAND_PREFIX = '0'
    C_COMMAND_PREFIX = '111'
    COMP_DICT = {
        "0": "0101010",
        "1": "0111111",
        "-1": "0111010",
        "D": "0001100",
        "A": "0110000",
        "!D": "0001101",
        "!A": "0110001",
        "-D": "0001111",
        "-A": "0110011",
        "D+1": "0011111",
        "A+1": "0110111",
        "D-1": "0001110",
        "A-1": "0110010",
        "D+A": "0000010",
        "D-A": "0010011",
        "A-D": "0000111",
        "D&A": "0000000",
        "D|A": "0010101",
        "M": "1110000",
        "!M": "1110001",
        "-M": "1110011",
        "M+1": "1110111",
        "M-1": "1110010",
        "D+M": "1000010",
        "D-M": "1010011",
        "M-D": "1000111",
        "D&M": "1000000",
        "D|M": "1010101"
    }
    DEST_DICT = {
        "": "000",
        "M": "001",
        "D": "010",
        "MD": "011",
        "A": "100",
        "AM": "101",
        "AD": "110",
        "AMD": "111"
    }
    JUMP_DICT = {
        "": "000",
        "JGT": "001",
        "JEQ": "010",
        "JGE": "011",
        "JLT": "100",
        "JNE": "101",
        "JLE": "110",
        "JMP": "111"
    }

    @staticmethod
    def dest(mnemonic):
        return Code.DEST_DICT[mnemonic]

    @staticmethod
    def comp(mnemonic):
        return Code.COMP_DICT[mnemonic]

    @staticmethod
    def jump(mnemonic):
        return Code.JUMP_DICT[mnemonic]


class Symbol:

    PREDEFINE_SYMBOL_DICT = {
        "SP": "0",
        "LCL": "1",
        "ARG": "2",
        "THIS": "3",
        "THAT": "4",
        "R0": "0",
        "R1": "1",
        "R2": "2",
        "R3": "3",
        "R4": "4",
        "R5": "5",
        "R6": "6",
        "R7": "7",
        "R8": "8",
        "R9": "9",
        "R10": "10",
        "R11": "11",
        "R12": "12",
        "R13": "13",
        "R14": "14",
        "R15": "15",
        "SCREEN": "16384",
        "KBD": "24576"
    }

    def __init__(self):
        self.symbols = self.PREDEFINE_SYMBOL_DICT.copy()
        self.next = 16

    def addEntry(self, symbol, address):
        self.symbols[symbol] = address

    def contains(self, symbol):
        return symbol in self.symbols.keys()

    def GetAddress(self, symbol):
        return self.symbols[symbol]


if __name__ == '__main__':
    print('...assembling...')
    filename = sys.argv[0]
    Assembler(filename)
