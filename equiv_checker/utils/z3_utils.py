from z3 import *


def normalize_smt2_string(smt2_string):
    declare_smt2, assms_smt2, conc_smt2 = [], [], []
    ignore_list = ["-smt", "set-logic", "check-sat", "get-proof"]
    opt_list = ["powr$", "times$", "divide$"]
    for s in smt2_string.split("\n"):
        if any([i in s for i in ignore_list]):
            continue
        if "declare-fun" in s:
            if any([i in s for i in opt_list]):
                continue
            declare_smt2.append(s)
        s = s.replace("powr$", "^").replace("times$", "*").replace("divide$", "/")
        if "assert" in s and "axiom" in s:
            assms_smt2.append(s)
        elif "assert" in s and "conjecture" in s:
            conc_smt2.append(s)
    return declare_smt2, assms_smt2, conc_smt2


def solve_smt2_string(smt2_string):
    # s = Tactic("smt").solver()
    s = Solver()
    s.set(timeout=60000)
    declare_smt2, assms_smt2, conc_smt2 = normalize_smt2_string(smt2_string)
    for t in declare_smt2 + assms_smt2:
        s.from_string(t)
    for t in conc_smt2:
        split_smt2_string2 = t.strip().split(":named ")
        formula_part, name_part = split_smt2_string2[0], split_smt2_string2[1]
        s.from_string(
            "(assert (! (not " + formula_part.strip()[11:] + ") :named " + name_part
        )
    result = s.check()
    if result == sat:
        return False, s.sexpr(), s.model()
    else:
        return True, s.sexpr(), None
