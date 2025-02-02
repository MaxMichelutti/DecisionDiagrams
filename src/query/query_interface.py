"""interface for all Query objects"""

from abc import ABC, abstractmethod
from typing import Dict, final

from pysmt.fnode import FNode

from theorydd.solvers.mathsat_total import MathSATTotalEnumerator
from theorydd.formula import get_normalized, get_atoms, without_double_neg, read_phi

from src.query.util import is_clause, is_cube, is_term, normalize_refinement


class QueryInterface(ABC):
    """interface for all Query objects"""

    source_folder: str
    refinement_mapping: Dict[object, FNode]
    abstraction_mapping: Dict[FNode, object]
    # solver used for normalization of input
    normalizer_solver: MathSATTotalEnumerator

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
        if(self.source_folder.endswith("/")):
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
            v: k for k, v in refinement_mapping.items()}

    @abstractmethod
    def check_consistency(self) -> bool:
        """function to check if the encoded formula is consistent

        Returns:
            bool: True if the formula is consistent, False otherwise"""
        raise NotImplementedError()

    @abstractmethod
    def check_validity(self) -> bool:
        """function to check if the encoded formula is valid

        Returns:
            bool: True if the formula is valid, False otherwise"""
        raise NotImplementedError()

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
        clause_atoms = frozenset(get_atoms(clause))
        if not phi_atoms.issuperset(clause_atoms):
            raise ValueError(
                "The clause must be on the same atoms as the encoded formula")
        return clause

    @final
    def check_entail_clause(self, clause_file: str) -> bool:
        """function to check if the encoded formula entails the clause specifoied in the clause_file

        Args:
            clause_file (str): the path to the smt2 file containing the clause to check

        Returns:
            bool: True if the clause is entailed bt the T-dDNNF, False otherwise
        """
        return self._check_entail_clause_body(self._clause_file_can_entail(clause_file))

    @abstractmethod
    def _check_entail_clause_body(self, clause: FNode) -> bool:
        """where the actual entailment checking for clauses is done"""
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
            term_file: str) -> bool:
        """function to check if the term specified in term_file is an implicant for the encoded formula

        Args:
            term_file (str): the path to the smt2 file containing the term to check

        Returns:
            bool: True if the term is an implicant, False otherwise
        """
        return self._check_implicant_body(self._term_file_can_be_implicant(term_file))

    @abstractmethod
    def _check_implicant_body(self, term: FNode) -> bool:
        """where the actual implicant checking is done"""
        raise NotImplementedError()

    @abstractmethod
    def count_models(self) -> int:
        """function to count the number of models for the encoded formula

        Returns:
            int: the number of models for the encoded formula
        """
        raise NotImplementedError()

    @abstractmethod
    def enumerate_models(self) -> None:
        """function to enumerate all models for the encoded formula
        """
        raise NotImplementedError()

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
            output_file: str | None = None) -> None:
        """function to obtain [compiled formula | alpha], where alpha is a literal or a cube specified in the provided .smt2 file

        Args:
            alpha_file (str): the path to the smt2 file containing the literal (or conjunction of literals) to condition the compiled formula
            output_file (str | None) [None]: the path to the .smt2 file where the conditioned compiled formula will be saved. Defaults to None.
        """
        alpha = self._alpha_file_can_condition(alpha_file)
        self._condition_body(alpha, output_file)

    @abstractmethod
    def _condition_body(self, alpha: FNode, output_file: str | None) -> None:
        """where the actual conditioning is done"""
        raise NotImplementedError()

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
