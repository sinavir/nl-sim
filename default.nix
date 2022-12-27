{ pkgs ? import ./nix/default.nix {} }: {
  nl-transpiler = pkgs.python310Packages.callPackage ./nl-transpiler.nix {};
}
