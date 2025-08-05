import sys

sys.path.append("/home/argustest/pysmt")
from pysmt.shortcuts import Solver

# (declare-fun initial_amoebae () Int)
# (assert (= 0 (log initial_amoebae)))
# (check-sat)
# (get-value (initial_amoebae))

statement = """
(declare-fun initial_amoebae () Real)
(assert (= 1 initial_amoebae))
(assert (= 0.0 (log initial_amoebae)))
(check-sat)
(get-value (initial_amoebae))
"""

#
from z3 import *


def solution():
    solver = Solver()
    # variables
    initial_trees = Int("initial_trees")
    final_trees = Int("final_trees")
    trees_planted = Int("trees_planted")
    # conditions
    solver.add(initial_trees == 15)
    solver.add(final_trees == 21)
    solver.add(trees_planted == final_trees - initial_trees)

    return trees_planted, solver


import json

*middle_book, solver = solution()
print(json.dumps(solver.sexpr()))
# if solver.check()== sat:
#     print([eval(str(solver.model().eval(e))) for e in middle_book])
#     print(solver.model())
# else:
#     print(solver.check())

# s = z3.Solver()
# s.from_string(statement.replace('pow', '^'))
# print(s)
# print(s.sexpr())
# print(s.check())
# print(s.model())

# smt_parser = SmtLibParser()
# res = SmtLibScript()
# # for cmd in smt_parser.get_command_generator(StringIO(statement)):
#     # print(cmd)
#     # res.add_command(cmd)
# script = smt_parser.get_script(StringIO(statement))
# print(script)

# buf_out = StringIO()
# script.serialize(buf_out, daggify=True)
# print(buf_out.getvalue())

# # s.from_string(statement)
# with Solver(name='msat') as solver:
#     logs = script.evaluate(solver)
# (cmd, res) = logs[-1]
# if cmd == "get-value":
#     solution = ",".join([str(res[key]) for key in res.keys()])
# print(solution)
