import os

from equiv_checker.checker import BatchChecker
from equiv_checker.test_cases import cases
from equiv_checker.utils import isa_utils


def define_test_case(idx=0):
    case = cases[idx]
    oracle, test = case.split("\n\n", 1)
    return oracle, test


def start_isa(port=40500):
    with open("./tmp/temp.thy", "w") as f:
        f.write("")
    isabelle_home = os.environ.get("ISABELLE_HOME")
    checker = BatchChecker(
        isa_path=isabelle_home,
        working_dir=isabelle_home + "/src/HOL",
        thy_path="./tmp/temp.thy",
    )
    theory = "Main HOL.HOL HOL.Real Complex_Main"
    print("create a new spark job with port %s" % (port))
    checker.initialize(theory, port=port)
    return checker


checker = start_isa(port=40500)
for i in range(len(cases)):
    print("=" * 50, f"\nstart to solve {i}-th case")
    oracle, test = define_test_case(idx=i)
    cxts0, vars0, assms0, norm_cons0 = isa_utils.normalize_statement(oracle)
    cxts1, vars1, assms1, norm_cons1 = isa_utils.normalize_statement(test)
    cxts, vars, assms = isa_utils.merge_statement(
        cxts0, cxts1, vars0, vars1, assms0, assms1, tau=0.0
    )
    formal_statement = (
        cxts
        + "\ntheorem\n"
        + vars
        + "\n"
        + assms
        + '\nshows "answer1 = answer2"'
        + "\n proof-\n show ?thesis using assms sledgehammer"
    )
    pre_tactic, heuristics = isa_utils.premise_select(formal_statement)
    print(f"Formal statement: {formal_statement}\nPremise selection: {pre_tactic}")
    if norm_cons0 != norm_cons1:
        print(f"Result: conclusions are not equivalent: {norm_cons0} and {norm_cons1}")
        continue
    # ok, results = checker.check(formal_statement, './tmp/temp.thy', pre_tactic, heuristics)
    # if results == "":
    #     print('Result: SYNTAX ERROR')
    # elif "sorry" in results:
    #     print('Result: FAIL', '\t', results)
    # else:
    #     print('Result: SUCCESS', '\t', results)
    # sys.stdout.flush()
