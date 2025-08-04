import argparse
import os
import json
from tqdm import tqdm
import utils.auto_utils as auto_utils

parser = argparse.ArgumentParser(description="Generate answer for problem")
parser.add_argument("--exp_name", default="", type=str, help="Exp name")
parser.add_argument("--version_name", default="", type=str, help="Version name")
parser.add_argument(
    "--data", default="test", choices=["train", "test"], type=str, help="dataset"
)
parser.add_argument(
    "--category", default="algebra", type=str, help="category of problems"
)
parser.add_argument(
    "--iter", default=10, type=int, help="ieration number of data generation"
)
args = parser.parse_args()

# Load and store the contents of each JSON file
category_array = args.category.split(",")

data = []
for i in range(len(category_array)):
    category = category_array[i]
    load_folder_path = os.path.join(
        "./data/task_" + args.data + "_" + args.exp_name, category
    )
    # Get a list of all files in the folder
    files = os.listdir(load_folder_path)
    num = len(files)
    for file in tqdm(files):
        load_file_path = os.path.join(load_folder_path, file)
        with open(load_file_path) as file:
            thy_series = json.load(file)
        nl_prob = (
            thy_series["natural problem"]
            + " "
            + f"The final answer is {thy_series['natural answer']}."
        )
        data.append(nl_prob)
        for k in range(args.iter):
            tmp_name = args.version_name + "_" + str(k)
            ifl_prob = thy_series.get(tmp_name, {}).get("informal problem", "")
            data.append(ifl_prob)

with open("data/%s_data.txt" % (args.data), "w") as f:
    for item in data:
        f.write(str(item).replace("\n", " ") + "\n")
