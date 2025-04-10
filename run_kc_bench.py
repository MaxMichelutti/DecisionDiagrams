"""
module for easily running the knowledge compiler on all the problems from a given benchmark source

If you want to run the benchmark on a different set of problems, 
you can add the bench to the VALID_BENCHS list and implement the 
prepare_paths_{bench} function
"""
import os
from typing import List

# TO ADD A NEW BENCHMARKS EXTEND THIS LIST
VALID_BENCHS = ["ldd_randgen", "randgen", "qfrdl"]

# never change this list
RUN_TYPES = ["allsmt", "dd", "both", "abstraction"]

# the valid solver options
# if you implement a custom SMTEnumerator, you can add it to this list
# also remember to:
# - add it into src.kc.main.py in the get_solver function
# - add it to the VALID_SOLVERS list in src.kc.constants.py
VALID_SOLVERS = ["total", "partial", "extended_partial",
                 "tabular_total", "tabular_partial"]

# the valid theory compilation options
# theory compilations are all compilations that necessitate of running AllSMT
VALID_THEORY_DD = ["tbdd", "tsdd", "tddnnf"]

# the valid abstract compilation options
# abstract compilation are all compilations that do not necessitate of running AllSMT
VALID_ABSTRACT_DD = ["abstraction_bdd",
                     "abstraction_sdd", "abstraction_ddnnf", "ldd"]

# the valid dDNNF compilers
VALID_DDNNF_COMPILER = ["c2d", "d4"]

# the main module of the knowledge compiler
COMPILER_MAIN_MODULE = "knowledge_compiler.py"

# can be changed to "python3" if python3 is the command for python in your system,
# or any other command that runs python on your system
PYTHON_CALLABLE = "python"


def prepare_paths_ldd_randgen(output_folder: str, tmp_folder: str) -> List[str]:
    """prepare the paths for the ldd_randgen benchmark
    and returns the input  files
    Returns:
        List[str]: list of input files
    """
    input_files = []
    if output_folder is not None and not os.path.isdir(f"benchmarks/ldd_randgen/{output_folder}"):
        os.mkdir(f"benchmarks/ldd_randgen/{output_folder}")
    if tmp_folder is not None and not os.path.isdir(f"benchmarks/ldd_randgen/{tmp_folder}"):
        os.mkdir(f"benchmarks/ldd_randgen/{tmp_folder}")
    for dataset in os.listdir("benchmarks/ldd_randgen/data"):
        if tmp_folder is not None and not os.path.isdir(f"benchmarks/ldd_randgen/{tmp_folder}/{dataset}"):
            os.mkdir(f"benchmarks/ldd_randgen/{tmp_folder}/{dataset}")
        if output_folder is not None and not os.path.isdir(f"benchmarks/ldd_randgen/{output_folder}/{dataset}"):
            os.mkdir(f"benchmarks/ldd_randgen/{output_folder}/{dataset}")
        for numbered_folder in os.listdir(f"benchmarks/ldd_randgen/data/{dataset}"):
            if tmp_folder is not None and not os.path.isdir(f"benchmarks/ldd_randgen/{tmp_folder}/{dataset}/{numbered_folder}"):
                os.mkdir(
                    f"benchmarks/ldd_randgen/{tmp_folder}/{dataset}/{numbered_folder}")
            if output_folder is not None and not os.path.isdir(f"benchmarks/ldd_randgen/{output_folder}/{dataset}/{numbered_folder}"):
                os.mkdir(
                    f"benchmarks/ldd_randgen/{output_folder}/{dataset}/{numbered_folder}")
            for filename in os.listdir(f"benchmarks/ldd_randgen/data/{dataset}/{numbered_folder}"):
                if not filename.endswith(".smt2"):
                    continue
                input_files.append(
                    f"benchmarks/ldd_randgen/data/{dataset}/{numbered_folder}/{filename}")
    return input_files


def prepare_paths_randgen(output_folder: str, tmp_folder: str) -> List[str]:
    """prepare the paths for the randgen benchmark
    and returns the input  files
    Returns:
        List[str]: list of input files
    """
    input_files = []
    if output_folder is not None and not os.path.isdir(f"benchmarks/randgen/{output_folder}"):
        os.mkdir(f"benchmarks/randgen/{output_folder}")
    if tmp_folder is not None and not os.path.isdir(f"benchmarks/randgen/{tmp_folder}"):
        os.mkdir(f"benchmarks/randgen/{tmp_folder}")
    for dataset in os.listdir("benchmarks/randgen/data"):
        if tmp_folder is not None and not os.path.isdir(f"benchmarks/randgen/{tmp_folder}/{dataset}"):
            os.mkdir(f"benchmarks/randgen/{tmp_folder}/{dataset}")
        if output_folder is not None and not os.path.isdir(f"benchmarks/randgen/{output_folder}/{dataset}"):
            os.mkdir(f"benchmarks/randgen/{output_folder}/{dataset}")
        for numbered_folder in os.listdir(f"benchmarks/randgen/data/{dataset}"):
            if tmp_folder is not None and not os.path.isdir(f"benchmarks/randgen/{tmp_folder}/{dataset}/{numbered_folder}"):
                os.mkdir(
                    f"benchmarks/randgen/{tmp_folder}/{dataset}/{numbered_folder}")
            if output_folder is not None and not os.path.isdir(f"benchmarks/randgen/{output_folder}/{dataset}/{numbered_folder}"):
                os.mkdir(
                    f"benchmarks/randgen/{output_folder}/{dataset}/{numbered_folder}")
            for filename in os.listdir(f"benchmarks/randgen/data/{dataset}/{numbered_folder}"):
                if not filename.endswith(".smt2"):
                    continue
                input_files.append(
                    f"benchmarks/randgen/data/{dataset}/{numbered_folder}/{filename}")
    return input_files


def prepare_paths_qfrdl(output_folder: str, tmp_folder: str) -> List[str]:
    """prepare the paths for the smtlib QF RDL benchmark
    and returns the input  files
    Returns:
        List[str]: list of input files
    """
    input_files = []
    if output_folder is not None and not os.path.isdir(f"benchmarks/smtlib/{output_folder}"):
        os.mkdir(f"benchmarks/smtlib/{output_folder}")
        os.mkdir(f"benchmarks/smtlib/{output_folder}/non-incremental")
        os.mkdir(f"benchmarks/smtlib/{output_folder}/non-incremental/QF_RDL")
    if tmp_folder is not None and not os.path.isdir(f"benchmarks/smtlib/{tmp_folder}"):
        os.mkdir(f"benchmarks/smtlib/{tmp_folder}")
        os.mkdir(f"benchmarks/smtlib/{tmp_folder}/non-incremental")
        os.mkdir(f"benchmarks/smtlib/{tmp_folder}/non-incremental/QF_RDL")
    for dataset in os.listdir("benchmarks/smtlib/data/non-incremental/QF_RDL"):
        if output_folder is not None and not os.path.isdir(f"benchmarks/smtlib/{output_folder}/non-incremental/QF_RDL/{dataset}"):
            os.mkdir(
                f"benchmarks/smtlib/{output_folder}/non-incremental/QF_RDL/{dataset}")
        if tmp_folder is not None and not os.path.isdir(f"benchmarks/smtlib/{tmp_folder}/non-incremental/QF_RDL/{dataset}"):
            os.mkdir(
                f"benchmarks/smtlib/{tmp_folder}/non-incremental/QF_RDL/{dataset}")
        for filename in os.listdir(f"benchmarks/smtlib/data/non-incremental/QF_RDL/{dataset}"):
            if not filename.endswith(".smt2"):
                continue
            input_files.append(
                f"benchmarks/smtlib/data/non-incremental/QF_RDL/{dataset}/{filename}")
    return input_files


def main() -> None:
    """main function for running the benchmarking script"""
    print(VALID_BENCHS)
    bench_source = input("Enter the benchmark name: ")
    bench_source = bench_source.strip().lower()
    if bench_source not in VALID_BENCHS:
        print("Invalid benchmark source")
        return
    print(RUN_TYPES)
    run_type = input("Enter the run type: ")
    run_type = run_type.strip().lower()
    if run_type not in RUN_TYPES:
        print("Invalid run type")
        return
    solver_type = None
    dd_type = None
    tmp_folder = None
    output_folder = None
    ddnnf_compiler = None
    save_dd = False
    enumerate_true = False
    negate_input = False
    preload_lemmas = None
    ddnnf_dont_quantify = False
    if run_type != "abstraction":
        tmp_folder = input("Enter the temporary folder name: ")
    nagated_input_prompt = input(
        "Do you want to negate the input formula? (y/n): ")
    nagated_input_prompt = nagated_input_prompt.strip().lower()
    if nagated_input_prompt == "y":
        negate_input = True
    if run_type == "allsmt" or run_type == "both":
        print(VALID_SOLVERS)
        solver_type = input("Enter the solver type: ")
        solver_type = solver_type.strip().lower()
        if solver_type not in VALID_SOLVERS:
            print("Invalid solver type")
            return
        enumerate_true_prompt = input(
            "Do you want to enumerate over true? (y/n): ")
        enumerate_true_prompt = enumerate_true_prompt.strip().lower()
        if enumerate_true_prompt == "y":
            enumerate_true = True
        preload_lemmas = input("Enter the path to the preloaded lemmas file (enter s to skip): ")
        if(preload_lemmas == "s"):
            preload_lemmas = None
    if run_type == "dd" or run_type == "both":
        print(VALID_THEORY_DD)
        dd_type = input("Enter the dd type: ")
        dd_type = dd_type.strip().lower()
        if dd_type not in VALID_THEORY_DD:
            print("Invalid dd type")
            return
        output_folder = input("Enter the output folder name: ")
        if dd_type == "tbdd" or dd_type == "tsdd":
            answer = input(
                "Do you want to serialize the generated DDs? (y/n): ")
            answer = answer.strip().lower()
            if answer == "y":
                save_dd = True
        if dd_type == "tddnnf":
            print(VALID_DDNNF_COMPILER)
            ddnnf_compiler = input("Select a tdDNNF compiler: ")
            if ddnnf_compiler not in VALID_DDNNF_COMPILER:
                print("Invalid dDNNF compiler")
                return
            answer = input(
                "Do you want to quantify fresh variables? (y/n): ")
            answer = answer.strip().lower()
            if answer == "n":
                ddnnf_dont_quantify = True
    if run_type == "abstraction":
        print(VALID_ABSTRACT_DD)
        dd_type = input("Enter the dd type: ")
        dd_type = dd_type.strip().lower()
        if dd_type not in VALID_ABSTRACT_DD:
            print("Invalid dd type")
            return
        if dd_type == "abstraction_bdd" or dd_type == "abstraction_sdd":
            answer = input(
                "Do you want to serialize the generated DDs? (y/n): ")
            answer = answer.strip().lower()
            if answer == "y":
                save_dd = True
        if dd_type == "abstraction_ddnnf":
            tmp_folder = input("Enter the tmp folder name: ")
            print(VALID_DDNNF_COMPILER)
            ddnnf_compiler = input("Select a tdDNNF compiler: ")
            if ddnnf_compiler not in VALID_DDNNF_COMPILER:
                print("Invalid dDNNF compiler")
                return
        output_folder = input("Enter the output folder name: ")

    # print a summary of selected options
    print("\n\n\nSUMMARY")
    print("Benchmark source:", bench_source)
    print("Run type:", run_type)
    print("Solver type:", solver_type)
    print("DD type:", dd_type)
    print("Temporary folder:", tmp_folder)
    print("Output folder:", output_folder)
    print("dDNNF compiler: ", ddnnf_compiler)
    print("Save DDs: ", save_dd)
    print("Enumerate true: ", enumerate_true)
    print("Negate input: ", negate_input)
    print("Preload lemmas: ", preload_lemmas)
    print("Do not quantify fresh variables: ", ddnnf_dont_quantify)
    # ask confirmation
    is_ok = input("Is this correct? (y/n): ")
    is_ok = is_ok.strip().lower()
    if is_ok != "y":
        return

    # prepare for the run
    if bench_source == "ldd_randgen":
        input_files = prepare_paths_ldd_randgen(output_folder, tmp_folder)
    elif bench_source == "randgen":
        input_files = prepare_paths_randgen(output_folder, tmp_folder)
    elif bench_source == "qfrdl":
        input_files = prepare_paths_qfrdl(output_folder, tmp_folder)
    # ADD NEW BENCHMARKS HERE
    # EXAMPLE:
    # elif bench_source == "new_bench":
    #     input_files = prepare_paths_new_bench(output_folder, tmp_folder)
    else:
        raise ValueError("Invalid benchmark source")

    # run the benchmarks
    total_files = len(input_files)
    negate_input_string = ""
    if negate_input:
        negate_input_string = "--negative"
    for file_index, input_file in enumerate(input_files):
        print("Progress: ", file_index + 1, "/", total_files)
        print(f"Running {input_file}...")
        # abstraction
        if run_type == "abstraction":
            result = 0
            output_folder_path = input_file.replace("data", output_folder)
            output_file = output_folder_path.replace(".smt2", ".json")
            save_dd_str = ""
            if os.path.exists(output_file):
                print(f"{output_file} already exists. Skipping...")
                continue
            if dd_type == "abstraction_bdd":
                if save_dd:
                    save_dd_folder = output_folder_path.replace(".smt2", "")
                    save_dd_str = f"--save_abstraction_bdd {save_dd_folder}_abstraction_bdd"
                result = os.system(
                    f"timeout 3600s {PYTHON_CALLABLE} {COMPILER_MAIN_MODULE} {negate_input_string} -v -i {input_file} --count_nodes --count_models --abstraction_bdd -d {output_file} {save_dd_str}")
            elif dd_type == "abstraction_sdd":
                if save_dd:
                    save_dd_folder = output_folder_path.replace(".smt2", "")
                    save_dd_str = f"--save_abstraction_sdd {save_dd_folder}_abstraction_sdd"
                result = os.system(
                    f"timeout 3600s {PYTHON_CALLABLE} {COMPILER_MAIN_MODULE} {negate_input_string} -v -i {input_file} --abstraction_sdd --count_nodes --count_models -d {output_file} --abstraction_vtree balanced {save_dd_str}")
            elif dd_type == "abstraction_ddnnf":
                tmp_folder_path = output_folder_path.replace(
                    ".smt2", f"_{ddnnf_compiler}")
                os.system(
                    f"{PYTHON_CALLABLE} {COMPILER_MAIN_MODULE} {negate_input_string} -v -i {input_file} --abstraction_dDNNF -d {output_file} --no_dDNNF_to_pysmt --save_dDNNF {tmp_folder_path} --dDNNF_compiler {ddnnf_compiler}")
            elif dd_type == "ldd":
                result = os.system(
                    f"timeout 3600s {PYTHON_CALLABLE} {COMPILER_MAIN_MODULE} {negate_input_string} -v -i {input_file} --ldd --ldd_theory TVPI --count_models --count_nodes -d {output_file}")
            if result != 0:
                print(f"Abstraction DD compilation timed out for {input_file}")
                with open(output_file, "w", encoding='utf8') as f:
                    f.write("{\"timeout\": \"DD\"}")
                continue

        # allsmt only
        elif run_type == "allsmt" or run_type == "both":
            enumerate_true_str = ""
            if enumerate_true:
                enumerate_true_str = "--enumerate_true"
            tmp_lemma_file = input_file.replace("data", tmp_folder)
            preload_lemmas_str = ""
            if preload_lemmas is not None:
                preload_lemmas_path = tmp_lemma_file.replace(tmp_folder, preload_lemmas)
                if not os.path.isfile(preload_lemmas_path):
                    print("Preloaded lemmas file does not exist. Skipping...")
                    continue
                print("Pre-loading lemmas from ", preload_lemmas_path, "...")
                preload_lemmas_str = f"--preload_lemmas {preload_lemmas_path}"
            tmp_json_file = tmp_lemma_file.replace(".smt2", ".json")
            print(f"Running allsmt on {input_file}...")
            if os.path.exists(tmp_json_file):
                print(f"{tmp_json_file} already exists. Skipping...")
                continue
            os.system(
                f"timeout 3600s {PYTHON_CALLABLE} {COMPILER_MAIN_MODULE} {negate_input_string} {preload_lemmas_str} {enumerate_true_str} -v -i {input_file} --save_lemmas {tmp_lemma_file} --solver {solver_type} -d {tmp_json_file} --count_models")

        # dd compilation only
        elif run_type == "dd" or run_type == "both":
            result = 0
            tmp_lemma_file = input_file.replace("data", tmp_folder)
            tmp_json_file = tmp_lemma_file.replace(".smt2", ".json")
            output_folder_path = input_file.replace("data", output_folder)
            output_file = output_folder_path.replace(".smt2", ".json")
            save_dd_str = ""
            print(f"Running DD compilation on {input_file}...")

            # check if allsmt timed out
            if not os.path.exists(tmp_json_file):
                print(f"{tmp_json_file} does not exist. AllSMT ended in timeout.")
                with open(output_file, "w", encoding='utf8') as f:
                    f.write("{\"timeout\": \"ALL SMT\"}")
                continue
            
            # check if dd compilation already exists
            if os.path.exists(output_file):
                print(f"{output_file} already exists. Skipping...")
                continue

            if dd_type == "tbdd":
                if save_dd:
                    save_dd_folder = output_folder_path.replace(".smt2", "")
                    save_dd_str = f"--save_tbdd {save_dd_folder}_tbdd"
                result = os.system(
                    f"timeout 3600s {PYTHON_CALLABLE} {COMPILER_MAIN_MODULE} {negate_input_string} -v -i {input_file} --load_lemmas {tmp_lemma_file} --load_details {tmp_json_file} --tbdd --count_nodes --count_models -d {output_file} {save_dd_str}")
            elif dd_type == "tsdd":
                if save_dd:
                    save_dd_folder = output_folder_path.replace(".smt2", "")
                    save_dd_str = f"--save_tsdd {save_dd_folder}_tsdd"
                result = os.system(
                    f"timeout 3600s {PYTHON_CALLABLE} {COMPILER_MAIN_MODULE} {negate_input_string} -v -i {input_file} --load_lemmas {tmp_lemma_file} --load_details {tmp_json_file}  --tsdd --count_nodes --count_models -d {output_file} --tvtree balanced {save_dd_str}")
            elif dd_type == "tddnnf":
                dont_quantify_str = ""
                if ddnnf_dont_quantify:
                    dont_quantify_str = "--dDNNF_do_not_quantify "
                tmp_ddnnf_folder = output_folder_path.replace(
                    ".smt2", f"_{ddnnf_compiler}")
                os.system(
                    f"{PYTHON_CALLABLE} {COMPILER_MAIN_MODULE} {negate_input_string} -v -i {input_file} {dont_quantify_str}--load_lemmas {tmp_lemma_file} --load_details {tmp_json_file} --tdDNNF -d {output_file} --no_dDNNF_to_pysmt --save_dDNNF {tmp_ddnnf_folder} --dDNNF_compiler {ddnnf_compiler}")

            if result != 0:
                print(f"DD compilation timed out for {input_file}")
                with open(output_file, "w", encoding='utf8') as f:
                    f.write("{\"timeout\": \"DD\"}")
                continue

        print(f"Finished running {input_file}")

    print("ALL  RUNS COMPLETED")
    print("\n\n\nSUMMARY")
    print("Benchmark source:", bench_source)
    print("Run type:", run_type)
    print("Solver type:", solver_type)
    print("DD type:", dd_type)
    print("Temporary folder:", tmp_folder)
    print("Output folder:", output_folder)
    print("dDNNF compiler: ", ddnnf_compiler)
    print("Save DDs: ", save_dd)
    print("Enumerate true: ", enumerate_true)
    print("Negate input: ", negate_input)
    print("Preload lemmas: ", preload_lemmas)
    print("Do not quantify fresh variables: ", ddnnf_dont_quantify)


if __name__ == "__main__":
    main()
