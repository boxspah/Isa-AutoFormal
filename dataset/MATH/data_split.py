import argparse
import os
import random
import shutil

parser = argparse.ArgumentParser(description="Score")
parser.add_argument("--input_path", default="./data", type=str, help="data path")
parser.add_argument("--output_path", default="./batch", type=str, help="data path")
parser.add_argument("--data", default="train", type=str, help="data path")
parser.add_argument("--num", default=100, type=int, help="data size")
args = parser.parse_args()

if args.data == "train":
    input_path = os.path.join(args.input_path, "task_train_gpt-4")
    output_path = os.path.join(args.output_path, "task_train_gpt-4")
else:
    input_path = os.path.join(args.input_path, "task_test_gpt-4")
    output_path = os.path.join(args.output_path, "task_test_gpt-4")

# get a list of all JSON files in source directory and its subdirectories
json_files = []
for dirpath, dirnames, filenames in os.walk(input_path):
    json_files.extend(
        [os.path.join(dirpath, file) for file in filenames if file.endswith(".json")]
    )
random.shuffle(json_files)
idx = 0
while True:
    batch = json_files[idx * args.num : (idx + 1) * args.num]
    if len(batch) == 0:
        break
    tmp_output_path = os.path.join(
        output_path,
        str(idx),
    )
    if not os.path.exists(tmp_output_path):
        os.makedirs(tmp_output_path)
    for file in batch:
        path = os.path.join(
            tmp_output_path,
            file.replace(input_path, "./").replace(file.split("/")[-1], ""),
        )
        if not os.path.exists(path):
            os.makedirs(path)
        shutil.copy(file, path)
    idx += 1
    print("%s batch copied" % (idx))
