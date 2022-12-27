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

eq: var "=" [keyword] arg

keyword: "AND" -> and
       | "OR" -> or
       | "XOR" -> xor
       | "NOT" -> not
       | "NAND" -> nand
       | "MUX" -> mux
       | "REG" -> reg
       | "CONCAT" -> concat
       | "SELECT" -> select
       | "SNIP" -> snip
       | "SLICE" -> slice
       | "ROM" -> rom
       | "RAM" -> ram
       | "COPY" -> copy

arg: (var | number)+

var: CNAME
typedvar: CNAME [":" number]
number: /0x[a-fA-F0-9]+/
      | /0b[01]+/
      | /[1-9][0-9]*/
      | "0"

%import common.CNAME
%import common.WS
%import common.WS_INLINE
%import common.HEXDIGIT
%ignore WS
"""


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

    def typedvar(self, args):
        l = 1 if args[1] is None else args[1]
        if args[0] not in self.buses:
            self.buses[args[0]] = ast.Var(l, args[0])
            print(f"New variable declared | {args[0]}: {l}")
        elif self.buses[args[0]].length == -1:
            self.buses[args[0]].length = l
            print(f"       Length set for | {args[0]}: {l}")
        return self.buses[args[0]]

    def var(self, args):
        if args[0] not in self.buses:
            self.buses[args[0]] = ast.Var(-1, args[0])
            print(f"New variable declared | {args[0]}: -1")
        return self.buses[args[0]]

    def eq(self, args):
        k = ("copy" if args[1] is None else args[1].data).upper()
        t = ast.Exprs[k]
        signature = ast.get_signature(t)
        sArgs = []
        dArgs = []
        for i in range(signature[1]):  # Static args
            sArgs.append(args[2].children[i])
        for i in range(signature[0]):
            a = args[2].children[i + signature[1]]
            if not isinstance(a, ast.Var):
                a = ast.Cst(-1, a)
            dArgs.append(a)
        print(f"Generating AST node for {args[0].label}")
        return ast.Eq(args[0], ast.Expression(t, dArgs, sArgs))

    def input(self, args):
        return args[0]

    def output(self, args):
        return args[0]

    def vars(self, args):
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


def parse(s):
    l = Lark(GRAMMAR, start="netlist")
    parsed_tree = l.parse(s)
    return RawTreeToAST().transform(parsed_tree)
