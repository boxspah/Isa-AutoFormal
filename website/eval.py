import os
import json
import numpy as np

path = "./batch/task_test_gpt-4/0"

k = 10
passk = [[] for i in range(k)]
for dirpath, dirnames, filenames in os.walk(path):
    json_files = [f for f in filenames if f.endswith(".json")]
    for json_file in json_files:
        file_path = os.path.join(dirpath, json_file)
        with open(file_path) as f:
            data = json.load(f)
        for i in range(k):
            name = f"a_{i}"
            passk[i].append(int(data[name]["label"]) * int(data[name]["syntax"]))

passk = np.array(passk)
for i in range(k):
    passi = np.sum(passk[: i + 1, :], axis=0)
    print(f"pass@{i + 1}: {(passi > 0).mean()}")
