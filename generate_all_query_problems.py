"""module to genrate all query problems for clausal entailment"""
import os


BASE_PATH = "benchmarks/ldd_randgen/data"
PYTHON_COMMAND = "python3"

PROBLEM_GEN_PATH = "src/problem_generators/problem_generator_ce_query.py"

NUMBER_OF_VARS = [1, 3, 5]
PROBLEMS_FOR_EACH = 10
SEEDS = [12345, 35724, 8546, 37645, 537254, 64738, 5372, 257654, 54, 542]


def main():
    items = []
    base_path_query = BASE_PATH.replace("data", "ce_data")
    if not os.path.exists(base_path_query):
        os.mkdir(base_path_query)
    for pathx, _subdirs, files in os.walk(BASE_PATH):
        for subdir in _subdirs:
            item = os.path.join(pathx, subdir)
            item = item.replace("data", "ce_data")
            if not os.path.exists(item):
                os.mkdir(item)
        for name in files:
            items.append(os.path.join(pathx, name))

    count = 1
    total = len(items)
    for filename in items:
        print(count, "/", total)
        count += 1
        query_folder = filename.replace(".smt2", "")
        query_folder = query_folder.replace("data", "ce_data")
        if not os.path.exists(query_folder):
            os.mkdir(query_folder)
        for variables in NUMBER_OF_VARS:
            for i in range(PROBLEMS_FOR_EACH):
                current_index = i+1
                current_seed = SEEDS[i] * current_index
                output_path = query_folder + "/ce_query_vars_" + \
                    str(variables) + "_index_" + str(current_index) + \
                    "_seed_"+str(current_seed)+".smt2"
                command = f"{PYTHON_COMMAND} {PROBLEM_GEN_PATH} --source {filename} --size {variables} --seed {current_seed} --output {output_path}"
                print("Executing command:", command)
                os.system(command)


if __name__ == "__main__":
    main()
