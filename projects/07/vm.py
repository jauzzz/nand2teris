class Parser(object):

    def __init__(self, filename):
        self.lines = self.read(filename)
        self.index = 0
        self.length = len(self.lines)

    def hasMoreCommands(self):
        return self.index < self.length

    def advance(self):
        self.command = self.current.split(' ')
        self.index += 1

    @property
    def commandType(self):
        return self.command[0]

    @property
    def arg1(self):
        if len(self.command) > 1:
            return self.command[1]
        raise Exception('No arg1')
    
    @property
    def arg2(self):
        if len(self.command) > 2:
            return self.command[2]
        raise Exception('No arg2')

    # util function
    def read(self, filename):
        with open(filename, 'r') as f:
            text = f.read()
            lines = text.splitlines()
            lines = self.format_line(lines)
            return lines

    def format_line(self, lines):
        # ignore blank line and comment
        result = []
        for l in lines:
            line = l.strip()
            if line and line.startswith("//") is False:
                result.append(line)
        return result

    @property
    def current(self):
        return self.lines[self.index]


class CodeWriter(object):

    def __init__(self, filename):
        self.asm = []
        self.target = self.target_file(filename)
        # command Dict
        self.commandDict = {
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
          'label': 'C_LABEL',
           'goto': 'C_GOTO',
        'if-goto': 'C_IF',
       'function': 'C_FUNCTION',
         'return': 'C_RETURN',
           'call': 'C_CALL'
        }
        # jump Dict
        self.jump_count = 0
        self.jumpDict = {
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

    def setFileName(self, filename):
        self.filename = filename.replace('.vm', '').split('/')[-1]

    def writeArithmetic(self, command):
        if command in ["add", "sub", "and", "or", "eq", "gt", "lt"]:
            self.pop_stack_to_D()
        
        self.decrement_SP()
        self.set_stack_to_A()
        
        if command == 'add':
            self.write('M=M+D')
        elif command == 'sub':
            self.write('M=M-D')
        elif command == 'and':
            self.write('M=M&D')
        elif command == 'or':
            self.write('M=M|D')
        elif command == 'neg':
            self.write('M=-M')
        elif command == 'not':
            self.write('M=!M')
        elif command in ["eq", "gt", "lt"]:
            self.write('D=M-D')
            # write jump
            self.write('@JUMP{}'.format(self.jump_count))
            self.write('D;{}'.format(self.jumpDict.get(command)))
            # default write
            self.set_stack_to_A()
            self.write('M=0')
            self.write('@ENDJUMP{}'.format(self.jump_count))
            self.write('0;JMP')
            # define jump
            self.write('(JUMP{})'.format(self.jump_count))
            self.set_stack_to_A()
            self.write('M=-1')
            # define endjump
            self.write('(ENDJUMP{}'.format(self.jump_count))
            self.increment_SP()
        else:
            raise Exception("Unknown Arithmetic: {}".format(command))

    def writePushPop(self, command, segment, index):                        
        self.resolve_address(segment, index)

        if command == 'C_PUSH':
            self.writePush(segment)
        elif command == 'C_POP':
            self.writePop() 

    def close(self):
        codes = "\n".join(self.asm)        
        self.target.write(codes)
        self.target.write("\n")
        self.target.close()

    # util function
    def resolve_address(self, segment, index):
        base = self.address.get(segment)
        if segment == "constant":
            self.write('@{}'.format(index))
        if segment in ["argument", "local", "this", "that"]:
            self.write('@{}'.format(base))
            self.write('D=A')
            self.write('@{}'.format(index))
            self.write('D=D+A')
            self.write('A=D')                
        elif segment == "static":
            self.write('@{filename}.{index}'.format(filename=self.filename, index=index))
        elif segment in ["temp", "pointer"]:
            addr = base + int(index)
            self.write("@R{}".format(addr))
    
    def writePush(self, segment):
        # memory to stack               
        if segment == 'constant':
            self.write('D=A')
        else:
            self.write('D=M')
        self.push_D_to_stack()

    def writePop(self):
        # stack to memory
        self.write('D=A')
        self.write('@R13')
        self.write('M=D')
        self.pop_stack_to_D()
        self.write('@13')
        self.write('A=M')
        self.write('M=D')        

    def decrement_SP(self):
        self.write('@SP')
        self.write('M=M-1')

    def increment_SP(self):
        self.write('@SP')
        self.write('M=M+1')

    def set_stack_to_A(self):
        self.write('@SP')
        self.write('A=M')

    def push_D_to_stack(self):
        self.set_stack_to_A()
        self.write('M=D')
        self.increment_SP()

    def pop_stack_to_D(self):
        self.write('@SP')
        self.write('M=M-1')
        self.write('A=M')
        self.write('D=M')

    def get_command_type(self, command):
        return self.commandDict.get(command)

    def target_file(self, filename):
        name = filename.replace('.vm', '.asm')
        f = open(name, 'w+')
        return f

    def write(self, s):
        self.asm.append(s)


class Compile(object):

    def __init__(self, file_path):        
        self.cw = CodeWriter(file_path)
        self.cw.setFileName(file_path)
        self.translate()           

    def translate(self):
        parser = Parser(file_path)
        while parser.hasMoreCommands():
            parser.advance()
            commandType = self.cw.get_command_type(parser.commandType)
            if commandType == 'C_ARITHMETIC':
                self.cw.writeArithmetic(parser.commandType)
            elif commandType == 'C_PUSH':
                self.cw.writePushPop('C_PUSH', parser.arg1, parser.arg2)
            elif commandType == 'C_POP':
                self.cw.writePushPop('C_POP', parser.arg1, parser.arg2)

        self.cw.close()


if __name__ == '__main__':
    import sys
    
    file_path = sys.argv[1]
    Compile(file_path)
