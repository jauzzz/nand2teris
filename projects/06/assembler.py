import os
import sys


HACK_FILETYPE = 'hack'
A_COMMAND_NOTION = '@'
C_COMMAND_NOTION = '1'
L_COMMAND_NOTION = '('
A_COMMAND_PREFIX = '0'
C_COMMAND_PREFIX = '111'
C_COMMAND_COMP = "="
C_COMMAND_JUMP = ";"
DEFAULT_DEST = '000'
DEFAULT_JUMP = '000'

COMP_DICT = {"0": "0101010", "1": "0111111", "-1": "0111010", "D": "0001100", "A": "0110000", 
             "!D": "0001101", "!A": "0110001", "-D": "0001111", "-A": "0110011", "D+1": "0011111",
             "A+1": "0110111", "D-1": "0001110", "A-1": "0110010", "D+A": "0000010", "D-A": "0010011",
             "A-D": "0000111", "D&A": "0000000", "D|A": "0010101", "M": "1110000", "!M": "1110001",
             "-M": "1110011", "M+1": "1110111", "M-1": "1110010", "D+M": "1000010", "D-M": "1010011",
             "M-D": "1000111", "D&M": "1000000", "D|M": "1010101"}
DEST_DICT = {"M": "001", "D": "010", "MD": "011", "A": "100", "AM": "101", "AD": "110", "AMD": "111"}
JUMP_DICT = {"JGT": "001", "JEQ": "010", "JGE": "011", "JLT": "100", "JNE": "101", "JLE": "110", "JMP": "111"}
DEFINE_SYMBOL_DICT = {"SP": "0", "LCL": "1", "ARG": "2", "THIS": "3", "THAT": "4", "R0": "0", "R1": "1", "R2": "2",
                     "R3": "3", "R4": "4", "R5": "5", "R6": "6", "R7": "7", "R8": "8", "R9": "9", "R10": "10", "R11": "11", 
                     "R12": "12", "R13": "13", "R14": "14", "R15": "15", "R16": "16", "SCREEN": "16384", "KBD": "24576"}


class Code(object):
    """ Read input file and parse it """
    
    def __init__(self, name):
        self.source = name
        self.base = os.getcwd()
        self.dir = os.path.dirname(name)
        self.type = os.path.split(name)[-1]
        self.name = os.path.split(name)[-1].split('.')[0]
        
    def read(self):
        lines = ''
        if os.path.exists(self.source):
            with open(self.source, 'r') as f:
                lines = f.read()
        return lines
    
    def write(self):
        output_name = self.name + '.' + HACK_FILETYPE
        output_file = os.path.join(self.base, self.dir, output_name)
        if self.code:
            with open(output_file, 'w+') as f:
                f.write(self.code)

    def assemble(self):
        lines = self.read()
        self.parser = Parser(lines)
        self.code = self.parser.parse()
        self.write()
    

class Parser(object):
    """ parse instruction to its binary representation """
    
    def __init__(self, lines):
        self.lines = self.format_lines(lines)     
        self.symbols = DEFINE_SYMBOL_DICT.copy()
        self.next = 16

    def format_lines(self, lines):
        # remove space and newline
        new_line = []
        split_line = lines.splitlines()
        for line in split_line:
            s = line.split('//')[0].strip()
            if s:
                new_line.append(s)
        return new_line

    def parse_label(self):
        line_num = 0
        for line in self.lines:
            if line.startswith(L_COMMAND_NOTION):
                symbol = line[1:-1]
                self.symbols[symbol] = line_num
            else:
                line_num += 1

    def parse(self):
        self.parse_label()

        codes = []
        for line in self.lines:
            if line.startswith(A_COMMAND_NOTION):
                code = self.parse_A_command(line) + '\n'
            elif line.startswith(L_COMMAND_NOTION):
                continue
            else:
                code = self.parse_C_command(line) + '\n'
            codes.append(code)
        return ''.join(codes)

    def parse_A_command(self, line):
        value = line[len(A_COMMAND_NOTION):]
        # number or symbol
        if value.isnumeric():
            address = self.int_to_hex(value)
        elif value in self.symbols.keys():
            new_value = self.symbols[value]
            address = self.int_to_hex(new_value)
        else:            
            self.symbols[value] = self.next
            address = str(self.int_to_hex(self.next))
            self.next += 1

        return A_COMMAND_PREFIX + address
    
    def int_to_hex(self, value):
        return bin(int(value))[2:].zfill(15)

    def parse_C_command(self, line):
        split_line = line.split(C_COMMAND_JUMP)
        split_line2 = split_line[0].split(C_COMMAND_COMP)

        dest = DEFAULT_DEST
        jump = DEFAULT_JUMP
        comp = split_line2[-1].strip().replace(' ', '')

        if len(split_line) == 2:
            jump = split_line[1].strip()
            jump = self.parse_jump(jump)
        if len(split_line2) == 2:
            dest = split_line2[0].strip()
            dest = self.parse_dest(dest)
                
        comp = self.parse_comp(comp)
        command = comp + dest + jump
        return C_COMMAND_PREFIX + command

    def parse_comp(self, comp):
        return COMP_DICT[comp]

    def parse_dest(self, dest):
        return DEST_DICT[dest]

    def parse_jump(self, jump):
        return JUMP_DICT[jump]


def usage():
	print (""" Assembling """)


def main(argv):
    usage()
    name = argv[1]
    Code(name).assemble()


if __name__ == '__main__':
    main(sys.argv)