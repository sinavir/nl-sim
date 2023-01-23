from enum import Enum

from .AST import Exprs


class CTypes(Enum):
    UINT8 = "uint8_t"
    UINT16 = "uint16_t"
    UINT32 = "uint32_t"
    UINT64 = "uint64_t"


def cTypeFromBusSize(size):
    if size <= 8:
        return CTypes.UINT8
    if size <= 16:
        return CTypes.UINT16
    if size <= 32:
        return CTypes.UINT32
    if size <= 64:
        return CTypes.UINT64
    raise ValueError


def size_from_bus_size(size):
    for i in [8, 16, 32, 64]:
        if size <= i:
            return i
    raise ValueError


"""
Dictionnaire indiquant les nappes aboutissant dans des registres
"""
REG_TYPES = {
    Exprs.REG: set((0,)),
    Exprs.RAM: set((1, 2, 3)),
}


def getOrderedNetList(netlist):
    """
    Fonction qui fait le tri topologique à partir d'un objet `NetList`.
    Renvoie une liste d'objet `Eq`
    """
    var_to_eq = {}
    graph = {}  # Dictionnaire du graph de dépendance des composants
    sorted_list = []  # composants triés
    explored = set()
    regs = set()  # Nappes aboutissant à un registre, on doit les calculer aussi
    for e in netlist.equations:
        var_to_eq[e.var] = e
        graph[e.var] = e.expr.getDeps()
        if e.expr.type in REG_TYPES:
            for i in REG_TYPES[e.expr.type]:
                regs.add(e.expr.args[i])

    def explore(v):
        if v in path:
            raise ValueError(
                f"Cyclic netlist. Path is made of {[i.label for i in path]}"
            )
        explored.add(v)
        if v in netlist.inputs:
            return
        path.add(v)
        if v not in graph:
            raise ValueError(
                f"{v.label} have no value. Please add {v.label} to inputs or provide a '{v.label} = ...' statement'"
            )
        for new in graph[v]:
            if new not in explored:
                explore(new)
        path.remove(v)
        if var_to_eq[v] not in sorted_list:
            sorted_list.append(var_to_eq[v])
            print(f"{len(sorted_list)}/{len(graph)}")

    for v in netlist.outputs:
        path = set()  # Ensembles des points du chemin en court d'exploration
        explore(v)
    for v in regs:
        path = set()
        explore(v)
    return sorted_list
