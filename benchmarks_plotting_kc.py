"""main and functions to plot the results of the program running on benchmarks"""
import copy
from enum import Enum
import json
import os
from dataclasses import dataclass
# from pprint import pprint
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt

import warnings
warnings.filterwarnings("ignore")

TITLE_SIZE = 20
TICK_SIZE = 14
AXES_LABEL_SIZE = 20

plt.rc('font', size=AXES_LABEL_SIZE)
plt.rc('axes', titlesize=TITLE_SIZE)
plt.rc('xtick', labelsize=TICK_SIZE)
plt.rc('ytick', labelsize=TICK_SIZE)


class DataSource(Enum):
    """annotation to keep track of which computation was used"""
    THEORY_BDD = 1
    ABSTRACTION_BDD = 2
    THEORY_SDD = 3
    ABSTRACTION_SDD = 4
    LDD = 5


@dataclass
class Point:
    """a Point that can be plotted"""
    source: DataSource
    phi_size: int
    computation_time: float
    all_smt_time: float
    dd_time: float
    dd_models: float
    dd_nodes: int
    total_lemmas: int
    fresh_atoms: int
    fresh_atoms_quantification_time: float
    title: str
    timeout: bool
    timeout_kind: str


def has_only_phi_size(data: Dict) -> bool:
    if len(data) != 1:
        return False
    if data.get("phi size") is not None:
        return True
    return False


def get_wmi_bench_data(kind: str, source: str) -> List[Point]:
    """gets the computation data from wmi bench"""
    points = []

    # retrieving mutex result
    files = os.listdir(source+"/mutex")
    for filename in files:
        f = open(source+"/mutex/"+filename, encoding="utf8")
        data = json.load(f)
        if len(data) == 0 or data.get("timeout") is not None:
            points.append(Point(DataSource.THEORY_SDD, 0, 0,
                          0, 0, 0, 0, 0, 0, 0, "mutex/"+filename, True, data["timeout"]))
            continue
        if data.get("All-SAT computation time") is not None:
            allsmttime = data.get("All-SAT computation time")
        else:
            allsmttime = 1000
        if data.get("T-lemmas amount") is not None:
            tlemmas = data["T-lemmas amount"]
        elif data.get("total lemmas") is not None:
            tlemmas = data["total lemmas"]
        else:
            tlemmas = 0
        if data.get("phi size") is not None:
            phi_size = data["phi size"]
        else:
            phi_size = 0
        points.append(Point(DataSource.THEORY_SDD,
                            phi_size,
                            data["total computation time"],
                            allsmttime,
                            data[kind]["total processing time"],
                            data[kind]["model count"],
                            data[kind]["DD nodes"],
                            tlemmas,
                            data[kind]["fresh T-atoms detected"],
                            data[kind]["fresh T-atoms quantification time"],
                            "mutex/"+filename,
                            False,
                            "None"))

    # retrieving xor result
    files = os.listdir(source+"/xor")
    for filename in files:
        f = open(source+"/xor/"+filename, encoding="utf8")
        data = json.load(f)
        if len(data) == 0 or data.get("timeout") is not None:
            points.append(Point(DataSource.THEORY_SDD, 0,
                          0, 0, 0, 0, 0, 0, 0, 0, "xor/"+filename, True, data["timeout"]))
            continue
        if data.get("All-SAT computation time") is not None:
            allsmttime = data.get("All-SAT computation time")
        else:
            allsmttime = 1000
        if data.get("T-lemmas amount") is not None:
            tlemmas = data["T-lemmas amount"]
        elif data.get("total lemmas") is not None:
            tlemmas = data["total lemmas"]
        else:
            tlemmas = 0
        if data.get("phi size") is not None:
            phi_size = data["phi size"]
        else:
            phi_size = 0
        points.append(Point(DataSource.THEORY_SDD,
                            phi_size,
                            data["total computation time"],
                            allsmttime,
                            data[kind]["total processing time"],
                            data[kind]["model count"],
                            data[kind]["DD nodes"],
                            tlemmas,
                            data[kind]["fresh T-atoms detected"],
                            data[kind]["fresh T-atoms quantification time"],
                            "xor/"+filename,
                            False,
                            "None"))

    return points

def get_list_of_unsat_problems(source: str) -> List[str]:
    """finds a list of problems that are unsat"""
    files_list: List[str] = []
    result=[]
    for path, _subdirs, files in os.walk(source):
        for name in files:
            files_list.append(os.path.join(path, name))
    for filename in files_list:
        if not filename.endswith(".json"):
            continue
        if filename.endswith("abstraction.json"):
            continue
        if filename.endswith("mapping.json"):
            continue
        if filename.endswith("important_labels.json"):
            continue
        f = open(filename, encoding="utf8")
        data = json.load(f)
        if len(data) == 0 or data.get("timeout") is not None:
            continue
        if not "All-SMT result" in data:
            continue
        if data["All-SMT result"] == "UNSAT":
            file_unsat = filename.replace(source+"/", '')
            result.append(file_unsat)
    return result

def get_ldd_randgen_bench_data(kind: str, source: str) -> List[Point]:
    """gets the computation data from a run on randomly generated LDD benchmark problems"""
    points = []
    files_list: List[str] = []
    for path, _subdirs, files in os.walk(source):
        for name in files:
            files_list.append(os.path.join(path, name))
    for filename in files_list:
        if not filename.endswith(".json"):
            continue
        if filename.endswith("abstraction.json"):
            continue
        if filename.endswith("mapping.json"):
            continue
        if filename.endswith("important_labels.json"):
            continue
        f = open(filename, encoding="utf8")
        data = json.load(f)
        if len(data) == 0 or data.get("timeout") is not None or has_only_phi_size(data):
            points.append(Point(DataSource.THEORY_BDD, 0, 0, 0, 0, 0, 0, 0, 0, 0, filename.replace(
                source+"/", ''), True, data["timeout"]))
            continue
        data.setdefault("All-SMT computation time", 0.1)
        if data.get("T-lemmas amount") is not None:
            tlemmas = data["T-lemmas amount"]
        elif data.get("total lemmas") is not None:
            tlemmas = data["total lemmas"]
        else:
            tlemmas = 0

        data.setdefault(kind, {})
        if "total computation time" in data[kind]:
            data[kind]["total DD computation time"] = data[kind]["total computation time"]
        data[kind].setdefault("total DD computation time", 0.1)
        if kind == "T-dDNNF":
            if "DIMACS translation time" in data[kind] and "refinement serialization time" in data[kind] and "dDNNF compilation time" in data[kind]:
                data[kind]["total DD computation time"] = data[kind]["DIMACS translation time"] + \
                    data[kind]["refinement serialization time"] + \
                    data[kind]["dDNNF compilation time"]
        data[kind].setdefault("DD models", 0)
        data[kind].setdefault("DD nodes", 0)
        if "nodes" in data[kind]:
            data[kind]["DD nodes"] = data[kind]["nodes"]
        data[kind].setdefault("fresh T-atoms detected", 0)
        data[kind].setdefault("fresh T-atoms quantification time", 0)
        data.setdefault("phi size", 0)

        points.append(Point(DataSource.THEORY_BDD,
                            data["phi size"],
                            data["total computation time"],
                            data["All-SMT computation time"],
                            data[kind]["total DD computation time"],
                            data[kind]["DD models"],
                            data[kind]["DD nodes"],
                            tlemmas,
                            data[kind]["fresh T-atoms detected"],
                            data[kind]["fresh T-atoms quantification time"],
                            filename.replace(source+"/", ''), False, "None"))
    return points


def get_randgen_bench_data(kind: str, source: str) -> List[Point]:
    """gets the computation data from a run on randomly generated benchmark problems"""
    points = []
    files_list: List[str] = []
    for path, _subdirs, files in os.walk(source):
        for name in files:
            files_list.append(os.path.join(path, name))
    for filename in files_list:
        if not filename.endswith(".json"):
            continue
        if filename.endswith("abstraction.json"):
            continue
        if filename.endswith("mapping.json"):
            continue
        if filename.endswith("important_labels.json"):
            continue
        f = open(filename, encoding="utf8")
        data = json.load(f)
        if len(data) == 0 or data.get("timeout") is not None or has_only_phi_size(data):
            points.append(Point(DataSource.THEORY_BDD, 0, 0, 0, 0, 0, 0, 0, 0, 0, filename.replace(
                source+"/", ''), True, data["timeout"]))
            continue
        data.setdefault("All-SMT computation time", 0.1)
        if data.get("T-lemmas amount") is not None:
            tlemmas = data["T-lemmas amount"]
        elif data.get("total lemmas") is not None:
            tlemmas = data["total lemmas"]
        else:
            tlemmas = 0
        data.setdefault(kind, {})
        if "total computation time" in data[kind]:
            data[kind]["total DD computation time"] = data[kind]["total computation time"]
        data[kind].setdefault("total DD computation time", 0.1)
        if kind == "T-dDNNF":
            if "DIMACS translation time" in data[kind] and "refinement serialization time" in data[kind] and "dDNNF compilation time" in data[kind]:
                data[kind]["total DD computation time"] = data[kind]["DIMACS translation time"] + \
                    data[kind]["refinement serialization time"] + \
                    data[kind]["dDNNF compilation time"]

        data[kind].setdefault("DD models", 0)
        if "nodes" in data[kind]:
            data[kind]["DD nodes"] = data[kind]["nodes"]
        data[kind].setdefault("DD nodes", 0)
        data[kind].setdefault("fresh T-atoms detected", 0)
        data[kind].setdefault("fresh T-atoms quantification time", 0)
        data.setdefault("phi size", 0)

        points.append(Point(DataSource.THEORY_BDD,
                            data["phi size"],
                            data["total computation time"],
                            data["All-SMT computation time"],
                            data[kind]["total DD computation time"],
                            data[kind]["DD models"],
                            data[kind]["DD nodes"],
                            tlemmas,
                            data[kind]["fresh T-atoms detected"],
                            data[kind]["fresh T-atoms quantification time"],
                            filename.replace(source+"/", ''), False, "None"))
    return points


def get_smtlib_bench_data(kind: str, source: str) -> List[Point]:
    """gets the computation data from a run on smtlib benchmark problems"""
    points = []
    files_list: List[str] = []
    for path, _subdirs, files in os.walk(source):
        for name in files:
            files_list.append(os.path.join(path, name))
    for filename in files_list:
        if not filename.endswith(".json"):
            continue
        if filename.endswith("abstraction.json"):
            continue
        if filename.endswith("mapping.json"):
            continue
        if filename.endswith("important_labels.json"):
            continue
        if filename.count("smt2") > 0:
            continue
        f = open(filename, encoding="utf8")
        data = json.load(f)
        if len(data) == 0 or data.get("timeout") is not None or has_only_phi_size(data):
            if data.get("timeout") is not None:
                points.append(Point(DataSource.THEORY_BDD, 0, 0, 0, 0, 0, 0, 0, 0, 0, filename.replace(
                    source+"/", ''), True, data["timeout"]))
            else:
                points.append(Point(DataSource.THEORY_BDD, 0, 0, 0, 0, 0, 0, 0, 0, 0, filename.replace(
                    source+"/", ''), True, "Unknown"))
            continue
        if data.get("All-SMT computation time") is not None:
            allsmttime = data["All-SMT computation time"]
        else:
            allsmttime = 3600

        if data.get(kind) is not None:
            if data.get(kind).get("total DD computation time") is not None:
                ddtime = data[kind]["total DD computation time"]
            elif data.get(kind).get("total processing time") is not None:
                ddtime = data[kind]["total processing time"]
            else:
                ddtime = 0.1
        else:
            ddtime = 0.1
            ddmodels = None
        
        if kind == "T-dDNNF" or kind == "Abstraction dDNNF":
            if "DIMACS translation time" in data[kind] and "refinement serialization time" in data[kind] and "dDNNF compilation time" in data[kind]:
                ddtime = data[kind]["DIMACS translation time"] + \
                    data[kind]["refinement serialization time"] + \
                    data[kind]["dDNNF compilation time"]
        # if kind == "Abstraction dDNNF":
        #     if "DIMACS translation time" in data[kind] and "refinement serialization time" in data[kind] and "dDNNF compilation time" in data[kind]:
        #         ddtime = data[kind]["DIMACS translation time"] + \
        #             data[kind]["refinement serialization time"] + \
        #             data[kind]["dDNNF compilation time"]

        # TODO()! Change if necessary
        ddmodels = None

        if data.get("T-lemmas amount") is not None:
            tlemmas = data["T-lemmas amount"]
        elif data.get("total lemmas") is not None:
            tlemmas = data["total lemmas"]
        else:
            tlemmas = 0

        if data.get(kind) is not None:
            if data.get(kind).get("DD models") is not None:
                ddmodels = data[kind]["DD models"]
            else:
                ddmodels = None

        if data.get(kind) is not None:
            if "nodes" in data[kind]:
                data[kind]["DD nodes"] = data[kind]["nodes"]
            if data.get(kind).get("DD nodes") is not None:
                ddnodes = data[kind]["DD nodes"]
            else:
                ddnodes = 0
        else:
            ddnodes = 0

        if data.get(kind) is not None:
            if data.get(kind).get("fresh T-atoms detected") is not None:
                fresh_atoms = data[kind]["fresh T-atoms detected"]
            else:
                fresh_atoms = 0
        else:
            fresh_atoms = 0

        if data.get(kind) is not None:
            if data.get(kind).get("fresh T-atoms quantification time") is not None:
                fresh_atoms_quant_time = data[kind]["fresh T-atoms quantification time"]
            else:
                fresh_atoms_quant_time = 0
        else:
            fresh_atoms_quant_time = 0

        data.setdefault("phi size", 0)

        points.append(Point(DataSource.THEORY_BDD,
                            data["phi size"],
                            data["total computation time"],
                            allsmttime,
                            ddtime,
                            ddmodels,
                            ddnodes,
                            tlemmas,
                            fresh_atoms,
                            fresh_atoms_quant_time,
                            filename.replace(source+"/", ''), False, "None"))
    return points


def get_time_points(
        theory_points: List[Point],
        abstraction_points: List[Point],
        timeout_value=None,
        unsat_sources=None) -> Tuple[List[float], List[float], int, List[float], List[float]]:
    """translate data into plottable points comparing time"""
    if unsat_sources is None:
        unsat_sources = []
    theory_points = copy.deepcopy(theory_points)
    abstraction_points = copy.deepcopy(abstraction_points)

    theory_list = []
    abstraction_list = []
    unsat_theory_list = []
    unsat_abstraction_list = []
    max_theory = theory_points[0].computation_time
    max_abstraction = abstraction_points[0].computation_time

    for t_p in theory_points:
        if t_p.computation_time > max_theory:
            max_theory = t_p.computation_time
    for a_p in abstraction_points:
        if a_p.computation_time > max_abstraction:
            max_abstraction = a_p.computation_time

    if timeout_value is not None:
        edge = timeout_value
    else:
        edge = max(max_theory, max_abstraction) * 10

    for t_p in theory_points:
        if t_p.timeout:
            t_p.computation_time = edge
    for a_p in abstraction_points:
        if a_p.timeout:
            a_p.computation_time = edge

    for t_p in theory_points:
        for a_p in abstraction_points:
            if t_p.title == a_p.title:
                if t_p.title in unsat_sources:
                    unsat_theory_list.append(t_p.computation_time)
                    unsat_abstraction_list.append(a_p.computation_time)
                else:
                    theory_list.append(t_p.computation_time)
                    abstraction_list.append(a_p.computation_time)
                break
    return (theory_list, abstraction_list, edge, unsat_theory_list, unsat_abstraction_list)


def get_allsmt_time_points(
        theory_points: List[Point],
        abstraction_points: List[Point]) -> Tuple[List[float], List[float], int]:
    """translate data into plottable points comparing all SMT time"""
    theory_points = copy.deepcopy(theory_points)
    abstraction_points = copy.deepcopy(abstraction_points)

    theory_list = []
    abstraction_list = []
    max_theory = theory_points[0].all_smt_time
    max_abstraction = abstraction_points[0].all_smt_time

    for t_p in theory_points:
        if t_p.all_smt_time > max_theory:
            max_theory = t_p.all_smt_time
    for a_p in abstraction_points:
        if a_p.all_smt_time > max_abstraction:
            max_abstraction = a_p.all_smt_time

    edge = max(max_theory, max_abstraction) * 10

    for t_p in theory_points:
        if t_p.timeout:
            t_p.all_smt_time = edge
    for a_p in abstraction_points:
        if a_p.timeout:
            a_p.all_smt_time = edge

    for t_p in theory_points:
        for a_p in abstraction_points:
            if t_p.title == a_p.title:
                theory_list.append(t_p.all_smt_time)
                abstraction_list.append(a_p.all_smt_time)
                break
    return (theory_list, abstraction_list, edge)


def get_dd_time_points(
        theory_points: List[Point],
        abstraction_points: List[Point],
        timeout_value =None,
        unsat_sources=None) -> Tuple[List[float], List[float], int, List[float], List[float]]:
    """translate data into plottable points comparing all SMT time"""
    if unsat_sources is None:
        unsat_sources = []
    theory_points = copy.deepcopy(theory_points)
    abstraction_points = copy.deepcopy(abstraction_points)

    theory_list = []
    abstraction_list = []
    unsat_theory_list = []
    unsat_abstraction_list = []
    max_theory = theory_points[0].dd_time
    max_abstraction = abstraction_points[0].dd_time

    for t_p in theory_points:
        if t_p.dd_time > max_theory:
            max_theory = t_p.dd_time
    for a_p in abstraction_points:
        if a_p.dd_time > max_abstraction:
            max_abstraction = a_p.dd_time

    if timeout_value is not None:
        edge = timeout_value
    else:
        edge = max(max_theory, max_abstraction) * 10

    for t_p in theory_points:
        if t_p.timeout:
            t_p.dd_time = edge
    for a_p in abstraction_points:
        if a_p.timeout:
            a_p.dd_time = edge

    for t_p in theory_points:
        for a_p in abstraction_points:
            if t_p.title == a_p.title:
                if t_p.title in unsat_sources:
                    unsat_theory_list.append(t_p.dd_time)
                    unsat_abstraction_list.append(a_p.dd_time)
                else:
                    theory_list.append(t_p.dd_time)
                    abstraction_list.append(a_p.dd_time)
                break
    return (theory_list, abstraction_list, edge, unsat_theory_list, unsat_abstraction_list)


def get_lemmas_points(
        theory_points: List[Point],
        abstraction_points: List[Point]) -> Tuple[List[float], List[float], int]:
    """translate data into plottable points comparing DD size in nodes"""
    theory_points = copy.deepcopy(theory_points)
    abstraction_points = copy.deepcopy(abstraction_points)

    theory_list = []
    abstraction_list = []
    max_theory = theory_points[0].total_lemmas
    max_abstraction = abstraction_points[0].total_lemmas

    for t_p in theory_points:
        if t_p.total_lemmas > max_theory:
            max_theory = t_p.total_lemmas
    for a_p in abstraction_points:
        if a_p.total_lemmas > max_abstraction:
            max_abstraction = a_p.total_lemmas

    edge = max(max_theory, max_abstraction) * 2

    for t_p in theory_points:
        if t_p.timeout:
            t_p.dd_nodes = edge
    for a_p in abstraction_points:
        if a_p.timeout:
            a_p.dd_nodes = edge

    for t_p in theory_points:
        for a_p in abstraction_points:
            if t_p.title == a_p.title and not t_p.timeout and not a_p.timeout:
                theory_list.append(t_p.total_lemmas)
                abstraction_list.append(a_p.total_lemmas)
                break
    return (theory_list, abstraction_list, edge)


def get_nodes_points(
        theory_points: List[Point],
        abstraction_points: List[Point]) -> Tuple[List[float], List[float], int]:
    """translate data into plottable points comparing DD size in nodes"""
    theory_points = copy.deepcopy(theory_points)
    abstraction_points = copy.deepcopy(abstraction_points)

    theory_list = []
    abstraction_list = []
    max_theory = theory_points[0].dd_nodes
    max_abstraction = abstraction_points[0].dd_nodes

    for t_p in theory_points:
        if t_p.dd_nodes > max_theory:
            max_theory = t_p.dd_nodes
    for a_p in abstraction_points:
        if a_p.dd_nodes > max_abstraction:
            max_abstraction = a_p.dd_nodes

    edge = max(max_theory, max_abstraction) * 2

    for t_p in theory_points:
        if t_p.timeout:
            t_p.dd_nodes = edge
    for a_p in abstraction_points:
        if a_p.timeout:
            a_p.dd_nodes = edge

    # count11 = 0
    for t_p in theory_points:
        for a_p in abstraction_points:
            if t_p.title == a_p.title and not t_p.timeout and not a_p.timeout:
                # if t_p.dd_nodes == 1 and a_p.dd_nodes == 1:
                #     count11 += 1
                theory_list.append(t_p.dd_nodes)
                abstraction_list.append(a_p.dd_nodes)
                break
    # print("Count 1 1", count11)
    return (theory_list, abstraction_list, edge)


def get_dd_fresh_atoms_points(
        theory_points: List[Point],
        abstraction_points: List[Point]) -> Tuple[List[float], List[float], int]:
    """translate data into plottable points comparing amount of fresh T-atoms"""
    theory_list = []
    abstraction_list = []
    max_theory = theory_points[0].fresh_atoms
    max_abstraction = abstraction_points[0].fresh_atoms

    theory_points = copy.deepcopy(theory_points)
    abstraction_points = copy.deepcopy(abstraction_points)

    for t_p in theory_points:
        if t_p.fresh_atoms is not None and (max_theory is None or t_p.fresh_atoms > max_theory):
            max_theory = t_p.fresh_atoms
    for a_p in abstraction_points:
        if a_p.fresh_atoms is not None and (max_abstraction is None or a_p.fresh_atoms > max_abstraction):
            max_abstraction = a_p.fresh_atoms
    if max_abstraction is None or max_theory is None:
        raise Exception("Un-plottable data provided!!!")

    edge = max(max_theory, max_abstraction) * 10

    # for t_p in theory_points:
    #     if t_p.timeout:
    #         t_p.fresh_atoms = edge
    # for a_p in abstraction_points:
    #     if a_p.timeout:
    #         a_p.fresh_atoms = edge

    for t_p in theory_points:
        for a_p in abstraction_points:
            if t_p.title == a_p.title and not t_p.timeout and not a_p.timeout:
                # print(t_p.fresh_atoms_quantification_time,a_p.fresh_atoms_quantification_time)
                theory_list.append(t_p.fresh_atoms)
                abstraction_list.append(a_p.fresh_atoms)
                break
    return (theory_list, abstraction_list, edge)


def get_timeout_map(points: List[Point]) -> Dict[str, int]:
    """returns a map of the timeout kinds and their counts"""
    timeout_map = {}
    for p in points:
        if p.timeout_kind not in timeout_map:
            timeout_map[p.timeout_kind] = 1
        else:
            timeout_map[p.timeout_kind] += 1
    timeout_map.pop("None", None)
    total_timeouts = 0
    for v in timeout_map.values():
        total_timeouts += v
    timeout_map["Total"] = total_timeouts
    return timeout_map


def get_phi_size_vs_dd_nodes_points(
        theory_points: List[Point]) -> Tuple[List[int], List[int], int]:
    """translate data into plottable points comparing phi size and DD size in nodes"""
    max_size = 0
    phi_size_points = []
    dd_nodes_points = []
    for item in theory_points:
        if item.timeout:
            continue
        if item.phi_size > max_size:
            max_size = item.phi_size
        if item.dd_nodes is not None:
            phi_size_points.append(item.phi_size)
            dd_nodes_points.append(item.dd_nodes)
            if item.dd_nodes > max_size:
                max_size = item.dd_nodes

    edge = max_size + 3
    return (phi_size_points, dd_nodes_points, edge)

def get_phi_size_vs_lemmas_points(
        theory_points: List[Point]) -> Tuple[List[int], List[int], int]:
    """translate data into plottable points comparing phi size and amount of lemmas"""
    max_size = 0
    phi_size_points = []
    lemmas_points = []
    for item in theory_points:
        if item.timeout:
            continue
        if item.phi_size > max_size:
            max_size = item.phi_size
        if item.total_lemmas is not None:
            phi_size_points.append(item.phi_size)
            lemmas_points.append(item.total_lemmas)
            if item.total_lemmas > max_size:
                max_size = item.total_lemmas

    edge = max_size * 10
    return (phi_size_points, lemmas_points, edge)


def get_dd_models_points(
        theory_points: List[Point],
        abstraction_points: List[Point]) -> Tuple[List[float], List[float], int]:
    """translate data into plottable points comparing DD size in nodes"""
    theory_list = []
    abstraction_list = []
    max_theory = theory_points[0].dd_models
    max_abstraction = abstraction_points[0].dd_models

    theory_points = copy.deepcopy(theory_points)
    abstraction_points = copy.deepcopy(abstraction_points)

    for t_p in theory_points:
        if t_p.dd_models is not None and (max_theory is None or t_p.dd_models > max_theory):
            max_theory = t_p.dd_models
    for a_p in abstraction_points:
        if a_p.dd_models is not None and (max_abstraction is None or a_p.dd_models > max_abstraction):
            max_abstraction = a_p.dd_models

    if max_abstraction is None or max_theory is None:
        raise Exception("Un-plottable data provided!!!")

    edge = max(max_theory, max_abstraction) * 10

    for t_p in theory_points:
        if t_p.timeout:
            t_p.dd_models = edge
    for a_p in abstraction_points:
        if a_p.timeout:
            a_p.dd_models = edge

    # count11 = 0
    for t_p in theory_points:
        for a_p in abstraction_points:
            if t_p.title == a_p.title and t_p.dd_models is not None and a_p.dd_models is not None and not t_p.timeout and not a_p.timeout:
                # if a_p.dd_models < t_p.dd_models:
                #     print(a_p.title)
                # if t_p.dd_nodes == 1 and a_p.dd_nodes == 1:
                #     count11 += 1
                # if t_p.dd_models > 10**30:
                #     print(t_p.title)
                # if a_p.dd_models > 10**30:
                #     print(a_p.title)
                # if(a_p.dd_models > 0):
                #     print(1-t_p.dd_models/a_p.dd_models)
                # else:
                #     print(t_p.dd_models, a_p.dd_models)
                #     print(t_p.title)
                theory_list.append(t_p.dd_models)
                abstraction_list.append(a_p.dd_models)
                break
    # print("Count 1 1", count11)
    return (theory_list, abstraction_list, edge)


def build_graphs(time_points, size_points, x_label: str, y_label: str) -> None:
    """builds and displays graphs"""
    build_time_graph(time_points, x_label, y_label)
    build_size_graph(size_points, x_label, y_label)


def build_time_graph(time_points, x_label: str, y_label: str, file: str | None = None,
                     secondary_ponts = None) -> None:
    """builds and displays the time graph"""
    if secondary_ponts is not None:
        plt.scatter(secondary_ponts[0], secondary_ponts[1], marker='x', color='#b30000')
    plt.scatter(time_points[0], time_points[1], marker='x')
    if len(time_points) > 3:
        plt.scatter(time_points[3], time_points[4], marker='x', color='#00b300')
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    # plt.title("Computation Time")
    ax = plt.gca()
    ax.set_yscale('log')
    ax.set_xscale('log')
    ax.set_aspect('equal', adjustable='box')
    diag_line, = ax.plot(ax.get_xlim(), ax.get_ylim(), ls=":", c=".3")

    multiplier = 0.001
    while multiplier < time_points[2]:
        plt.plot([0.0001, time_points[2]], [multiplier, time_points[2]
                 * multiplier*10000], 'r-', ls=":", c=".3", alpha=0.2)
        plt.plot([multiplier, time_points[2]*multiplier*10000],
                 [0.0001, time_points[2]], 'r-', ls=":", c=".3", alpha=0.2)
        multiplier = multiplier*10

    def on_change_time(_axes):
        x_lims = ax.get_xlim()
        y_lims = ax.get_ylim()
        diag_line.set_data(x_lims, y_lims)
    ax.callbacks.connect('xlim_changed', on_change_time)
    ax.callbacks.connect('ylim_changed', on_change_time)
    plt.axvline(x=time_points[2], ls="--", c=".3")
    plt.axhline(y=time_points[2], ls="--", c=".3")
    plt.xlim((0.0001, 10*time_points[2]))
    plt.ylim((0.0001, 10*time_points[2]))
    # plt.axis('square')

    if file is not None:
        plt.savefig(file, bbox_inches='tight')
    plt.show()


def build_size_graph(size_points, x_label: str, y_label: str, file: str | None = None, 
                     no_central_diagonal: bool = False) -> None:
    """builds and shows the size graph"""
    plt.scatter(size_points[0], size_points[1], marker='x')
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    # plt.title("DD size in nodes")
    ax = plt.gca()
    ax.set_yscale('log')
    ax.set_xscale('log')
    ax.set_aspect('equal', adjustable='box')
    if no_central_diagonal:
        diag_line, = ax.plot(ax.get_xlim(), ax.get_ylim(), ls=":", c=".3", alpha=0.2)
    else:
        diag_line, = ax.plot(ax.get_xlim(), ax.get_ylim(), ls=":", c=".3")

    multiplier = 10
    while multiplier < size_points[2]:
        plt.plot([1, size_points[2]], [multiplier, size_points[2]
                 * multiplier], 'r-', ls=":", c=".3", alpha=0.2)
        plt.plot([multiplier, size_points[2]*multiplier],
                 [1, size_points[2]], 'r-', ls=":", c=".3", alpha=0.2)
        multiplier = multiplier*10

    def on_change(_axes):
        x_lims = ax.get_xlim()
        y_lims = ax.get_ylim()
        diag_line.set_data(x_lims, y_lims)
    ax.callbacks.connect('xlim_changed', on_change)
    ax.callbacks.connect('ylim_changed', on_change)
    # plt.axis('square')
    # plt.axvline(x=size_points[2], ls="--", c=".3")
    # plt.axhline(y=size_points[2], ls="--", c=".3")
    plt.xlim((1, size_points[2]))
    plt.ylim((1, size_points[2]))

    if file is not None:
        plt.savefig(file, bbox_inches='tight')
    plt.show()


def build_models_graph(points, x_label: str, y_label: str, file: str | None = None) -> None:
    """builds and shows the model count graph"""
    plt.scatter(points[0], points[1], marker='x')
    plt.xlabel(x_label)
    plt.ylabel(y_label)

    # plt.title("DD amount of models")
    ax = plt.gca()
    ax.set_yscale('log')
    ax.set_xscale('log')
    ax.set_aspect('equal', adjustable='box')
    diag_line, = ax.plot(ax.get_xlim(), ax.get_ylim(), ls=":", c=".3")

    multiplier = 1000
    while multiplier < points[2]:
        plt.plot([1, points[2]], [multiplier, points[2]*multiplier],
                 'r-', ls=":", c=".3", alpha=0.2)
        plt.plot([multiplier, points[2]*multiplier],
                 [1, points[2]], 'r-', ls=":", c=".3", alpha=0.2)
        multiplier = multiplier*1000

    def on_change(_axes):
        x_lims = ax.get_xlim()
        y_lims = ax.get_ylim()
        diag_line.set_data(x_lims, y_lims)
    ax.callbacks.connect('xlim_changed', on_change)
    ax.callbacks.connect('ylim_changed', on_change)
    # plt.axis('square')
    # plt.axvline(x=points[2], ls="--", c=".3")
    # plt.axhline(y=points[2], ls="--", c=".3")
    plt.xlim((1, points[2]*10))
    plt.ylim((1, points[2]*10))

    if file is not None:
        plt.savefig(file, bbox_inches='tight')
    plt.show()


def build_lemmas_graph(points, x_label: str, y_label: str, file: str | None = None) -> None:
    """builds and shows the model count graph"""
    plt.scatter(points[0], points[1], marker='x')
    plt.xlabel(x_label)
    plt.ylabel(y_label)

    # plt.title("DD amount of models")
    ax = plt.gca()
    ax.set_yscale('log')
    ax.set_xscale('log')
    ax.set_aspect('equal', adjustable='box')
    diag_line, = ax.plot(ax.get_xlim(), ax.get_ylim(), ls=":", c=".3")

    multiplier = 1000
    while multiplier < points[2]:
        plt.plot([1, points[2]], [multiplier, points[2]*multiplier],
                 'r-', ls=":", c=".3", alpha=0.2)
        plt.plot([multiplier, points[2]*multiplier],
                 [1, points[2]], 'r-', ls=":", c=".3", alpha=0.2)
        multiplier = multiplier*1000

    def on_change(_axes):
        x_lims = ax.get_xlim()
        y_lims = ax.get_ylim()
        diag_line.set_data(x_lims, y_lims)
    ax.callbacks.connect('xlim_changed', on_change)
    ax.callbacks.connect('ylim_changed', on_change)
    # plt.axis('square')
    # plt.axvline(x=points[2], ls="--", c=".3")
    # plt.axhline(y=points[2], ls="--", c=".3")
    plt.xlim((1, points[2]*10))
    plt.ylim((1, points[2]*10))

    if file is not None:
        plt.savefig(file, bbox_inches='tight')
    plt.show()


def build_phi_size_vs_dd_size_graph(points, x_label: str, y_label: str, file: str | None = None) -> None:
    """builds and shows the model count graph"""
    plt.scatter(points[0], points[1], marker='x')
    plt.xlabel(x_label)
    plt.ylabel(y_label)

    # plt.title("DD amount of models")
    ax = plt.gca()
    ax.set_yscale('log')
    ax.set_xscale('log')
    ax.set_aspect('equal', adjustable='box')
    diag_line, = ax.plot(ax.get_xlim(), ax.get_ylim(), ls=":", c=".3", alpha=0.2)

    multiplier = 100
    while multiplier < points[2]:
        plt.plot([1, points[2]], [multiplier, points[2]*multiplier],
                 'r-', ls=":", c=".3", alpha=0.2)
        plt.plot([multiplier, points[2]*multiplier],
                 [1, points[2]], 'r-', ls=":", c=".3", alpha=0.2)
        multiplier = multiplier * 100

    def on_change(_axes):
        x_lims = ax.get_xlim()
        y_lims = ax.get_ylim()
        diag_line.set_data(x_lims, y_lims)
    ax.callbacks.connect('xlim_changed', on_change)
    ax.callbacks.connect('ylim_changed', on_change)
    # plt.axis('square')
    # plt.axvline(x=points[2], ls="--", c=".3")
    # plt.axhline(y=points[2], ls="--", c=".3")
    plt.xlim((1, points[2]*10))
    plt.ylim((1, points[2]*10))

    if file is not None:
        plt.savefig(file, bbox_inches='tight')
    plt.show()


def timeout_to_str(points: List[Point]) -> str:
    """returns a string of the timeout kinds and their counts"""
    timeout_map = get_timeout_map(points)
    timeout_str = ""
    for k, v in timeout_map.items():
        timeout_str += "[" + k + ": " + str(v) + "] "
    return timeout_str


def main() -> None:
    """main function"""
    # --------------------------------------------------------------
    # WMI

    # wmi_bdds_points = get_wmi_bench_data(
    #     "BDD", "benchmarks/wmi/output")
    # wmi_abstraction_bdd_points = get_wmi_bench_data(
    #     "BDD", "benchmarks/wmi/output_abstraction")
    # wmi_sdds_points = get_wmi_bench_data(
    #     "SDD", "benchmarks/wmi/output_sdd")
    # wmi_abstraction_sdd_points = get_wmi_bench_data(
    #     "SDD", "benchmarks/wmi/output_abstraction_sdd")

    # print("WMI BDD graphs")
    # time_points = get_time_points(
    #     wmi_bdds_points, wmi_abstraction_bdd_points)
    # size_points = get_nodes_points(
    #     wmi_bdds_points, wmi_abstraction_bdd_points)
    # models_points = get_dd_models_points(
    #     wmi_bdds_points, wmi_abstraction_bdd_points)
    # build_time_graph(time_points, "T-OBDD", "Abs. BDD",
    #                  "plots/wmi/abstr_bdd_vs_tbdd_time.pdf")
    # build_size_graph(size_points, "T-OBDD", "Abs. BDD",
    #                  "plots/wmi/abstr_bdd_vs_tbdd_size.pdf")
    # build_models_graph(models_points, "T-OBDD", "Abs. BDD",
    #                    "plots/wmi/abstr_bdd_vs_tbdd_models.pdf")

    # print("WMI SDD graphs")
    # time_points = get_time_points(
    #     wmi_sdds_points, wmi_abstraction_sdd_points)
    # size_points = get_nodes_points(
    #     wmi_sdds_points, wmi_abstraction_sdd_points)
    # build_time_graph(time_points, "T-SDD", "Abs. SDD",
    #                  "plots/wmi/abstr_sdd_vs_tsdd_time.pdf")
    # build_size_graph(size_points, "T-SDD", "Abs. SDD",
    #                  "plots/wmi/abstr_sdd_vs_tsdd_size.pdf")

    # --------------------------------------------------------------
    # LDD RANDGEN

    ldd_randgen_ldds_points = get_ldd_randgen_bench_data(
        "LDD", "benchmarks/ldd_randgen/output_ldd")
    print("LDD randgen size: ", len(ldd_randgen_ldds_points))
    print("Timeouts of LDDs on LDD randgen: ",
          timeout_to_str(ldd_randgen_ldds_points))
    ldd_randgen_bdds_points = get_ldd_randgen_bench_data(
        "T-BDD", "benchmarks/ldd_randgen/output_tbdd_total")
    print("Timeouts of T-BDDs on LDD randgen: ",
          timeout_to_str(ldd_randgen_bdds_points))
    # ldd_randgen_bdds_fp_points = get_ldd_randgen_bench_data(
    #     "T-BDD", "benchmarks/ldd_randgen/output_tbdd_full_partial")
    # print("Timeouts of full partial T-BDDs on LDD randgen: ",
    #       timeout_to_str(ldd_randgen_bdds_fp_points))
    ldd_randgen_abstraction_bdd_points = get_ldd_randgen_bench_data(
        "Abstraction BDD", "benchmarks/ldd_randgen/output_abstraction")
    print("Timeouts of Abs-BDDs on LDD randgen: ",
          timeout_to_str(ldd_randgen_abstraction_bdd_points))
    ldd_randgen_sdds_points = get_ldd_randgen_bench_data(
        "T-SDD", "benchmarks/ldd_randgen/output_sdd")
    print("Timeouts of T-SDDs on LDD randgen: ",
          timeout_to_str(ldd_randgen_sdds_points))
    ldd_randgen_abstraction_sdd_points = get_ldd_randgen_bench_data(
        "Abstraction SDD", "benchmarks/ldd_randgen/output_abstraction_sdd")
    print("Timeouts of Abs-SDDs on LDD randgen: ",
          timeout_to_str(ldd_randgen_abstraction_sdd_points))
    # ldd_randgen_bdds_points_noeqsplit = get_ldd_randgen_bench_data(
    #     "T-BDD", "benchmarks/ldd_randgen/output_tbdd_total")
    # print("Timeouts of T-BDDs on LDD randgen (no eq split): ",
    #       timeout_to_str(ldd_randgen_bdds_points_noeqsplit))
    # ldd_randgen_ddnnf_partial_points = get_ldd_randgen_bench_data(
    #     "T-dDNNF", "benchmarks/ldd_randgen/output_dDNNF_fp")
    # print("Timeouts of T-dDNNFs fp on LDD randgen: ",
    #       timeout_to_str(ldd_randgen_ddnnf_partial_points))
    ldd_randgen_ddnnf_abstract_c2d_points = get_ldd_randgen_bench_data(
        "Abstraction dDNNF", "benchmarks/ldd_randgen/output_abstraction_ddnnf_c2d")
    print("Timeouts of Abstraction dDNNFs C2D on LDD randgen: ",
          timeout_to_str(ldd_randgen_ddnnf_abstract_c2d_points))
    ldd_randgen_ddnnf_abstract_d4_points = get_ldd_randgen_bench_data(
        "Abstraction dDNNF", "benchmarks/ldd_randgen/output_abstraction_ddnnf_d4")
    print("Timeouts of Abstraction dDNNFs D4 on LDD randgen: ",
          timeout_to_str(ldd_randgen_ddnnf_abstract_d4_points))
    # ldd_randgen_sample_points = get_ldd_randgen_bench_data(
    #     "T-dDNNF", "benchmarks/ldd_randgen/output_dDNNF_sample")
    # print("Timeouts of T-dDNNFs sample on LDD randgen: ",
    #       timeout_to_str(ldd_randgen_sample_points))
    # ldd_randgen_sdd_full_partial_points = get_ldd_randgen_bench_data(
    #     "T-SDD", "benchmarks/ldd_randgen/output_sdd_full_partial")
    # print("Timeouts of T-SDDs full partial on LDD randgen: ",
    #       timeout_to_str(ldd_randgen_sdd_full_partial_points))

    # ldd_randgen_allsmt_total_points = get_ldd_randgen_bench_data(
    #     "NoDD", "benchmarks/ldd_randgen/tmp_total")
    # ldd_randgen_allsmt_partial_points = get_ldd_randgen_bench_data(
    #     "NoDD", "benchmarks/ldd_randgen/tmp_full_partial")
    # ldd_randgen_allsmt_tabular_total_points = get_ldd_randgen_bench_data(
    #     "NoDD", "benchmarks/ldd_randgen/tmp_tabular_total")
    
    # time_points = get_allsmt_time_points(
    #     ldd_randgen_allsmt_total_points,ldd_randgen_allsmt_tabular_total_points
    # )
    # build_time_graph(time_points, "MathSAT", "Tabular",
    #                     "plots/ldd_randgen/allsmt_total_vs_tabular_total_time.pdf")
                     

    ldd_randgen_ddnnf_c2d_total_points = get_ldd_randgen_bench_data(
        "T-dDNNF", "benchmarks/ldd_randgen/output_tddnnf_c2d_total_new")
    print("Timeouts of T-dDNNFs c2d on LDD randgen: ",
          timeout_to_str(ldd_randgen_ddnnf_c2d_total_points))
    ldd_randgen_ddnnf_c2d_total_not_quantified_points = get_ldd_randgen_bench_data(
        "T-dDNNF", "benchmarks/ldd_randgen/output_tddnnf_c2d_not_quantified_total_new")
    print("Timeouts of T-dDNNFs c2d (no quant) on LDD randgen: ",
          timeout_to_str(ldd_randgen_ddnnf_c2d_total_not_quantified_points))
    ldd_randgen_ddnnf_d4_total_points = get_ldd_randgen_bench_data(
        "T-dDNNF", "benchmarks/ldd_randgen/output_tddnnf_d4_total_new")
    print("Timeouts of T-dDNNFs d4 on LDD randgen: ",
          timeout_to_str(ldd_randgen_ddnnf_d4_total_points))
    ldd_randgen_ddnnf_d4_total_not_quantified_points = get_ldd_randgen_bench_data(
        "T-dDNNF", "benchmarks/ldd_randgen/output_tddnnf_d4_not_quantified_total_new")
    print("Timeouts of T-dDNNFs d4 (no quant) on LDD randgen: ",
          timeout_to_str(ldd_randgen_ddnnf_d4_total_not_quantified_points))
    
    ldd_randgen_unsat_points = get_list_of_unsat_problems(
        "benchmarks/ldd_randgen/output_tbdd_total")
    print(ldd_randgen_unsat_points)

    # # T-dDNNF size vs phi size
    # size_points = get_phi_size_vs_dd_nodes_points(
    #     ldd_randgen_ddnnf_c2d_total_points)
    # build_phi_size_vs_dd_size_graph(size_points, "Phi size", "T-dDNNF size",
    #                                 "plots/ldd_randgen/ddnnf_c2d_phi_size_vs_dd_size.pdf")

    # size_points = get_phi_size_vs_dd_nodes_points(
    #     ldd_randgen_ddnnf_c2d_total_not_quantified_points)
    # build_phi_size_vs_dd_size_graph(size_points, "Phi size", "T-dDNNF size",
    #                                 "plots/ldd_randgen/ddnnf_c2d_phi_size_vs_dd_size_no_quant.pdf")

    # size_points = get_phi_size_vs_dd_nodes_points(
    #     ldd_randgen_ddnnf_abstract_d4_points)
    # build_phi_size_vs_dd_size_graph(size_points, "Phi size", "dDNNF size",
    #                                 "plots/ldd_randgen/abstract_ddnnf_d4_phi_size_vs_dd_size.pdf")
    
    # size_points = get_phi_size_vs_dd_nodes_points(
    #     ldd_randgen_ddnnf_abstract_c2d_points)
    # build_phi_size_vs_dd_size_graph(size_points, "Phi size", "dDNNF size",
    #                                 "plots/ldd_randgen/abstract_ddnnf_c2d_phi_size_vs_dd_size.pdf")
    
    # size_points = get_phi_size_vs_dd_nodes_points(
    #     ldd_randgen_ddnnf_d4_total_points)
    # build_phi_size_vs_dd_size_graph(size_points, "Phi size", "T-dDNNF size",
    # #                                 "plots/ldd_randgen/ddnnf_d4_phi_size_vs_dd_size.pdf")

    # # size_points = get_phi_size_vs_dd_nodes_points(
    # #     ldd_randgen_ddnnf_d4_total_not_quantified_points)
    # # build_phi_size_vs_dd_size_graph(size_points, "Phi size", "T-dDNNF size",
    # #                                 "plots/ldd_randgen/ddnnf_d4_phi_size_vs_dd_size_no_quant.pdf")
    
    # # size_points = get_phi_size_vs_dd_nodes_points(
    # #     ldd_randgen_bdds_points)
    # # build_phi_size_vs_dd_size_graph(size_points, "Phi size", "T-OBDD size",
    # #                                 "plots/ldd_randgen/bdd_phi_size_vs_dd_size.pdf")
    
    # # size_points = get_phi_size_vs_dd_nodes_points(
    # #     ldd_randgen_sdds_points)
    # # build_phi_size_vs_dd_size_graph(size_points, "Phi size", "T-SDD size",
    # #                                 "plots/ldd_randgen/sdd_phi_size_vs_dd_size.pdf")
    
    # # size_points = get_nodes_points(
    # #     ldd_randgen_ddnnf_c2d_total_points, ldd_randgen_ddnnf_abstract_c2d_points)
    # # build_size_graph(size_points, "T-dDNNF", "Abstr. dDNNF",
    # #                  "plots/ldd_randgen/ddnnf_c2d_vs_ddnnf_abstr_size.pdf")
    
    time_points = get_time_points(
        ldd_randgen_ddnnf_c2d_total_points, ldd_randgen_ddnnf_abstract_c2d_points)
    time_points_dd = get_dd_time_points(
        ldd_randgen_ddnnf_c2d_total_points, ldd_randgen_ddnnf_abstract_c2d_points,
        timeout_value=time_points[2])
    build_time_graph(time_points, "T-dDNNF", "Abstr. dDNNF",
                     "plots/ldd_randgen/ddnnf_c2d_vs_ddnnf_abstr_time.pdf")
    #                  secondary_ponts=time_points_dd)
    build_time_graph(time_points_dd, "T-dDNNF", "Abstr. dDNNF",
                     "plots/ldd_randgen/ddnnf_c2d_vs_ddnnf_abstr_dd_time.pdf")
    
    # # size_points = get_nodes_points(
    # #     ldd_randgen_ddnnf_d4_total_points, ldd_randgen_ddnnf_abstract_d4_points)
    # # build_size_graph(size_points, "T-dDNNF", "Abstr. dDNNF",
    # #                  "plots/ldd_randgen/ddnnf_d4_vs_ddnnf_abstr_size.pdf")
    
    time_points = get_time_points(
        ldd_randgen_ddnnf_d4_total_points, ldd_randgen_ddnnf_abstract_d4_points)
    time_points_dd = get_dd_time_points(
        ldd_randgen_ddnnf_d4_total_points, ldd_randgen_ddnnf_abstract_d4_points,
        timeout_value=time_points[2])
    build_time_graph(time_points, "T-dDNNF", "Abstr. dDNNF",
                     "plots/ldd_randgen/ddnnf_d4_vs_ddnnf_abstr_time.pdf")
    #                  secondary_ponts=time_points_dd)
    build_time_graph(time_points_dd, "T-dDNNF", "Abstr. dDNNF",
                     "plots/ldd_randgen/ddnnf_d4_vs_ddnnf_abstr_dd_time.pdf")
    
    # size_points = get_phi_size_vs_dd_nodes_points(
    #     ldd_randgen_abstraction_bdd_points)
    # build_phi_size_vs_dd_size_graph(size_points, "Phi size", "Abstr. OBDD size",
    #                                 "plots/ldd_randgen/abstract_bdd_phi_size_vs_dd_size.pdf")
    
    # size_points = get_phi_size_vs_dd_nodes_points(
    #     ldd_randgen_abstraction_sdd_points)
    # build_phi_size_vs_dd_size_graph(size_points, "Phi size", "Abstr. SDD size",
    #                                 "plots/ldd_randgen/abstract_sdd_vs_phi_size.pdf")
    
    # size_points = get_nodes_points(
    #     ldd_randgen_bdds_points, ldd_randgen_abstraction_bdd_points)
    # build_size_graph(size_points, "T-OBDD", "Abs. OBDD",
    #                  "plots/ldd_randgen/abstr_bdd_vs_tbdd_size.pdf")
    
    # size_points = get_nodes_points(
    #     ldd_randgen_sdds_points, ldd_randgen_abstraction_sdd_points)
    # build_size_graph(size_points, "T-SDD", "Abs. SDD",
    #                  "plots/ldd_randgen/abstr_sdd_vs_tsdd_size.pdf")
    
    # size_points = get_phi_size_vs_lemmas_points(
    #     ldd_randgen_bdds_points
    # )
    # build_size_graph(size_points, "Phi size", "Amount of lemmas",
    #                  "plots/ldd_randgen/phi_size_vs_lemmas.pdf", no_central_diagonal=True)
    
    
    # time_points = get_dd_time_points(
    #         ldd_randgen_ddnnf_d4_total_points, ldd_randgen_ddnnf_d4_total_not_quantified_points)
    # build_time_graph(time_points, "Total enum. T-dDNNF", "Total enum. T-dDNNF (no quant)",
    #                  "plots/ldd_randgen/ddnnf_d4_total_vs_no_quant_time.pdf")
    
    # time_points = get_dd_time_points(
    #     ldd_randgen_ddnnf_c2d_total_points, ldd_randgen_ddnnf_c2d_total_not_quantified_points)
    # build_time_graph(time_points, "Total enum. T-dDNNF", "Total enum. T-dDNNF (no quant)",
    #                  "plots/ldd_randgen/ddnnf_c2d_total_vs_no_quant_time.pdf")


    # dDNNF
    # dDNNF partial vs total
    # time_points = get_time_points(
    #     ldd_randgen_ddnnf_total_points, ldd_randgen_ddnnf_partial_points)
    # build_time_graph(time_points, "Total enum. T-dDNNF", "Partial enum. T-dDNNF",
    #                  "plots/ldd_randgen/ddnnf_partial_vs_total_time.pdf")
    # size_points = get_nodes_points(
    #     ldd_randgen_ddnnf_total_points, ldd_randgen_ddnnf_partial_points)
    # build_size_graph(size_points, "Total enum. T-dDNNF", "Partial enum. T-dDNNF",
    #                  "plots/ldd_randgen/ddnnf_partial_vs_total_size.pdf")
    # dDNNF abstract vs total
    # time_points = get_time_points(
    #     ldd_randgen_ddnnf_total_points, ldd_randgen_ddnnf_abstract_points)
    # build_time_graph(time_points, "Total enum. T-dDNNF", "Abstraction dDNNF",
    #                  "plots/ldd_randgen/ddnnf_abstract_vs_total_time.pdf")
    # size_points = get_nodes_points(
    #     ldd_randgen_ddnnf_total_points, ldd_randgen_ddnnf_abstract_points)
    # build_size_graph(size_points, "Total enum. T-dDNNF", "Abstraction dDNNF",
    #                  "plots/ldd_randgen/ddnnf_abstract_vs_total_size.pdf")
    # dDNNF abstract vs partial
    # time_points = get_time_points(
    #     ldd_randgen_ddnnf_partial_points, ldd_randgen_ddnnf_abstract_points)
    # build_time_graph(time_points, "Partial enum. T-dDNNF", "Abstraction dDNNF",
    #                  "plots/ldd_randgen/ddnnf_abstract_vs_partial_time.pdf")
    # size_points = get_nodes_points(
    #     ldd_randgen_ddnnf_partial_points, ldd_randgen_ddnnf_abstract_points)
    # build_size_graph(size_points, "Partial enum. T-dDNNF", "Abstraction dDNNF",
    #                  "plots/ldd_randgen/ddnnf_abstract_vs_partial_size.pdf")
    # dDNNF vs BDD
    # time_points = get_time_points(
    #     ldd_randgen_ddnnf_partial_points, ldd_randgen_bdds_points_noeqsplit)
    # build_time_graph(time_points, "Partial T-dDNNF", "T-BDD",
    #                  "plots/ldd_randgen/ddnnf_vs_bdd_time.pdf")

    # # BDD total vs partial
    # time_points = get_time_points(
    #     ldd_randgen_bdds_points, ldd_randgen_bdds_fp_points)
    # build_time_graph(time_points, "Total T-BDD", "Partial T-BDD",
    #                  "plots/ldd_randgen/bdd_partial_vs_total_time.pdf")
    # size_points = get_nodes_points(
    #     ldd_randgen_bdds_points, ldd_randgen_bdds_fp_points)
    # build_size_graph(size_points, "Total T-BDD", "Partial T-BDD",
    #                  "plots/ldd_randgen/bdd_partial_vs_total_size.pdf")
    # models_points = get_dd_models_points(
    #     ldd_randgen_bdds_points, ldd_randgen_bdds_fp_points)
    # build_models_graph(models_points, "Total T-BDD", "Partial T-BDD",
    #                    "plots/ldd_randgen/bdd_partial_vs_total_models.pdf")

    # # SDD total vs partial
    # time_points = get_time_points(
    #     ldd_randgen_sdds_points, ldd_randgen_sdd_full_partial_points)
    # build_time_graph(time_points, "Total T-SDD", "Partial T-SDD",
    #                  "plots/ldd_randgen/sdd_partial_vs_total_time.pdf")
    # size_points = get_nodes_points(
    #     ldd_randgen_sdds_points, ldd_randgen_sdd_full_partial_points)
    # build_size_graph(size_points, "Total T-SDD", "Partial T-SDD",
    #                  "plots/ldd_randgen/sdd_partial_vs_total_size.pdf")

    # # Partial BDD vs LDD
    # time_points = get_time_points(
    #     ldd_randgen_bdds_fp_points, ldd_randgen_ldds_points)
    # build_time_graph(time_points, "Partial T-BDD", "LDD",
    #                  "plots/ldd_randgen/bdd_partial_vs_ldd_time.pdf")
    # size_points = get_nodes_points(
    #     ldd_randgen_bdds_fp_points, ldd_randgen_ldds_points)
    # build_size_graph(size_points, "Partial T-BDD", "LDD",
    #                  "plots/ldd_randgen/bdd_partial_vs_ldd_size.pdf")
    # models_points = get_dd_models_points(
    #     ldd_randgen_bdds_fp_points, ldd_randgen_ldds_points)
    # build_models_graph(models_points, "Partial T-BDD", "LDD",
    #                    "plots/ldd_randgen/bdd_partial_vs_ldd_models.pdf")

    # # Partial DDNNF vs sample
    # time_points = get_time_points(
    #     ldd_randgen_ddnnf_partial_points, ldd_randgen_sample_points)
    # build_time_graph(time_points, "Partial T-dDNNF", "Sample T-dDNNF",
    #                  "plots/ldd_randgen/ddnnf_partial_vs_sample_time.pdf")
    # size_points = get_nodes_points(
    #     ldd_randgen_ddnnf_partial_points, ldd_randgen_sample_points)
    # build_size_graph(size_points, "Partial T-dDNNF", "Sample T-dDNNF",
    #                  "plots/ldd_randgen/ddnnf_partial_vs_sample_size.pdf")

    # # print("LDD randgen LDD vs BDD graphs")
    time_points = get_time_points(
        ldd_randgen_bdds_points, ldd_randgen_ldds_points)
    time_points_dd = get_dd_time_points(
        ldd_randgen_bdds_points, ldd_randgen_ldds_points,
        timeout_value=time_points[2])
    # size_points = get_nodes_points(
    #     ldd_randgen_bdds_points, ldd_randgen_ldds_points)
    # # models_points = get_dd_models_points(
    # #     ldd_randgen_bdds_points, ldd_randgen_ldds_points)
    build_time_graph(time_points, "T-OBDD", "LDD",
                     "plots/ldd_randgen/ldd_vs_tbdd_time.pdf")
                    #  secondary_ponts=time_points_dd)
    build_time_graph(time_points_dd, "T-OBDD", "LDD",
                     "plots/ldd_randgen/ldd_vs_tbdd_dd_time.pdf")
    # build_size_graph(size_points, "T-OBDD", "LDD",
    #                  "plots/ldd_randgen/ldd_vs_tbdd_size.pdf")
    # build_models_graph(models_points, "T-OBDD", "LDD",
    #                    "plots/ldd_randgen/ldd_vs_tbdd_models.pdf")

    # print("LDD randgen BDD no eq graphs")
    # time_points = get_time_points(
    #     ldd_randgen_bdds_points, ldd_randgen_bdds_points_noeqsplit)
    # size_points = get_nodes_points(
    #     ldd_randgen_bdds_points, ldd_randgen_bdds_points_noeqsplit)
    # models_points = get_dd_models_points(
    #     ldd_randgen_bdds_points, ldd_randgen_bdds_points_noeqsplit)
    # build_time_graph(time_points, "NO Opt", "Opt")
    # # build_size_graph(size_points, "NO Opt", "Opt")
    # # build_models_graph(models_points, "NO Opt", "Opt")

    # # print("LDD randgen BDD graphs")
    time_points = get_time_points(
        ldd_randgen_bdds_points, ldd_randgen_abstraction_bdd_points)
    time_points_dd = get_dd_time_points(
        ldd_randgen_bdds_points, ldd_randgen_abstraction_bdd_points,
        timeout_value=time_points[2])
    # size_points = get_nodes_points(
    #     ldd_randgen_bdds_points, ldd_randgen_abstraction_bdd_points)
    # # models_points = get_dd_models_points(
    # #     ldd_randgen_bdds_points, ldd_randgen_abstraction_bdd_points)
    build_time_graph(time_points, "T-OBDD", "Abs. BDD",
                     "plots/ldd_randgen/abstr_bdd_vs_tbdd_time.pdf")
    #                  secondary_ponts = time_points_dd)
    build_time_graph(time_points_dd, "T-OBDD", "Abs. BDD",
                     "plots/ldd_randgen/abstr_bdd_vs_tbdd_dd_time.pdf")
    # build_size_graph(size_points, "T-OBDD", "Abs. BDD",
    #                  "plots/ldd_randgen/abstr_bdd_vs_tbdd_size.pdf")
    # # build_models_graph(models_points, "T-OBDD", "Abs. BDD",
    # #                    "plots/ldd_randgen/abstr_bdd_vs_tbdd_models.pdf")

    # # print("LDD randgen SDD graphs")
    time_points = get_time_points(
        ldd_randgen_sdds_points, ldd_randgen_abstraction_sdd_points)
    time_points_dd = get_dd_time_points(
        ldd_randgen_sdds_points, ldd_randgen_abstraction_sdd_points,
        timeout_value=time_points[2])
    # size_points = get_nodes_points(
    #     ldd_randgen_sdds_points, ldd_randgen_abstraction_sdd_points)
    build_time_graph(time_points, "T-SDD", "Abs. SDD",
                     "plots/ldd_randgen/abstr_sdd_vs_tsdd_time.pdf")
    #                  secondary_ponts = time_points_dd)
    build_time_graph(time_points_dd, "T-SDD", "Abs. SDD",
                     "plots/ldd_randgen/abstr_sdd_vs_tsdd_dd_time.pdf")
    # build_size_graph(size_points, "T-SDD", "Abs. SDD",
    #                  "plots/ldd_randgen/abstr_sdd_vs_tsdd_size.pdf")

    # print("LDD randgen DD gen graphs")
    # time_points = get_dd_time_points(
    #     ldd_randgen_bdds_points, ldd_randgen_bdds_newgen_points)
    # size_points = get_nodes_points(
    #     ldd_randgen_bdds_points, ldd_randgen_bdds_newgen_points)
    # models_points = get_dd_models_points(
    #     ldd_randgen_bdds_points, ldd_randgen_bdds_newgen_points)
    # build_time_graph(time_points, "Old DD", "New DD",
    #                  "plots/ldd_randgen/old_vs_new_dd_time.pdf")
    # build_size_graph(size_points, "Old DD", "New DD",
    #                  "plots/ldd_randgen/old_vs_new_dd_size.pdf")
    # build_models_graph(models_points, "Old DD", "New DD",
    #                    "plots/ldd_randgen/old_vs_new_dd_models.pdf")

    # --------------------------------------------------------------
    # RANDGEN

    randgen_bdds_points = get_randgen_bench_data(
        "T-BDD", "benchmarks/randgen/output_tsetsin")
    print("Randgen size: ", len(randgen_bdds_points))
    print("Timeouts of T-BDDs on randgen: ",
          timeout_to_str(randgen_bdds_points))
    # randgen_bdds_fp_points = get_randgen_bench_data(
    #     "T-BDD", "benchmarks/randgen/output_bdd_fp")
    # print("Timeouts of T-BDDs full partial on randgen: ",
    #       timeout_to_str(randgen_bdds_fp_points))
    randgen_abstraction_bdd_points = get_randgen_bench_data(
        "Abstraction BDD", "benchmarks/randgen/output_abstraction")
    print("Timeouts of Abs-BDDs on randgen: ",
          timeout_to_str(randgen_abstraction_bdd_points))
    randgen_sdds_points = get_randgen_bench_data(
        "T-SDD", "benchmarks/randgen/output_sdd")
    print("Timeouts of T-SDDs on randgen: ",
          timeout_to_str(randgen_sdds_points))
    randgen_abstraction_sdd_points = get_randgen_bench_data(
        "Abstraction SDD", "benchmarks/randgen/output_abstraction_sdd")
    print("Timeouts of Abs-SDDs on randgen: ",
          timeout_to_str(randgen_abstraction_sdd_points))
    # randgen_no_eqsplit_points = get_randgen_bench_data(
    #     "T-BDD", "benchmarks/randgen/output_noeqsplit")
    # print("Timeouts of T-OBDDs on randgen no eq split: ",
    #       timeout_to_str(randgen_no_eqsplit_points))

    # randgen_ddnnf_full_partial_points = get_randgen_bench_data(
    #     "T-dDNNF", "benchmarks/randgen/output_ddnnf_fp")
    # print("Timeouts of T-dDNNFs partial on randgen: ",
    #       timeout_to_str(randgen_ddnnf_full_partial_points))
    randgen_ddnnf_abstraction_d4_points = get_randgen_bench_data(
        "Abstraction dDNNF", "benchmarks/randgen/output_abstraction_ddnnf_d4")
    print("Timeouts of Abstraction dDNNFs on randgen D4: ",
          timeout_to_str(randgen_ddnnf_abstraction_d4_points))
    randgen_ddnnf_abstraction_c2d_points = get_randgen_bench_data(
        "Abstraction dDNNF", "benchmarks/randgen/output_abstraction_ddnnf_c2d")
    print("Timeouts of Abstraction dDNNFs on C2D randgen: ",
          timeout_to_str(randgen_ddnnf_abstraction_c2d_points))
    # randgen_sample_points = get_randgen_bench_data(
    #     "T-dDNNF", "benchmarks/randgen/output_ddnnf_sample")
    # print("Timeouts of T-dDNNFs sample on randgen: ",
    #       timeout_to_str(randgen_sample_points))
    # randgen_sdd_fp_points = get_randgen_bench_data(
    #     "T-SDD", "benchmarks/randgen/output_sdd_fp")
    # print("Timeouts of T-SDDs full partial on randgen: ",
    #       timeout_to_str(randgen_sdd_fp_points))

    # randgen_allsmt_total_points = get_ldd_randgen_bench_data(
    #     "NoDD", "benchmarks/randgen/tmp_total")
    # randgen_allsmt_partial_points = get_ldd_randgen_bench_data(
    #     "NoDD", "benchmarks/randgen/tmp_fp")
    # randgen_allsmt_tabular_total_points = get_ldd_randgen_bench_data(
    #     "NoDD", "benchmarks/randgen/tmp_tabular_total")
    # old_randgen_allsmt_total_points = get_ldd_randgen_bench_data(
    #     "NoDD", "benchmarks/randgen/old_tmp_total")
    # old_randgen_allsmt_total_partial_points = get_ldd_randgen_bench_data(
    #     "NoDD", "benchmarks/randgen/old_tmp_partial")
    
    # time_points = get_allsmt_time_points(
    #     randgen_allsmt_total_points,randgen_allsmt_tabular_total_points
    # )
    # build_time_graph(time_points, "MathSAT", "Tabular",
    #                     "plots/randgen/allsmt_total_vs_tabular_total_time.pdf",
    #                     secondary_ponts=([10,20],[20,10]))

    randgen_ddnnf_c2d_total_points = get_randgen_bench_data(
        "T-dDNNF", "benchmarks/randgen/output_tddnnf_c2d_total_new")
    print("Timeouts of T-dDNNFs total on randgen: ",
          timeout_to_str(randgen_ddnnf_c2d_total_points))
    randgen_ddnnf_c2d_total_not_quantified_points = get_randgen_bench_data(
        "T-dDNNF", "benchmarks/randgen/output_tddnnf_c2d_not_quantified_total_new")
    print("Timeouts of T-dDNNFs total (no quant) on randgen: ",
          timeout_to_str(randgen_ddnnf_c2d_total_not_quantified_points))
    randgen_ddnnf_d4_total_points = get_randgen_bench_data(
        "T-dDNNF", "benchmarks/randgen/output_tddnnf_d4_total_new")
    print("Timeouts of T-dDNNFs d4 on randgen: ",
          timeout_to_str(randgen_ddnnf_d4_total_points))
    randgen_ddnnf_d4_total_not_quantified_points = get_randgen_bench_data(
        "T-dDNNF", "benchmarks/randgen/output_tddnnf_d4_not_quantified_total_new")
    print("Timeouts of T-dDNNFs d4 (no quant) on randgen: ",
          timeout_to_str(randgen_ddnnf_d4_total_not_quantified_points))
    
    randgen_unsat_points = get_list_of_unsat_problems(
        "benchmarks/randgen/output_bdd")
    print(randgen_unsat_points)

    # # T-dDNNF size vs phi size
    # size_points = get_phi_size_vs_dd_nodes_points(
    #     randgen_ddnnf_c2d_total_points)
    # build_phi_size_vs_dd_size_graph(size_points, "Phi size", "T-dDNNF size",
    #                                 "plots/randgen/ddnnf_c2d_phi_size_vs_dd_size.pdf")

    # size_points = get_phi_size_vs_dd_nodes_points(
    #     randgen_ddnnf_c2d_total_not_quantified_points)
    # build_phi_size_vs_dd_size_graph(size_points, "Phi size", "T-dDNNF size",
    #                                 "plots/randgen/ddnnf_c2d_phi_size_vs_dd_size_no_quant.pdf")

    # size_points = get_phi_size_vs_dd_nodes_points(
    #     randgen_ddnnf_d4_total_points)
    # build_phi_size_vs_dd_size_graph(size_points, "Phi size", "T-dDNNF size",
    #                                 "plots/randgen/ddnnf_d4_phi_size_vs_dd_size.pdf")
    
    # size_points = get_phi_size_vs_dd_nodes_points(
    #     randgen_ddnnf_abstraction_d4_points)
    # build_phi_size_vs_dd_size_graph(size_points, "Phi size", "dDNNF size",
    #                                 "plots/randgen/abstract_ddnnf_d4_phi_size_vs_dd_size.pdf")
    
    # size_points = get_phi_size_vs_dd_nodes_points(
    #     randgen_ddnnf_abstraction_c2d_points)
    # build_phi_size_vs_dd_size_graph(size_points, "Phi size", "dDNNF size",
    #                                 "plots/randgen/abstract_ddnnf_c2d_phi_size_vs_dd_size.pdf")

    # size_points = get_phi_size_vs_dd_nodes_points(
    #     randgen_ddnnf_d4_total_not_quantified_points)
    # build_phi_size_vs_dd_size_graph(size_points, "Phi size", "T-dDNNF size",
    #                                 "plots/randgen/ddnnf_d4_phi_size_vs_dd_size_no_quant.pdf")

    # time_points = get_dd_time_points(
    #     randgen_ddnnf_d4_total_points, randgen_ddnnf_d4_total_not_quantified_points)
    # build_time_graph(time_points, "Total enum. T-dDNNF", "Total enum. T-dDNNF (no quant)",
    #                  "plots/randgen/ddnnf_d4_total_vs_no_quant_time.pdf")
    
    # time_points = get_dd_time_points(
    #     randgen_ddnnf_c2d_total_points, randgen_ddnnf_c2d_total_not_quantified_points)
    # build_time_graph(time_points, "Total enum. T-dDNNF", "Total enum. T-dDNNF (no quant)",
    #                  "plots/randgen/ddnnf_c2d_total_vs_no_quant_time.pdf")

    # size_points = get_phi_size_vs_dd_nodes_points(
    #     randgen_bdds_points)
    # build_phi_size_vs_dd_size_graph(size_points, "Phi size", "T-OBDD size",
    #                                 "plots/randgen/bdd_phi_size_vs_dd_size.pdf")
    
    # size_points = get_phi_size_vs_dd_nodes_points(
    #     randgen_sdds_points)
    # build_phi_size_vs_dd_size_graph(size_points, "Phi size", "T-SDD size",
    #                                 "plots/randgen/sdd_phi_size_vs_dd_size.pdf")
    
    # size_points = get_nodes_points(
    #     randgen_ddnnf_c2d_total_points, randgen_ddnnf_abstraction_c2d_points)
    # build_size_graph(size_points, "T-dDNNF", "Abstr. dDNNF",
    #                  "plots/randgen/ddnnf_c2d_vs_ddnnf_abstr_size.pdf")
    
    # # print(randgen_ddnnf_c2d_total_points)
    # # # print(randgen_ddnnf_abstraction_c2d_points)
    # time_points = get_time_points(
    #     randgen_ddnnf_c2d_total_points, randgen_ddnnf_abstraction_c2d_points)
    # time_points_dd = get_dd_time_points(
    #     randgen_ddnnf_c2d_total_points, randgen_ddnnf_abstraction_c2d_points,
    #     timeout_value=time_points[2])
    # build_time_graph(time_points, "T-dDNNF", "Abstr. dDNNF",
    #                  "plots/randgen/ddnnf_c2d_vs_ddnnf_abstr_time.pdf")
    #                 #  secondary_ponts=time_points_dd)
    # build_time_graph(time_points_dd, "T-dDNNF", "Abstr. dDNNF",
    #                  "plots/randgen/ddnnf_c2d_vs_ddnnf_abstr_dd_time.pdf")
    
    # # size_points = get_nodes_points(
    # #     randgen_ddnnf_d4_total_points, randgen_ddnnf_abstraction_d4_points)
    # # build_size_graph(size_points, "T-dDNNF", "Abstr. dDNNF",
    # #                  "plots/randgen/ddnnf_d4_vs_ddnnf_abstr_size.pdf")
    
    # time_points = get_time_points(
    #     randgen_ddnnf_d4_total_points, randgen_ddnnf_abstraction_d4_points)
    # time_points_dd = get_dd_time_points(
    #     randgen_ddnnf_d4_total_points, randgen_ddnnf_abstraction_d4_points,
    #     timeout_value=time_points[2])
    # build_time_graph(time_points, "T-dDNNF", "Abstr. dDNNF",
    #                  "plots/randgen/ddnnf_d4_vs_ddnnf_abstr_time.pdf")
    #                 #  secondary_ponts=time_points_dd)
    # build_time_graph(time_points_dd, "T-dDNNF", "Abstr. dDNNF",
    #                  "plots/randgen/ddnnf_d4_vs_ddnnf_abstr_dd_time.pdf")
    
    # size_points = get_phi_size_vs_dd_nodes_points(
    #     randgen_abstraction_bdd_points)
    # build_phi_size_vs_dd_size_graph(size_points, "Phi size", "Abstr. OBDD size",
    #                                 "plots/randgen/abstract_bdd_phi_size_vs_dd_size.pdf")
    
    # size_points = get_phi_size_vs_dd_nodes_points(
    #     randgen_abstraction_sdd_points)
    # build_phi_size_vs_dd_size_graph(size_points, "Phi size", "Abstr. SDD size",
    #                                 "plots/randgen/abstract_sdd_vs_phi_size.pdf")
    
    # size_points = get_nodes_points(
    #     randgen_bdds_points, randgen_abstraction_bdd_points)
    # build_size_graph(size_points, "T-OBDD", "Abs. OBDD",
    #                  "plots/randgen/abstr_bdd_vs_tbdd_size.pdf")
    
    # size_points = get_nodes_points(
    #     randgen_sdds_points, randgen_abstraction_sdd_points)
    # build_size_graph(size_points, "T-SDD", "Abs. SDD",
    #                  "plots/randgen/abstr_sdd_vs_tsdd_size.pdf")
    
    # size_points = get_phi_size_vs_lemmas_points(
    #     randgen_bdds_points
    # )
    # build_size_graph(size_points, "Phi size", "Amount of lemmas",
    #                  "plots/randgen/phi_size_vs_lemmas.pdf", no_central_diagonal=True)

    # tlemmas_points = get_lemmas_points(
    #     old_randgen_allsmt_total_points, old_randgen_allsmt_total_partial_points)
    # build_lemmas_graph(tlemmas_points, "Old Total", "Old Extended Partial",
    #                    "plots/randgen/old_vs_new_lemmas.pdf")
    # tlemmas_points = get_lemmas_points(
    #     old_randgen_allsmt_total_points, randgen_allsmt_tabular_total_points)
    # build_lemmas_graph(tlemmas_points, "Old Total", "Tabular",
    #                    "plots/randgen/old_total_vs_tabular_lemmas.pdf")

    # # allsmt time total vs partial
    # allsmt_points = get_allsmt_time_points(
    #     randgen_allsmt_total_points, randgen_allsmt_tabular_total_points)
    # build_time_graph(allsmt_points, "MathSAT", "Tabular",
    #                  "plots/randgen/allsmt_mathsat_vs_tabular_time.pdf")

    # allsmt_points = get_allsmt_time_points(
    #     randgen_ddnnf_points, randgen_ddnnf_total_points)
    # build_time_graph(allsmt_points, "Partial enum. T-dDNNF", "Total enum. T-dDNNF")
    # time_points = get_time_points(
    #     randgen_ddnnf_points, randgen_ddnnf_total_points)
    # build_time_graph(time_points, "Partial enum. T-dDNNF", "Total enum. T-dDNNF",
    #                  "plots/randgen/ddnnf_partial_vs_total_time.pdf")
    # time_points = get_time_points(
    #     randgen_ddnnf_points, randgen_no_eqsplit_points)
    # build_time_graph(time_points, "T-dDNNF", "T-BDD",
    #                  "plots/randgen/ddnnf_vs_bdd_time.pdf")

    # dDNNF partial vs total
    # time_points = get_time_points(
    #     randgen_ddnnf_total_points, randgen_ddnnf_full_partial_points)
    # build_time_graph(time_points, "Total enum. T-dDNNF", "Partial enum. T-dDNNF",
    #                  "plots/randgen/ddnnf_partial_vs_total_time.pdf")
    # size_points = get_nodes_points(
    #     randgen_ddnnf_total_points, randgen_ddnnf_full_partial_points)
    # build_size_graph(size_points, "Total enum. T-dDNNF", "Partial enum. T-dDNNF",
    #                     "plots/randgen/ddnnf_partial_vs_total_size.pdf")
    # # dDNNF abstract vs total
    # time_points = get_time_points(
    #     randgen_ddnnf_total_points, randgen_ddnnf_abstraction_points)
    # build_time_graph(time_points, "Total enum. T-dDNNF", "Abstr. dDNNF",
    #                  "plots/randgen/ddnnf_total_vs_abstraction_time.pdf")
    # size_points = get_nodes_points(
    #     randgen_ddnnf_total_points, randgen_ddnnf_abstraction_points)
    # build_size_graph(size_points, "Total enum. T-dDNNF", "Abstr. dDNNF",
    #                  "plots/randgen/ddnnf_total_vs_abstraction_size.pdf")
    # dDNNF abstract vs partial
    # time_points = get_time_points(
    #     randgen_ddnnf_full_partial_points, randgen_ddnnf_abstraction_points)
    # build_time_graph(time_points, "Partial enum. T-dDNNF", "Abstraction dDNNF",
    #                  "plots/randgen/ddnnf_abstract_vs_partial_time.pdf")
    # size_points = get_nodes_points(
    #     randgen_ddnnf_full_partial_points, randgen_ddnnf_abstraction_points)
    # build_size_graph(size_points, "Partial enum. T-dDNNF", "Abstraction dDNNF",
    #                  "plots/randgen/ddnnf_abstract_vs_partial_size.pdf")
    # # dDNNF vs BDD
    # # time_points = get_time_points(
    # #     randgen_ddnnf_full_partial_points, randgen_bdds_points)
    # # build_time_graph(time_points, "Partial T-dDNNF", "T-BDD",
    # #                  "plots/randgen/ddnnf_vs_bdd_time.pdf")

    # # BDD total vs partial
    # time_points = get_time_points(
    #     randgen_bdds_points, randgen_bdds_fp_points)
    # build_time_graph(time_points, "Total T-BDD", "Partial T-BDD",
    #                  "plots/randgen/bdd_partial_vs_total_time.pdf")
    # size_points = get_nodes_points(
    #     randgen_bdds_points, randgen_bdds_fp_points)
    # build_size_graph(size_points, "Total T-BDD", "Partial T-BDD",
    #                  "plots/randgen/bdd_partial_vs_total_size.pdf")
    # models_points = get_dd_models_points(
    #     randgen_bdds_points, randgen_bdds_fp_points)
    # build_models_graph(models_points, "Total T-BDD", "Partial T-BDD",
    #                    "plots/randgen/bdd_partial_vs_total_models.pdf")

    # # SDD total vs partial
    # time_points = get_time_points(
    #     randgen_sdds_points, randgen_sdd_fp_points)
    # build_time_graph(time_points, "Total T-SDD", "Partial T-SDD",
    #                  "plots/randgen/sdd_partial_vs_total_time.pdf")
    # size_points = get_nodes_points(
    #     randgen_sdds_points, randgen_sdd_fp_points)
    # build_size_graph(size_points, "Total T-SDD", "Partial T-SDD",
    #                  "plots/randgen/sdd_partial_vs_total_size.pdf")

    # # Partial dDNNF vs sample
    # time_points = get_time_points(
    #     randgen_ddnnf_full_partial_points, randgen_sample_points)
    # build_time_graph(time_points, "Partial enum. T-dDNNF", "Sample enum. T-dDNNF",
    #                  "plots/randgen/ddnnf_sample_vs_partial_time.pdf")
    # size_points = get_nodes_points(
    #     randgen_ddnnf_full_partial_points, randgen_sample_points)
    # build_size_graph(size_points, "Partial enum. T-dDNNF", "Sample enum. T-dDNNF",
    #                  "plots/randgen/ddnnf_sample_vs_partial_size.pdf")

    # print("randgen BDD graphs")
    # time_points = get_time_points(
    #     randgen_bdds_points, randgen_abstraction_bdd_points)
    # time_points_dd = get_dd_time_points(
    #     randgen_bdds_points, randgen_abstraction_bdd_points,
    #     timeout_value=time_points[2])
    # # size_points = get_nodes_points(
    # #     randgen_bdds_points, randgen_abstraction_bdd_points)
    # # # models_points = get_dd_models_points(
    # # #     randgen_bdds_points, randgen_abstraction_bdd_points)
    # build_time_graph(time_points, "T-OBDD", "Abs. BDD",
    #                  "plots/randgen/abstr_bdd_vs_tbdd_time.pdf")
    # #                  secondary_ponts=time_points_dd)
    # build_time_graph(time_points_dd, "T-OBDD", "Abs. BDD",
    #                  "plots/randgen/abstr_bdd_vs_tbdd_dd_time.pdf")
    # # build_size_graph(size_points, "T-OBDD", "Abs. BDD",
    #                  "plots/randgen/abstr_bdd_vs_tbdd_size.pdf")
    # build_models_graph(models_points, "T-BDD", "Abs. BDD",
    #                    "plots/randgen/abstr_bdd_vs_tbdd_models.pdf")

    # print("randgen BDD graphs")
    # time_points = get_time_points(
    #     randgen_bdds_points, randgen_no_eqsplit_points)
    # size_points = get_nodes_points(
    #     randgen_bdds_points, randgen_no_eqsplit_points)
    # models_points = get_dd_models_points(
    #     randgen_bdds_points, randgen_no_eqsplit_points)
    # allsmt_points = get_allsmt_time_points(
    #     randgen_bdds_points, randgen_no_eqsplit_points)
    # build_time_graph(time_points, "No opt", "Opt")
    # build_size_graph(size_points, "No opt", "Opt")
    # build_models_graph(models_points, "No opt", "Opt")
    # build_time_graph(allsmt_points, "No opt", "Opt")

    # print("randgen SDD graphs")
    # time_points = get_time_points(
    #     randgen_sdds_points, randgen_abstraction_sdd_points)
    # time_points_dd = get_dd_time_points(
    #     randgen_sdds_points, randgen_abstraction_sdd_points,
    #     timeout_value=time_points[2])
    # # size_points = get_nodes_points(
    # #     randgen_sdds_points, randgen_abstraction_sdd_points)
    # build_time_graph(time_points, "T-SDD", "Abs. SDD",
    #                  "plots/randgen/abstr_sdd_vs_tsdd_time.pdf")
    # #                  secondary_ponts=time_points_dd)
    # build_time_graph(time_points_dd, "T-SDD", "Abs. SDD",
    #                  "plots/randgen/abstr_sdd_vs_tsdd_dd_time.pdf")
    # build_size_graph(size_points, "T-SDD", "Abs. SDD",
    #                  "plots/randgen/abstr_sdd_vs_tsdd_size.pdf")

    # --------------------------------------------------------------
    # SMTLIB QF RDL

    # qfrdl_ldds_points = get_smtlib_bench_data(
    #     "LDD", "benchmarks/smtlib/output_ldd/non-incremental/QF_RDL")
    # print("QF RDL size: ", len(qfrdl_ldds_points))
    # print("Timeouts of LDDs on smtlib QF RDL: ",
    #       timeout_to_str(qfrdl_ldds_points))
    # qfrdl_bdds_points = get_smtlib_bench_data(
    #     "T-BDD", "benchmarks/smtlib/output_tbdd_total_new/non-incremental/QF_RDL")
    # print("Timeouts of T-BDDs on smtlib QF RDL: ",
    #       timeout_to_str(qfrdl_bdds_points))
    # # qfrdl_bdds_fp_points = get_smtlib_bench_data(
    # #     "T-BDD", "benchmarks/smtlib/output_bdd_noeqsplit_full_partial/non-incremental/QF_RDL")
    # # print("Timeouts of partial T-BDDs on smtlib QF RDL: ",
    # #       timeout_to_str(qfrdl_bdds_fp_points))
    # qfrdl_abstraction_bdd_points = get_smtlib_bench_data(
    #     "Abstraction BDD", "benchmarks/smtlib/output_abstraction_bdd/non-incremental/QF_RDL")
    # print("Timeouts of Abs-BDDs on smtlib QF RDL: ",
    #       timeout_to_str(qfrdl_abstraction_bdd_points))
    # qfrdl_sdds_points = get_smtlib_bench_data(
    #     "T-SDD", "benchmarks/smtlib/output_tsdd_total_new/non-incremental/QF_RDL")
    # print("Timeouts of T-SDDs on smtlib QF RDL: ",
    #       timeout_to_str(qfrdl_sdds_points))
    # qfrdl_abstraction_sdd_points = get_smtlib_bench_data(
    #     "Abstraction SDD", "benchmarks/smtlib/output_abstraction_sdd/non-incremental/QF_RDL")
    # print("Timeouts of Abs-SDDs on smtlib QF RDL: ",
    #       timeout_to_str(qfrdl_abstraction_sdd_points))
    # # qfrdl_sdd_full_partial_points = get_smtlib_bench_data(
    # #     "T-SDD", "benchmarks/smtlib/output_sdd_full_partial/non-incremental/QF_RDL")
    # # print("Timeouts of full partial T-SDDs on smtlib QF RDL: ",
    # #       timeout_to_str(qfrdl_sdd_full_partial_points))
    # # qfrdl_bdds_noeqsplit_points = get_smtlib_bench_data(
    # #     "T-BDD", "benchmarks/smtlib/output_bdd_noeqsplit/non-incremental/QF_RDL")
    # # print("Timeouts of T-BDDs no eq split on smtlib QF RDL: ",
    # #       timeout_to_str(qfrdl_bdds_noeqsplit_points))
    # # qfrdl_ddnnf_total_points = get_smtlib_bench_data(
    # #     "T-dDNNF", "benchmarks/smtlib/output_ddnnf_total/non-incremental/QF_RDL")
    # # print("Timeouts of T-dDNNFs total on smtlib QF RDL: ", timeout_to_str(qfrdl_ddnnf_total_points))
    # # qfrdl_ddnnf_partial_points = get_smtlib_bench_data(
    # #     "T-dDNNF", "benchmarks/smtlib/output_ddnnf_full_partial/non-incremental/QF_RDL")
    # # print("Timeouts of T-dDNNFs partial on smtlib QF RDL: ",
    # #       timeout_to_str(qfrdl_ddnnf_partial_points))
    # qfrdl_ddnnf_abstraction_points = get_smtlib_bench_data(
    #     "Abstraction dDNNF", "benchmarks/smtlib/output_ddnnf_abstract/non-incremental/QF_RDL")
    # print("Timeouts of Abstraction dDNNFs on smtlib QF RDL: ",
    #       timeout_to_str(qfrdl_ddnnf_abstraction_points))
    # # qfrdl_allsmt_total_points = get_ldd_randgen_bench_data(
    # #     "NoDD", "benchmarks/smtlib/tmp_noeqsplit_total/non-incremental/QF_RDL")
    # # qfrdl_allsmt_partial_points = get_ldd_randgen_bench_data(
    # #     "NoDD", "benchmarks/smtlib/tmp_noeqsplit_full_partial/non-incremental/QF_RDL")

    # qfrdl_ddnnf_c2d_total_points = get_smtlib_bench_data(
    #     "T-dDNNF", "benchmarks/smtlib/output_tddnnf_c2d_total_new/non-incremental/QF_RDL")
    # print("Timeouts of T-dDNNFs c2d on smtlib QF RDL: ",
    #       timeout_to_str(qfrdl_ddnnf_c2d_total_points))
    # qfrdl_ddnnf_c2d_total_not_quantified_points = get_smtlib_bench_data(
    #     "T-dDNNF", "benchmarks/smtlib/output_tddnnf_c2d_not_quantified_total_new/non-incremental/QF_RDL")
    # print("Timeouts of T-dDNNFs c2d (no quant) on smtlib QF RDL: ",
    #       timeout_to_str(qfrdl_ddnnf_c2d_total_not_quantified_points))
    # qfrdl_ddnnf_d4_total_points = get_smtlib_bench_data(
    #     "T-dDNNF", "benchmarks/smtlib/output_tddnnf_d4_total_new/non-incremental/QF_RDL")
    # print("Timeouts of T-dDNNFs d4 on smtlib QF RDL: ",
    #       timeout_to_str(qfrdl_ddnnf_d4_total_points))
    # qfrdl_ddnnf_d4_total_not_quantified_points = get_smtlib_bench_data(
    #     "T-dDNNF", "benchmarks/smtlib/output_tddnnf_d4_not_quantified_total_new/non-incremental/QF_RDL")
    # print("Timeouts of T-dDNNFs d4 (no quant) on smtlib QF RDL: ",
    #       timeout_to_str(qfrdl_ddnnf_d4_total_not_quantified_points))
    
    # qfrdl_abstraction_ddnnf_c2d_points = get_smtlib_bench_data(
    #     "Abstraction dDNNF", "benchmarks/smtlib/output_abstraction_ddnnf_c2d/non-incremental/QF_RDL")
    # print("Timeouts of Abstraction dDNNFs c2d on smtlib QF RDL: ",
    #         timeout_to_str(qfrdl_abstraction_ddnnf_c2d_points))
    # qfrdl_abstraction_ddnnf_d4_points = get_smtlib_bench_data(
    #     "Abstraction dDNNF", "benchmarks/smtlib/output_abstraction_ddnnf_d4/non-incremental/QF_RDL")
    # print("Timeouts of Abstraction dDNNFs d4 on smtlib QF RDL: ",
    #         timeout_to_str(qfrdl_abstraction_ddnnf_d4_points))

    # qfrdl_unsat_points = get_list_of_unsat_problems(
    #     "benchmarks/smtlib/output_tbdd_total_new/non-incremental/QF_RDL")
    # print(qfrdl_unsat_points)

    # # # T-dDNNF size vs phi size
    # # size_points = get_phi_size_vs_dd_nodes_points(
    # #     qfrdl_ddnnf_c2d_total_points)
    # # build_phi_size_vs_dd_size_graph(size_points, "Phi size", "DD size",
    # #                                 "plots/smtlib/QF_RDL/ddnnf_c2d_phi_size_vs_dd_size.pdf")

    # # size_points = get_phi_size_vs_dd_nodes_points(
    # #     qfrdl_ddnnf_c2d_total_not_quantified_points)
    # # build_phi_size_vs_dd_size_graph(size_points, "Phi size", "DD size",
    # #                                 "plots/smtlib/QF_RDL/ddnnf_c2d_phi_size_vs_dd_size_no_quant.pdf")

    # # size_points = get_phi_size_vs_dd_nodes_points(
    # #     qfrdl_ddnnf_d4_total_points)
    # # build_phi_size_vs_dd_size_graph(size_points, "Phi size", "DD size",
    # #                                 "plots/smtlib/QF_RDL/ddnnf_d4_phi_size_vs_dd_size.pdf")

    # # size_points = get_phi_size_vs_dd_nodes_points(
    # #     qfrdl_ddnnf_d4_total_not_quantified_points)
    # # build_phi_size_vs_dd_size_graph(size_points, "Phi size", "DD size",
    # #                                 "plots/smtlib/QF_RDL/ddnnf_d4_phi_size_vs_dd_size_no_quant.pdf")

    # # time_points = get_dd_time_points(
    # #     qfrdl_ddnnf_d4_total_points, qfrdl_ddnnf_d4_total_not_quantified_points)
    # # build_time_graph(time_points, "Total enum. T-dDNNF", "Total enum. T-dDNNF (no quant)",
    # #                  "plots/smtlib/QF_RDL/ddnnf_d4_total_vs_no_quant_time.pdf")
    
    # time_points = get_dd_time_points(
    #     qfrdl_ddnnf_c2d_total_points, qfrdl_ddnnf_c2d_total_not_quantified_points)
    # build_time_graph(time_points, "Total enum. T-dDNNF", "Total enum. T-dDNNF (no quant)",
    #                  "plots/smtlib/QF_RDL/ddnnf_c2d_total_vs_no_quant_time.pdf")
    
    # size_points = get_phi_size_vs_lemmas_points(
    #     qfrdl_bdds_points
    # )
    # build_size_graph(size_points, "Phi size", "Amount of lemmas",
    #                  "plots/smtlib/QF_RDL/phi_size_vs_lemmas.pdf",
    #                  no_central_diagonal=True)
    
    # time_points = get_time_points(
    #     qfrdl_ddnnf_c2d_total_points, qfrdl_abstraction_ddnnf_c2d_points,
    #     unsat_sources=qfrdl_unsat_points)
    # time_points_dd = get_dd_time_points(
    #     qfrdl_ddnnf_c2d_total_points, qfrdl_abstraction_ddnnf_c2d_points,
    #     timeout_value=time_points[2],
    #     unsat_sources=qfrdl_unsat_points)
    # build_time_graph(time_points, "T-dDNNF", "Abstr. dDNNF",
    #                  "plots/smtlib/QF_RDL/ddnnf_c2d_vs_ddnnf_abstr_time.pdf")
    # build_time_graph(time_points_dd, "T-dDNNF", "Abstr. dDNNF",
    #                  "plots/smtlib/QF_RDL/ddnnf_c2d_vs_ddnnf_abstr_dd_time.pdf")
    
    # size_points = get_nodes_points(
    #     qfrdl_ddnnf_c2d_total_points, qfrdl_abstraction_ddnnf_c2d_points)
    # build_size_graph(size_points, "T-dDNNF", "Abstr. dDNNF",
    #                  "plots/smtlib/QF_RDL/ddnnf_c2d_vs_ddnnf_abstr_size.pdf")
    
    # time_points = get_time_points(
    #     qfrdl_ddnnf_d4_total_points, qfrdl_abstraction_ddnnf_d4_points,
    #     unsat_sources=qfrdl_unsat_points)
    # time_points_dd = get_dd_time_points(
    #     qfrdl_ddnnf_d4_total_points, qfrdl_abstraction_ddnnf_d4_points,
    #     timeout_value=time_points[2],
    #     unsat_sources=qfrdl_unsat_points)
    # build_time_graph(time_points, "T-dDNNF", "Abstr. dDNNF",
    #                  "plots/smtlib/QF_RDL/ddnnf_d4_vs_ddnnf_abstr_time.pdf")
    #                 #  secondary_ponts=time_points_dd)
    # build_time_graph(time_points_dd, "T-dDNNF", "Abstr. dDNNF",
    #                  "plots/smtlib/QF_RDL/ddnnf_d4_vs_ddnnf_abstr_dd_time.pdf")
    
    # size_points = get_nodes_points(
    #     qfrdl_ddnnf_d4_total_points, qfrdl_abstraction_ddnnf_d4_points)
    # build_size_graph(size_points, "T-dDNNF", "Abstr. dDNNF",
    #                  "plots/smtlib/QF_RDL/ddnnf_d4_vs_ddnnf_abstr_size.pdf")

    # # allsmt time total vs partial
    # # allsmt_points = get_allsmt_time_points(
    # #     qfrdl_allsmt_total_points, qfrdl_allsmt_partial_points)
    # # build_time_graph(allsmt_points, "Total All-SMT", "Partial All-SMT",
    # #                  "plots/smtlib/QF_RDL/allsmt_partial_vs_total_time.pdf")

    # # dDNNF partial vs total
    # # time_points = get_time_points(
    # #     qfrdl_ddnnf_total_points, qfrdl_ddnnf_partial_points)
    # # build_time_graph(time_points, "Total enum. T-dDNNF", "Partial enum. T-dDNNF",
    # #                  "plots/smtlib/QF_RDL/ddnnf_partial_vs_total_time.pdf")
    # # size_points = get_nodes_points(
    # #     qfrdl_ddnnf_total_points, qfrdl_ddnnf_partial_points)
    # # build_size_graph(size_points, "Total enum. T-dDNNF", "Partial enum. T-dDNNF",
    # #                     "plots/smtlib/QF_RDL/ddnnf_partial_vs_total_size.pdf")
    # # # dDNNF abstraction vs total
    # # time_points = get_time_points(
    # #     qfrdl_ddnnf_total_points, qfrdl_ddnnf_abstraction_points)
    # # build_time_graph(time_points, "Total enum. T-dDNNF", "Abstr. dDNNF",
    # #                  "plots/smtlib/QF_RDL/ddnnf_total_vs_abstraction_time.pdf")
    # # size_points = get_nodes_points(
    # # #     qfrdl_ddnnf_total_points, qfrdl_ddnnf_abstraction_points)
    # # # build_size_graph(size_points, "Total enum. T-dDNNF", "Abstr. dDNNF",
    # # #                     "plots/smtlib/QF_RDL/ddnnf_total_vs_abstraction_size.pdf")
    # # # dDNNF abstraction vs partial
    # # time_points = get_time_points(
    # #     qfrdl_ddnnf_partial_points, qfrdl_ddnnf_abstraction_points)
    # # build_time_graph(time_points, "Partial enum. T-dDNNF", "Abstraction dDNNF",
    # #                  "plots/smtlib/QF_RDL/ddnnf_abstract_vs_partial_time.pdf")
    # # size_points = get_nodes_points(
    # #     qfrdl_ddnnf_partial_points, qfrdl_ddnnf_abstraction_points)
    # # build_size_graph(size_points, "Partial enum. T-dDNNF", "Abstraction dDNNF",
    # #                  "plots/smtlib/QF_RDL/ddnnf_abstract_vs_partial_size.pdf")
    # # # dDNNF vs BDD
    # # # time_points = get_time_points(
    # # #     qfrdl_ddnnf_partial_points, qfrdl_bdds_noeqsplit_points)
    # # # build_time_graph(time_points, "Partial T-dDNNF", "T-BDD",
    # # #                  "plots/smtlib/QF_RDL/ddnnf_vs_bdd_time.pdf")

    # # # BDD total vs partial
    # # time_points = get_time_points(
    # #     qfrdl_bdds_points, qfrdl_bdds_fp_points)
    # # build_time_graph(time_points, "Total T-BDD", "Partial T-BDD",
    # #                  "plots/smtlib/QF_RDL/bdd_partial_vs_total_time.pdf")
    # # size_points = get_nodes_points(
    # #     qfrdl_bdds_points, qfrdl_bdds_fp_points)
    # # build_size_graph(size_points, "Total T-BDD", "Partial T-BDD",
    # #                  "plots/smtlib/QF_RDL/bdd_partial_vs_total_size.pdf")
    # # models_points = get_dd_models_points(
    # #     qfrdl_bdds_points, qfrdl_bdds_fp_points)
    # # build_models_graph(models_points, "Total T-BDD", "Partial T-BDD",
    # #                    "plots/smtlib/QF_RDL/bdd_partial_vs_total_models.pdf")

    # # # SDD total vs partial
    # # time_points = get_time_points(
    # #     qfrdl_sdds_points, qfrdl_sdd_full_partial_points)
    # # build_time_graph(time_points, "Total T-SDD", "Partial T-SDD",
    # #                  "plots/smtlib/QF_RDL/sdd_partial_vs_total_time.pdf")
    # # size_points = get_nodes_points(
    # #     qfrdl_sdds_points, qfrdl_sdd_full_partial_points)
    # # build_size_graph(size_points, "Total T-SDD", "Partial T-SDD",
    # #                  "plots/smtlib/QF_RDL/sdd_partial_vs_total_size.pdf")

    # # # BDD partial vs LDD
    # # time_points = get_time_points(
    # #     qfrdl_bdds_fp_points, qfrdl_ldds_points)
    # # build_time_graph(time_points, "Partial T-BDD", "LDD",
    # #                  "plots/smtlib/QF_RDL/bdd_partial_vs_ldd_time.pdf")
    # # size_points = get_nodes_points(
    # #     qfrdl_bdds_fp_points, qfrdl_ldds_points)
    # # build_size_graph(size_points, "Partial T-BDD", "LDD",
    # #                  "plots/smtlib/QF_RDL/bdd_partial_vs_ldd_size.pdf")
    # # models_points = get_dd_models_points(
    # #     qfrdl_bdds_fp_points, qfrdl_ldds_points)
    # # build_models_graph(models_points, "Partial T-BDD", "LDD",
    # #                    "plots/smtlib/QF_RDL/bdd_partial_vs_ldd_models.pdf")

    # # print("QF RDL LDD vs BDD graphs")
    # time_points = get_time_points(
    #     qfrdl_bdds_points, qfrdl_ldds_points,
    #     unsat_sources=qfrdl_unsat_points)
    # time_points_dd = get_dd_time_points(
    #     qfrdl_bdds_points, qfrdl_ldds_points,
    #     timeout_value=time_points[2],
    #     unsat_sources=qfrdl_unsat_points)
    # # size_points = get_nodes_points(
    # #     qfrdl_bdds_points, qfrdl_ldds_points)
    # # models_points = get_dd_models_points(
    # #     qfrdl_bdds_points, qfrdl_ldds_points)
    # build_time_graph(time_points, "T-OBDD", "LDD",
    #                  "plots/smtlib/QF_RDL/ldd_vs_tbdd_time.pdf")
    # build_time_graph(time_points_dd, "T-OBDD", "LDD",
    #                  "plots/smtlib/QF_RDL/ldd_vs_tbdd_dd_time.pdf")
    #                 #  secondary_ponts=time_points_dd)
    # # build_size_graph(size_points, "T-OBDD", "LDD",
    # #                  "plots/smtlib/QF_RDL/ldd_vs_tbdd_size.pdf")
    # # build_models_graph(models_points, "T-OBDD", "LDD",
    #                    "plots/smtlib/QF_RDL/ldd_vs_tbdd_models.pdf")

    # # print("QF RDL Opt vs No Opt graphs")
    # # time_points = get_time_points(
    # #     qfrdl_bdds_points, qfrdl_bdds_noeqsplit_points)
    # # size_points = get_nodes_points(
    # #     qfrdl_bdds_points, qfrdl_bdds_noeqsplit_points)
    # # models_points = get_dd_models_points(
    # #     qfrdl_bdds_points, qfrdl_bdds_noeqsplit_points)
    # # lemmas_points = get_lemmas_points(
    # #     qfrdl_bdds_points, qfrdl_bdds_noeqsplit_points)
    # # fresh_atoms_points = get_dd_fresh_atoms_points(
    # #     qfrdl_bdds_points, qfrdl_bdds_noeqsplit_points)
    # # build_time_graph(time_points, "No Opt", "Opt")
    # # build_size_graph(size_points, "No Opt", "Opt")
    # # build_models_graph(models_points, "No Opt", "Opt")
    # # build_lemmas_graph(lemmas_points, "No Opt", "Opt")
    # # print(fresh_atoms_points)
    # # build_models_graph(fresh_atoms_points, "No Opt", "Opt")

    # # lemmas_points = get_lemmas_points(
    # #     qfrdl_tmp, qfrdl_tmp_noeqsplit)
    # # print(len(qfrdl_tmp))
    # # print(len(qfrdl_tmp_noeqsplit))
    # # build_lemmas_graph(lemmas_points, "No Opt", "Opt")

    # # # print("QF RDL BDD graphs")
    # time_points = get_time_points(
    #     qfrdl_bdds_points, qfrdl_abstraction_bdd_points,
    #     unsat_sources=qfrdl_unsat_points)
    # time_points_dd = get_dd_time_points(
    #     qfrdl_bdds_points, qfrdl_abstraction_bdd_points,
    #     timeout_value=time_points[2],
    #     unsat_sources=qfrdl_unsat_points)
    # # size_points = get_nodes_points(
    # #     qfrdl_bdds_points, qfrdl_abstraction_bdd_points)
    # # models_points = get_dd_models_points(
    # #     qfrdl_bdds_points, qfrdl_abstraction_bdd_points)
    # build_time_graph(time_points, "T-OBDD", "Abs. BDD",
    #                  "plots/smtlib/QF_RDL/abstr_bdd_vs_tbdd_time.pdf")
    # build_time_graph(time_points_dd, "T-OBDD", "Abs. BDD",
    #                  "plots/smtlib/QF_RDL/abstr_bdd_vs_tbdd_dd_time.pdf")
                    #  secondary_ponts=dd_time_points)
    # build_size_graph(size_points, "T-OBDD", "Abs. BDD",
    #                  "plots/smtlib/QF_RDL/abstr_bdd_vs_tbdd_size.pdf")
    # # build_models_graph(models_points, "T-OBDD", "Abs. BDD",
    #                    "plots/smtlib/QF_RDL/abstr_bdd_vs_tbdd_models.pdf")

    # # print("QF RDL SDD graphs")
    # time_points = get_time_points(
    #     qfrdl_sdds_points, qfrdl_abstraction_sdd_points,
    #     unsat_sources=qfrdl_unsat_points)
    # time_points_dd = get_dd_time_points(
    #     qfrdl_sdds_points, qfrdl_abstraction_sdd_points,
    #     timeout_value=time_points[2],
    #     unsat_sources=qfrdl_unsat_points)
    # # size_points = get_nodes_points(
    # #     qfrdl_sdds_points, qfrdl_abstraction_sdd_points)
    # build_time_graph(time_points, "T-SDD", "Abs. SDD",
    #                  "plots/smtlib/QF_RDL/abstr_sdd_vs_tsdd_time.pdf")
    # #                  secondary_ponts=time_points_dd)
    # build_time_graph(time_points_dd, "T-SDD", "Abs. SDD",
    #                  "plots/smtlib/QF_RDL/abstr_sdd_vs_tsdd_dd_time.pdf")
    # build_size_graph(size_points, "T-SDD", "Abs. SDD",
    #                  "plots/smtlib/QF_RDL/abstr_sdd_vs_tsdd_size.pdf")

    # --------------------------------------------------------------
    # SMTLIB QF UF

    # DATA NOT READY: parsing/msat problem

    # qfuf_bdds_points = get_smtlib_bench_data(
    #     "T-BDD", "benchmarks/smtlib/output_bdd/non-incremental/QF_UF")
    # qfuf_abstraction_bdd_points = get_smtlib_bench_data(
    #     "Abstraction BDD", "benchmarks/smtlib/output_abstraction_bdd/non-incremental/QF_UF")
    # qfuf_sdds_points = get_smtlib_bench_data(
    #     "T-SDD", "benchmarks/smtlib/output_sdd/non-incremental/QF_UF")
    # qfuf_abstraction_sdd_points = get_smtlib_bench_data(
    #     "Abstraction SDD", "benchmarks/smtlib/output_abstraction_sdd/non-incremental/QF_UF")

    # time_points = get_time_points(
    #     qfuf_bdds_points, qfuf_abstraction_bdd_points)
    # size_points = get_nodes_points(
    #     qfuf_bdds_points, qfuf_abstraction_bdd_points)
    # models_points = get_dd_models_points(
    #     qfuf_bdds_points, qfuf_abstraction_bdd_points)
    # build_time_graph(time_points, "T-BDD", "Abs. BDD",
    #                  "plots/smtlib/QF_UF/abstr_bdd_vs_tbdd_time.pdf")
    # build_size_graph(size_points, "T-BDD", "Abs. BDD",
    #                  "plots/smtlib/QF_UF/abstr_bdd_vs_tbdd_size.pdf")
    # build_models_graph(models_points, "T-BDD", "Abs. BDD",
    #                  "plots/smtlib/QF_UF/abstr_bdd_vs_tbdd_models.pdf")
    # time_points = get_time_points(
    #     qfuf_sdds_points, qfuf_abstraction_sdd_points)
    # size_points = get_nodes_points(
    #     qfuf_sdds_points, qfuf_abstraction_sdd_points)
    # build_time_graph(time_points, "T-SDD", "Abs. SDD",
    #                  "plots/smtlib/QF_UF/abstr_sdd_vs_tsdd_time.pdf")
    # build_size_graph(size_points, "T-SDD", "Abs. SDD",
    #                  "plots/smtlib/QF_UF/abstr_sdd_vs_tsdd_size.pdf")

    # --------------------------------------------------------------
    # SMTLIB QF UFLRA

    # DATA NOT READY: parsing/msat problem

    # qfuflra_ldds_points = get_smtlib_bench_data(
    #     "LDD", "benchmarks/smtlib/output_ldd/non-incremental/QF_UFLRA")
    # qfuflra_bdds_points = get_smtlib_bench_data(
    #     "T-BDD", "benchmarks/smtlib/output_bdd/non-incremental/QF_UFLRA")
    # qfuflra_abstraction_bdd_points = get_smtlib_bench_data(
    #     "Abstraction BDD", "benchmarks/smtlib/output_abstraction_bdd/non-incremental/QF_UFLRA")
    # qfuflra_sdds_points = get_smtlib_bench_data(
    #     "T-SDD", "benchmarks/smtlib/output_sdd/non-incremental/QF_RDL")
    # qfuflra_abstraction_sdd_points = get_smtlib_bench_data(
    #     "Abstraction SDD", "benchmarks/smtlib/output_abstraction_sdd/non-incremental/QF_UFLRA")

    # time_points = get_time_points(
    #     qfuflra_bdds_points, qfuflra_ldds_points)
    # size_points = get_nodes_points(
    #     qfuflra_bdds_points, qfuflra_ldds_points)
    # models_points = get_dd_models_points(
    #     qfuflra_bdds_points, qfuflra_ldds_points)
    # build_time_graph(time_points, "T-BDD", "LDD",
    #                  "plots/smtlib/UFLRA/ldd_vs_tbdd_time.pdf")
    # build_size_graph(size_points, "T-BDD", "LDD",
    #                  "plots/smtlib/UFLRA/ldd_vs_tbdd_size.pdf")
    # build_models_graph(models_points, "T-BDD", "LDD",
    #                  "plots/smtlib/UFLRA/ldd_vs_tbdd_models.pdf")
    # time_points = get_time_points(
    #     qfuflra_bdds_points, qfuflra_abstraction_bdd_points)
    # size_points = get_nodes_points(
    #     qfuflra_bdds_points, qfuflra_abstraction_bdd_points)
    # models_points = get_dd_models_points(
    #     qfuflra_bdds_points, qfuflra_abstraction_bdd_points)
    # build_time_graph(time_points, "T-BDD", "Abs. BDD",
    #                  "plots/smtlib/UFLRA/abstr_bdd_vs_tbdd_time.pdf")
    # build_size_graph(size_points, "T-BDD", "Abs. BDD",
    #                  "plots/smtlib/UFLRA/abstr_bdd_vs_tbdd_size.pdf")
    # build_models_graph(models_points, "T-BDD", "Abs. BDD",
    #                  "plots/smtlib/UFLRA/abstr_bdd_vs_tbdd_models.pdf")
    # time_points = get_time_points(
    #     qfuflra_sdds_points, qfuflra_abstraction_sdd_points)
    # size_points = get_nodes_points(
    #     qfuflra_sdds_points, qfuflra_abstraction_sdd_points)
    # build_time_graph(time_points, "T-SDD", "Abs. SDD",
    #                  "plots/smtlib/UFLRA/abstr_sdd_vs_tsdd_time.pdf")
    # build_size_graph(size_points, "T-SDD", "Abs. SDD",
    #                  "plots/smtlib/UFLRA/abstr_sdd_vs_tsdd_size.pdf")


def test_plotting_lib() -> None:
    """test plotting lib"""
    x = [5, 7, 8, 7, 2, 17, 2, 9, 4, 11, 12, 9, 6]
    y = [99, 86, 87, 88, 111, 86, 103, 87, 94, 78, 77, 85, 86]
    plt.scatter(x, y)
    plt.show()


if __name__ == "__main__":
    main()
