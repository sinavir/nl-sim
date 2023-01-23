from lark import Lark, Transformer

from . import AST as ast

GRAMMAR = """
netlist: input output vars code
input: "INPUT" varlist
output: "OUTPUT" varlist
vars: "VAR" typedvarlist
code: "IN" eqlist

varlist: var? ( "," var)* ","?
typedvarlist: typedvar ( "," typedvar)* ","?

eqlist: eq+

eq: var "=" op

op: andand | oror | xor | notnot | nand | mux | reg | concat | select | snip | slice | rom | ram | copy

andand: "AND" arg arg
oror: "OR" arg arg
xor: "XOR" arg arg
notnot: "NOT" arg
nand: "NAND" arg arg
mux: "MUX" arg arg arg
reg: "REG" arg
concat: "CONCAT" arg arg
select: "SELECT" sarg arg
snip: "SNIP" sarg sarg arg
slice: "SLICE" sarg sarg arg
rom: "ROM" sarg sarg arg
ram: "RAM" sarg sarg arg arg arg arg
copy: "COPY"? arg

arg: (var | constant)
sarg: number

var: CNAME
typedvar: CNAME [":" number]

number: /0x[a-fA-F0-9]+/
      | /0b[01]+/
      | /[1-9][0-9]*/
      | "0"

constant: /[01]+/

%import common.CNAME
%import common.WS
%import common.WS_INLINE
%import common.HEXDIGIT
%ignore WS
"""

#


class RawTreeToAST(Transformer):
    """
    Objet Transformer qui transforme l'arbre produit par Lark en un AST
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.buses = (
            {}
        )  # Utilisé pour stocker les bus déjà inspectés (table de symboles)

    CNAME = str

    def number(self, args):
        if len(args) == 0:  # If no children then "0" have been matched
            return 0
        return int(args[0], 0)  # On laisse python parser la valeur

    def constant(self, args):
        return int("0b" + args[0][::-1], 0)  # On laisse python parser la valeur

    def typedvar(self, args):
        l = 1 if args[1] is None else args[1]
        if args[0] not in self.buses:
            self.buses[args[0]] = ast.Var(l, args[0])
        elif self.buses[args[0]].length == -1:
            self.buses[args[0]].length = l
        return self.buses[args[0]]

    def var(self, args):
        if args[0] not in self.buses:
            self.buses[args[0]] = ast.Var(-1, args[0])
        return self.buses[args[0]]

    def eq(self, args):
        return ast.Eq(args[0], args[1])

    def op(self, args):
        return args[0]

    def andand(self, args):
        return self._parse_sdargs("AND", args)

    def oror(self, args):
        return self._parse_sdargs("OR", args)

    def xor(self, args):
        return self._parse_sdargs("XOR", args)

    def notnot(self, args):
        return self._parse_sdargs("NOT", args)

    def nand(self, args):
        return self._parse_sdargs("NAND", args)

    def mux(self, args):
        return self._parse_sdargs("MUX", args)

    def reg(self, args):
        return self._parse_sdargs("REG", args)

    def concat(self, args):
        return self._parse_sdargs("CONCAT", args)

    def select(self, args):
        return self._parse_sdargs("SELECT", args)

    def snip(self, args):
        return self._parse_sdargs("SNIP", args)

    def slice(self, args):
        return self._parse_sdargs("SLICE", args)

    def rom(self, args):
        return self._parse_sdargs("ROM", args)

    def ram(self, args):
        return self._parse_sdargs("RAM", args)

    def copy(self, args):
        return self._parse_sdargs("COPY", args)

    def input(self, args):
        return args[0]

    def output(self, args):
        return args[0]

    def vars(self, args):
        return args[0]

    def arg(self, args):
        return args[0]

    def sarg(self, args):
        return args[0]

    def varlist(self, args):
        return set(args)

    def typedvarlist(self, args):
        return set(args)

    def eqlist(self, args):
        return set(args)

    def code(self, args):
        return args[0]

    def netlist(self, args):
        return ast.NetList(*args)

    def _parse_sdargs(self, k, args):
        t = ast.Exprs[k]
        signature = ast.get_signature(t)
        sArgs = []
        dArgs = []
        for i in range(signature[1]):  # Static args
            sArgs.append(args[i])
        for i in range(signature[0]):
            a = args[i + signature[1]]
            if not isinstance(a, ast.Var):
                a = ast.Cst(-1, a)
            dArgs.append(a)
        return ast.Expression(t, dArgs, sArgs)


def parse(s):
    l = Lark(GRAMMAR, start="netlist")
    parsed_tree = l.parse(s)
    print(parsed_tree.pretty())
    return RawTreeToAST().transform(parsed_tree)
