import argparse

from .netlist2C import transpile2C


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("netlist", help="Netlist file to transpile")
    parser.add_argument("outname", help="The simulation C file name")
    args = parser.parse_args()
    with open(args.netlist) as f:
        nl = f.read()
        form = {
            "short_name": "netlist",
            "filename": args.outname,
            "functionName": "simulateNetlist",
        }
        h_file, c_file = transpile2C(nl)
        with open(args.outname + ".h", "w") as h:
            h.write(h_file.format(**form))
        with open(args.outname + ".c", "w") as c:
            c.write(c_file.format(**form))


if __name__ == "__main__":
    main()
