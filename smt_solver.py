'''this module handles interactions with the mathsat solver'''

from typing import List, Dict
from pysmt.shortcuts import Solver, Iff
from pysmt.fnode import FNode
import mathsat

SAT = True
UNSAT = False


def _allsat_callback(model, converter, models):
    py_model = {converter.back(v) for v in model}
    models.append(py_model)
    return 1


class SMTSolver:
    '''A wrapper for the mathsat T-solver'''

    def __init__(self) -> None:
        solver_options_dict = {
            "dpll.allsat_minimize_model": "false",  # - truth assignment totali
            # "dpll.allsat_allow_duplicates": "false", # - per produrre truth assignment non necessariamente disjoint.
            #                                          # ha senso metterla a true solo se minimize_model=true.
            # - necessari per disabilitare step di preprocessing fatti
            "preprocessor.toplevel_propagation": "false",
            "preprocessor.simplification": "0",  # da mathsat
            "dpll.store_tlemmas": "true",  # - necessario per ottenere t-lemmi
        }
        self.solver = Solver("msat", solver_options=solver_options_dict)
        self._last_phi = None
        self._tlemmas = []
        self._models = []
        self._converter = self.solver.converter

    def check_all_sat(self, phi: FNode, boolean_mapping: Dict[FNode, FNode] = None) -> bool:
        '''computes All-SAT for the SMT-formula phi'''
        self._last_phi = phi

        # atoms = phi.get_atoms()

        self.solver.add_assertion(phi)

        if not boolean_mapping is None:
            for k, v in boolean_mapping.items():
                self.solver.add_assertion(Iff(k, v))

        self._models = []
        mathsat.msat_all_sat(self.solver.msat_env(),
                             # self.get_converted_atoms(atoms),
                             self.get_converted_atoms(
                                 list(boolean_mapping.keys())),
                             callback=lambda model: _allsat_callback(model, self._converter, self._models))
        self._tlemmas = [self._converter.back(
            l) for l in mathsat.msat_get_theory_lemmas(self.solver.msat_env())]
        if len(self._models) == 0:
            return UNSAT
        return SAT

    def get_theory_lemmas(self) -> List[FNode]:
        '''Returns the theory lemmas found during the All-SAT computation'''
        return self._tlemmas

    def get_models(self) -> List:
        '''Returns the models found during the All-SAT computation'''
        return self._models

    def get_converter(self):
        '''Returns the converter used for the normalization of T-atoms'''
        return self._converter

    def get_converted_atoms(self, atoms):
        '''Returns a list of normalized atoms'''
        return [self._converter.convert(a) for a in atoms]
