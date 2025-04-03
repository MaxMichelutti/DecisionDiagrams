"""interface for all Query objects"""

from abc import ABC, abstractmethod
import time
import os
from typing import Dict, List, Tuple, final

from pysmt.fnode import FNode
from pysmt.shortcuts import And, Or, Not

from theorydd.solvers.mathsat_total import MathSATTotalEnumerator
from theorydd.formula import get_normalized, get_atoms, without_double_neg, read_phi

from src.query.util import is_clause, is_cube, is_term, normalize_refinement, select_random_items, time_limit, LocalTimeoutException


class QueryInterface(ABC):
    """interface for all Query objects"""

    source_folder: str
    refinement_mapping: Dict[object, FNode]
    abstraction_mapping: Dict[FNode, object]
    # solver used for normalization of input
    normalizer_solver: MathSATTotalEnumerator
    details: Dict[str, object]

    def __init__(self,
                 source_folder: str,
                 refinement_mapping: Dict[object, FNode] | None = None,
                 abstraction_mapping: Dict[FNode, object] | None = None,
                 ):
        """
        initialize the query object.
        Always provide either the refinement_mapping or the abstraction_mapping or both when initializing the object,
        otherwise a ValueError will be raises

        Args:
            source_folder (str): the path to the folder where the serialized compiled formula is stored
            refinement_mapping (Dict[int, FNode]) [None]: the mapping of the indices on the compiled formula's abstraction to the atoms in its refinement
            abstraction_mapping (Dict[FNode, int]) [None]: the mapping of the atoms of the formula to the indices in the compiled formula's abstraction
        """
        self.source_folder = source_folder
        if (self.source_folder.endswith("/")):
            self.source_folder = self.source_folder[:-1]
        if refinement_mapping is None and abstraction_mapping is None:
            raise ValueError(
                "Either the refinement_mapping or the abstraction_mapping must be provided")
        if refinement_mapping is None:
            refinement_mapping = {v: k for k, v in abstraction_mapping.items()}

        # normalize atoms in the mapping
        self.normalizer_solver = MathSATTotalEnumerator()
        self.refinement_mapping = normalize_refinement(
            refinement_mapping, self.normalizer_solver)

        # compute reverse mapping to generate the abstraction funciton
        self.abstraction_mapping = {
            v: k for k, v in self.refinement_mapping.items()}

        self.details = {}

    @abstractmethod
    def _check_consistency(self) -> Tuple[bool, float]:
        """where the actual consistency checking is done

        Returns:
            Tuple[bool,float]: the result of the consistency checking and the time taken to load the structure"""
        raise NotImplementedError()

    @final
    def check_consistency(self, timeout:int=600) -> bool:
        """function to check if the encoded formula is consistent

        Args:
            timeout (int) [600]: the timeout for the consistency check in seconds. Defaults to 600.

        Returns:
            bool: True if the formula is consistent, False otherwise
        """
        start_time = time.time()
        try:
            with time_limit(timeout):
                result, load_time = self._check_consistency()
        except LocalTimeoutException:
            print("Timeout reached for consistency check")
            self.details["consistency"] = "timeout"
            return False
        self.details["consistency"] = result
        self.details["consistency time"] = time.time() - start_time - load_time
        return result

    @abstractmethod
    def _check_validity(self) -> Tuple[bool, float]:
        """where the actual validity checking is done

        Returns:
            Tuple[bool,float]: the result of the validity checking and the time taken to load the structure"""
        raise NotImplementedError()

    @final
    def check_validity(self, timeout:int=600) -> bool:
        """function to check if the encoded formula is valid

        Args:
            timeout (int) [600]: the timeout for the validity check in seconds. Defaults to 600.

        Returns:
            bool: True if the formula is valid, False otherwise"""
        start_time = time.time()
        try:
            with time_limit(timeout):
                result, _load_time = self._check_validity()
        except LocalTimeoutException:
            print("Timeout reached for validity check")
            self.details["validity"] = "timeout"
            return False
        result, loading_time = self._check_validity()
        self.details["validity"] = result
        self.details["validity time"] = time.time() - start_time - loading_time
        return result

    @final
    def _clause_file_can_entail(self, clause_file: str) -> FNode:
        """checks if the provided input file can be used to check entailment

        raises exceptions if something is wrong with the file or its contents

        Args:
            clause_file (str): the path to the clause file

        Returns:
            (FNode): the correctly formatted clause provided as input"""
        # read data
        clause = read_phi(clause_file)

        # normalize the clause
        clause.simplify()
        clause = get_normalized(clause, self.normalizer_solver.get_converter())
        clause = without_double_neg(clause)

        if not is_term(clause) and not is_clause(clause):
            raise ValueError(
                "The clause must be a literal or a disjunction of literals")

        # check that the clause is on the same atoms as phi
        phi_atoms = set()
        for value in self.abstraction_mapping.keys():
            phi_atoms.add(get_atoms(value)[0])
        phi_atoms = frozenset(phi_atoms)
        clause_atoms = get_atoms(clause)
        if not phi_atoms.issuperset(clause_atoms):
            raise ValueError(
                "The clause must be on the same atoms as the encoded formula.\n"
                "The atoms in the clause are: {}\n"
                "The atoms in the encoded formula are: {}".format(clause_atoms, phi_atoms))
        return clause

    @final
    def check_entail_clause(self, clause_files: List[str],timeout:int=600) -> List[bool|None]:
        """function to check if the encoded formula entails the clause specifoied in the clause_file

        Args:
            clause_file (List[str]): the path to the smt2 files containing the clauses to check
            timeout (int) [600]: the timeout for the entailment check in seconds. Defaults to 600. 

        Returns:
            List[bool|None]: For each clause, True if the clause is entailed, False otherwise, None if some error occurs
        """
        self.details["entailment"] ={}
        results = []
        for clause_file in clause_files:
            if not os.path.isfile(clause_file):
                print(f"File not found: {clause_file}")
                results.append(None)
                continue
            self.details["entailment"][clause_file] = {}
            clause = self._clause_file_can_entail(clause_file)
            self.details["entailment"][clause_file]["entailment clause"] = str(clause)
            start_time = time.time()
            try:
                with time_limit(timeout):
                    result, load_time = self._check_entail_clause_body(clause)
            except LocalTimeoutException:
                self.details["entailment"][clause_file]["clause entailment result"] = "timeout"
                results.append(None)
                continue
            self.details["entailment"][clause_file]["clause entailment result"] = result
            self.details["entailment"][clause_file]["clause entailment time"] = time.time() - start_time - load_time
            results.append(result)
        return results

    @abstractmethod
    def _check_entail_clause_random_body(self, clause_items: List[Tuple[object, bool]]) -> Tuple[bool, float]:
        """where the actual entailment checking for random clauses is done

        Args:
            clause_items (List[Tuple[object,bool]]): the items in the clause

        Returns:
            Tuple[bool,float]: the result of the entailment checking and the time taken to load the structure"""
        raise NotImplementedError()

    @final
    def check_entail_clause_random(self, random_seed: int | None = None) -> bool:
        """
        function to check if the encoded formula entails a random clause

        Args:
            random_seed (int | None) [None]: the seed to use for the random clause generation. Defaults to None.

        Returns:
            bool: True if the clause is entailed, False otherwise
        """
        start_time = time.time()
        if random_seed is None:
            seed = int(time.time())
        else:
            seed = random_seed
        self.details["random clause seed"] = seed
        clause_items = select_random_items(
            self.refinement_mapping.keys(), random_seed=seed)
        self.details["random entailment clause"] = str(self._get_refinement_clause(
            clause_items).serialize())
        result, load_time = self._check_entail_clause_random_body(clause_items)
        self.details["random clause entailment result"] = result
        self.details["random clause entailment time"] = time.time() - start_time - load_time
        return result

    @final
    def _get_refinement_clause(self, clause_items: List[Tuple[object, bool]]) -> FNode:
        """
        function to get the refinement clause from the clause items

        Args:
            clause_items (List[Tuple[object,bool]]): the items in the clause

        Returns:
            FNode: the refinement clause
        """
        nodes = [self.refinement_mapping[x[0]] if x[1] else Not(
            self.refinement_mapping[x[0]]) for x in clause_items]
        return Or(*nodes)

    @abstractmethod
    def _check_entail_clause_body(self, clause: FNode) -> Tuple[bool, float]:
        """where the actual entailment checking for clauses is done

        Returns:
            Tuple[bool,float]: the result of the entailment checking and the time taken to load the structure"""
        raise NotImplementedError()

    @final
    def _term_file_can_be_implicant(self, term_file: str) -> FNode:
        """checks if the provided input file can be used to query for implicant

        raises exceptions if something is wrong with the file or its contents

        Args:
            term_file (str): the path to the term file

        Returns:
            (FNode): the correctly formatted term provided as input"""
        term = read_phi(term_file)

        # normalize the term
        term.simplify()
        term = get_normalized(term, self.normalizer_solver.get_converter())
        term = without_double_neg(term)

        if not is_term(term):
            raise ValueError(
                "The term must be a literal which is an atom or a negated atom")

        # check that the term is on the same atoms as phi
        phi_atoms = set()
        for value in self.abstraction_mapping.keys():
            phi_atoms.add(get_atoms(value)[0])
        phi_atoms = frozenset(phi_atoms)
        term_atom = get_atoms(term)[0]
        if term_atom not in phi_atoms:
            raise ValueError(
                "The clause must be on the same atoms as the encoded formula")

        return term

    @final
    def check_implicant(
            self,
            term_file: str,
            timeout:int=600) -> bool:
        """function to check if the term specified in term_file is an implicant for the encoded formula

        Args:
            term_file (str): the path to the smt2 file containing the term to check
            timeout (int) [600]: the timeout for the implicant check in seconds. Defaults to 600.

        Returns:
            bool: True if the term is an implicant, False otherwise
        """
        term = self._term_file_can_be_implicant(term_file)
        self.details["implicant term"] = str(term)
        start_time = time.time()
        try:
            with time_limit(600):
                result, loading_time = self._check_implicant_body(term)
        except LocalTimeoutException:
            self.details["implicant result"] = "timeout"
            return False
        self.details["implicant result"] = result
        self.details["implicant time"] = time.time() - start_time - loading_time
        return result

    @abstractmethod
    def _check_implicant_body(self, term: FNode) -> Tuple[bool, float]:
        """where the actual implicant checking is done

        Returns:
            Tuple[bool,float]: the result of the implicant checking and the time taken to load the structure"""
        raise NotImplementedError()

    @abstractmethod
    def _check_implicant_random_body(self, term_item: Tuple[object, bool]) -> Tuple[bool, float]:
        """where the actual implicant checking for random terms is done

        Args:
            term_item (Tuple[object,bool]): the term to check

        Returns:
            Tuple[bool,float]: the result of the implicant checking and the time taken to load the structure"""
        raise NotImplementedError()

    @final
    def check_implicant_random(self, random_seed: int | None = None) -> bool:
        """
        function to check if a random term is an implicant for the formula

        Args:
            random_seed (int | None) [None]: the seed to use for the random term generation. Defaults to None.

        Returns:
            bool: True if the term is an implicant, False otherwise
        """
        start_time = time.time()
        if random_seed is None:
            seed = int(time.time())
        else:
            seed = random_seed
        self.details["random term seed"] = seed
        term_item = select_random_items(
            self.refinement_mapping.keys(), random_seed=seed, amount=1)[0]
        refined_term = self.refinement_mapping[term_item[0]] if term_item[1] else Not(
            self.refinement_mapping[term_item[0]])
        self.details["random implicant term"] = str(refined_term.serialize())
        result, load_time = self._check_implicant_random_body(term_item)
        self.details["random implicant checking result"] = result
        self.details["random implicant checking time"] = time.time() - start_time - load_time
        return result

    @abstractmethod
    def _count_models(self) -> Tuple[int, float]:
        """function to count the number of models for the encoded formula

        Returns:
            int: the number of models for the encoded formula
            float: the structure loading time
        """
        raise NotImplementedError()

    @final
    def count_models(self, timeout:int=600) -> int:
        """function to count the number of models for the encoded formula

        Args:
            timeout (int) [600]: the timeout for the model counting in seconds. Defaults to 600.

        Returns:
            int: the number of models for the encoded formula
        """
        start_time = time.time()
        try:
            with time_limit(timeout):
                result, loading_time = self._count_models()
        except LocalTimeoutException:
            self.details["model count"] = "timeout"
            return 0
        result, loading_time = self._count_models()
        self.details["model count"] = result
        self.details["model count time"] = time.time() - start_time - loading_time
        return result

    @abstractmethod
    def _enumerate_models(self) -> float:
        """function to enumerate all models for the encoded formula

        Returns:
            float: the structure loading time
        """
        raise NotImplementedError()

    @final
    def enumerate_models(self,timeout:int=600) -> None:
        """function to enumerate all models for the encoded formula

        Args:
            timeout (int) [600]: the timeout for the model enumeration in seconds. Defaults to 600.
        """
        start_time = time.time()
        try:
            with time_limit(timeout):
                load_time = self._enumerate_models()
        except LocalTimeoutException:
            self.details["model enumeration time"] = "timeout"
            return
        self.details["model enumeration time"] = time.time() - start_time - load_time

    @final
    def _alpha_file_can_condition(self, alpha_file: str) -> FNode:
        """checks if the provided input file can be used to apply conditioning

        raises exceptions if something is wrong with the file or its contents

        Args:
            alpha_file (str): the path to the file where the conditioning atoms are specified

        Returns:
            (FNode): the correctly formatted cube provided as input"""
        alpha = read_phi(alpha_file)

        # normalize alpha
        alpha.simplify()
        alpha = get_normalized(alpha, self.normalizer_solver.get_converter())
        alpha = without_double_neg(alpha)

        if not is_term(alpha) and not is_cube(alpha):
            raise ValueError(
                "The alpha must be a literal or a conjunction of literals")

        # check that alpha is on the same atoms as phi
        phi_atoms = set()
        for value in self.abstraction_mapping.keys():
            phi_atoms.add(get_atoms(value)[0])
        phi_atoms = frozenset(phi_atoms)
        alpha_atoms = frozenset(get_atoms(alpha))
        if not phi_atoms.issuperset(alpha_atoms):
            raise ValueError(
                "Alpha must be on the same atoms as the encoded formula")

        return alpha

    @final
    def condition(
            self,
            alpha_file: str,
            timeout:int=600,
            output_file: str | None = None) -> None:
        """function to obtain [compiled formula | alpha], where alpha is a literal or a cube specified in the provided .smt2 file

        Args:
            alpha_file (str): the path to the smt2 file containing the literal (or conjunction of literals) to condition the compiled formula
            timeout (int) [600]: the timeout for the conditioning in seconds. Defaults to 600.
            output_file (str | None) [None]: the path to the .smt2 file where the conditioned compiled formula will be saved. Defaults to None.
        """
        alpha = self._alpha_file_can_condition(alpha_file)
        start_time = time.time()
        self.details["conditioning cube"] = str(alpha)
        try:
            with time_limit(timeout):
                self._condition_body(alpha, output_file)
        except LocalTimeoutException:
            self.details["conditioning time"] = "timeout"
            return
        self.details["conditioning time"] = time.time() - start_time

    @abstractmethod
    def _condition_body(self, alpha: FNode, output_file: str | None) -> float:
        """where the actual conditioning is done

        Returns:
            float: the structure loading time"""
        raise NotImplementedError()

    @abstractmethod
    def _condition_random_body(self, cube_items: List[Tuple[object, bool]]) -> float:
        """where the actual conditioning on random items is done

        Args:
            cube_items (List[Tuple[object,bool]]): the items in the cube
        
        Returns:
            float: the structure loading time"""
        raise NotImplementedError()

    @final
    def condition_random(self, random_seed: int | None = None) -> None:
        """
        function to condition the formula with a random cube

        Args:
            random_seed (int | None) [None]: the seed to use for the random cube generation. Defaults to None.
        """
        start_time = time.time()
        if random_seed is None:
            seed = int(time.time())
        else:
            seed = random_seed
        self.details["random cube seed"] = seed
        clause_items = select_random_items(
            self.refinement_mapping.keys(), random_seed=seed)
        self.details["random conditioning cube"] = str(self._get_refinement_cube(
            clause_items).serialize())
        load_time = self._condition_random_body(clause_items)
        self.details["random conditioning time"] = time.time() - start_time - load_time

    @final
    def _get_refinement_cube(self, cube_items: List[Tuple[object, bool]]) -> FNode:
        """
        function to get the refinement cube from the cube items

        Args:
            cube_items (List[Tuple[object,bool]]): the items in the cube

        Returns:
            FNode: the refinement cube
        """
        nodes = [self.refinement_mapping[x[0]] if x[1] else Not(
            self.refinement_mapping[x[0]]) for x in cube_items]
        return And(*nodes)

    @abstractmethod
    def check_entail(self, data_folder: str) -> bool:
        """function to check entailment of the compiled formula with respect to the data in data_folder.
        The data in data folder must be of the correct format, which is the same of for the queried structure

        Args:
            data_folder (str): the path to the folder where the data is stored

        Returns:
            bool: True if the compiled formula entails the data, False otherwise
        """

        raise NotImplementedError()

    @abstractmethod
    def conjunction(self, data_folder: str, output_path: str | None = None) -> None:
        """function to compute the conjunction of the compiled formula the data in data_folder.
        The data in data folder must be of the correct format, which is the same of for the queried structure

        Args:
            data_folder (str): the path to the folder where the data is stored
            output_path (str | None) [None]: the path to the file where the conjunction will be saved
        """
        raise NotImplementedError()

    @abstractmethod
    def disjunction(self, data_folder: str, output_path: str | None = None) -> None:
        """function to compute the disjunction of the compiled formula the data in data_folder.
        The data in data folder must be of the correct format, which is the same of for the queried structure

        Args:
            data_folder (str): the path to the folder where the data is stored
            output_path (str | None) [None]: the path to the file where the disjunction will be saved
        """
        raise NotImplementedError()

    @abstractmethod
    def negation(self, output_path: str | None = None) -> None:
        """function to compute the negation of the compiled formula

        Args:
            output_path (str | None) [None]: the path to the file where the negation will be saved
        """
        raise NotImplementedError()

    @final
    def get_details(self) -> Dict[str, object]:
        """function to get the details of the last query

        Returns:
            Dict[str,object]: the details of the last query"""
        return self.details
