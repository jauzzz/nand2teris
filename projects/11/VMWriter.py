class VMWriter:
    def __init__(self, output_file):
        vm_file = output_file.replace('.jack', '.vm1')
        self.output = open(vm_file, 'w')

    # CONST, ARG, LOCAL, STATIC, THIS, THAT, POINTER, TEMP
    def writePush(self, segment, index):
        if segment == 'CONST':
            segment = 'constant'
        elif segment == 'ARG':
            segment = 'argument'

        self.output.write('push {} {}\n'.format(segment.lower(), index))

    def writePop(self, segment, index):
        if segment == 'CONST':
            segment = 'constant'
        elif segment == 'ARG':
            segment = 'argument'

        self.output.write('pop {} {}\n'.format(segment.lower(), index))

    # command (ADD, SUB, NEG, EQ, GT, LT, AND, OR, NOT)
    def writeArithmetic(self, command):
        self.output.write(command.lower() + '\n')

    def writeLabel(self, label):
        self.output.write('label {}\n'.format(label))

    def writeGoto(self, label):
        self.output.write('goto {}\n'.format(label))

    def writeIf(self, label):
        self.output.write('if-goto {}\n'.format(label))

    def writeCall(self, name, nArgs):
        self.output.write('call {} {}\n'.format(name, nArgs))

    def writeFunction(self, name, nLocals):
        self.output.write('function {} {}\n'.format(name, nLocals))

    def writeReturn(self):
        self.output.write('return\n')

    def close(self):
        self.output.close()

    def write(self, stuff):
        self.output.write(stuff)
