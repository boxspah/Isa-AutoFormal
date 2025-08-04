import os
import json
import tqdm
import numpy as np
from checker import BatchChecker

path = "/datadisk/v-yifanwu/AutoMath/equiv_checker/batch/task_test_gpt-4/48"


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
k = 10
passk = [[] for i in range(k)]
for dirpath, dirnames, filenames in os.walk(path):
    json_files = [f for f in filenames if f.endswith(".json")]
    for json_file in tqdm.tqdm(json_files):
        file_path = os.path.join(dirpath, json_file)
        with open(file_path) as f:
            data = json.load(f)
        for i in range(k):
            name = f"a_{i}"
            formal = data[name]["formal problem"]
            ok = checker.check(formal, "./tmp/temp.thy")
            data[name]["syntax"] = int(ok)
        with open(file_path, "w") as file:
            json.dump(data, file, indent=4)
