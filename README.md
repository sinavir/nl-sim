# Simulateur de netlists

Simulateur de netlist pour le projet de sysnum

# Dépendances:

- `python >= 3.10`
- `lark >= 1.1.2`
- `gcc` (en réalité marche sûrement avec une grandes partie des toolchains C, mais dans ce cas il faut adapter `builder.sh`

On peut aussi utiliser le makefile fourni pour construire tous les tests

## Avec `nix`

`TODO`

## Format de la ROM

Un fichier ROM valide est une succession de valeurs hexadécimales de 8, 16, 32 ou 64 bits (la plus petite taille permettant de faire rentrer un mot de la ROM)  séparées par des nouvelles lignes.

Ces valeurs sont tronquées à la taille des mots.

Lorsqu'il y a plusieurs ROMs, les premières valeurs décrivent la ROM dont le label de la "nappe sortante" est le premier dans l'ordre lexicographique. Les valeurs suivantes la seconde ROM, etc

# Descriptions générale du projet

Mon simulateur transpile la netlist en code C ensuite compilé. Le code C est constitué d'une fonction principale simulant un cycle de netlist. Les effets de bord induits par les registres sont traités grace au mot-clef `static`. Cette fonction a pour signature:

```
void simulateNetlist(Input_netlist *input, Output_netlist *output, Rom_netlist* roms);
```

Les types des 3 arguments sont des struct d'entiers pour les deux premiers, un struct de pointeurs pour le dernier.

les code généré propose aussi des petites fonctions pour remplir les 3 `struct`.

Le code généré est ensuite lié à un fichier simpliste contenant la fonction `main` (le fichier `main_example.c`) mais l'idée est surtout d'écrire un `main.c` adapté aux entrées sorties que l'on veut pour notre processeur (par exemple pourquoi pas lire la rom sur l'entrée standard ou alors la mettre directement dans le binaire de simulation ?)

Aussi ma façon de coder les nappes fait que j'ai pas trop eu à penser aux problèmes de "boutisme" ("endianness")

## Encodage des nappes de fils

Les nappes de fil sont codées sur des entiers non signés de taille 8, 16, 32 ou 64 bit selon la taille de la nappe. Cela permet de réutiliser les opérateurs bit à bit du C. Cela introduit aussi la limitation suivante: **les nappes doivent être de taille inférieure ou égale à 64 bits**.

## Composants implémentés

- `NOT`
- `AND`
- `OR`
- `XOR`
- `NAND`
- `NXOR`
- `MUX`
- `REG`
- `RAM`
- `ROM`
- `SNIP`: Un slice avec le deuxième indice exclu
- `CONCAT`
- `SLICE`
- `SELECT`
- `COPY`: Copie une nappe. Un sucre syntaxique est d'omettre la commande (j'ai dû ajouter ça à cause d'un fichier de test qui avait un bloc de type `a = b`

## Remarque sur le scheduling

- `REG` ne dépend que des valeurs à l'étape `n-1` donc n'a pas de dépendances
- `RAM` dépend uniquement de l'adresse de lecture. L'opération d'écriture s'effectuant après la lecture.
