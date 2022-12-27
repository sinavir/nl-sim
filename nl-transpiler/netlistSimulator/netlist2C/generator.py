"""
Module qui transpile la netlist en C
"""
from . import AST as ast
from . import parser, utils


def _getExpr(eq):
    """
    Renvoie un quadruplet de string représentant la valeur à assigner et des
    instructions supplémentaire à ajouter en préambule et postambule de la
    fonction C. Le dernière valeur contient les instructions ROMs
    """

    def full_exp_from_righthand_side(var, exp):
        return f"\t{utils.cTypeFromBusSize(var.length).value} {var.label} = {exp};\n"

    expr = eq.expr
    match expr.type:
        case ast.Exprs.NOT:
            return (
                full_exp_from_righthand_side(eq.var, f"~{expr.args[0].label}"),
                "",
                "",
                None,
            )
        case ast.Exprs.AND:
            return (
                full_exp_from_righthand_side(
                    eq.var, f"{expr.args[0].label} & {expr.args[1].label}"
                ),
                "",
                "",
                None,
            )
        case ast.Exprs.OR:
            return (
                full_exp_from_righthand_side(
                    eq.var, f"{expr.args[0].label} | {expr.args[1].label}"
                ),
                "",
                "",
                None,
            )
        case ast.Exprs.XOR:
            return (
                full_exp_from_righthand_side(
                    eq.var, f"{expr.args[0].label} ^ {expr.args[1].label}"
                ),
                "",
                "",
                None,
            )
        case ast.Exprs.NAND:
            return (
                full_exp_from_righthand_side(
                    eq.var, f"~({expr.args[0].label} & {expr.args[1].label})"
                ),
                "",
                "",
                None,
            )
        case ast.Exprs.NXOR:
            return (
                full_exp_from_righthand_side(
                    eq.var, f"~({expr.args[0].label} ^ {expr.args[1].label})"
                ),
                "",
                "",
                None,
            )
        case ast.Exprs.MUX:
            mask = f"(({utils.cTypeFromBusSize(expr.args[0].length).value}) 1 << {expr.args[0].length}) - 1"
            return (
                full_exp_from_righthand_side(
                    eq.var,
                    f"{expr.args[0].label} & {mask} == 0 ? {expr.args[1].label} : {expr.args[2].label}",
                ),
                "",
                "",
                None,
            )
        case ast.Exprs.CONCAT:
            out_type = utils.cTypeFromBusSize(
                expr.args[0].length + expr.args[1].length
            ).value
            return (
                full_exp_from_righthand_side(
                    eq.var,
                    f"(({out_type}) {expr.args[0].label} << {expr.args[1].length}) + ({out_type}) {expr.args[1].label}",
                ),
                "",
                "",
                None,
            )
        case ast.Exprs.SNIP:
            mask = f"(((({utils.cTypeFromBusSize(expr.args[0].length).value}) 1 << {expr.static_args[1]-expr.static_args[0]}) - 1) << {expr.static_args[0]})"
            return (
                full_exp_from_righthand_side(
                    eq.var,
                    f"({utils.cTypeFromBusSize(expr.static_args[1]-expr.static_args[0]).value}) (({expr.args[0].label} & {mask}) >> {expr.static_args[0]})",
                ),
                "",
                "",
                None,
            )
        case ast.Exprs.SLICE:
            mask = f"(((({utils.cTypeFromBusSize(expr.args[0].length).value}) 1 << {expr.static_args[1]-expr.static_args[0]+1}) - 1) << {expr.static_args[0]})"
            return (
                full_exp_from_righthand_side(
                    eq.var,
                    f"({utils.cTypeFromBusSize(expr.static_args[1]-expr.static_args[0]+1).value}) (({expr.args[0].label} & {mask}) >> {expr.static_args[0]})",
                ),
                "",
                "",
                None,
            )
        case ast.Exprs.SELECT:
            mask = f"(({utils.cTypeFromBusSize(expr.args[0].length).value}) 1 << {expr.static_args[0]})"
            return (
                full_exp_from_righthand_side(
                    eq.var,
                    f"({utils.cTypeFromBusSize(1).value}) (({expr.args[0].label} & {mask}) >> {expr.static_args[0]})",
                ),
                "",
                "",
                None,
            )
        case ast.Exprs.REG:
            return (
                full_exp_from_righthand_side(eq.var, f"REG_{expr.args[0].label}"),
                f"\tstatic {utils.cTypeFromBusSize(expr.args[0].length).value} REG_{expr.args[0].label} = 0;\n",
                f"\tREG_{expr.args[0].label} = {expr.args[0].label};\n",
                None,
            )
        case ast.Exprs.COPY:
            print(f"{expr.args[0].label}")
            return (
                full_exp_from_righthand_side(eq.var, f"{expr.args[0].label}"),
                "",
                "",
                None,
            )
        case ast.Exprs.RAM:
            mask = f"(({utils.cTypeFromBusSize(expr.args[1].length).value}) 1 << {expr.args[1].length}) - 1"
            read_mask = f"(({utils.cTypeFromBusSize(expr.args[0].length).value}) 1 << {expr.args[0].length}) - 1"
            write_mask = f"(({utils.cTypeFromBusSize(expr.args[2].length).value}) 1 << {expr.args[2].length}) - 1"
            label = expr.args[3].label
            read_address = f"{expr.args[0].label} & {read_mask}"
            write_address = f"{expr.args[2].label} & {write_mask}"
            ram_size = f"1 << {expr.static_args[0]}"
            return (
                full_exp_from_righthand_side(eq.var, f"RAM_{label}[{read_address}]"),
                f"\tstatic {utils.cTypeFromBusSize(expr.static_args[1]).value} RAM_{label}[{ram_size}];\n",
                f"\tif({expr.args[1].label} & {mask} != 0) RAM_{label}[{write_address}] = {expr.args[3].label};\n",
                None,
            )
        case ast.Exprs.ROM:
            label = eq.var.label
            read_mask = f"(({utils.cTypeFromBusSize(expr.args[0].length).value}) 1 << {expr.args[0].length}) - 1"
            read_address = f"{expr.args[0].label} & {read_mask}"
            return (
                full_exp_from_righthand_side(
                    eq.var, f"(roms->{label})[{read_address}]"
                ),
                "",
                "",
                eq,
            )
        case _:
            raise NotImplementedError()
    return "", "", ""  # pour faire marcher pylint


def _get_struct(varset, label):
    prefix = "typedef struct {{\n"
    content = ""
    for i in varset:
        content += f"\t{utils.cTypeFromBusSize(i.length).value} {i.label};\n"
    suffix = f"}}}} {label};\n"
    return prefix + content + suffix


def _get_rom_struct(roms):
    prefix = "typedef struct {{\n"
    content = ""
    for i in roms:
        content += f"\t{utils.cTypeFromBusSize(i.var.length).value}* {i.var.label};\n"
    suffix = f"}}}} Rom_{{short_name}};\n"
    return prefix + content + suffix


def _get_print_output(varset):
    prefix = "void print_{short_name}_output(Output_{short_name} *output) {{\n"
    content = ""
    for i in varset:
        content += f'\tprintf("{i.label}=%" PRIx{utils.size_from_bus_size(i.length)} ", ", output->{i.label} & (1 << {i.length}) - 1);\n'
    suffix = '\tprintf("\\n");\n}}\n'
    return prefix + content + suffix


def _get_prompt_input(varset):
    content = "void prompt_{short_name}_input(Input_{short_name} *input) {{\n"
    for i in varset:
        content += f'\tprintf("{i.label}[{i.length}]:=");\n'
        content += f'\tscanf("%" SCNx{utils.size_from_bus_size(i.length)} "; ", &input->{i.label});\n'
    content += "}}"
    return content


def _get_prompt_rom(roms):
    prefix = "void fscan_rom(FILE * f, Rom_{short_name} * roms) {{\n"
    content = ""
    for e in roms:
        content += (
            f"roms->{e.var.label} = calloc(1 << {e.expr.static_args[0]}, {utils.size_from_bus_size(e.expr.static_args[1])});"
            f'\tprintf("Scanning ROM {e.var.label}\\n");\n'
            f"\tfor(unsigned int i = 0; i < (1 << {e.expr.static_args[0]}); i++) {{{{\n"
            f'\t\tif(1 != fscanf(f, "%" SCNx{utils.size_from_bus_size(e.expr.static_args[1])}, roms->{e.var.label} + i)) {{{{\n'
            f'\t\t\tprintf("Error while scanning ROM {e.var.label} at line %d.Exiting", i);\n'
            f"\t\t\texit(1);\n"
            f"\t\t}}}}\n"
            f"}}}}\n"
        )
    suffix = '\tprintf("\\n");\n}}\n'
    return prefix + content + suffix


def transpile2C(netlist_string, helper_functions=True):
    """
    Renvoie un couple de strings correpondant au fichier headers et aux
    sources. Il comportent 3 placeholders compatibles avec la fonctions
    `format`:
      - functionName: le nom de la fonction à appeler pour calculer un cycle de
        netList
      - short_name: un nom court pour les structure de données d'entrée et de
        sortie
      - filename: le nom prévu pour le fichier fichier source (dépourvu de
        l'extension .c (le fichier source contiendra un include vers
        `{filename}.h`
    """
    netlist = getAST(netlist_string)
    ordered_eqns = utils.getOrderedNetList(netlist)

    # Generating header file
    h_file = "#ifndef {filename}_H\n#include <stdint.h>\n"
    if helper_functions:
        h_file += "#include <stdlib.h>\n#include <stdio.h>\n#include <inttypes.h>\n"
    h_file += "\n#define {filename}_H\n"
    # Input struct
    h_file += _get_struct(netlist.inputs, "Input_{short_name}")
    # output struct
    h_file += _get_struct(netlist.outputs, "Output_{short_name}")

    # Generating the C file
    # String containing the C code file
    c_file = '#include <stdint.h>\n#include "{filename}.h"\n\n'
    if helper_functions:
        c_file += "#include <stdlib.h>\n#include <stdio.h>\n#include <inttypes.h>\n\n"
    c_file += "void {functionName}(Input_{short_name} *input, Output_{short_name} *output, Rom_{short_name}* roms) {{\n"

    c_func_prefix = ""
    c_func_body = ""
    c_func_suffix = ""
    roms = []  # Une liste qui stocke toute les roms

    for v in netlist.inputs:
        c_func_prefix += f"\t{utils.cTypeFromBusSize(v.length).value} {v.label} = input->{v.label};\n"

    for eq in ordered_eqns:
        exp, pre, suf, r = _getExpr(eq)
        if r is not None:
            roms.append(r)
        c_func_body += exp
        c_func_prefix += pre
        c_func_suffix += suf

    for v in netlist.outputs:
        c_func_suffix += f"\toutput->{v.label} = {v.label};\n"

    roms.sort(key=lambda x: x.var.label)

    c_file += f"{c_func_prefix}\n{c_func_body}\n{c_func_suffix}\n"
    c_file += "}}\n"

    if helper_functions:
        c_file += _get_print_output(netlist.outputs)
        c_file += _get_prompt_input(netlist.inputs)
        c_file += _get_prompt_rom(roms)

    # On termine le fichier de headers
    h_file += _get_rom_struct(roms)
    h_file += "void {functionName}(Input_{short_name} *input, Output_{short_name} *output, Rom_{short_name}* roms);\n"
    if helper_functions:
        h_file += "void print_{short_name}_output(Output_{short_name} *output);\n"
        h_file += "void prompt_{short_name}_input(Input_{short_name} *input);\n"
        h_file += "void fscan_rom(FILE * f, Rom_{short_name} * roms);\n"
    h_file += "\n#endif"

    return h_file, c_file


def getAST(code_string):
    return parser.parse(code_string)
