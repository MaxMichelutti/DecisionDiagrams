"""main module to query compiled formulas

THIS MODULE IS SMART ENOUGH TO KNOW WHICH MANAGER TO USE
FROM THE CONTENTS OF THE PROVIDED DATA
IF MULTIPLE COMPILATION RESULTS ARE PUT INTO THE SAME FOLDER
THE MANAGER WILL DEFAULT INTO THE FIRST ONE IT FINDS
IN THE FOLLOWING ORDER: C2D T-dDNNF, D4 T-dDNNF, T-BDD, T-SDD

PLEASE SAVE DIFFERENT COMPILATION RESULTS
INTO DIFFERENT FOLDERS TO AVOID POSSIBLE ISSUES
WITH THIS BEHAVIOUR

SOME QUERIES MAY NOT BE SUPPORTED BY ALL MANAGERS,
IF A QUERY IS NOT SUPPORTED BY THE MANAGER
THE PROGRAM WILL RAISE A NotImplementedError
"""

import json
import os.path as path
from os import remove as rmv
from theorydd.formula import load_refinement, load_abstraction_function

from src.query.commands import get_args
from src.query.util import (
    is_c2d_tddnnf_loading_folder_correct,
    is_d4_tddnnf_loading_folder_correct,
    is_tbdd_loading_folder_correct,
    is_tsdd_loading_folder_correct,
    create_random_clause,
    create_random_term,
    create_random_cube)
from src.query.tddnnf.c2d.manager import C2D_DDNNFQueryManager
from src.query.tddnnf.d4.manager import D4_DDNNFQueryManager
from src.query.tbdd.manager import TBDDQueryManager
from src.query.tsdd.manager import TSDDQueryManager
from src.query.smt_solver.manager import SMTQueryManager
from src.query.constants import TEMPORARY_QUERY_INPUT_FILE

def clean_tmp_file():
    if path.exists(TEMPORARY_QUERY_INPUT_FILE):
        rmv(TEMPORARY_QUERY_INPUT_FILE)

def _get_c2d_manager(input_folder: str) -> C2D_DDNNFQueryManager:
    """initialize a C2D manager from the input folder"""
    with open(path.join(input_folder, "quantification.exist"), "r", encoding='utf8') as file:
        data = file.readlines()[0].split(" ")
        # skip first item because it is the amount of quantified variables
        quantified_labels = set([int(x) for x in data[1:]])

    # load refinement funvtion as a mapping
    refinement_mapping = load_refinement(path.join(
        input_folder, "mapping/mapping.json"))
    
    total_vars = len(refinement_mapping)

    # remove non important items from the mapping
    keys_to_remove = set()
    for key in refinement_mapping.keys():
        if key in quantified_labels:
            keys_to_remove.add(key)
    for key in keys_to_remove:
        del refinement_mapping[key]

    return C2D_DDNNFQueryManager(input_folder, total_vars, refinement_mapping = refinement_mapping)


def _get_d4_manager(input_folder: str) -> D4_DDNNFQueryManager:
    """initialize a D4 manager from the input folder"""
    # load the important labels
    with open(path.join(input_folder, "mapping/important_labels.json"), "r", encoding='utf8') as file:
        important_labels = json.load(file)

    # load refinement funvtion as a mapping
    refinement_mapping = load_refinement(
        path.join(input_folder, "mapping/mapping.json"))
    
    total_vars = len(refinement_mapping)

    # remove non important items from the mapping
    keys_to_remove = set()
    for key in refinement_mapping.keys():
        if key not in important_labels:
            keys_to_remove.add(key)
    for key in keys_to_remove:
        del refinement_mapping[key]

    return D4_DDNNFQueryManager(input_folder, total_vars, refinement_mapping = refinement_mapping)


def _get_tbdd_manager(input_folder: str) -> TBDDQueryManager:
    # LOAD REFINEMENT
    abstraction_mapping = load_abstraction_function(
        path.join(input_folder, "abstraction.json"))
    refinement_mapping = {v: k for k, v in abstraction_mapping.items()}

    # LOAD QVARS
    with open(path.join(input_folder, "qvars.qvars"), "r", encoding='utf8') as qvars_file:
        qvars = json.load(qvars_file)

    # FILTER REFINEMENT BY REMOVING KEYS IN QVARS
    keys_to_remove = set()
    for key in refinement_mapping.keys():
        if key in qvars:
            keys_to_remove.add(key)
    for key in keys_to_remove:
        del refinement_mapping[key]

    # INITIALIZE QUERY MANAGER
    return TBDDQueryManager(input_folder, refinement_mapping = refinement_mapping)


def _get_tsdd_manager(input_folder: str) -> TSDDQueryManager:
    # LOAD REFINEMENT
    abstraction_mapping = load_abstraction_function(
        path.join(input_folder, "abstraction.json"))
    refinement_mapping = {v: k for k, v in abstraction_mapping.items()}

    # LOAD QVARS
    with open(path.join(input_folder, "qvars.qvars"), "r", encoding='utf8') as qvars_file:
        qvars = json.load(qvars_file)

    # FILTER REFINEMENT BY REMOVING KEYS IN QVARS
    keys_to_remove = set()
    for key in refinement_mapping.keys():
        if key in qvars:
            keys_to_remove.add(key)
    for key in keys_to_remove:
        del refinement_mapping[key]

    # INITIALIZE QUERY MANAGER
    return TSDDQueryManager(input_folder, refinement_mapping = refinement_mapping)


def main():
    """
    main function to quering compiled formulas
    """
    args = get_args()

    input_folder = args.load_data

    # LOAD THE CORRECT MANAGER
    if is_c2d_tddnnf_loading_folder_correct(input_folder):
        query_manager = _get_c2d_manager(input_folder)
    elif is_d4_tddnnf_loading_folder_correct(input_folder):
        query_manager = _get_d4_manager(input_folder)
    elif is_tbdd_loading_folder_correct(input_folder):
        query_manager = _get_tbdd_manager(input_folder)
    elif is_tsdd_loading_folder_correct(input_folder):
        query_manager = _get_tsdd_manager(input_folder)
    elif input_folder.endswith(".smt") or input_folder.endswith(".smt2"):
        query_manager = SMTQueryManager(input_folder)
    else:
        raise ValueError(
            "The folder where the compiled formula files are stored was not found, or some files are missing from it.")

    if args.consistency:
        query_manager.check_consistency()

    if args.validity:
        query_manager.check_validity()

    if args.entail_clause is not None:
        if args.random is not None:
            args.entail_clause = TEMPORARY_QUERY_INPUT_FILE
            if args.seed is not None:
                create_random_clause(
                    list(query_manager.refinement_mapping.values()), args.entail_clause, args.seed)
            else:
                create_random_clause(list(query_manager.refinement_mapping.values()), args.entail_clause)
        query_manager.check_entail_clause(args.entail_clause)

    if args.implicant is not None:
        if args.random is not None:
            args.implicant = TEMPORARY_QUERY_INPUT_FILE
            if args.seed is not None:
                create_random_term(
                    list(query_manager.refinement_mapping.values()), args.implicant, args.seed)
            else:
                create_random_term(list(query_manager.refinement_mapping.values()), args.implicant)
        query_manager.check_implicant(args.implicant)

    if args.count:
        query_manager.count_models()

    if args.enumerate:
        query_manager.enumerate_models()

    if args.condition is not None:
        if args.random is not None:
            args.condition = TEMPORARY_QUERY_INPUT_FILE
            if args.seed is not None:
                create_random_cube(
                    list(query_manager.refinement_mapping.values()), args.condition, args.seed)
            else:
                create_random_cube(list(query_manager.refinement_mapping.values()), args.condition)
        query_manager.condition(args.condition, args.save_conditioned)

    if args.entail is not None:
        query_manager.check_entail(args.entail)

    if args.conjunction is not None:
        query_manager.conjunction(args.conjunction, args.save_conjunction)

    if args.disjunction is not None:
        query_manager.disjunction(args.disjunction, args.save_disjunction)

    if args.negation:
        query_manager.negation(args.save_negation)

    clean_tmp_file()

if __name__ == "__main__":
    main()
