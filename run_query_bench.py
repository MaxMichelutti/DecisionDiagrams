import os
from typing import List

# the main module of the knowledge compiler
QUERY_MAIN_MODULE = "query_tool.py"

# can be changed to "python3" if python3 is the command for python in your system,
# or any other command that runs python on your system
PYTHON_CALLABLE = "python"

VALID_SOURCES = ["randgen","ldd_randgen"]

VALID_STRUCTURES = ["smt","tbdd","tsdd","tddnnf"]

DDNNF_CPOMPILERS = ["c2d","d4"]

# 10 minutes
TIMEOUT_SECONDS=600


def prepare_paths_ldd_randgen(output_folder: str, tmp_folder: str =  None) -> List[str]:
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


def prepare_paths_randgen(output_folder: str, tmp_folder: str = None) -> List[str]:
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


def main():
    """main function to run the query benchmark"""
    source = input("Enter the source of the benchmark among "+str(VALID_SOURCES)+":\n")
    if source not in VALID_SOURCES:
        raise ValueError(
            f"Invalid source {source}. Valid sources are {VALID_SOURCES}")
    target = input("Enter the name of the output folder:")
    struc_type = input("Enter the structure type among "+str(VALID_STRUCTURES)+":\n")
    if struc_type not in VALID_STRUCTURES:
        raise ValueError(
            f"Invalid structure type {struc_type}. Valid structure types are {VALID_STRUCTURES}")
    if struc_type == "tddnnf":
        ddnnf_compiler = input("Enter the ddnnf compiler among "+str(DDNNF_CPOMPILERS)+":\n")
        if ddnnf_compiler not in DDNNF_CPOMPILERS:
            raise ValueError(
                f"Invalid ddnnf compiler {ddnnf_compiler}. Valid ddnnf compilers are {DDNNF_CPOMPILERS}")
    structures_folder = input("Enter the folder name for the structures:\n")
    if not os.path.isdir(f"benchmarks/{source}/{structures_folder}"):
        raise ValueError(
            f"Invalid folder name {structures_folder} for the source {source}")
    if source == "ldd_randgen":
        input_files = prepare_paths_ldd_randgen(target)
    else:
        input_files = prepare_paths_randgen(target)
    count = 1
    for input_file in input_files:
        print(count, "/", len(input_files))
        count += 1
        input_files_folder = input_file.replace(".smt2", "/")
        input_files_folder = input_files_folder.replace("data", "ce_data",1)
        all_query_files = []
        for item in os.listdir(input_files_folder):
            all_query_files.append(input_files_folder + item)
        all_query_files_string = " ".join(all_query_files)
        if len(all_query_files) == 0:
            print("SKIPPING: No query files available!")
            continue
        structure_location = ""
        if struc_type == "smt":
            structure_location = input_file
        elif struc_type == "tbdd":
            structure_location = input_file.replace("data",structures_folder)
            structure_location = structure_location.replace(".smt2", "_tbdd")
        elif struc_type == "tsdd":
            structure_location = input_file.replace("data",structures_folder)
            structure_location = structure_location.replace(".smt2", "_tsdd")
        elif struc_type == "tddnnf":
            structure_location = input_file.replace("data",structures_folder)
            structure_location = structure_location.replace(".smt2", "")
            if ddnnf_compiler == "c2d":
                structure_location = structure_location + "_c2d"
            elif ddnnf_compiler == "d4":
                structure_location = structure_location + "_d4"
        else:
            raise ValueError(
                f"Invalid structure type {struc_type}. Valid structure types are {VALID_STRUCTURES}")
        if not structure_location.endswith(".smt2") and not os.path.isdir(structure_location):
            print("SKIPPING: Structure not available!")
            continue
        print(f"Running query benchmark on {input_file}...")
        output_file = input_file.replace("data",target)
        output_file = output_file.replace(".smt2", ".json")
        command = f"{PYTHON_CALLABLE} {QUERY_MAIN_MODULE} --load_data {structure_location} --entail_clause {all_query_files_string} -d {output_file} -t {TIMEOUT_SECONDS}"
        result = os.system(command)
        if result != 0:
            print(f"Command failed with error code {result}")
            with open(output_file, "w", encoding='utf8') as f:
                f.write("{\"timeout\":\"query\"}")
            continue
        print(f"Finished running {input_file}")
    print("ALL  RUNS COMPLETED")
    print("\n\n\nSUMMARY")
    print("Benchmark source:", source)
    print("Run type:", "query")
    print("Structure type:", struc_type)
    print("Temporary folder:", structures_folder)
    print("Output folder:", target)
    if ddnnf_compiler:
        print("dDNNF compiler: ", ddnnf_compiler)
    print("Timeout seconds: ", TIMEOUT_SECONDS)
        
        

if __name__ == "__main__":
    main()