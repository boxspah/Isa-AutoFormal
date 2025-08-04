import os
import sys
import utils.isa_utils as isa_utils
import utils.all_exceptions as E
from test_cases import cases
import tqdm

import utils.logging_utils as log_utils
from datetime import datetime

log_utils.logging_init(
    os.path.join("./logs/log_%s.log" % (datetime.now().strftime("%Y-%m-%d_%H:%M:%S")))
)


def define_test_case(idx=0):
    case = cases[idx]
    oracle, test = case.split("\n\n", 1)
    return oracle, test


def restart_test(checker):
    print(checker)
    checker.exit()
    isa_utils.researt_isa(checker)
    print(checker)


checker = isa_utils.start_isa(port=40500)
for i in tqdm.tqdm(range(len(cases))):
    print("\n" + "=" * 50, f"\nstart to solve {i}-th case")
    oracle, test = define_test_case(idx=i)
    try:
        flag, msg = isa_utils.naive_check_solve_direct(oracle, test, checker, [])
    except (E.ThmFormatException, E.SimplifyException, E.ConcException) as e:
        flag = False
        msg = str(e)
    print("naive check", msg)
    if flag:
        continue
checker.exit()
