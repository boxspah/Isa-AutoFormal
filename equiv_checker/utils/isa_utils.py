import itertools
import logging
import os
import re
import time

import numpy as np
import z3
from munkres import Munkres

from . import z3_utils
from .all_exceptions import ThmFormatException, ConcException, SimplifyException
from ..checker import BatchChecker, DEBUG, init_port


def parse_statement(statement):
    """
    parse the assumption and conclusion from given statement
    """
    quotes_pattern = re.compile(r'"([\s\S]*?)"')
    if "theorem" not in statement:
        raise ThmFormatException("No theorem keyword in the statement", statement)
    cxts, thms = (item.strip() for item in statement.split("theorem", 1))
    ### parse and rewrite the conclusion
    match = re.search(r"shows(.*)", thms, re.DOTALL)
    if match is None:
        raise ThmFormatException("No conclusion in the theorem", statement)
    concls = quotes_pattern.findall(match.group(1))
    # if len(concls) > 1:
    #     raise E.ConcException('Multiple conclusions in the theorem', statement)
    concls = r" \<and> ".join([f"({c})" for c in concls])
    ### parse and rewrite the assumptions
    match = re.search(r"assumes(.*?)shows", thms, re.DOTALL)
    assms = quotes_pattern.findall(match.group(1).strip()) if match is not None else []
    assms = r" \<and> ".join([f"({a})" for a in assms])
    return cxts, assms, concls


def split_equation(equation):
    # parse equation should except the case like "(a `=` b) = True"
    equation = re.sub(
        r"\([^)]*=[^(]*\)", lambda x: x.group(0).replace("=", "#?#"), equation
    )
    equation = re.sub(
        r"\{[^}]*=[^{}]*\}", lambda x: x.group(0).replace("=", "#?#"), equation
    )
    parts = equation.split("=")
    if len(parts) != 2:
        raise ConcException(
            f"ConcError: Conclusion cannot be parsed: {equation}", equation
        )
    else:
        return [item.replace("#?#", "=").strip() for item in parts]


def ThmCheck(statement):
    if "shows" not in statement:
        raise ThmFormatException("No conclusion in the theorem", statement)
    answer = statement.split("shows")
    if "assumes" in answer[0]:
        header = answer[0].split("assumes")[0]
        assumptions = "assumes" + answer[0].split("assumes")[1]
    else:
        header = answer[0]
        assumptions = ""
    conclusion = answer[1]
    quotes_pattern = re.compile(r'"([\s\S]*?)"')
    header_match = quotes_pattern.findall(header)
    assumes_match = quotes_pattern.findall(assumptions)
    shows_match = quotes_pattern.findall(conclusion)
    if any(
        (s in "\n".join(assumes_match) or s in "\n".join(header_match))
        for s in shows_match
    ):
        raise ThmFormatException(
            "The conclusion is written in the assumptions", statement
        )
    return True


def normalize_statement(statement):
    quotes_pattern = re.compile(r'"([\s\S]*?)"')
    if "theorem" not in statement:
        raise ThmFormatException("No theorem keyword in the statement", statement)
    cxts, thms = (item.strip() for item in statement.split("theorem", 1))
    ### parse and rewrite the conclusion
    ok = ThmCheck(statement)
    match = re.search(r"shows(.*)", thms, re.DOTALL)
    # if match is None:
    #     raise E.ThmFormatException('No conclusion in the theorem', statement)
    cons = quotes_pattern.findall(match.group(1))
    # if len(cons) > 1:
    # raise E.ConcException('Multiple conclusions in the theorem', statement)
    norm_cons = []
    add_ass = []
    add_var = []
    for i, con in enumerate(cons):
        lhs, rhs = split_equation(con)
        if lhs == rhs:
            raise ConcException(f"ConcError: Conclusion is trivial {lhs} = {rhs}", con)
        add_ass.append(f"answer_{i} = {lhs} - {rhs}")
        ### if lhs is a float-point number, define answer :: real; else using general type instead
        if re.match(r"^-?\d+(\.\d+)?$", lhs):
            cur_var = "answer :: real"
        else:
            cur_var = "answer::"
        add_var.append(cur_var)
        norm_cons.append(f"answer_{i} = 0")
    if DEBUG:
        logger.debug(
            f"checkpoint 1: rewrite cons {add_ass} {norm_cons}"
        )  # checkpoint 1
    ### parse and rewrite the fixes
    match = re.search(r"fixes(.*?)(assumes|shows)", thms, re.DOTALL)
    if match is not None:
        vars = match.group(1).strip().split(" and ") + add_var
    else:
        vars = add_var
    if DEBUG:
        logger.debug(f"checkpoint 2: rewrite vars {vars}")  # checkpoint 2
    ### parse and rewrite the assumptions
    match = re.search(r"assumes(.*?)shows", thms, re.DOTALL)
    if match is not None:
        assms = quotes_pattern.findall(match.group(1).strip()) + add_ass
    else:
        assms = add_ass
    if DEBUG:
        logger.debug(f"checkpoint 3: rewrite assms {assms}")  # checkpoint 3
    return cxts, vars, assms, norm_cons


def parse_check_result(formal_statement, result, checker):
    final_ok = result.get("final_ok", False)
    if final_ok == "syntax error":
        msg = "Result: SYNTAX ERROR"
        return False, msg
    elif final_ok == False:
        try:
            smt2lib = checker.isa2smt(formal_statement, checker.path_to_file)
            ok, expr, sol = z3_utils.solve_smt2_string(smt2lib)
        except z3.z3types.Z3Exception as e:
            ok, expr, sol = False, "", str(e)
        except Exception as e:
            ok, expr, sol = False, "", str(e)
        if ok == False:
            msg = "Result: FAIL" + "\t" + expr + "\n" + "z3 solution: " + str(sol)
            return False, msg
        else:
            msg = "Result: SUCCESS" + "\t" + "solved by z3"
            return True, msg
    elif final_ok == True:
        msg = (
            "Result: SUCCESS"
            + "\t"
            + "using tactic: "
            + result.get("step_0", {}).get("statement", "")
            + result.get("step_4", {}).get("statement", "")
        )
        # logger.info(f"Checking parsing result: {result}")
        final_round = result.get("step_4", {}).get("results", "")
        # logger.info(f"origin result {result}")
        # logger.info(f"Checking parsing result: {final_round}")
        if "subgoal" in final_round:
            return False, msg + "\n" + final_round
        return True, msg
    return None, ""


def merge_vars(vars1, vars2):
    """
    here we do NOT verify the type consistency
    """
    new_vars_with_types = []
    new_vars_without_types = []
    # handle like a_1 var_0 :: "real * real"
    for vs in vars1.split(" and ") + vars2.split(" and "):
        if "::" in vs:
            name, vtype = (item.strip() for item in vs.split("::", 1))
        else:
            name, vtype = vs, ""
        for v in name.split(" "):
            merge_v = v + " :: " + vtype if vtype != "" else v
            if v not in new_vars_without_types:
                new_vars_without_types.append(v)
                new_vars_with_types.append(merge_v)
    vars = " and ".join(new_vars_with_types)
    return vars


def start_isa(port=4050):
    file_path = "./logs/temp_%s.thy" % (port)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open("./logs/temp_%s.thy" % (port), "w") as f:
        f.write("")
    isabelle_home = os.environ.get("ISABELLE_HOME")
    global logger
    logger = logging.getLogger(f"logger_{port - init_port}")
    checker = BatchChecker(
        isa_path=isabelle_home,
        working_dir=isabelle_home + "/src/HOL",
        thy_path="./logs/temp_%s.thy" % (port),
    )
    theory = "Main HOL.HOL HOL.Real Complex_Main"  # "HOL-Analysis.Derivative" "HOL-Computational_Algebra.Computational_Algebra"'
    # print('create a new spark job with port %s' %(port))
    logger.info("create a new spark job with port %s" % (port))
    checker.initialize(theory, port=port)
    return checker


def researt_isa(checker):
    checker_port = checker.get_port()
    checker.exit()
    logger.info(f"restarting the checker with port {checker_port}")
    time.sleep(30)
    theory = "Main HOL.HOL HOL.Real Complex_Main"  # "HOL-Analysis.Derivative" "HOL-Computational_Algebra.Computational_Algebra"'
    checker.initialize(theory, port=checker_port)


def naive_check(statement1, checker, memory_heuristics=[]):
    formal_statement = f"{statement1}\n proof-\n show ?thesis using assms sledgehammer"
    pre_tactic, heuristics = premise_select(formal_statement)
    heuristics = memory_heuristics + heuristics
    logger.info(
        f"Formal statement: \n{formal_statement.strip()}\nPremise selection: {pre_tactic}"
    )
    ok, results = checker.check(
        formal_statement, checker.path_to_file, pre_tactic, heuristics
    )
    ok, msg = parse_check_result(formal_statement, results, checker)
    msg = msg.replace(pre_tactic, "")  # remove pre_tactic
    ### check vacuous truth
    if ok == True:
        vacuous_statement = formal_statement.split("shows", 1)[0]
        vacuous_statement = (
            vacuous_statement
            + 'shows "0=1"'
            + "\n proof-\n show ?thesis using assms sledgehammer"
        )
        ok, results = checker.check(
            vacuous_statement, checker.path_to_file, pre_tactic, heuristics
        )
        if results["final_ok"] == True:
            return False, "Vacuous truth!"
    return ok, msg


def naive_check_solve_direct(statement1, statement2, checker, memory_heuristics=[]):
    if statement1.replace(" ", "") == statement2.replace(" ", ""):
        return True, "proved by trivial; the two statements are exactly same"
    statement1 = statement1.replace("theorem", "theorem first_theorem:")
    statement2 = statement2.replace("theorem", "theorem second_theorem:")
    formal_statement = f"{statement1}\n sorry \n\n{statement2}"
    pre_tactic, heuristics = premise_select(formal_statement)
    pre_tactic = "apply(auto)"
    heuristics = []
    logger.info(
        f"Formal statement: \n{formal_statement.strip()}\nPremise selection: {pre_tactic}"
    )
    ok, results = checker.plain_check(
        formal_statement,
        checker.path_to_file,
        "apply (rule first_theorem) using assms ",
    )
    # print(results)
    # exit()
    ok, msg = parse_check_result(formal_statement, results, checker)
    final_round = results.get("step_0", {}).get("results", "")
    if ok == True and "No subgoals" not in final_round:
        ok = False
        msg = "Result: FAIL :" + results.get("step_0", {}).get("statement", "")
        return ok, msg
    logger.info(f"Checking the first theorem: result: {ok}, message:{msg}")
    msg = msg.replace(pre_tactic, "")  # remove pre_tactic

    if ok == True:
        formal_statement = f"{statement2}\n sorry\n\n{statement1}\n "
        pre_tactic, heuristics = premise_select(formal_statement)
        pre_tactic = "apply(auto)"
        heuristics = []
        logger.info(
            f"Formal statement: \n{formal_statement.strip()}\nPremise selection: {pre_tactic}"
        )
        ok, results = checker.plain_check(
            formal_statement,
            checker.path_to_file,
            "apply (rule second_theorem) using assms ",
        )
        ok, msg = parse_check_result(formal_statement, results, checker)
        final_round = results.get("step_0", {}).get("results", "")
        if ok == True and "No subgoals" not in final_round:
            ok = False
            msg = "Result: FAIL :" + results.get("step_0", {}).get("statement", "")
            return ok, msg
        logger.info(f"Checking the second theorem: result: {ok}, message:{msg}")
        msg = msg.replace(pre_tactic, "")  # remove pre_tactic
    else:
        return ok, msg

    return ok, msg
    ### check vacuous truth
    if ok == True:
        logger.info(f"Checking vacuous truth for statement1")
        vacuous_statement = statement1.split("shows", 1)[0]
        vacuous_statement = (
            vacuous_statement
            + 'shows "0=1"'
            + "\n proof-\n show ?thesis using assms sledgehammer"
        )
        ok, results = checker.check(
            vacuous_statement, checker.path_to_file, pre_tactic, heuristics
        )
        if results["final_ok"] == True:
            return False, "Vacuous truth!"
        logger.info(f"Checking vacuous truth for statement2")
        vacuous_statement = statement2.split("shows", 1)[0]
        vacuous_statement = (
            vacuous_statement
            + 'shows "0=1"'
            + "\n proof-\n show ?thesis using assms sledgehammer"
        )
        ok, results = checker.check(
            vacuous_statement, checker.path_to_file, pre_tactic, heuristics
        )
        if results["final_ok"] == True:
            return False, "Vacuous truth!"
    return ok, msg


def check_equivalence(statement1, statement2, checker, memory_heuristics=[]):
    cxts0, vars0, assms0, norm_cons0 = normalize_statement(statement1)
    cxts1, vars1, assms1, norm_cons1 = normalize_statement(statement2)
    cxts, vars, assms = merge_statement(
        cxts0, cxts1, vars0, vars1, assms0, assms1, tau=0.0
    )
    if len(norm_cons0) != len(norm_cons1):
        raise ConcException(
            f"ConcError: Conclusions are not aligned: {norm_cons0} and {norm_cons1}",
            [norm_cons0, norm_cons1],
        )
    concls = f'"{" and ".join([f"answer1_{i} = answer2_{i}" for i in range(len(norm_cons0))])}"'
    formal_statement = f"{cxts}\ntheorem\n{vars}\n{assms}\nshows {concls}\n proof-\n show ?thesis using assms sledgehammer"
    pre_tactic, heuristics = premise_select(formal_statement)
    heuristics = memory_heuristics + heuristics
    logger.info(
        f"Formal statement: \n{formal_statement.strip()}\nPremise selection: {pre_tactic}"
    )
    ok, results = checker.check(
        formal_statement, checker.path_to_file, pre_tactic, heuristics
    )
    ok, msg = parse_check_result(formal_statement, results, checker)
    msg = msg.replace(pre_tactic, "")  # remove pre_tactic
    ### check vacuous truth
    if ok == True:
        vacuous_statement = formal_statement.split("shows", 1)[0]
        vacuous_statement = (
            vacuous_statement
            + 'shows "0=1"'
            + "\n proof-\n show ?thesis using assms sledgehammer"
        )
        ok, results = checker.check(
            vacuous_statement, checker.path_to_file, pre_tactic, heuristics
        )
        if results["final_ok"] == True:
            return False, "Vacuous truth!"
    return ok, msg


def check_equivalence_simplify(statement1, statement2, checker, memory_heuristics=[]):
    """
    1) first simplify the statements
    2) call check_equivalence
    """
    try:
        ok1, state1 = checker.simplify(statement1, checker.path_to_file)
        ok2, state2 = checker.simplify(statement2, checker.path_to_file)
        if (
            ok1 == False
            or ok2 == False
            or r"\<Longrightarrow>" not in state1
            or r"\<Longrightarrow>" not in state2
        ):
            raise SimplifyException(
                f"SimplifyError: Simplification failed in\n {statement1} \nOR\n {statement2}",
                [statement1, statement2],
            )
        assms1, concls1 = (
            item.strip() for item in state1.split(r"\<Longrightarrow>", 1)
        )
        assms1 = assms1.replace(r"\<lbrakk>", "").replace(r"\<rbrakk>", "").split(";")
        assms1 = r" \<and> ".join([f"({a.strip()})" for a in sorted(assms1, key=len)])
        assms2, concls2 = (
            item.strip() for item in state2.split(r"\<Longrightarrow>", 1)
        )
        assms2 = assms2.replace(r"\<lbrakk>", "").replace(r"\<rbrakk>", "").split(";")
        assms2 = r" \<and> ".join([f"({a.strip()})" for a in sorted(assms2, key=len)])
    except (SimplifyException, ConcException) as e:
        cxts1, assms1, concls1 = parse_statement(statement1)
        cxts2, assms2, concls2 = parse_statement(statement2)

    ### quick check
    if re.sub(r"\s", "", assms1) == re.sub(r"\s", "", assms2) and re.sub(
        r"\s", "", concls1
    ) == re.sub(r"\s", "", concls2):
        return True, "proved by trivial; the two statements are exactly same"

    ### get vars in the conclusion
    match = re.search(r"fixes(.*?)(assumes|shows)", statement1, re.DOTALL)
    vars1 = match.group(1).strip().split(" and ") if match is not None else []
    vars1, vars1_list = (
        " and ".join(vars1),
        list(itertools.chain(*[v.split("::")[0].strip().split(" ") for v in vars1])),
    )
    match = re.search(r"fixes(.*?)(assumes|shows)", statement2, re.DOTALL)
    vars2 = match.group(1).strip().split(" and ") if match is not None else []
    vars2, vars2_list = (
        " and ".join(vars2),
        list(itertools.chain(*[v.split("::")[0].strip().split(" ") for v in vars2])),
    )
    matches1 = re.findall(r"\b\w+\b", concls1)
    matches2 = re.findall(r"\b\w+\b", concls2)
    vars_in_concls1 = [
        match for match in matches1 if any([match in v for v in vars1_list])
    ]
    vars_in_concls2 = [
        match for match in matches2 if any([match in v for v in vars2_list])
    ]
    if len(set(vars_in_concls1)) != len(set(vars_in_concls2)):
        raise ThmFormatException(
            f"The variables of two statements are not aligned:\n{vars_in_concls1}\nAND\n{vars_in_concls2}",
            vars_in_concls1 + vars_in_concls2,
        )
    ### fuse the two statements together
    i, new_vars1 = 0, []
    for v in vars1_list:
        if v in vars_in_concls1:
            new_v = f"var_{i}"
            i += 1
        else:
            new_v = v + "_1"
        new_vars1.append(new_v)
        pattern = re.compile(f"(?<![a-zA-Z]){v}(?![a-zA-Z])")
        vars1 = pattern.sub(new_v, vars1)
        assms1 = pattern.sub(new_v, assms1)
        concls1 = pattern.sub(new_v, concls1)
    i, new_vars2 = 0, []
    for v in vars2_list:
        if v in vars_in_concls2:
            new_v = f"var_{i}"
            i += 1
        else:
            new_v = v + "_2"
        new_vars2.append(new_v)
        pattern = re.compile(f"(?<![a-zA-Z]){v}(?![a-zA-Z])")
        vars2 = pattern.sub(new_v, vars2)
        assms2 = pattern.sub(new_v, assms2)
        concls2 = pattern.sub(new_v, concls2)

    common_vars = ",".join([f"var_{j}" for j in range(i)])
    vars = merge_vars(vars1, vars2)
    # cxts = cxts1 + '\n' + cxts2 # TODO: handle the cxts
    ### check the equivalence of the conclusions
    if concls1:
        concls1 = ". " + concls1
    if concls2:
        concls2 = ". " + concls2
    statement = f'theorem\nfixes {vars} \nshows "{{({common_vars}){concls1}}} = {{({common_vars}){concls2}}}"'
    logger.info(f"Formal statement of conclusion equivalence: \n{statement.strip()}")
    pre_tactic, heuristics = premise_select(statement)
    heuristics = memory_heuristics + heuristics
    ok, results = checker.meta_check(
        statement, checker.path_to_file, pre_tactic=pre_tactic, heuristics=heuristics
    )
    ok, concls_msg = parse_check_result(statement, results, checker)
    concls_msg = concls_msg.replace(pre_tactic, "")  # remove pre_tactic
    # print(concls_msg)
    if ok == False:
        return False, "Conclusion equivalence " + concls_msg
    ### check the equivalence of the assumptions
    if assms1:
        assms1 = ". " + assms1
    if assms2:
        assms2 = ". " + assms2
    statement = f'theorem\nfixes {vars} \nshows "{{({common_vars}){assms1}}} = {{({common_vars}){assms2}}}"'
    logger.info(f"Formal statement of assumption equivalence: \n{statement.strip()}")
    pre_tactic, heuristics = premise_select(statement)
    heuristics = memory_heuristics + heuristics
    ok, results = checker.meta_check(
        statement, checker.path_to_file, pre_tactic=pre_tactic, heuristics=heuristics
    )
    ok, assms_msg = parse_check_result(statement, results, checker)
    assms_msg = assms_msg.replace(pre_tactic, "")  # remove pre_tactic
    # print(assms_msg)
    if ok == False:
        return False, "Assumption equivalence " + assms_msg
    return True, assms_msg + "\n" + concls_msg


def custom_edit_distance(assms0, assms1, vars):
    # Initialize matrix of zeros
    assms0 = assms0.split(" ")
    assms1 = assms1.split(" ")
    distances = np.zeros(shape=(len(assms0) + 1, len(assms1) + 1))
    # matched_vars = set()

    # Initialize first column and row
    for i in range(len(assms0) + 1):
        distances[i][0] = i
    for j in range(len(assms1) + 1):
        distances[0][j] = j

    # Fill in the rest of the matrix
    for i in range(1, len(assms0) + 1):
        for j in range(1, len(assms1) + 1):
            if assms0[i - 1] == assms1[j - 1] or (
                assms0[i - 1] in vars and assms1[j - 1] in vars
            ):
                distances[i, j] = distances[i - 1, j - 1]
                # if assms0[i-1] in vars and assms1[j-1] in vars:
                # matched_vars.add((assms0[i-1], assms1[j-1]))
            else:
                distances[i, j] = min(
                    distances[i - 1, j] + 1,  # delete
                    distances[i, j - 1] + 1,  # insert
                    distances[i - 1, j - 1] + 1,  # substitute
                )
    return distances[-1, -1]


def predicate_alignment(assms0, assms1, vars0, vars1, tau=0.0):
    common_vars, common_assms = [], []
    new_vars0 = [
        v.split("::")[0].strip().split(" ") for v in vars0 if "\\<Rightarrow>" in v
    ]
    new_vars1 = [
        v.split("::")[0].strip().split(" ") for v in vars1 if "\\<Rightarrow>" in v
    ]
    new_vars0 = [item for sublist in new_vars0 for item in sublist]
    new_vars1 = [item for sublist in new_vars1 for item in sublist]
    if len(new_vars0) == 0 or len(new_vars1) == 0:
        return assms0, assms1, common_assms, vars0, vars1, common_vars

    pairs = []
    m = Munkres()
    for v0 in new_vars0:
        for v1 in new_vars1:
            # Remove the last assms, i.e., answer = xxx
            tmp_vars = [v0, v1]
            new_assms0 = [a for a in assms0[:-1] if any(t == v0 for t in a.split(" "))]
            new_assms1 = [a for a in assms1[:-1] if any(t == v1 for t in a.split(" "))]
            ### RISK Here: we may ignore (at most) one assm when comparing
            if (
                len(new_assms0) == 0
                or len(new_assms1) == 0
                or abs(len(new_assms1) - len(new_assms0)) > 1
            ):
                continue
            # Modify the matrix computation to save the matched variables
            matrix = [
                [custom_edit_distance(s1, s2, tmp_vars) for s2 in new_assms1]
                for s1 in new_assms0
            ]
            indexes = m.compute(matrix)
            if all(matrix[row][column] <= tau for row, column in indexes):
                # print([f"{new_assms0[row]} <==> {new_assms1[column]}: {matrix[row][column]}" for row, column in indexes])
                logger.info(
                    [
                        f"{new_assms0[row]} <==> {new_assms1[column]}: {matrix[row][column]}"
                        for row, column in indexes
                    ]
                )
                pairs.append((v0, v1))
                continue

    if len(pairs) == 0:
        return assms0, assms1, common_assms, vars0, vars1, common_vars

    for v0, v1 in pairs:
        tmp_v = f"com_{v0[:-1]}_{v1[:-1]}"
        common_vars += [v.replace(v0, tmp_v) for v in vars0 if v0 in v]
        vars0 = [v for v in vars0 if v0 not in v]
        vars1 = [v for v in vars1 if v1 not in v]
        pattern = re.compile(f"(?<![a-zA-Z]){v0}(?![a-zA-Z])")
        common_assms += [pattern.sub(tmp_v, a) for a in assms0 if v0 in a]
        pattern = re.compile(f"(?<![a-zA-Z]){v1}(?![a-zA-Z])")
        common_assms += [
            pattern.sub(tmp_v, a) for a in assms1 if v1 in a and "answer" in a
        ]
        assms0 = [a for a in assms0 if v0 not in a]
        assms1 = [a for a in assms1 if v1 not in a]

    return assms0, assms1, common_assms, vars0, vars1, common_vars


def normalize_operator(equation):
    #### TODO: write in ML function to normalize the operator
    r"""
    Convert equation to its normal form (in the sense of string)
    (1) replace "a+b" by "a + b"
    (2) replace ∀n > 1. to ∀n. n > 1 \<longrightarrow>
    (3) replace \exists n > 1. to \exists n. n > 1 \<longrightarrow>
    """
    equation = re.sub(r"(?<!<)(?<!\s)([+\-*/])(?!\s)(?![^<>]*>)", r" \1 ", equation)
    equation = re.sub(
        r"\\<forall>(\w+) > (\d+)\.",
        r"\\<forall>\1. \1 > \2 \<longrightarrow>",
        equation,
    )
    equation = re.sub(
        r"\\<exists>(\w+) > (\d+)\.",
        r"\\<exists>\1. \1 > \2 \<longrightarrow>",
        equation,
    )
    return equation


def merge_statement(cxts0, cxts1, vars0, vars1, assms0, assms1, tau=0.0):
    """
    1) replace all vars and assms by fresh ones
    2) align functions, i.e., match the complex predicates (Note: tau < 0 means no matching)
    """
    cxts = cxts0 + cxts1
    new_vars0, new_assms0 = [], []
    old_vs = []
    for v in vars0:
        vs, ts = (item.strip() for item in v.split("::", 1))
        old_vs += vs.split(" ")
        new_vs = []
        for v in vs.split(" "):
            new_v = v + "1"
            new_vs.append(new_v)
        if ts != "":
            new_vars0.append(" ".join(new_vs) + " :: " + ts)
        else:
            new_vars0.append(" ".join(new_vs))
    num_v = len(old_vs)
    for a in assms0:
        # catch local var in quantifier
        match = re.search(r"\\\<forall\>(.*?)[><=.]", a, re.DOTALL)
        qt_vs = match.group(1).strip().split(" ") if match is not None else []
        match = re.search(r"\\\<exists\>(.*?)[><=.]", a, re.DOTALL)
        qt_vs += match.group(1).strip().split(" ") if match is not None else []
        for i in range(num_v):
            if old_vs[i] in qt_vs:
                continue
            pattern = re.compile(f"(?<![a-zA-Z]){old_vs[i]}(?![a-zA-Z])")
            a = pattern.sub(f"{old_vs[i]}1", a)
        new_assms0.append(a)
    new_vars1, new_assms1 = [], []
    old_vs = []
    for v in vars1:
        vs, ts = (item.strip() for item in v.split("::", 1))
        old_vs += vs.split(" ")
        new_vs = []
        for v in vs.split(" "):
            new_v = v + "2"
            new_vs.append(new_v)
        if ts != "":
            new_vars1.append(" ".join(new_vs) + " :: " + ts)
        else:
            new_vars1.append(" ".join(new_vs))
    num_v = len(old_vs)
    for a in assms1:
        # catch local var in quantifier
        match = re.search(r"\\\<forall\>(.*?)[><=.]", a, re.DOTALL)
        qt_vs = match.group(1).strip().split(" ") if match is not None else []
        match = re.search(r"\\\<exists\>(.*?)[><=.]", a, re.DOTALL)
        qt_vs += match.group(1).strip().split(" ") if match is not None else []
        for i in range(num_v):
            if old_vs[i] in qt_vs:
                continue
            pattern = re.compile(f"(?<![a-zA-Z]){old_vs[i]}(?![a-zA-Z])")
            a = pattern.sub(f"{old_vs[i]}2", a)
        new_assms1.append(a)

    #### match same predicates
    new_assms0 = [normalize_operator(a) for a in new_assms0]
    new_assms1 = [normalize_operator(a) for a in new_assms1]
    results = predicate_alignment(new_assms0, new_assms1, new_vars0, new_vars1, tau=tau)
    new_assms0, new_assms1, common_assms, new_vars0, new_vars1, common_vars = results
    ### merge them together
    vars = [v for v in new_vars0 + new_vars1 + common_vars]
    vars = "fixes " + "\nand ".join(vars)
    assms = [f'"{a}"' for a in new_assms0 + new_assms1 + common_assms]
    assms = "assumes " + "\nand ".join(assms)
    return cxts, vars, assms


def premise_select(formal):
    heuristics = [
        "done",
        "by auto",
        "by simp",
        "by eval",
        "supply [[smt_trace=true]] by smt",
        "by blast",
        "by fastforce",
        "by force",
        "by eval",
        "by presburger",
        "by arith",
        "by linarith",
        "by (auto simp: field_simps)",
    ]
    pre_tactic = []
    if ("root " in formal or "sqrt " in formal) and "powr " in formal:
        pre_tactic.append("root_powr_inverse")
    if "fold " in formal:
        pre_tactic.append("upt_def")

    if len(pre_tactic) > 0:
        pre_tactic = f"apply(auto simp add: {' '.join(pre_tactic)})"
    else:
        pre_tactic = "apply(auto)"

    return pre_tactic, heuristics
