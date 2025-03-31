"""module to handle the options for the main compiled formula quering tool"""
import argparse
from dataclasses import dataclass
from typing import List

@dataclass
class QueryOptions:
    """dataclass that holds options for the tool"""
    load_data: str
    consistency: bool
    validity: bool
    entail_clause: List[str]
    implicant: str | None
    count: bool
    enumerate: bool
    condition: str | None
    save_conditioned: str | None
    conjunction: str | None
    save_conjunction: str | None
    disjunction: str | None
    save_disjunction: str | None
    negation: bool
    save_negation: str | None
    entail: str | None
    random: int | None
    seed: int | None
    details: str | None

    def __init__(self, args: argparse.Namespace):
        self.load_data = args.load_data
        # trim the trailing slash if it exists
        if self.load_data.endswith("/"):
            self.load_data = self.load_data[:-1]
        self.consistency = args.consistency
        self.validity = args.validity
        self.entail_clause = args.entail_clause if args.entail_clause is not None else []
        self.implicant = args.implicant
        self.count = args.count
        self.enumerate = args.enumerate
        self.condition = args.condition
        self.save_conditioned = args.save_conditioned
        self.conjunction = args.conjunction
        self.save_conjunction = args.save_conjunction
        self.disjunction = args.disjunction
        self.save_disjunction = args.save_disjunction
        self.negation = args.negation
        self.save_negation = args.save_negation
        self.entail = args.entail
        self.random = args.random
        self.details = args.details
        try:
            self.seed = int(args.seed) if args.seed is not None else None
        except ValueError:
            raise ValueError("The seed provided is not an integer")

def get_args() -> QueryOptions:
    """Reads the args from the command line"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--load_data",
        help="Specify the path to the folder where all necessary compiled formula files are stored",
        type=str,
        required=True)
    parser.add_argument(
        "--consistency",
        help="Query the compiled formula to check if the encoded formula is consistent",
        action="store_true")
    parser.add_argument(
        "--validity",
        help="Query the compiled formula to check if the encoded formula is valid",
        action="store_true")
    parser.add_argument(
        "--entail_clause",
        help="Query the compiled formula to check if the encoded formula entails the clause from the specified smt2 file",
        nargs='+',
        type=str)
    parser.add_argument(
        "--implicant",
        help="Query the compiled formula to check if the term in the specified smt2 file is an implicant for the encoded formula",
        type=str)
    parser.add_argument(
        "--count",
        help="Query the compiled formula to count the number of models for the encoded formula",
        action="store_true")
    parser.add_argument(
        "--enumerate",
        help="Query the compiled formula to enumerate all models for the encoded formula",
        action="store_true")
    parser.add_argument(
        "--condition",
        help="Transform the compiled formula in compiled formula | alpha, where alpha is a literal or a cube specified in the provided .smt2 file",
        type=str)
    parser.add_argument(
        "--save_conditioned",
        help="Specify the path to the file or folder (depending on compiled language) where the conditioned compiled formula will be saved",
        type=str)
    parser.add_argument(
        "--conjunction",
        help="Transform the compiled formula in compiled (formula and data), where data is another compiled formula in the same language",
        type=str)
    parser.add_argument(
        "--save_conjunction",
        help="Specify the path to the file or folder (depending on compiled language) where the conjunction of compiled formulas will be saved",
        type=str)
    parser.add_argument(
        "--disjunction",
        help="Transform the compiled formula in compiled (formula or data), where data is another compiled formula in the same language",
        type=str)
    parser.add_argument(
        "--save_disjunction",
        help="Specify the path to the file or folder (depending on compiled language) where the disjunction of compiled formulas will be saved",
        type=str)
    parser.add_argument(
        "--negation",
        help="Transform the compiled formula into its negation",
        action="store_true")
    parser.add_argument(
        "--save_negation",
        help="Specify the path to the file or folder (depending on compiled language) where the negation of the compiled formula will be saved",
        type=str)
    parser.add_argument(
        "--entail",
        help="Specify the path to the file or folder (depending on compiled language) where the formula for entailment is stored and query for entailment",
        type=str)
    parser.add_argument(
        "-r",
        "--random",
        help="select a random clause/implicant/term instead of loading from a file",
        action="store_true")
    parser.add_argument(
        "-s",
        "--seed",
        help="select a seed for the random selection",
        type=str)
    parser.add_argument(
        "-d",
        "--details",
        help="save the details for computation in the specified file",
        type=str)
    args = parser.parse_args()
    return QueryOptions(args)
