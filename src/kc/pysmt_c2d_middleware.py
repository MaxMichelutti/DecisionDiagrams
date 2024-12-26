"""midddleware for pysmt-c2d compatibility"""

import random
import os
import time
from typing import Dict, List, Tuple
from pysmt.shortcuts import (
    write_smtlib,
    read_smtlib,
    And,
    Or,
    get_atoms,
    TRUE,
    FALSE,
    Not,
)
from pysmt.fnode import FNode
from allsat_cnf.label_cnfizer import LabelCNFizer
from theorydd.formula import save_refinement,load_refinement, get_phi_and_lemmas as _get_phi_and_lemmas

# load c2d executable location from dotenv
from dotenv import load_dotenv as _load_env

from src.kc.ddnnf_compiler import DDNNFCompiler
_load_env()
_C2D_EXECUTABLE = os.getenv("C2D_BINARY")

# fix command to launch c2d compiler
if _C2D_EXECUTABLE is not None and os.path.isfile(_C2D_EXECUTABLE) and not _C2D_EXECUTABLE.startswith("."):
    if _C2D_EXECUTABLE.startswith("/"):
        _C2D_EXECUTABLE = f".{_C2D_EXECUTABLE}"
    else:
        _C2D_EXECUTABLE = f"./{_C2D_EXECUTABLE}"

class C2DCompiler(DDNNFCompiler):
    
    def __init__(self):
        super().__init__()

    def from_smtlib_to_dimacs_file(
        self,
        phi: FNode,
        dimacs_file: str,
        tlemmas: List[FNode] | None = None,
        quantification_file: str = "quantification.exist",
    ) -> None:
        """
        translates an SMT formula in DIMACS format and saves it on file.
        All fresh variables are saved inside quantification_file.
        The mapping use to translate the formula is then returned.

        This function also resets the abstraction and refinement functions.

        Args:
            phi (FNode) -> the pysmt formula to be translated
            dimacs_file (str) -> the path to the file where the dimacs output need to be saved
            tlemmas (List[FNode] | None) -> a list of theory lemmas to be added to the formula
            quantification_file (str) -> the path to the file where the quantified variables
                need to be saved
        """
        if tlemmas is None:
            phi_and_lemmas = phi
        else:
            phi_and_lemmas = _get_phi_and_lemmas(phi, tlemmas)
        phi_cnf: FNode = LabelCNFizer().convert_as_formula(phi_and_lemmas)
        phi_atoms: frozenset = get_atoms(phi)
        phi_cnf_atoms: frozenset = get_atoms(phi_cnf)
        fresh_atoms: List[FNode] = list(phi_cnf_atoms.difference(phi_atoms))
        
        count = 1
        self.abstraction = {}
        self.refinement = {}
        for atom in phi_cnf_atoms:
            self.abstraction[atom] = count
            self.refinement[count] = atom
            count += 1

        # check if formula is top
        if phi_cnf.is_true():
            self.write_dimacs_true(dimacs_file)
            return

        # check if formula is bottom
        if phi_cnf.is_false():
            self.write_dimacs_false(dimacs_file)
            return

        # CONVERTNG IN DIMACS FORMAT AND SAVING ON FILE
        self.write_dimacs(dimacs_file, phi_cnf, fresh_atoms)

        # SAVING QUANTIFICATION FILE
        self._save_quantification_file(quantification_file, fresh_atoms)

        # SAVING QUANTIFICATION FILE
    def _save_quantification_file(self, quantification_file: str, fresh_atoms: List[FNode]) -> None:
        with open(quantification_file, "w", encoding="utf8") as quantification_out:
            quantified_indexes = [str(self.abstraction[atom]) for atom in fresh_atoms]
            quantified_indexes_str: str = " ".join(quantified_indexes)
            quantification_out.write(
                f"{len(quantified_indexes)} {quantified_indexes_str}")


    def from_nnf_to_pysmt(self,nnf_file: str) -> Tuple[FNode,int,int]:
        """
        Translates the formula contained in the file c2d_file from nnf format to a pysmt FNode

        Args:
            c2d_file (str) -> the path to the file where the dimacs output need to be saved

        Returns:
            (FNode,int,int) -> the pysmt formula, the total nodes and the total edges of the formula
        """
        with open(nnf_file, "r", encoding="utf8") as data:
            contents = data.read()
        lines: List[str] = contents.split("\n")
        lines = list(filter(lambda x: x != "", lines))
        pysmt_nodes: List[FNode] = []
        total_nodes = 0
        total_edges = 0
        for line in lines:
            if line.startswith("nnf "):
                # I DO NOT CARE ABOUT THIS DATA FOR PARSING
                continue
            elif line.startswith("A "):
                # AND node
                total_nodes += 1
                if line.startswith("A 0"):
                    pysmt_nodes.append(TRUE())
                    continue
                tokens = line.split(" ")[2:]
                and_nodes = [pysmt_nodes[int(t)] for t in tokens]
                total_edges += len(and_nodes)
                if len(and_nodes) == 1:
                    pysmt_nodes.append(and_nodes[0])
                    continue
                pysmt_nodes.append(And(*and_nodes))
            elif line.startswith("O "):
                # OR node
                total_nodes += 1
                tokens = line.split(" ")[1:]
                _j = tokens[0]
                tokens = tokens[1:]
                c = tokens[0]
                tokens = tokens[1:]
                if c == "0":
                    pysmt_nodes.append(FALSE())
                    continue
                or_nodes = [pysmt_nodes[int(t)] for t in tokens]
                total_edges += len(or_nodes)
                if len(or_nodes) == 1:
                    pysmt_nodes.append(or_nodes[0])
                    continue
                pysmt_nodes.append(Or(*or_nodes))
            elif line.startswith("L "):
                # LITERAL
                total_nodes += 1
                tokens = line.split(" ")[1:]
                variable = int(tokens[0])
                if variable > 0:
                    pysmt_nodes.append(self.refinement[variable])
                else:
                    pysmt_nodes.append(Not(self.refinement[abs(variable)]))
        return pysmt_nodes[len(pysmt_nodes) - 1], total_nodes, total_edges


    def count_nodes_and_edges_from_nnf(self,nnf_file: str) -> Tuple[int, int]:
        """
        Counts nodes and edges of the formula contained in the file c2d_file from nnf format to a pysmt FNode

        Args:
            nnf_file (str) -> the path to the file where the dimacs output needs to be saved

        Returns:
            (int,int) -> the total nodes and edges of the formula (#nodes,#edges)
        """
        total_nodes = 0
        total_edges = 0
        with open(nnf_file, "r", encoding="utf8") as data:
            contents = data.read()
        lines: List[str] = contents.split("\n")
        lines = list(filter(lambda x: x != "", lines))
        for line in lines:
            if line.startswith("nnf "):
                # I DO NOT CARE ABOUT THIS DATA FOR PARSING
                continue
            elif line.startswith("A "):
                # AND node
                total_nodes += 1
                if line.startswith("A 0"):
                    continue
                tokens = line.split(" ")[2:]
                and_nodes = [int(t) for t in tokens]
                total_edges += len(and_nodes)
            elif line.startswith("O "):
                # OR node
                total_nodes += 1
                tokens = line.split(" ")[1:]
                _j = tokens[0]
                tokens = tokens[1:]
                c = tokens[0]
                tokens = tokens[1:]
                if c == "0":
                    continue
                or_nodes = [int(t) for t in tokens]
                total_edges += len(or_nodes)
            elif line.startswith("L "):
                # LITERAL
                total_nodes += 1
        return (total_nodes, total_edges)


    def compile_dDNNF(
        self,
        phi: FNode,
        tlemmas: List[FNode] | None = None,
        save_path: str | None = None,
        back_to_fnode: bool = False,
        verbose: bool = False,
        computation_logger: Dict | None = None,
        timeout: int = 3600
    ) -> Tuple[FNode | None, int, int]:
        """
        Compiles an FNode in dDNNF through the c2d compiler

        Args:
            phi (FNode) -> a pysmt formula
            tlemmas (List[FNode] | None) -> a list of theory lemmas to be added to the formula
            save_path (str | None) -> the path where the dDNNF will be saved
            back_to_fnode (bool) -> if True, the function returns the pysmt formula
            verbose (bool) -> if True, the function prints the steps of the computation
            computation_logger (Dict | None) -> a dictionary to store the computation time
            timeout (int) -> the maximum time allowed for the computation

        Returns:
            Tuple[FNode,int,int] | None -> if back_to_fnode is set to True, the function returns:
            (FNode | None) -> the input pysmt formula in dDNNF, or None if back_to_fnode is False
            (int) -> the number of nodes in the dDNNF
            (int) -> the number of edges in the dDNNF
        """
        # check if c2d is available and executable
        if _C2D_EXECUTABLE is None or not os.path.isfile(_C2D_EXECUTABLE):
            raise FileNotFoundError(
                "The binary for the c2d compiler is missing. Please check the installation path and update the .env file.")
        if not os.access(_C2D_EXECUTABLE, os.X_OK):
            raise PermissionError(
                "The c2d binary is not executable. Please check the permissions for the file and grant execution rights.")

        # failsafe for computation_logger
        if computation_logger is None:
            computation_logger = {}

        computation_logger["dDNNF compiler"] = "c2d"

        # choose temporary folder
        if save_path is None:
            tmp_folder = "temp_" + str(random.randint(0, 9223372036854775807))
        else:
            tmp_folder = save_path

        # translate to CNF DIMACS and get mapping used for translation
        if not os.path.exists(tmp_folder):
            os.mkdir(tmp_folder)
        start_time = time.time()
        if verbose:
            print("Translating to DIMACS...")
        self.from_smtlib_to_dimacs_file(
            phi, f"{tmp_folder}/dimacs.cnf", tlemmas, f"{tmp_folder}/quantification.exist"
        )
        elapsed_time = time.time() - start_time
        computation_logger["DIMACS translation time"] = elapsed_time
        if verbose:
            print(f"DIMACS translation completed in {elapsed_time} seconds")

        # save mapping for refinement
        if not os.path.exists(f"{tmp_folder}/mapping"):
            os.mkdir(f"{tmp_folder}/mapping")
        if verbose:
            print("Saving refinement...")
        save_refinement(self.refinement, f"{tmp_folder}/mapping/mapping.json")
        if verbose:
            print("Refinement saved")

        # call c2d for compilation
        # output should be in file temp_folder/test_dimacs.cnf.nnf
        start_time = time.time()
        if verbose:
            print("Compiling dDNNF...")
        timeout_string = ""
        if timeout > 0:
            timeout_string = f"timeout {timeout}s "
        result = os.system(
            f"{timeout_string}{_C2D_EXECUTABLE} -in {tmp_folder}/dimacs.cnf -exist {tmp_folder}/quantification.exist > /dev/null"
        )
        if result != 0:
            raise TimeoutError("c2d compilation failed: timeout")
        elapsed_time = time.time() - start_time
        computation_logger["dDNNF compilation time"] = elapsed_time
        if verbose:
            print(f"dDNNF compilation completed in {elapsed_time} seconds")

        # return if not back to fnode
        if not back_to_fnode:
            nodes, edges = self.count_nodes_and_edges_from_nnf(f"{tmp_folder}/dimacs.cnf.nnf")
            return None, nodes, edges

        # translate to pysmt
        start_time = time.time()
        if verbose:
            print("Translating to pysmt...")
        result, nodes, edges = self.from_nnf_to_pysmt(
            f"{tmp_folder}/dimacs.cnf.nnf")
        # clean if necessary
        if os.path.exists(tmp_folder) and save_path is None:
            os.system(f"rm -rd {tmp_folder}")
        elapsed_time = time.time() - start_time
        computation_logger["pysmt translation time"] = elapsed_time
        if verbose:
            print(f"pysmt translation completed in {elapsed_time} seconds")
        return result, nodes, edges


    def load_dDNNF(self, nnf_path: str, mapping_path: str) -> FNode:
        """
        Load a dDNNF from file and translate it to pysmt

        Args:
            nnf_path (str) ->       the path to the file containing the dDNNF in 
                                    NNF format provided by the c2d compiler
            mapping_path (str) ->   the path to the file containing the mapping,
                                    which describes the refinement function

        Returns:
            (FNode) -> the pysmt formula translated from the dDNNF
        """
        self.refinement = load_refinement(mapping_path)
        self.abstraction = {v: k for k, v in self.refinement.items()}
        return self.from_nnf_to_pysmt(nnf_path)


if __name__ == "__main__":
    test_phi = read_smtlib("test.smt2")

    print(test_phi.serialize())

    c2d_compiler = C2DCompiler()

    phi_ddnnf, _a, _b = c2d_compiler.compile_dDNNF(test_phi, back_to_fnode=True)

    print(phi_ddnnf.serialize())
