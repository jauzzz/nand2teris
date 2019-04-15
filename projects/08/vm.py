import os


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
           'call': 'C_CALL',
        }
        # jump Dict
        self.call_count = 0
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

        # write_init
        self.write_init()

    def setFileName(self, filename):
        self.filename = filename.replace('.vm', '').split('/')[-1]

    def write_init(self):
        self.write('@256')
        self.write('D=A')
        self.write('@SP')
        self.write('M=D')
        # call init
        self.writeCall('Sys.init', 0)

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
        else:
            raise Exception("Unknown Arithmetic: {}".format(command))
        
        self.increment_SP()

    def writePushPop(self, command, segment, index):
        self.resolve_address(segment, index)

        if command == 'C_PUSH':
            self.writePush(segment)
        elif command == 'C_POP':
            self.writePop() 

    def writeLabel(self, label):
        self.write('({}${})'.format(self.filename, label))

    def writeGoto(self, label):
        self.write('@{}${}'.format(self.filename, label))
        self.write('0;JMP')

    def writeIf(self, label):
        self.pop_stack_to_D()
        self.write('@{}.{}'.format(self.filename, label))
        self.write('D;JNE')

    def writeFunction(self, function, numLocals):
        self.write('({})'.format(function))

        # TODO: why push local 0
        numLocals = int(numLocals)
        while numLocals > 0:
            self.write('D=0')
            self.push_D_to_stack()
            numLocals -= 1

    def writeCall(self, function, numArgs):
        RET = 'RET.{}.{}'.format(function, self.call_count)
        self.call_count += 1

        self.write('@{}'.format(RET))
        self.write('D=A')
        self.push_D_to_stack()

        for seg in ["LCL", "ARG", "THIS", "THAT"]:
            self.write('@{}'.format(seg))
            self.write('D=M')
            self.push_D_to_stack()

        # reposition LCL
        self.write('@SP')
        self.write('D=M')
        self.write('@LCL')
        self.write('M=D')

        # repostion ARG
        self.write('@{}'.format(int(numArgs) + 5))
        self.write('D=D-A')
        self.write('@ARG')
        self.write('M=D')

        # goto function
        self.write('@{}'.format(function))
        self.write('0;JMP')

        # return address
        self.write('({})'.format(RET))        

    def writeReturn(self):
        FRAME = 'R13'
        RET = 'R14'

        # FRAME = LCL
        self.write('@LCL')
        self.write('D=M')
        self.write('@{}'.format(FRAME))
        self.write('M=D')

        # RETURN = *(FRAME-5)
        self.write('@{}'.format(FRAME))
        self.write('D=M')
        self.write('@5')
        self.write('D=D-A')
        self.write('A=D')
        self.write('D=M')
        self.write('@{}'.format(RET))
        self.write('M=D')

        # pop()
        self.pop_stack_to_D()
        self.write('@ARG')
        self.write('A=M')
        self.write('M=D')

        # SP = ARG + 1
        self.write('@ARG')
        self.write('D=M')
        self.write('@SP')
        self.write('M=D+1')

        # restore function scope
        offset = 1
        for seg in ['THAT', 'THIS', 'ARG', 'LCL']:
            self.write('@{}'.format(FRAME))
            self.write('D=M')
            self.write('@{}'.format(offset))
            self.write('D=D-A')
            self.write('A=D')
            self.write('D=M')
            self.write('@{}'.format(seg))
            self.write('M=D')
            offset += 1

        # return
        self.write('@{}'.format(RET))
        self.write('A=M')
        self.write('0;JMP')

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
            self.write('D=M')
            self.write('@{}'.format(index))
            self.write('A=D+A')                         
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
        self.write('@R13')
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
        self.files = file_path

        if len(file_path) > 1:
            ele = file_path[-1]
            fname = ele.split('/')[-2] + '.asm'
            dirname = os.path.dirname(ele)
            name = os.path.join(dirname, fname)
            self.cw = CodeWriter(name)
        else:
            self.cw = CodeWriter(file_path[0])

        for f in self.files:
            self._compile(f)
        self.cw.close()

    def _compile(self, file_path):        
        self.cw.setFileName(file_path)
        self.translate(file_path)

    def translate(self, file_path):
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
            elif commandType == 'C_LABEL':
                self.cw.writeLabel(parser.arg1)
            elif commandType == 'C_GOTO':
                self.cw.writeGoto(parser.arg1)
            elif commandType == 'C_IF':
                self.cw.writeIf(parser.arg1)
            elif commandType == 'C_FUNCTION':
                self.cw.writeFunction(parser.arg1, parser.arg2)
            elif commandType == 'C_CALL':
                self.cw.writeCall(parser.arg1, parser.arg2)
            elif commandType == 'C_RETURN':
                self.cw.writeReturn()
            

if __name__ == '__main__':
    import sys
    
    file_path = sys.argv[1:]
    Compile(file_path)
