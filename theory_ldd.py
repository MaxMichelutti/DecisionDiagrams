"""LDD handling module"""
import time

from pysmt.shortcuts import BOOL, INT
from pysmt.fnode import FNode
from dd import ldd as _ldd

from walker_ldd import LDDWalker
import formula
from custom_exceptions import UnsupportedSymbolException
from string_generator import SequentialStringGenerator

def compute_ldd(phi: FNode,
                     output_file: str | None = None,
                     count_nodes: bool = False,
                     computation_logger: any = {}):
    '''Computes the LDD for the boolean formula phi and saves it on a file'''
    # BUILDING LDD
    start_time = time.time()
    print("Building LDD...")
    symbols = formula.get_symbols(phi)
    boolean_symbols:dict[FNode,str]={}
    integer_symbols:dict[FNode,int]={}
    int_ctr = 1
    str_gen = SequentialStringGenerator()
    for s in symbols:
        if s.get_type() == BOOL:
            boolean_symbols.update({s:str_gen.next_string()})
        elif s.get_type() == INT:
            integer_symbols.update({s:int_ctr})
            int_ctr+=1
        else:
            raise UnsupportedSymbolException(str(s))
    # LDD(Id theory,#int vars,#bool vars)
    ldd = _ldd.LDD(_ldd.TVPI,len(integer_symbols.keys()),len(boolean_symbols.keys()))
    walker = LDDWalker(boolean_symbols,integer_symbols,ldd)
    root = walker.walk(phi)
    elapsed_time = (time.time() - start_time)
    print("LDD for phi built in ", elapsed_time, " seconds")
    computation_logger["LDD"]["DD building time"] = elapsed_time

    # COUNTING NODES
    if count_nodes:
        n_nodes = len(root)
        print("Nodes: ",n_nodes)
        computation_logger["LDD"]["DD nodes"] = n_nodes

    # DUMPING FILE
    if output_file is not None:
        ldd.dump(output_file,[root])
    