from pysmt.fnode import FNode
from pysmt.walkers import DagWalker, handles
import pysmt.operators as op

from custom_exceptions import UnsupportedNodeException

class BDDCUDDParser(DagWalker):
    '''A walker to translate the DAG formula quickly with memoization into the Promela syntax representation of the formula'''

    def __init__(self, mapping: dict[FNode, str], env=None, invalidate_memoization=False):
        DagWalker.__init__(self, env, invalidate_memoization)
        self.mapping = mapping
        return

    def _apply_mapping(self, arg: FNode):
        '''applies the mapping when possible, returns None othrwise'''
        if not (self.mapping.get(arg) is None):
            return self.mapping[arg]
        return None

    def walk_and(self, formula: FNode, args, **kwargs):
        '''translate AND node'''
        # pylint: disable=unused-argument
        if len(args) == 1:
            return args[0]
        res = "(" + args[0]
        for i in range(1, len(args)):
            res = res + " & " + args[i]
        return res + ")"

    def walk_or(self, formula: FNode, args, **kwargs):
        '''translate OR node'''
        # pylint: disable=unused-argument
        if len(args) == 1:
            return args[0]
        res = "(" + args[0]
        for i in range(1, len(args)):
            res = res + " | " + args[i]
        return res+")"

    def walk_not(self, formula: FNode, args, **kwargs):
        '''translate NOT node'''
        # pylint: disable=unused-argument
        return " ! " + args[0]

    def walk_symbol(self, formula: FNode, args, **kwargs):
        '''translate SYMBOL node'''
        # pylint: disable=unused-argument
        return self._apply_mapping(formula)

    def walk_bool_constant(self, formula: FNode, args, **kwargs):
        '''translate BOOL const node'''
        # pylint: disable=unused-argument
        value = formula.constant_value()
        if value:
            return "TRUE"
        return "FALSE"

    def walk_iff(self, formula, args, **kwargs):
        '''translate IFF node'''
        # pylint: disable=unused-argument
        return "(" + args[0] + " <-> " + args[1] + ")"

    def walk_implies(self, formula, args, **kwargs):
        '''translate IMPLIES node'''  # a -> b === (~ a) v b
        # pylint: disable=unused-argument
        return "( " + args[0] + " -> " + args[1] + ")"

    def walk_ite(self, formula, args, **kwargs):
        '''translate ITE node'''
        # pylint: disable=unused-argument
        return "((! " + args[0] + " | " + args[1] + ") & (" + args[0] + " | " + args[2] + "))"
    
    def walk_forall(self, formula, args, **kwargs):
        '''translate For-all node'''
        # pylint: disable=unused-argument
        raise UnsupportedNodeException('Quantifiers are yet to be supported')
    
    def walk_exists(self, formula, args, **kwargs):
        '''translate Exists node'''
        # pylint: disable=unused-argument
        raise UnsupportedNodeException('Quantifiers are yet to be supported')

    @handles(*op.THEORY_OPERATORS, *op.BV_RELATIONS, *op.IRA_RELATIONS, *op.STR_RELATIONS)
    def walk_theory(self, formula, args, **kwargs):
        '''translate theory node'''
        # pylint: disable=unused-argument
        return self._apply_mapping(formula)
