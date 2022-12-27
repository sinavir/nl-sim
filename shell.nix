{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  buildInputs = [
    (pkgs.python310.withPackages (
      ps: [
        ps.lark
      ]
    ))
  ];
}
