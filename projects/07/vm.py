# -*- coding: utf-8 -*-

import os


class Parser(object):
    
    def __init__(self, text, filename):
        self.text = text                
        self.filename = filename
        self.lines = self.format_text()
        self.length = len(self.lines)
        self.index = 0
        self.jump_count = 0
        self.result = []
        # command_dict
        self.command_dict = {
            'add': 'C_ARITHMETIC',
            'sub': 'C_ARITHMETIC',
            'neg': 'C_ARITHMETIC',
            'eq': 'C_ARITHMETIC',
            'gt': 'C_ARITHMETIC',
            'lt': 'C_ARITHMETIC',
            'and': 'C_ARITHMETIC',
            'or': 'C_ARITHMETIC',
            'not': 'C_ARITHMETIC',
            'push': 'C_PUSH',
            'pop': 'C_POP',
        }
        # arithmetic function
        self.arithmetic = {
            'add': 'M=M+D',
            'sub': 'M=M-D',
            'neg': 'M=-M',
            'and': 'M=M&D',
            'or': 'M=M|D',
            'not': 'M=!M',
            'eq': 'D=M-D',
            'gt': 'D=M-D',
            'lt': 'D=M-D',            
        }
        # condition
        self.condition = {
            'eq': 'JEQ',
            'gt': 'JGT',
            'lt': 'JLT',
        }
        # address
        self.address = {
            'local': 'LCL', # Base R1
            'argument': 'ARG', # Base R2
            'this': 'THIS', # Base R3
            'that': 'THAT', # Base R4
            'pointer': 3, # Edit R3, R4
            'temp': 5, # Edit R5-12
            # R13-15 are free
            'static': 16, # Edit R16-255
        }

    def format_text(self):
        # remove comment and blank lines
        text = self.text.splitlines()
        text = filter(lambda x: x != '', text)
        text = filter(lambda x: x.strip().startswith('//') is False, text)
        return list(text)

    def hasMoreCommand(self):
        return self.index < self.length

    def advance(self):
        if self.hasMoreCommand():
            self.write('// ' + self.lines[self.index])
            self.process()       
            self.increment_index()
            self.advance()        

    def increment_index(self):
        self.index += 1

    def increment_jump(self):
        self.jump_count += 1
    
    def process(self):
        """
        ARITHMETIC
            - Number
                - One Operand: neg、not
                - Two Operand: add/sub, and/or
            - Jump: eq/gt/lt
        Memory (PUSH/POP)
            - Static
            - Argument
            - Local
            - This/That
            - Pointer
            - Constant
            - Temp
        """
        if self.command_type == 'C_ARITHMETIC':
            self.writeArithmetic()
        elif self.command_type == 'C_PUSH':
            self.writePush()
        elif self.command_type == 'C_POP':
            self.writePop()

    def writeArithmetic(self):
        command = self.current[0]
        if command not in ['neg', 'not']:
            self.pop_stack_to_D()
        
        self.decrement_sp()
        self.set_A_to_stack()
        self.calculate()

        # Jump
        if command in ['eq', 'gt', 'lt']:
            self.write('@JUMP{}'.format(self.jump_count))
            self.write('D;{cond}'.format(cond=self.condition.get(command)))
            # default write
            self.set_A_to_stack()
            self.write('M=0')
            self.write('@ENDJUMP{}'.format(self.jump_count))
            self.write('0;JMP')
            # define jump
            self.write('(JUMP{})'.format(self.jump_count))
            self.set_A_to_stack()
            self.write('M=-1')
            # define endjump
            self.write('(ENDJUMP{})'.format(self.jump_count))            
            self.increment_jump()
        
        self.increment_sp()

    def write(self, s):
        self.result.append(s)

    def calculate(self):
        func = self.arithmetic.get(self.current[0])        
        self.write(func)

    def decrement_sp(self):
        self.write('@SP')
        self.write('M=M-1')

    def increment_sp(self):
        self.write('@SP')
        self.write('M=M+1')

    def set_A_to_stack(self):
        self.write('@SP')
        self.write('A=M')

    def pop_stack_to_D(self):
        self.write('@SP')
        self.write('M=M-1')
        self.write('A=M')
        self.write('D=M')

    def push_D_to_stack(self):
        self.write('@SP')
        self.write('A=M')
        self.write('M=D')
        self.increment_sp()

    def writePush(self):
        # push: where, what
        # load M[address] to D
        segment, num = self.args1, self.args2
        self.resolve_address(segment, num)
        
        if segment == 'constant':
            self.write('D=A')
        else:
            self.write('D=M')
        self.push_D_to_stack()

    def resolve_address(self, segment, num):
        if segment == 'constant':
            self.write('@{num}'.format(num=num))
        elif segment == 'static':
            self.write('@{filename}.{num}'.format(filename=self.filename, num=num))
        elif segment in ['local', 'argument', 'this', 'that']:
            base = self.address.get(segment)
            self.write('@{base}'.format(base=base))
            self.write('D=M')
            self.write('@{num}'.format(num=num))
            self.write('A=A+D')
        elif segment in ['pointer', 'temp']:
            base = self.address.get(segment)
            addr = base + int(num)            
            self.write('@R{addr}'.format(addr=addr))

    def writePop(self):
        # load D to M[address]
        segment, num = self.args1, self.args2
        self.resolve_address(segment, num)
        self.write('D=A')
        # store A
        self.write('@R13')
        self.write('M=D')
        self.pop_stack_to_D()
        self.write('@R13')
        self.write('A=M')
        self.write('M=D')        

    @property
    def current(self):            
        return self.lines[self.index].split(' ')

    @property
    def command_type(self):
        com_type = self.current[0]
        return self.command_dict.get(com_type)

    @property
    def args1(self):
        return self.current[1]

    @property
    def args2(self):
        return self.current[2]
        

class Writer(object):

    def __init__(self, file_path):
        self.path = file_path
        self.dir = os.path.dirname(self.path)
        self.fname = os.path.basename(self.path)
        self.name = os.path.splitext(self.fname)[0]
        self.target = os.path.join(self.dir, self.name + '.asm')
        self.text = self.read()
    
    def setFileName(self):
        pass

    def read(self):
        with open(self.path) as f:            
            return f.read()

    def translate(self, result):
        result = '\n'.join(result)
        with open(self.target, 'w+') as f:
            f.write(result)


def main(file_path):
    writer = Writer(file_path)
    parser = Parser(writer.text, writer.name)
    parser.advance()    
    writer.translate(parser.result)


if __name__ == '__main__':
    import sys
    
    file_path = sys.argv[1]
    main(file_path)
