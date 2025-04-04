"""module where all the queries functions are defined. These queries are executed through SMTsolver calls"""

import os
import time
from typing import List, Tuple

from pysmt.fnode import FNode
from pysmt.shortcuts import is_sat, Not, And, Or, Solver
import mathsat

from theorydd.formula import read_phi as _get_phi, save_phi as _save_phi, get_atoms as _get_atoms, get_normalized as _get_normalized
from theorydd.solvers.mathsat_total import MathSATTotalEnumerator

from src.query.query_interface import QueryInterface

class Timer(object): # pylint: disable=too-few-public-methods,locally-disabled
    """A simple timer object."""

    def __init__(self, timeout):
        """
        Timer Constructor.

        :param timeout: the number of seconds before a timeout.
        """
        self._timeout = timeout
        self._started = False
        self._start = 0.0
        self._end = 0.0

    def __call__(self):
        """
        Callback function.

        :returns: non-zero upon timeout.
        """
        now = time.time()
        if not self._started:
            self._started = now
        self._end = now
        ret = 0
        if self._end - self._started > self._timeout:
            ret = 1
        return ret

    def reset(self):
        """
        Reset the timer.
        """
        self._started = False
        return

class SMTQueryManager(QueryInterface):
    """manager to handle all queries using a SMT solver"""

    loading_time: float
    phi : FNode

    def __init__(
            self,
            source_file: str):
        """
        initialize the manager with the path to the source file

        Args:
            source_file (str): the path to a smt or smt2 file where an SMT formula is defined
        """
        super().__init__(source_file, {}, {})

        start_time = time.time()
        self.phi = _get_phi(source_file)
        self.loading_time = time.time() - start_time

        solver_options_dict = {
            "preprocessor.toplevel_propagation": "false",
            "preprocessor.simplification": "0",  # from mathsat
        }
        self.solver = Solver("msat", solver_options=solver_options_dict)

        phi_atoms = _get_atoms(self.phi)
        for atom in phi_atoms:
            norm_atom = _get_normalized(atom, self.normalizer_solver.get_converter())
            self.refinement_mapping[norm_atom] = norm_atom
        self.abstraction_mapping = self.refinement_mapping
        
        

    def _check_consistency(self) -> Tuple[bool, float]:
        """function to check if the encoded formula is consistent

        Returns:
            bool: True if the formula is consistent, False otherwise
            float: the structure loading time"""
        # load phi
        start_time = time.time()
        phi = _get_phi(self.source_folder)
        load_time = time.time() - start_time

        # check coinsistency by calling SMT solver
        is_satisfiable = is_sat(phi, solver_name="msat")

        return is_satisfiable, load_time

    def _check_validity(self) -> Tuple[bool, float]:
        """function to check if the encoded formula is valid

        Returns:
            bool: True if the formula is valid, False otherwise
            float: the structure loading time"""
        # load phi
        start_time = time.time()
        phi = _get_phi(self.source_folder)
        load_time = time.time() - start_time

        # check validity
        # if not phi is satisfiable, than the formula is not valid
        # this notion of validity is not completely
        # correct since we are checking boolean a validity
        # concept for a SMT formula
        is_valid = not is_sat(Not(phi), solver_name="msat")

        return is_valid, load_time

    def _check_entail_clause_body(self, clause: FNode) -> Tuple[bool|None, float]:
        """function to check if the encoded formula entails the given clause

        Args:
            clause (FNode): the clause to check for entailment

        Returns:
            bool|None: True if the formula entails the clause, False otherwise. None in case of timeout
            float: the structure loading time
        """
        # LOAD THE FORMULA
        # start_time = time.time()
        # phi = _get_phi(self.source_folder)
        # load_time = time.time() - start_time

        # # CHECK IF THE FORMULA ENTAILS THE CLAUSE
        # # phi and not clause must be unsatisfiable
        # entailment = not is_sat(And(phi, Not(clause)), solver_name="msat")
        self.solver.push()
        self.solver.add_assertion(Not(clause))
        check_sat_result = mathsat.msat_solve(self.solver.msat_env())
        if check_sat_result == 0:
            entailment = True
        elif check_sat_result == 1:
            entailment = False
        else:
            entailment = None
        self.solver.pop()
        return entailment, 0.0
    
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
        self.solver.add_assertion(self.phi)
        my_timer_callback = Timer(float(timeout))
        mathsat.msat_set_termination_test(self.solver.msat_env(), my_timer_callback)
        for clause_file in clause_files:
            if not os.path.isfile(clause_file):
                print(f"File not found: {clause_file}")
                results.append(None)
                continue
            self.details["entailment"][clause_file] = {}
            clause = self._clause_file_can_entail(clause_file)
            self.details["entailment"][clause_file]["entailment clause"] = str(clause)
            start_time = time.time()
            cur_result, load_time = self._check_entail_clause_body(clause)
            if cur_result is None:
                self.details["entailment"][clause_file]["clause entailment result"] = "timeout"
                results.append(None)
                continue
            self.details["entailment"][clause_file]["clause entailment result"] = cur_result
            self.details["entailment"][clause_file]["clause entailment time"] = time.time() - start_time - load_time
            results.append(cur_result)
        return results


    def _check_entail_clause_random_body(self, clause_items: List[Tuple[FNode, bool]]) -> Tuple[bool, float]:
        """function to check if the encoded formula entails the given clause

        Args:
            clause_items (List[Tuple[FNode, bool]]): the clause to check for entailment

        Returns:
            bool: True if the formula entails the clause, False otherwise
            float: the structure loading time
        """
        clause = self._get_refinement_clause(clause_items)
        return self._check_entail_clause_body(clause)

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
        # LOAD THE FORMULA
        start_time = time.time()
        phi = _get_phi(self.source_folder)
        load_time = time.time() - start_time

        # IMPLICANT = term -> phi
        # term and not phi must be unsatisfiable
        implicant = not is_sat(And(term, Not(phi)), solver_name="msat")

        return implicant, load_time
    
    def _check_implicant_random_body(self, term_item: Tuple[FNode, bool]) -> Tuple[bool, float]:
        """function to check if the term is an implicant for the encoded formula

        Args:
            term (FNode): the term to check

        Returns:
            bool: True if the term is an implicant, False otherwise
            float: the structure loading time
        """
        term = term_item[0] if term_item[1] else Not(term_item[0])
        return self._check_implicant_body(term)

    def _count_models(self) -> Tuple[int, float]:
        """function to count the number of models for the encoded formula

        Returns:
            int: the number of models for the encoded formula
            float: the structure loading time
        """
        # load phi
        start_time = time.time()
        phi = _get_phi(self.source_folder)
        load_time = time.time() - start_time

        # count models
        solver = MathSATTotalEnumerator()
        solver.check_all_sat(phi, boolean_mapping=None)
        models_total = len(solver.get_models())

        return models_total, load_time

    def _enumerate_models(self) -> float:
        """function to enumerate all models for the encoded formula

        Returns:
            float: the structure loading time
        """
        # load phi
        start_time = time.time()
        phi = _get_phi(self.source_folder)
        load_time = time.time() - start_time

        solver = MathSATTotalEnumerator()
        solver.check_all_sat(phi, boolean_mapping=None)
        models = solver.get_models()
        for model in models:
            print(model)

        return load_time

    def _condition_body(
            self,
            alpha: FNode,
            output_file: str | None = None) -> float:
        """function to obtain [compiled formula | alpha], where alpha is a literal or a cube

        Args:
            alpha (FNode): the literal (or conjunction of literals) to condition the SMT formula
            output_file (str, optional): the path to the folder where the conditioned formula will be saved. Defaults to None.

        Returns:
            float: the structure loading time
        """
        # load phi
        start_time = time.time()
        phi = _get_phi(self.source_folder)
        load_time = time.time() - start_time

        # condition the formula
        conditioned_formula = And(phi, alpha)

        # save the conditioned formula
        if output_file is not None:
            _save_phi(conditioned_formula, output_file)

        return load_time
    
    def _condition_random_body(self, cube_items: List[Tuple[FNode, bool]]) -> float:
        """function to obtain [compiled formula | alpha], where alpha is a literal or a cube

        Args:
            alpha (FNode): the literal (or conjunction of literals) to condition the SMT formula
        
        Returns:
            float: the structure loading time
        """
        alpha = self._get_refinement_cube(cube_items)
        return self._condition_body(alpha)

    def check_entail(self, data_folder: str) -> bool:
        """function to check entailment of the compiled formula with respect to the data in the file data_folder.

        Args:
            data_folder (str): the path to the file where the data is stored

        Returns:
            bool: True if the compiled formula entails the data, False otherwise
        """
        if not os.path.exists(data_folder):
            raise FileNotFoundError(f"Data file {data_folder} does not exist")
        if not data_folder.endswith(".smt2") and not data_folder.endswith(".smt"):
            raise ValueError("Data file must be in SMT or SMT2 format")

        start_time = time.time()
        phi = _get_phi(self.source_folder)
        load_time = time.time() - start_time

        data = _get_phi(data_folder)
        # ENTAILMENT: phi -> data
        # phi and not data must be unsatisfiable
        entailment = not is_sat(And(phi, Not(data)), solver_name="msat")
        entailment_time = time.time() - start_time - load_time

        return entailment

    def conjunction(self, data_folder: str, output_path: str | None = None) -> None:
        """function to compute the conjunction of the compiled formula the data in data_folder.

        Args:
            data_folder (str): the path to the file where the data is stored
            output_path (str | None) [None]: the path to the file where the conjunction will be saved
        """
        if not os.path.exists(data_folder):
            raise FileNotFoundError(f"Data file {data_folder} does not exist")
        if not data_folder.endswith(".smt2") and not data_folder.endswith(".smt"):
            raise ValueError("Data file must be in SMT or SMT2 format")

        # load phi
        start_time = time.time()
        phi = _get_phi(self.source_folder)
        load_time = time.time() - start_time

        data = _get_phi(data_folder)
        conjunction_formula = And(phi, data)
        conjunction_time = time.time() - start_time - load_time

        # save the conditioned formula
        if output_path is not None:
            _save_phi(conjunction_formula, output_path)

    def disjunction(self, data_folder: str, output_path: str | None = None) -> None:
        """function to compute the disjunction of the compiled formula the data in data_folder.

        Args:
            data_folder (str): the path to the file where the data is stored
            output_path (str | None) [None]: the path to the file where the disjunction will be saved
        """
        if not os.path.exists(data_folder):
            raise FileNotFoundError(f"Data file {data_folder} does not exist")
        if not data_folder.endswith(".smt2") and not data_folder.endswith(".smt"):
            raise ValueError("Data file must be in SMT or SMT2 format")
        # load phi
        start_time = time.time()
        phi = _get_phi(self.source_folder)
        load_time = time.time() - start_time

        data = _get_phi(data_folder)
        disjunction_formula = Or(phi, data)
        disjunction_time = time.time() - start_time - load_time

        # save the conditioned formula
        if output_path is not None:
            _save_phi(disjunction_formula, output_path)

    def negation(self, output_path: str | None = None) -> None:
        """function to compute the negation of the compiled formula

        Args:
            output_path (str | None) [None]: the path to the file where the negation will be saved
        """
        # load phi
        start_time = time.time()
        phi = _get_phi(self.source_folder)
        load_time = time.time() - start_time

        negation_formula = Not(phi)
        negation_time = time.time() - start_time - load_time

        # save the conditioned formula
        if output_path is not None:
            _save_phi(negation_formula, output_path)
