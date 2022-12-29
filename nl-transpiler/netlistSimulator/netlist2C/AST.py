"""
This module provides objects to represent a NetList and methods to check bus
length coherence (and also size inference

Objects are thought as non-mutable but this is not enforced
"""

from enum import Enum


class WrongBusLength(Exception):
    pass


class WrongArgsNumber(Exception):
    pass


class WrongStaticArgsNumber(Exception):
    pass


class BusTooLong(Exception):
    """
    Les bus sont limités à 64 fils car ça ma semblé suffisant
    """

    pass


class BusTooShort(Exception):
    pass


class CantTypeExpression(Exception):
    pass


class Expression:
    """
    Représente une instruction de la netlist
    """

    def __init__(self, instruction, args, sargs):
        self.args = args
        self.static_args = sargs  # Args that must be explicitely static
        self.type = instruction
        self.out_length = None
        self.checkAndType()

    def checkAndType(self):
        s = get_signature(self.type)
        self._checkArgsNumber(s[0])
        self._checkStaticArgsNumber(s[1])
        match self.type:
            case Exprs.NOT | Exprs.REG | Exprs.COPY:
                self.out_length = self.args[0].length
            case Exprs.AND | Exprs.OR | Exprs.XOR | Exprs.NAND | Exprs.NXOR:
                if not equalLengthTyping(self.args[0], self.args[1]):
                    raise WrongBusLength(
                        f"{self.type} keyword takes two buses of same size as input (provided: {self.args[0].label}[{self.args[0].length}] and {self.args[1].label}[{self.args[1].length}])"
                    )
                self.out_length = self.args[0].length
            case Exprs.MUX:
                if not equalLengthTyping(self.args[1], self.args[2]):
                    raise WrongBusLength(
                        f"{self.type} keyword takes two buses of same size as last two arguments (provided: {self.args[1].label}[{self.args[1].length}] and {self.args[2].label}[{self.args[2].length}]"
                    )
                self.out_length = self.args[1].length
            case Exprs.CONCAT:
                match numberOfTypedArgs(*self.args):
                    case 0:
                        raise CantTypeExpression(
                            "CONCAT instruction must have at least one argument with fixed length"
                        )
                    case 1:
                        self.out_length = -1
                    case 2:
                        self.out_length = self.args[0].length + self.args[1].length
                    case _:
                        raise Exception("Not reachable")
            case Exprs.ROM:
                if self.args[0].length != self.static_args[0]:
                    raise WrongBusLength(
                        f"ROM read address doesn't have the right size (expected {self.static_args[0]})"
                    )
                self.out_length = self.static_args[1]
            case Exprs.RAM:
                if self.args[0].length != self.static_args[0]:
                    raise WrongBusLength(
                        f"RAM read address doesn't have the right size (expected {self.static_args[0]}, provided {self.args[1].length}-bits-long bus)"
                    )
                if self.args[2].length != self.static_args[0]:
                    raise WrongBusLength(
                        f"RAM write address doesn't have the right size(expected {self.static_args[0]})"
                    )
                if self.args[3].length != self.static_args[1]:
                    raise WrongBusLength(
                        f"RAM write data doesn't have the right size (expected {self.static_args[1]})"
                    )
                self.out_length = self.static_args[1]
            case Exprs.SNIP:
                if self.static_args[0] > self.static_args[1]:
                    raise ValueError("SNIP bounds are not in the right order")
                if self.static_args[1] > self.args[0].length:
                    raise BusTooShort(
                        f"SNIP upper bound is too big (must be at most {self.args[0].length}, found {self.static_args[1]}"
                    )
                self.out_length = self.static_args[1] - self.static_args[0]
            case Exprs.SLICE:
                if self.static_args[0] > self.static_args[1]:
                    raise ValueError("SLICE bounds are not in the right order")
                if self.static_args[1] >= self.args[0].length:
                    raise BusTooShort(
                        f"SLICE upper bound is too big (must be at most {self.args[0].length}, found {self.static_args[1]}"
                    )
                self.out_length = self.static_args[1] - self.static_args[0] + 1
            case Exprs.SELECT:
                if self.static_args[0] >= self.args[0].length:
                    raise BusTooShort(
                        f"Trying to SELECT a out of range bit (must be at most {self.args[0].length}, found {self.static_args[1]}"
                    )
                self.out_length = 1
            case _:
                raise NotImplementedError(f"Check for {self.type} not implemented")

    def getDeps(self):
        match self.type:
            case Exprs.REG:
                return set()
            case Exprs.RAM:
                return set((self.args[0],))
            case _:
                return set(i for i in self.args if isinstance(i, Var))

    def _checkArgsNumber(self, n):
        if len(self.args) != n:
            raise WrongArgsNumber(
                f"{self.type} keyword is expecting {n} bus argument whereas {len(self.args)} where provided"
            )

    def _checkStaticArgsNumber(self, n):
        if len(self.static_args) != n:
            raise WrongStaticArgsNumber(
                f"{self.type} keyword is expecting {n} static arguments whereas {len(self.args)} where provided"
            )


class Arg:
    """
    Représente l'argument d'une instruction
    """

    def __init__(self, length):
        if length > 64:
            raise BusTooLong("Bus size must be <= 64")
        self.length = length


class Cst(Arg):
    """
    Représente une nappe de fil de valeur fixée
    """

    def __init__(self, length, value):
        self.value = value
        self.label = hex(value)
        super().__init__(length)


class Var(Arg):
    """
    Représente une nappe de fils
    """

    def __init__(self, length, label):
        self.label = label
        super().__init__(length)


class Eq:
    """
    Représente une instruction de la netlist
    """

    def __init__(self, var, expr):
        self.var = var
        self.expr = expr
        self.check()

    def check(self):
        """
        Essaie d'inférer le type des arguments d'une instruction et vérifie que l'instruction est bien typée
        """
        if (
            self.expr.out_length == -1
        ):  # Si l'expression n'est pas complètement typée, on essaie d'inférer son type
            match self.expr.type:
                case Exprs.CONCAT:
                    lengthSumTyping(*self.expr.args, self.var.length)
                case Exprs.AND | Exprs.OR | Exprs.XOR | Exprs.NAND | Exprs.NXOR:
                    equalLengthTyping(*self.expr.args)
                case Exprs.NOT | Exprs.REG | Exprs.COPY:
                    self.expr.args[0].length = self.var.length
                    self.expr.out_length = self.var.length

        if self.var.length != self.expr.out_length:
            raise WrongBusLength(
                f"Left-sided var `{self.var.label}` is a {self.var.length}-bit long bus whereas a {self.expr.out_length}-bit long expression were provided"
            )


class NetList:
    """
    Représente une netlist
    """

    def __init__(self, inputs, outputs, var, eqs):
        self.inputs = set(inputs)
        self.outputs = set(outputs)
        self.vars = set(var)
        self.equations = set(eqs)


class Exprs(Enum):
    """
    Enum représentant les différents composants
    """

    NOT = 0
    AND = 1
    OR = 2
    XOR = 3
    NAND = 4
    NXOR = 5
    MUX = 6
    REG = 7
    RAM = 8
    ROM = 9
    SNIP = 10
    CONCAT = 11
    SLICE = 12
    SELECT = 13
    COPY = 14


"""
Dictionnaire qui liste les arguments attendus par chaque expression
sous la forme `(x, y)` où
 - `x`: nombre d'arguments qui peuvent être des registres
 - `y`: nombre d'arguments qui doivent être des valeurs statiques
"""
SIGNATURES = {
    Exprs.AND: (2, 0),
    Exprs.OR: (2, 0),
    Exprs.XOR: (2, 0),
    Exprs.NXOR: (2, 0),
    Exprs.NAND: (2, 0),
    Exprs.REG: (1, 0),
    Exprs.NOT: (1, 0),
    Exprs.MUX: (3, 0),
    Exprs.SNIP: (1, 2),
    Exprs.SLICE: (1, 2),
    Exprs.CONCAT: (2, 0),
    Exprs.RAM: (4, 2),
    Exprs.ROM: (1, 2),
    Exprs.SELECT: (1, 1),
    Exprs.COPY: (1, 0),
}


def get_signature(exprs):
    """
    Return the tuple (number of argument, number of static arguments) required
    by each instruction
    """
    if exprs in SIGNATURES:
        Exception(f"{exprs}")
    return SIGNATURES[exprs]


# ****************
# * Typing utils *
# ****************


def binTyping(a, b, a_from_b, b_from_a):
    """
    Essaie de d'inférer les types de a (resp. b) en fonction de b (resp. a). Renvoie `True` si il réussi, `False` si il échoue
    """
    if a.length == -1:
        if b == -1:
            return False
        a.length = a_from_b(b.length)
    elif b.length == -1:
        b.length = b_from_a(a.length)
    return True


def equalLengthTyping(a, b):
    """
    Essaie de typer a et b pour qu'ils aient la même longueur
    """
    ident = lambda x: x
    return binTyping(a, b, ident, ident)


def lengthSumTyping(a, b, tot):
    diff = lambda x: max(tot - x, 0)
    return binTyping(a, b, diff, diff)


def numberOfTypedArgs(*a):
    n = 0
    for i in a:
        if i.length != -1:
            n += 1
    return n
