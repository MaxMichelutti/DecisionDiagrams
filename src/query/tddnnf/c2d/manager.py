"""module where all the queries functions are defined"""

import os
import time
import subprocess
from typing import Dict

from pysmt.fnode import FNode

from dotenv import load_dotenv as _load_dotenv

from src.query.util import indexes_from_mapping
from src.query.query_interface import QueryInterface

_load_dotenv()
_DDNNF_REASONER_PATH = os.getenv("DDNNF_REASONER_PATH")
if _DDNNF_REASONER_PATH is not None and os.path.isfile(_DDNNF_REASONER_PATH) and not _DDNNF_REASONER_PATH.startswith("."):
    if _DDNNF_REASONER_PATH.startswith("/"):
        _DDNNF_REASONER_PATH = f".{_DDNNF_REASONER_PATH}"
    else:
        _DDNNF_REASONER_PATH = f"./{_DDNNF_REASONER_PATH}"

_CONDITIONED_INPUT_FILE = "conditioned_ddnnf_reasoner_input.nnf"

_COMMANDS_FILE = "ddnnf_reasoner_commands.txt"

class C2D_DDNNFQueryManager(QueryInterface):
    """manager to handle all queries on T-dDNNF generated by the C2D compiler"""

    quantified_vars: set[int]
    # the compiled formula loading time in seconds 
    # to be subtracted frm the total time of queries
    loading_time_seconds: float

    def __init__(
            self,
            source_folder: str,
            ddnnf_vars: int,
            refinement_mapping: Dict[int, FNode] | None = None,
            abstraction_mapping: Dict[FNode, int] | None = None):
        """
        initialize the manager
        Always provide either the refinement_mapping or the abstraction_mapping or both when initializing the object,
        otherwise a ValueError will be raises

        Args:
            source_folder (str): the path to the folder where the serialized compiled formula is stored
            ddnnf_vars (int): the number of variables in the compiled formula (including the existentially quantified ones)
            refinement_mapping (Dict[int, FNode]) [None]: the mapping of the indices on the compiled formula's abstraction to the atoms in its refinement
            abstraction_mapping (Dict[FNode, int]) [None]: the mapping of the atoms of the formula to the indices in the compiled formula's abstraction
        """
        super().__init__(source_folder, refinement_mapping, abstraction_mapping)

        # check if the reasoner can be used
        self._check_executable()

        # find the quantified variables by checking
        # which variables are not in the abstraction mapping keys
        self.quantified_vars = set()
        for i in range(1, ddnnf_vars+1):
            if i not in self.abstraction_mapping:
                self.quantified_vars.add(i)

        # load, condition and store the compiled formula
        with open(_COMMANDS_FILE, 'w', encoding='utf8') as commands_file:
            # load the compiled formula
            commands_file.write(f"load {source_folder}/dimacs.cnf.nnf\n")
            # condition the compiled formula
            condition_string = " ".join(self.quantified_vars)
            commands_file.write(f"cond {condition_string}\n")
            # store the conditioned formula in a file
            commands_file.write(f"store {source_folder}/{_CONDITIONED_INPUT_FILE}\n")
        # run the reasoner with given commands
        result = os.system(f"{_DDNNF_REASONER_PATH} -cmd {_COMMANDS_FILE}")
        if result != 0:
            raise RuntimeError(
                f"Reasoner error loading the conditioned formula from {source_folder}")

        # time the reasoner loading the conditioned formula
        with open(_COMMANDS_FILE, 'w', encoding='utf8') as commands_file:
            commands_file.write(f"load {source_folder}/{_CONDITIONED_INPUT_FILE}\n")
        start_time = time.time()
        result = os.system(f"{_DDNNF_REASONER_PATH} -cmd {_COMMANDS_FILE}")
        elapsed_time = time.time() - start_time
        self.loading_time_seconds = elapsed_time


    def _check_executable(self) -> None:
        """function to check if the reasoner can be used, 
        raises exceptions if the reasoner cannot be called

        Raises:
            ValueError: if the path to the reasoner is not provided
            FileNotFoundError: if the path to the reasoner is invalid
            PermissionError: if the reasoner is not executable"""
        if _DDNNF_REASONER_PATH is None:
            raise ValueError(
                "Please provide the path to the ddnnf reasoner in the .env file")
        if not os.path.isfile(_DDNNF_REASONER_PATH):
            raise FileNotFoundError(
                f"Invalid path to the ddnnf reasoner: {_DDNNF_REASONER_PATH}")
        if not os.access(_DDNNF_REASONER_PATH, os.X_OK):
            raise PermissionError(
                f"File {_DDNNF_REASONER_PATH} is not executable")

    def check_consistency(self) -> bool:
        """function to check if the encoded formula is consistent

        Returns:
            bool: True if the formula is consistent, False otherwise"""
        models = self._count_models()
        result = (models > 0)

        return result

    def check_validity(self) -> bool:
        """function to check if the encoded formula is valid

        Returns:
            bool: True if the formula is valid, False otherwise"""
        models = self._count_models()
        max_models = 2 ** len(self.refinement_mapping)
        result = (models == max_models)

        return result

    def _check_entail_clause_body(self, clause: FNode) -> bool:
        """function to check if the encoded formula entails the clause

        Args:
            clause (FNode): an FNode representing the clause to check

        Returns:
            bool: True if the formula entails the clause, False otherwise
        """
        # RETRIEVE THE INDEXES ON WHICH TO OPERATE
        clause_items = indexes_from_mapping(clause, self.abstraction_mapping)
        raise NotImplementedError()

    def _check_implicant_body(
            self,
            term: FNode) -> bool:
        """function to check if the term is an implicant for the encoded formula

        Args:
            term (FNode): the term to be checked
        """
        # RETRIEVE THE INDEX ON WHICH TO OPERATE
        term_index = indexes_from_mapping(term, self.abstraction_mapping)[0]
        raise NotImplementedError()

    def _count_models(self) -> int:
        """count_model body"""
        with open(_COMMANDS_FILE, 'w', encoding='utf8') as commands_file:
            commands_file.write(f"load {self.source_folder}/{_CONDITIONED_INPUT_FILE}\n")
            commands_file.write("mc\n")
        try:
            output_data = subprocess.check_output(f"{_DDNNF_REASONER_PATH} -cmd {_COMMANDS_FILE}", shell=True, text=True)
        except subprocess.CalledProcessError as e:
            exit_code = e.returncode
            raise RuntimeError(
                f"Reasoner error while counting models: {exit_code}") from e
        models = int(output_data.split(" ")[-1])
        return models

    def count_models(self) -> int:
        """function to count the number of models for the encoded formula

        Returns:
            int: the number of models for the encoded formula
        """
        result = self._count_models()

        return result

    def enumerate_models(self) -> None:
        """function to enumerate all models for the encoded formula
        """
        raise NotImplementedError()

    def _condition_body(
            self,
            alpha: FNode,
            output_file: str | None = None) -> None:
        """function to obtain [compiled formula | alpha], where alpha is a literal or a cube

        Args:
            alpha (FNode): the literal (or conjunction of literals) to condition the T-dDNNF
            output_file (str, optional): the path to the .smt2 file where the conditioned T-dDNNF will be saved. Defaults to None.
        """
        # RETRIEVE THE INDEXES ON WHICH TO OPERATE
        alpha_items = indexes_from_mapping(alpha, self.abstraction_mapping)

        raise NotImplementedError()
