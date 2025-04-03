"""utility functions for query_ddnnf"""
import os
import random
from typing import Dict, List, Tuple
from pysmt.fnode import FNode
from pysmt.shortcuts import Not, Or
from theorydd.solvers.solver import SMTEnumerator
from theorydd.formula import get_normalized, get_atoms, save_phi, top, bottom, big_and, without_double_neg

import signal
from contextlib import contextmanager

class LocalTimeoutException(Exception): pass

@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise LocalTimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

class UnsupportedQueryException(Exception):
    """Exception raised when an unsupported query is called"""

    def __init__(self, message: str = "Unsupported query type"):
        super().__init__(message)


def check_executable(file_path: str) -> None:
    """function to check if a binary can be called, 
    raises exceptions if the reasoner cannot be called

    Args:
        file_path (str): the path to the reasoner

    Raises:
        ValueError: if the path to the reasoner is not provided
        FileNotFoundError: if the path to the reasoner is invalid
        PermissionError: if the reasoner is not executable"""
    if file_path is None:
        raise ValueError(
            "Please provide the path to the decdnnf reasoner in the .env file")
    if not os.path.isfile(file_path):
        raise FileNotFoundError(
            f"Invalid path to the ddnnf reasoner: {file_path}")
    if not os.access(file_path, os.X_OK):
        raise PermissionError(
            f"File {file_path} is not executable")


def is_tbdd_loading_folder_correct(folder: str) -> bool:
    """checks if the folder where the T-BDD files are stored 
    has all the required content to load the T-BDD

    Args:
        folder (str): the path to the folder where the T-BDD files are stored

    Returns:
        bool: True if the folder has all required files and subfolders, False otherwise
    """
    # check that the folder exists
    if not os.path.exists(folder):
        return False
    # trim if path finishes with / <-- done on arg parsing
    # if folder.endswith("/"):
    #     folder = folder[:-1]
    # check that bdd_data.dddmp exists
    if not os.path.exists(f"{folder}/tbdd_data.dddmp"):
        return False
    # check that bdd_data.pickle exists
    if not os.path.exists(f"{folder}/tbdd_data.pickle"):
        return False
    # check that abstraction.json exists
    if not os.path.exists(f"{folder}/abstraction.json"):
        return False
    # check that qvars.qvars exists
    if not os.path.exists(f"{folder}/qvars.qvars"):
        return False
    return True


def is_tsdd_loading_folder_correct(folder: str) -> bool:
    """checks if the folder where the T-SDD files are stored 
    has all the required content to load the T-SDD

    Args:
        folder (str): the path to the folder where the T-SDD files are stored

    Returns:
        bool: True if the folder has all required files and subfolders, False otherwise
    """
    # check that the folder exists
    if not os.path.exists(folder):
        return False
    # trim if path finishes with / <-- done on arg parsing
    # if folder.endswith("/"):
    #     folder = folder[:-1]
    # check that sdd.sdd exists
    if not os.path.exists(f"{folder}/sdd.sdd"):
        return False
    # check that vtree.vtree exists
    if not os.path.exists(f"{folder}/vtree.vtree"):
        return False
    # check that abstraction.json exists
    if not os.path.exists(f"{folder}/abstraction.json"):
        return False
    # check that qvars.qvars exists
    if not os.path.exists(f"{folder}/qvars.qvars"):
        return False
    return True


def is_d4_tddnnf_loading_folder_correct(folder: str) -> bool:
    """checks if the folder where the dDNNF files are stored 
    has all the required content to load the T-dDNNF

    This only works for dDNNFs generated by the D4 compiler

    Args:
        folder (str): the path to the folder where the dDNNF files are stored

    Returns:
        bool: True if the folder has all required files and subfolders, False otherwise
    """
    # check that the folder exists
    if not os.path.exists(folder):
        return False
    # trim if path finishes with / <-- done on arg parsing
    # if folder.endswith("/"):
    #     folder = folder[:-1]
    # check that mapping subfolder exists
    if not os.path.exists(os.path.join(folder, "mapping")):
        return False
    # check that the mapping subfolder has a mapping.json file
    if not os.path.exists(os.path.join(folder, "mapping/mapping.json")):
        return False
    # check that the mapping subfolder has a important_labels.json file
    if not os.path.exists(os.path.join(folder, "mapping/important_labels.json")):
        return False
    # check that the file compilation_output.nnf exists
    if not os.path.exists(os.path.join(folder, "compilation_output.nnf")):
        return False
    return True


def is_c2d_tddnnf_loading_folder_correct(folder: str) -> bool:
    """checks if the folder where the dDNNF files are stored 
    has all the required content to load the T-dDNNF

    This only works for dDNNFs generated by the C2D compiler

    Args:
        folder (str): the path to the folder where the dDNNF files are stored

    Returns:
        bool: True if the folder has all required files and subfolders, False otherwise
    """
    # check that the folder exists
    if not os.path.exists(folder):
        return False
    # trim if path finishes with / <-- done on arg parsing
    # if folder.endswith("/"):
    #     folder = folder[:-1]
    # check that mapping subfolder exists
    if not os.path.exists(os.path.join(folder, "mapping")):
        return False
    # check that the mapping subfolder has a mapping.json file
    if not os.path.exists(os.path.join(folder, "mapping/mapping.json")):
        return False
    # check that the file cdimacs.cnf.nnf exists
    if not os.path.exists(os.path.join(folder, "dimacs.cnf.nnf")):
        return False
    # check that the file quantification.exist exists
    if not os.path.exists(os.path.join(folder, "quantification.exist")):
        return False
    return True


def is_clause(clause: FNode) -> bool:
    """checks if the given formula is a clause

    Args:
        clause (FNode): the formula to check

    Returns:
        bool: True if the formula is a clause, False otherwise
    """
    if not clause.is_or():
        return False
    if clause.is_or():
        for arg in clause.args():
            if not is_term(arg):
                return False
    return True


def is_term(term: FNode) -> bool:
    """checks if the given formula is a term

    Args:
        term (FNode): the formula to check

    Returns:
        bool: True if the formula is a term, False otherwise
    """
    if term.is_not():
        return is_term(term.arg(0))
    if term.is_and() or term.is_or() or term.is_implies() or term.is_iff() or term.is_bool_constant():
        return False
    return True


def is_negated(term: FNode) -> bool:
    """checks if the given formula is a negated term

    Args:
        term (FNode): the formula to check

    Returns:
        bool: True if the formula is a negated term, False otherwise
    """
    if not term.is_not():
        return False
    if not is_term(term.arg(0)):
        return False
    return True


def is_cube(phi: FNode) -> bool:
    """checks if the given formula is a cube

    Args:
        phi (FNode): the formula to check

    Returns:
        bool: True if the formula is a cube, False otherwise
    """
    if not phi.is_and():
        return False
    for arg in phi.args():
        if not is_term(arg):
            return False
    return True


def normalize_refinement(refinement: Dict[int | str, FNode], normalizer_solver: SMTEnumerator) -> Dict[int | str, FNode]:
    """normalizes the mapping of the atoms to the indices (or aliases) in the compiled formula

    Args:
        refinement (Dict[int | str, FNode]): the mapping of the atoms to the indices (or aliases) in the compiled formula
        normalizer_solver (SMTEnumerator): the solver that needs to be used for the normalization of the mapping

    Returns:
        Dict[int, FNode]: the normalized mapping
    """
    normalized_mapping = {}
    for key, value in refinement.items():
        normalized_mapping[key] = get_normalized(
            value, normalizer_solver.get_converter())
    return normalized_mapping


# class NegatedMappingKeyException(Exception):
#     """Exception raised when the mapping contains negated atoms"""

#     def __init__(self, message: str = "Mapping contains negated atoms!!!"):
#         super().__init__(message)


def indexes_from_mapping(phi: FNode, abstraction: Dict[FNode, int]) -> List[int]:
    """applyies the mapping to retrive the list of integer indexes,
    where a negative value implies a negated index

    Args:
        phi (FNode): a clause, cube or term formula
        abstraction (Dict[FNode,int]): a mapping from atoms to integers

    Returns:
        (List[int]) : the list of corresponding indexes, a negative value implies a negated atom"""
    index_items = []
    if is_term(phi):
        index_items.append(_indexes_from_arg(phi, abstraction))
    elif is_clause(phi) or is_cube(phi):
        for arg in phi.args():
            index_items.append(_indexes_from_arg(arg, abstraction))
    else:
        raise ValueError(
            "Cannot extract indexes from a formula which is not a cube, clause or term!")
    return index_items


def _indexes_from_arg(phi: FNode, abstraction: Dict[FNode, int]) -> int:
    """applyies the mapping to retrive the integer index of a single term

    Args:
        phi (FNode): a FNode which only contains an atom
        abstraction (Dict[FNode,int]): a mapping from atoms to integers

    Returns:
        (int) : the corresponding index, a negative value implies a negated atom
    """
    index = 1
    atom = get_atoms(phi)[0]
    # check if the atom is negated as a key in the abstraction
    # in case that happens treat the atom as negated
    if atom not in abstraction.keys():
        index = -1
        atom = Not(atom)
    index = index * abstraction[atom]
    if is_negated(phi):
        index *= -1
    return index


def aliases_from_mapping(phi: FNode, abstraction: Dict[FNode, str]) -> List[str]:
    """applyies the mapping to retrieve the list of string aliases,
    where a string starting with "-" indicates a negated alias

    Args:
        phi (FNode): a clause, cube or term formula
        abstraction (Dict[FNode,str]): a mapping from atoms to strings

    Returns:
        (List[str]) : the list of corresponding aliases, a string starting with "-" implies a negated atom
    """
    alias_items = []
    if is_term(phi):
        alias_items.append(_aliases_from_arg(phi, abstraction))
    elif is_clause(phi) or is_cube(phi):
        for arg in phi.args():
            alias_items.append(_aliases_from_arg(arg, abstraction))
    else:
        raise ValueError(
            "Cannot extract indexes from a formula which is not a cube, clause or term!")
    return alias_items


def _aliases_from_arg(phi: FNode, mapping: Dict[FNode, str]) -> str:
    """applyies the mapping to retrieve the string alias of a single term

    Args:
        phi (FNode): a FNode which only contains an atom
        mapping (Dict[FNode,str]): a mapping from atoms to strings

    Returns:
        (str) : the corresponding alias, starting with a - if the atom is negated
    """
    alias_start = ""
    atom = get_atoms(phi)[0]
    # check if the atom in the mapping is negated
    if atom not in mapping.keys():
        alias_start = "-"
        atom = Not(atom)
    alias = alias_start + mapping[atom]
    if is_negated(phi):
        if alias.startswith("-"):
            alias = alias[1:]
        else:
            alias = "-" + alias
    return alias


def create_random_clause(atoms: List[FNode], filename: str, seed: int | None = None) -> None:
    """
    creates a random clause from the given atoms and saves it to the specified SMT2 file

    Args:
        atoms (List[FNode]): the list of atoms to create the clause from
        filename (str): the name of the file where the clause will be saved
        seed (int | None): the seed for the random generator, if None the seed will be random
    """
    if len(atoms) == 0:
        save_phi(bottom(), filename)
        return
    if seed is not None:
        random.seed(seed)
    clause_atoms = random.sample(
        atoms, random.randint(1, max(1, len(atoms)//2)))
    for i, atom in enumerate(clause_atoms):
        if random.choice([True, False]):  # 50% chance to negate the atom
            clause_atoms[i] = without_double_neg(Not(atom))
    save_phi(Or(*clause_atoms), filename)


def create_random_cube(atoms: List[FNode], filename: str, seed: int | None = None) -> None:
    """
    creates a random cube from the given atoms and saves it to the specified SMT2 file

    Args:
        atoms (List[FNode]): the list of atoms to create the clause from
        filename (str): the name of the file where the clause will be saved
        seed (int | None): the seed for the random generator, if None the seed will be random
    """
    if len(atoms) == 0:
        save_phi(top(), filename)
        return
    if seed is not None:
        random.seed(seed)
    clause_atoms = random.sample(
        atoms, random.randint(1, max(1, len(atoms)//2)))
    for i, atom in enumerate(clause_atoms):
        if random.choice([True, False]):  # 50% chance to negate the atom
            clause_atoms[i] = without_double_neg(Not(atom))
    save_phi(big_and(clause_atoms), filename)


def create_random_term(atoms: List[FNode], filename: str, seed: int | None = None) -> None:
    """
    creates a random term from the given atoms and saves it to the specified SMT2 file

    Args:
        atoms (List[FNode]): the list of atoms to create the clause from
        filename (str): the name of the file where the clause will be saved
        seed (int | None): the seed for the random generator, if None the seed will be random
    """
    if len(atoms) == 0:
        save_phi(top(), filename)
        return
    if seed is not None:
        random.seed(seed)
    term_atom = random.choice(atoms)
    if random.choice([True, False]):
        term_atom = without_double_neg(Not(term_atom))
    save_phi(term_atom, filename)


def select_random_items(items: List[object], amount: int | None = None, random_seed: int | None = None) -> List[Tuple[object,bool]]:
    """
    selects a random subset of items from a selction of items

    Args:
        items (List[object]): the list of items to select from
        amount (int| None): the number of items to select, None will select a random number of items
        random_seed (int | None): the seed for the random generator, if None the seed will be random

    Returns:
        List[Tuple(object,bool)]: the list of selected items, each pèaired with a boolean indicating if the item is positive or negative
    """
    if random_seed is not None:
        random.seed(random_seed)

    if amount is None:
        amount = random.randint(1, max(1, len(items)//2))

    samples = random.sample(items, amount)

    result = [(sample, random.choice([True, False])) for sample in samples]
    return result
