import os
import json
import tqdm
import numpy as np
from checker import BatchChecker
import argparse

# path = '../dataset/miniF2F'


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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process JSON files for a specific node."
    )
    parser.add_argument(
        "--root_dir_list",
        default="../dataset/miniF2F/informal/",
        type=str,
        help="Comma-separated list of root directories",
    )
    args = parser.parse_args()
    root_dir_list = args.root_dir_list.split(",")

    checker = start_isa(port=40500)
    k = 10
    passk = [[] for i in range(k)]
    for path in root_dir_list:
        for dirpath, dirnames, filenames in os.walk(path):
            json_files = [f for f in filenames if f.endswith(".json")]
            print("Processing %d files" % len(json_files))
            for json_file in tqdm.tqdm(json_files):
                file_path = os.path.join(dirpath, json_file)
                with open(file_path) as f:
                    data = json.load(f)
                for i in range(k):
                    name = f"a_{i}_gpt3.5"
                    formal = data[name]["formal problem"]
                    ok = checker.check(formal, "./tmp/temp.thy")
                    data[name]["syntax"] = int(ok[0])
                with open(file_path, "w") as file:
                    json.dump(data, file, indent=4)
    for path in root_dir_list:
        for dirpath, dirnames, filenames in os.walk(path):
            json_files = [f for f in filenames if f.endswith(".json")]
            print("Processing %d files" % len(json_files))
            for json_file in tqdm.tqdm(json_files):
                file_path = os.path.join(dirpath, json_file)
                with open(file_path) as f:
                    data = json.load(f)
                for i in range(k):
                    name = f"a_{i}_deepseek"
                    formal = data[name]["formal problem"]
                    ok = checker.check(formal, "./tmp/temp.thy")
                    data[name]["syntax"] = int(ok[0])
                with open(file_path, "w") as file:
                    json.dump(data, file, indent=4)
