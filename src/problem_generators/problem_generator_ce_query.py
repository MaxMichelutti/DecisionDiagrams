"""module for the generation of random clauses for querying"""
import random
import argparse
import os
from pysmt.shortcuts import Not, Or
from theorydd.formula import get_atoms as _get_atoms
from theorydd.formula import read_phi as _read_phi
from theorydd.formula import save_phi as _save_phi


def parse_input():
    """Parse the input arguments for the script."""
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--size",
        help="Size as number of variables in the output clause",
        type=int,
        required=True)
    arg_parser.add_argument(
        "--seed",
        help="Random seed to use",
        type=int,
        default=0,
        required=False)
    arg_parser.add_argument(
        "--source",
        help="Number of variables in the output clause",
        type=str,
        required=True)
    arg_parser.add_argument(
        "--output",
        help="Output file",
        type=str,
        required=True)
    return arg_parser.parse_args()


def main():
    """Main function to generate a random clause."""
    args = parse_input()
    if args.seed is not None:
        random.seed(args.seed)
    size: int = args.size
    input_file: str = args.source
    output_file: str = args.output

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file {input_file} does not exist.")

    input_formula = _read_phi(input_file)
    input_atoms = _get_atoms(input_formula)

    if len(input_atoms) < size:
        size = len(input_atoms)

    if size < 1:
        raise ValueError("Cannot generate a query for an empty set of atoms!")

    chosen_set = set()
    while len(chosen_set) < size:
        choice = random.choice(input_atoms)
        input_atoms.remove(choice)
        if random.randint(0, 1) == 0:  # negate 50 % of atoms
            choice = Not(choice)
        chosen_set.add(choice)

    chosen_set = list(chosen_set)
    clause = Or(*chosen_set)
    _save_phi(clause, output_file)


if __name__ == "__main__":
    main()
