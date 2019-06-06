"""
ClassScope: 
    - ClassVarDec: ('static' | 'field') type varName

SubroutineScope:
    - SubroutineVarDec: 'var' type varName
    - Argument

"""


class SymbolTable:
    " Manage the variable’s life cycle and scope "

    def __init__(self):
        self.class_scope = {}
        self.subroutine_scope = {}
        self.counts = {
            'STATIC': 0,
            'FIELD': 0,
            'ARG': 0,
            'VAR': 0,
        }

    def startSubroutine(self):
        self.subroutine_scope = {}
        self.counts['ARG'] = self.counts["VAR"] = 0

    def define(self, name, type, kind):
        kind = kind.upper()
        index = self.varCount(kind)

        if kind in ['STATIC', 'FIELD']:
            self.class_scope[name] = (type, kind, index)
        elif kind in ['VAR', 'ARG']:
            self.subroutine_scope[name] = (type, kind, index)
        else:
            raise Exception("Unknown symbol kind {} {} {}".format(name, type, kind))

        self.counts[kind] += 1

    def varCount(self, kind):
        return self.counts[kind]

    def kindOf(self, name):
        return self.lookup(name)[1]

    def typeOf(self, name):
        return self.lookup(name)[0]

    def indexOf(self, name):
        return self.lookup(name)[2]

    # Non API
    def lookup(self, name):
        if name in self.subroutine_scope.keys():
            return self.subroutine_scope[name]
        elif name in self.class_scope.keys():
            return self.class_scope[name]
        else:
            return (None, None, None)
