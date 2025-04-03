"""module where all the queries functions are defined"""

import os
import subprocess
from typing import Dict, List, Tuple

from pysmt.fnode import FNode
from pysmt.shortcuts import Not

from src.query.util import indexes_from_mapping, UnsupportedQueryException, check_executable
from src.query.query_interface import QueryInterface
from src.query.constants import (
    DDNNF_CONDITION_PATH as _DDNNF_CONDITION_PATH,
    DECDNNF_PATH as _DECDNNF_PATH,
    CONDITION_DDNNF_OUTPUT_OPTION as _CONDITION_DDNNF_OUTPUT_OPTION,
    CONDITION_D4_OUTPUT_OPTION as _CONDITION_D4_OUTPUT_OPTION,
    TEPORARY_CONDITION_FILE as _TEMPORARY_CONDITIONED_FILE)


class DDNNFQueryManager(QueryInterface):
    """manager to handle all queries on T-dDNNF"""

    quantified_vars: set[int]
    total_vars: int
    output_option: str

    # IMPORTANT!
    # classes that inherit from this class must define this attribute
    d4_file: str

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

        # check if the binaries are available
        check_executable(_DDNNF_CONDITION_PATH)
        check_executable(_DECDNNF_PATH)

        self.total_vars = ddnnf_vars
        self.output_option = _CONDITION_DDNNF_OUTPUT_OPTION

        # find the quantified variables by checking
        # which variables are not in the abstraction mapping keys
        self.quantified_vars = set()
        for i in range(1, ddnnf_vars+1):
            if i not in self.abstraction_mapping:
                self.quantified_vars.add(i)

        self.d4_file = ""

    def _check_consistency(self) -> Tuple[bool, float]:
        """function to check if the encoded formula is consistent

        Returns:
            bool: True if the formula is consistent, False otherwise
            float: the strucutre loading time"""
        models = self._count_models_body(self.d4_file)
        result = (models > 0)

        return self._check_consistency_body(self.d4_file)
    
    def _check_consistency_body(self, d4_file:str) -> Tuple[bool, float]:
        """function to check if the encoded formula is consistent

        Args:
            d4_file (str): the path to the d4 file
        Returns:
            bool: True if the formula is consistent, False otherwise
        """
        # TODO()!: change consistency check 
        command = [_DECDNNF_PATH, "compute-model", "-i",d4_file]
        try:
            sat_command = " ".join(command)
            process_data = subprocess.check_output(
                sat_command,
                shell=True,
                text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                "An error occurred while checking satisfiability") from e
        is_sat = None
        # find not empty output line that does not start with "["
        for line in process_data.split("\n"):
            if line and line.startswith("s"):
                sat_result = line[2:]
                if(sat_result == "SATISFIABLE"):
                    is_sat = True
                elif(sat_result == "UNSATISFIABLE"):
                    is_sat = False
                break
        if is_sat is None:
            raise RuntimeError(
                "An error occurred while checking satisfiability")

        return is_sat, 0

    def _check_validity(self) -> Tuple[bool, float]:
        """function to check if the encoded formula is valid

        Returns:
            bool: True if the formula is valid, False otherwise
            float: the strucutre loading time"""
        models = self._count_models_body(self.d4_file)
        max_models = 2 ** len(self.abstraction_mapping)
        result = (models == max_models)

        return result, 0

    def _check_entail_clause_body(self, clause: FNode) -> Tuple[bool, float]:
        """function to check if the encoded formula entails the clause

        Args:
            clause (FNode): an FNode representing the clause to check

        Returns:
            bool: True if the formula entails the clause, False otherwise
            float: the entailment checking time
        """

        # RETRIEVE THE INDEXES ON WHICH TO OPERATE
        clause_items = indexes_from_mapping(clause, self.abstraction_mapping)

        clause_items_tuples = [(abs(item), item > 0) for item in clause_items]

        return self._check_entail_clause_random_body(clause_items_tuples)

    def _check_entail_clause_random_body(self, clause_items: List[Tuple[int, bool]]) -> Tuple[bool, float]:
        """function to check if the encoded formula entails the clause

        Args:
            clause_items (List[Tuple[int,bool]]): the clause to be checked

        Returns:
            bool: True if the formula entails the clause, False otherwise
            float: the structure loading time
        """
        clause_items_indexes = [item[0] if item[1]
                                else -item[0] for item in clause_items]

        # NEGATE ALL ITEMS IN THE CLAUSE
        # TO OBTAIN A CUBE EQUIVALENT TO
        # NOT CLAUSE
        clause_items_negated = [-item for item in clause_items_indexes]

        # CONDITION OVER CLAUSE ITEMS NEGATED
        self._condition_all_variables(
            clause_items_negated, _CONDITION_D4_OUTPUT_OPTION, _TEMPORARY_CONDITIONED_FILE)
        # CHECK IF THE CONDITIONED T-dDNNF IS SAT
        is_sat, _time = self._check_consistency_body(_TEMPORARY_CONDITIONED_FILE)
        # IF THE CONDITIONED T-dDNNF IS SAT, THEN THE FORMULA DOES NOT ENTAIL THE CLAUSE
        entailment = not is_sat

        self._clear_tmp_file()

        return entailment, 0

    def _clear_tmp_file(self) -> None:
        """function to clear the temporary file created during the execution"""
        if os.path.exists(_TEMPORARY_CONDITIONED_FILE):
            os.remove(_TEMPORARY_CONDITIONED_FILE)

    def _check_implicant_body(
            self,
            term: FNode) -> Tuple[bool, float]:
        """function to check if the term is an implicant for the encoded formula

        Args:
            term (FNode): the term to be checked

        Returns:
            bool: True if the term is an implicant, False otherwise
            float: the implicant checking time
        """
        # RETRIEVE THE INDEX ON WHICH TO OPERATE
        term_index = indexes_from_mapping(term, self.abstraction_mapping)[0]
        is_positive = True
        if term_index < 0:
            is_positive = False
        return self._check_implicant_random_body((abs(term_index), is_positive))

    def _check_implicant_random_body(self, term_item: Tuple[int, bool]) -> Tuple[bool, float]:
        """function to check if the term is an implicant for the encoded formula

        Args:
            term_item (Tuple[int,bool]): the term to be checked

        Returns:
            bool: True if the term is an implicant, False otherwise"""
        term_index = term_item[0] if term_item[1] else -term_item[0]

        # CONSTRUCT T-dDNNF | term
        self._condition_all_variables(
            [term_index], _CONDITION_D4_OUTPUT_OPTION, _TEMPORARY_CONDITIONED_FILE)
        # COUNT MODELS OF CONDITIONED T-dDNNF
        conditioned_mc = self._count_models_body(_TEMPORARY_CONDITIONED_FILE)
        # CHECK IF THE CONDITIONED T-dDNNF IS VALID (HAS 2**N MODELS)
        validity = (conditioned_mc == 2 ** len(self.abstraction_mapping))
        # IF THE CONDITIONED T-BDD IS VALID, THEN THE TERM IS AN IMPLICANT
        implicant = validity

        self._clear_tmp_file()

        return implicant, 0

    def _count_models_body(self, input_file: str) -> int:
        """count_model body

        Args:
            input_file (str): the path to the input file for MC
        """
        try:
            mc_command = " ".join([_DECDNNF_PATH, "model-counting", "-i",
                                   input_file, "--n-vars", str(self.total_vars)])
            process_data = subprocess.check_output(
                mc_command,
                shell=True,
                text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                "An error occurred while counting the models") from e
        models_found = 0
        # find not empty output line that does not start with "["
        for line in process_data.split("\n"):
            if line and not line.startswith("!"):
                models_found = int(line)
                break
        # remove quantified vars from the total number of models
        return models_found / (2 ** len(self.quantified_vars))

    def _count_models(self) -> Tuple[int, float]:
        """function to count the number of models for the encoded formula

        Returns:
            int: the number of models for the encoded formula
            float: the model counting time
        """
        result = self._count_models_body(self.d4_file)
        return result, 0

    def _enumerate_models(self) -> float:
        """function to enumerate all models for the encoded formula

        Returns:
            float: the structure loading time
        """
        try:
            process_data = subprocess.check_output(
                " ".join([_DECDNNF_PATH, "model-enumeration", "-i",
                          self.d4_file, "-c", "--n-vars", str(self.total_vars)]),
                shell=True,
                text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                "An error occurred while enumerating the models") from e
        for line in process_data.split("\n"):
            if len(line) == 0:
                continue
            if not line.startswith("!") and not line == "TRUE":
                print(self._refine(line))
        return 0

    def _refine(self, model: str) -> str:
        """refines a model by replacing the indices with the corresponding atoms"""
        refined_model = ""
        items = model.split()
        # skip initial 'v' and final '0'
        items = items[1:-1]
        for item in items:
            if item.startswith('*'):
                # skip the variables that can be both positive and negative
                continue
            variable = int(item)
            variable_name = abs(variable)
            atom = self.refinement_mapping[variable_name]
            if variable < 0:
                if atom.is_not():
                    refined_model += str(atom.arg(0)) + ", "
                else:
                    refined_model += "!" + str(Not(atom)) + ", "
            else:
                refined_model += str(atom) + ", "
        if refined_model == "":
            return "TRUE"
        # remove the trailing comma and space
        refined_model = refined_model[:-2]
        return refined_model

    def _condition_all_variables(self, vars_to_condition: List[int], output_option: str | None = None, output_file: str | None = None) -> None:
        """function to condition the T-dDNNF on the specified variables

        Args:
            vars_to_condition (List[int]): the list of variables to condition on
            output_option (str): the option to pass to the T-dDNNF compiler for the output file
            output_file (str, optional): the path to the .smt2 file where the conditioned T-dDNNF will be saved. Defaults to None
        """
        if (len(vars_to_condition) == 0):
            raise ValueError("No variables to condition on")
        condition_option = "-c "
        for var in vars_to_condition:
            condition_option += str(var) + " "
        # trim the trailing space
        condition_option = condition_option[:-1]
        command = [_DDNNF_CONDITION_PATH, condition_option, "-i_d4",
                   self.d4_file]
        if output_file is not None:
            if (output_option is None):
                # default output option
                if hasattr(self, "output_option"):
                    output_option = self.output_option
                else:
                    output_option = _CONDITION_DDNNF_OUTPUT_OPTION
            command.append(output_option)
            command.append(output_file)
        command_str = " ".join(command)
        result = os.system(command_str)
        if result != 0:
            raise RuntimeError(
                "An error occurred while conditioning the T-dDNNF")

    def _condition_body(
            self,
            alpha: FNode,
            output_file: str | None = None) -> float:
        """function to obtain [compiled formula | alpha], where alpha is a literal or a cube

        Args:
            alpha (FNode): the literal (or conjunction of literals) to condition the T-dDNNF
            output_file (str, optional): the path to the .smt2 file where the conditioned T-dDNNF will be saved. Defaults to None.

        Returns:
            float: the structure loading time
        """
        # RETRIEVE THE INDEXES ON WHICH TO OPERATE
        alpha_items = indexes_from_mapping(alpha, self.abstraction_mapping)

        self._condition_all_variables(
            alpha_items, self.output_option, output_file)

        return 0

    def _condition_random_body(self, cube_items: List[Tuple[int, bool]]) -> float:
        """function to condition the encoded formula on the random cube

        Args:
            cube_items (List[Tuple[int,bool]]): the cube to condition

        Returns:
            float: the structure loading time
        """
        variables = [item[0] if item[1] else -item[0] for item in cube_items]
        self._condition_all_variables(variables)
        return 0

    def check_entail(self, data_folder: str) -> bool:
        """
        raises UnsupportedQueryException
        """

        raise UnsupportedQueryException(
            "T-dDNNFs do not support polytime entailment checking")

    def conjunction(self, data_folder: str, output_path: str | None = None) -> None:
        """
        raises UnsupportedQueryException
        """
        raise UnsupportedQueryException(
            "T-dDNNFs do not support polytime conjunction")

    def disjunction(self, data_folder: str, output_path: str | None = None) -> None:
        """
        raises UnsupportedQueryException
        """
        raise UnsupportedQueryException(
            "T-dDNNFs do not support polytime disjunction")

    def negation(self, output_path: str | None = None) -> None:
        """
        raises UnsupportedQueryException
        """
        raise UnsupportedQueryException(
            "T-dDNNFs do not support polytime negation")
