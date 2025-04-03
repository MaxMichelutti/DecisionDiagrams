"""module where all the queries functions are defined"""

import time
from typing import Dict, List, Tuple

from pysmt.fnode import FNode

from theorydd.tdd.theory_sdd import TheorySDD

from src.query.util import indexes_from_mapping, is_tsdd_loading_folder_correct
from src.query.query_interface import QueryInterface


class TSDDQueryManager(QueryInterface):
    """manager to handle all queries on T-SDDs"""

    def __init__(
            self,
            source_folder: str,
            refinement_mapping: Dict[str, FNode] | None = None,
            abstraction_mapping: Dict[FNode, str] | None = None):
        """
        initialize the manager
        Always provide either the refinement_mapping or the abstraction_mapping or both when initializing the object,
        otherwise a ValueError will be raises

        Args:
            source_folder (str): the path to the folder where the serialized compiled formula is stored
            refinement_mapping (Dict[int, FNode]) [None]: the mapping of the indices on the compiled formula's abstraction to the atoms in its refinement
            abstraction_mapping (Dict[FNode, int]) [None]: the mapping of the atoms of the formula to the indices in the compiled formula's abstraction
        """
        super().__init__(source_folder, refinement_mapping, abstraction_mapping)

        start_time = time.time()
        self.tsdd = self._load_tsdd()
        self.loading_time = time.time() - start_time
        self.details["loading time"] = self.loading_time

    def _load_tsdd(self) -> TheorySDD:
        """function to load the T-SDD from the serialized files"""
        return TheorySDD(None, folder_name=self.source_folder, solver=self.normalizer_solver)

    def _check_consistency(self) -> Tuple[bool, float]:
        """function to check if the encoded formula is consistent

        Returns:
            bool: True if the formula is consistent, False otherwise
            float: the structure loading time"""
        # load TSDD
        start_time = time.time()
        tsdd = self._load_tsdd()
        load_time = time.time() - start_time

        # check consistency
        consistency = tsdd.is_sat()

        return consistency, load_time

    def _check_validity(self) -> Tuple[bool, float]:
        """function to check if the encoded formula is valid

        Returns:
            bool: True if the formula is valid, False otherwise
            float: the structure loading time"""
        # load TSDD
        start_time = time.time()
        tsdd = self._load_tsdd()
        load_time = time.time() - start_time

        # check validity
        validity = tsdd.is_valid()

        return validity, load_time

    def _check_entail_clause_body(self, clause: FNode) -> Tuple[bool, float]:
        """function to check if the encoded formula entails the given clause

        Args:
            clause (FNode): the clause to check for entailment

        Returns:
            bool: True if the formula entails the clause, False otherwise
            float: the structure loading time
        """
        # RETRIEVE THE INDEXES ON WHICH TO OPERATE
        clause_indexes = indexes_from_mapping(clause, self.abstraction_mapping)

        # clause_items = [(item[0] if item[1] else -item[0], item[1]) for item in clause_indexes]
        clause_items = [(item if item > 0 else -item, item > 0) for item in clause_indexes]

        return self._check_entail_clause_random_body(clause_items)

    def _check_entail_clause_random_body(self, clause_items: List[Tuple[int,bool]]) -> Tuple[bool, float]:
        """function to check if the encoded formula entails the given clause

        Args:
            clause_items (List[Tuple[int,bool]]): the clause to check for entailment

        Returns:
            bool: True if the formula entails the clause, False otherwise
            float: the structure loading time
        """
        clause_items_negated = [(item[0], not item[1]) for item in clause_items]

        clause_items_negated_indexes = [item[0] if item[1] else -item[0] for item in clause_items_negated]

        # LOAD THE T-SDD
        start_time = time.time()
        tsdd = self._load_tsdd()
        load_time = time.time() - start_time

        # CONDITION OVER CLAUSE ITEMS NEGATED
        self._condition_tsdd(tsdd, clause_items_negated_indexes)
        # CHECK IF THE CONDITIONED T-SDD IS UNSAT
        consistency = tsdd.is_sat()
        # IF THE CONDITIONED T-SDD IS UNSAT, THEN THE FORMULA ENTAILS THE CLAUSE
        entailment = not consistency

        return entailment, load_time

    def _check_implicant_body(
            self,
            term: FNode) -> Tuple[bool, float]:
        """function to check if the term is an implicant for the encoded formula

        Args:
            term (FNode): the term to check

        Returns:
            bool: True if the term is an implicant, False otherwise
            float: the structure loading time
        """
        # RETRIEVE THE INDEX ON WHICH TO OPERATE
        term_index = indexes_from_mapping(term, self.abstraction_mapping)[0]

        term_item = (term_index[0] if term_index[1] else -term_index[0], term_index[1])

        return self._check_implicant_random_body(term_item)
        

    def _check_implicant_random_body(self, term_item: Tuple[int,bool]) -> Tuple[bool,float]:
        """function to check if the term is an implicant for the encoded formula
        
        Args:
            term_item (Tuple[int,bool]): the term to check
            
        Returns:
            bool: True if the term is an implicant, False otherwise
            float: the structure loading time
        """
        term_index = term_item[0] if term_item[1] else -term_item[0]

        # LOAD THE T-SDD
        start_time = time.time()
        tsdd = self._load_tsdd()
        load_time = time.time() - start_time

        # CONSTRUCT TSDD | term
        tsdd.condition(term_index)
        # CHECK IF THE CONDITIONED T-SDD IS VALID
        validity = tsdd.is_valid()
        # IF THE CONDITIONED T-SDD IS VALID, THEN THE TERM IS AN IMPLICANT
        implicant = validity

        return implicant, load_time


    def _count_models(self) -> Tuple[int, float]:
        """function to count the number of models for the encoded formula

        Returns:
            int: the number of models for the encoded formula
            float: the structure loading time
        """
        start_time = time.time()
        tsdd = self._load_tsdd()
        load_time = time.time() - start_time

        # count models
        model_count = tsdd.count_models()

        return model_count, load_time

    def _enumerate_models(self) -> float:
        """function to enumerate all models for the encoded formula

        Returns:
            float: the structure loading time
        """
        start_time = time.time()
        tsdd = self._load_tsdd()
        load_time = time.time() - start_time

        # enumerate models
        for model in tsdd.pick_all_iter():
            print(model)

        return load_time

    def _condition_body(
            self,
            alpha: FNode,
            output_file: str | None = None) -> float:
        """function to obtain [compiled formula | alpha], where alpha is a literal or a cube

        Args:
            alpha (FNode): the literal (or conjunction of literals) to condition the T-SDD
            output_file (str, optional): the path to the .smt2 file where the conditioned T-SDD will be saved. Defaults to None.

        Returns:
            float: the structure loading time
        """
        # RETRIEVE THE INDEXES ON WHICH TO OPERATE
        alpha_items = indexes_from_mapping(alpha, self.abstraction_mapping)

        # LOAD THE T-SDD
        start_time = time.time()
        tsdd = self._load_tsdd()
        load_time = time.time() - start_time

        # CONDITION THE T-SDD
        self._condition_tsdd(tsdd, alpha_items)

        # SAVE CONDITIONED TSDD
        if output_file is not None:
            tsdd.save_to_folder(output_file)

        return load_time
    
    def _condition_random_body(self, cube_items: List[Tuple[int,bool]]) -> float:
        """function to obtain [compiled formula | alpha], where alpha is a literal or a cube
        described by the given cube_items
        
        Args:
            cube_items (List[Tuple[int,bool]]): the literal (or conjunction of literals) to condition the T-SDD
        
        Returns:
            float: the structure loading time
        """
        alpha_indexes = [item[0] if item[1] else -item[0] for item in cube_items]

        # LOAD THE T-SDD
        start_time = time.time()
        tsdd = self._load_tsdd()
        load_time = time.time() - start_time

        # CONDITION THE T-SDD
        self._condition_tsdd(tsdd, alpha_indexes)

        return load_time

    def _condition_tsdd(self, tsdd: TheorySDD, items: List[str]) -> None:
        """function to condition the T-SDD with the given items

        Args:
            tsdd (TheorySDD): the T-SDD to condition
            items (List[str]): the items to condition the T-SDD with
        """
        for item in items:
            tsdd.condition(item)

    def check_entail(self, data_folder: str) -> bool:
        """function to check entailment of the compiled formula with respect to the data in data_folder.
        The data in data folder must be of the correct format, which is the same of for the queried structure

        Args:
            data_folder (str): the path to the folder where the data is stored

        Returns:
            bool: True if the compiled formula entails the data, False otherwise
        """
        if not is_tsdd_loading_folder_correct(data_folder):
            raise ValueError(
                "The data folder is not in the correct format fro T-SDDs")
        raise NotImplementedError()

    def conjunction(self, data_folder: str, output_path: str | None = None) -> None:
        """function to compute the conjunction of the compiled formula the data in data_folder.
        The data in data folder must be of the correct format, which is the same of for the queried structure

        Args:
            data_folder (str): the path to the folder where the data is stored
            output_path (str | None) [None]: the path to the file where the conjunction will be saved
        """
        if not is_tsdd_loading_folder_correct(data_folder):
            raise ValueError(
                "The data folder is not in the correct format fro T-SDDs")
        raise NotImplementedError()

    def disjunction(self, data_folder: str, output_path: str | None = None) -> None:
        """function to compute the disjunction of the compiled formula the data in data_folder.
        The data in data folder must be of the correct format, which is the same of for the queried structure

        Args:
            data_folder (str): the path to the folder where the data is stored
            output_path (str | None) [None]: the path to the file where the disjunction will be saved
        """
        if not is_tsdd_loading_folder_correct(data_folder):
            raise ValueError(
                "The data folder is not in the correct format fro T-SDDs")
        raise NotImplementedError()

    def negation(self, output_path: str | None = None) -> None:
        """function to compute the negation of the compiled formula

        Args:
            output_path (str | None) [None]: the path to the file where the negation will be saved
        """
        raise NotImplementedError()
