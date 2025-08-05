import argparse
import json
import os

import torch
from scipy.spatial.distance import cosine
from tqdm import tqdm
from transformers import BertTokenizer, BertModel

from .utils import auto_utils

parser = argparse.ArgumentParser(description="Generate answer for problem")
parser.add_argument("--exp_name", default="", type=str, help="Exp name")
parser.add_argument("--version_name", default="", type=str, help="Version name")
parser.add_argument(
    "--data", default="test", choices=["train", "test"], type=str, help="dataset"
)
parser.add_argument(
    "--category", default="algebra", type=str, help="category of problems"
)
parser.add_argument("--lb", default=0.9, type=float, help="threshold to accept")
parser.add_argument("--ub", default=1.0, type=float, help="threshold to accept")
parser.add_argument(
    "--iter", default=10, type=int, help="ieration number of data generation"
)
args = parser.parse_args()

# Load and store the contents of each JSON file
with open("./retrieval/data/auto_problem_examples_init.json") as file:
    prob_message = json.load(file)
auto_prob_message = prob_message["messages"]
print("original size of auto prob databse: %s" % ((len(prob_message) - 1) / 2))

with open("./retrieval/data/inauto_problem_examples_init.json") as file:
    prob_message = json.load(file)
inauto_prob_message = prob_message["messages"]
print("original size of inauto prob databse: %s" % ((len(inauto_prob_message) - 1) / 2))


tokenizer = BertTokenizer.from_pretrained("AnReu/math_pretrained_bert")
model = BertModel.from_pretrained("AnReu/math_pretrained_bert")

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
        texts = [nl_prob]
        fls = []
        ifls = []
        for k in range(args.iter):
            tmp_name = args.version_name + "_" + str(k)
            fl_prob = thy_series.get(tmp_name, {}).get("formal problem", "")
            fl_prob = auto_utils.normalize_statement(fl_prob)
            ifl_prob = thy_series.get(tmp_name, {}).get("informal problem", "")
            texts.append(ifl_prob)
            fls.append(fl_prob)
            ifls.append(ifl_prob)
        inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
        with torch.no_grad():
            embeddings = model(
                **inputs, output_hidden_states=True, return_dict=True
            ).pooler_output
        best_score = 0.0
        best_result = ["", "", ""]
        for e in range(1, args.iter + 1):
            cosine_sim_0_1 = 1 - cosine(embeddings[0], embeddings[e])
            if (
                best_score < cosine_sim_0_1
                and cosine_sim_0_1 >= args.lb
                and cosine_sim_0_1 <= args.ub
            ):
                data.append("=" * 100)
                data.append(
                    "\nScore: %s\nNL: %s \nIFL: %s\nFL: %s \n"
                    % (cosine_sim_0_1, nl_prob, ifls[e - 1], fls[e - 1])
                )
                best_result = [nl_prob, fls[e - 1], ifls[e - 1]]
                best_score = cosine_sim_0_1
        if best_score > 0.0:
            auto_prob_message.append(
                {
                    "role": "user",
                    "content": 'Natural language version: "%s" \nTranslate the natural language version to an Isabelle version:'
                    % (best_result[0]),
                }
            )
            auto_prob_message.append(
                {"role": "assistant", "content": "%s" % (best_result[1])}
            )
            inauto_prob_message.append(
                {
                    "role": "user",
                    "content": 'Isabelle version: "%s" \nTranslate the Isabelle version to a natural language version:'
                    % (best_result[1]),
                }
            )
            inauto_prob_message.append(
                {"role": "assistant", "content": "%s" % (best_result[2])}
            )


print("The size of updated auto prob database: %d" % ((len(auto_prob_message) - 1) / 2))
auto_prob_message = {"messages": auto_prob_message}
with open("./retrieval/data/auto_problem_examples.json", "w") as file:
    json.dump(auto_prob_message, file, indent=4)

print(
    "The size of updated inauto prob database: %d"
    % ((len(inauto_prob_message) - 1) / 2)
)
inauto_prob_message = {"messages": inauto_prob_message}
with open("./retrieval/data/inauto_problem_examples.json", "w") as file:
    json.dump(inauto_prob_message, file, indent=4)
