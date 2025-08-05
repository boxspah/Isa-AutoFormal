import argparse
import json
import os

import matplotlib.pyplot as plt
import torch
from scipy.spatial.distance import cosine
from tqdm import tqdm
from transformers import BertTokenizer, BertModel

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

tokenizer = BertTokenizer.from_pretrained("AnReu/math_pretrained_bert")
model = BertModel.from_pretrained("AnReu/math_pretrained_bert")

# Load and store the contents of each JSON file
category_array = args.category.split(",")

data = []
score = []
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
            ifl_prob = thy_series.get(tmp_name, {}).get("informal problem", "")
            texts.append(ifl_prob)
            fls.append(fl_prob)
            ifls.append(ifl_prob)
        inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt")
        with torch.no_grad():
            embeddings = model(
                **inputs, output_hidden_states=True, return_dict=True
            ).pooler_output
        for e in range(1, args.iter + 1):
            cosine_sim_0_1 = 1 - cosine(embeddings[0], embeddings[e])
            if cosine_sim_0_1 >= args.lb and cosine_sim_0_1 <= args.ub:
                data.append("=" * 100)
                data.append("\nfilename: " + (str(file.name)))
                data.append(
                    "\nScore: %s\nNL: %s \nIFL: %s\nFL: %s \n"
                    % (cosine_sim_0_1, nl_prob, ifls[e - 1], fls[e - 1])
                )
                score.append(cosine_sim_0_1)

with open(
    "res/results_{}_{}_{}.txt".format(args.version_name, args.lb, args.ub), "w"
) as f:
    for item in data:
        f.write(item)

plt.figure()
plt.hist(score, bins=20)
plt.savefig(
    "res/results_{}_{}_{}.pdf".format(args.version_name, args.lb, args.ub), format="pdf"
)
