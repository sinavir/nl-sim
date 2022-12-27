{ lib , pkgs, buildPythonPackage, pythonPackages , fetchFromGitHub }:
buildPythonPackage rec {
  pname = "netlistSimulator";
  version = "1.0";
  doCheck = false;
  src = ./../nl-transpiler ;
  propagatedBuildInputs = [ pythonPackages.lark ];
}
