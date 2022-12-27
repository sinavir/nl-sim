#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#include "%headername%"

int main(int argc, char *argv[]) {
	Output_netlist output;
	Input_netlist input;
	Rom_netlist rom;
        if (argc > 1) {
		FILE * fp = fopen(argv[1], "r");
		if(fp == NULL) {
			printf("ROM file not found");
			return 1;
		}
		fscan_rom(fp, &rom);
	} else {
			printf("ROM file not provided. If there is a ROM component in the netlist, the program may segfault. Specify /dev/zero as ROM file to disable this warning");
	}
	while (1) {
		prompt_netlist_input(&input);
		simulateNetlist(&input, &output, &rom);
		print_netlist_output(&output);
	};
	return 0;
};
