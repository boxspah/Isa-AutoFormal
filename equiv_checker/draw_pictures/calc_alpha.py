import argparse
import json
import math
import os

import torch


def get_json_files(root_dir, suffix=[]):
    json_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                json_files.append(file_path)
    return json_files


def get_scores(json_file_paths):
    T = 1
    pass1, pass10, correct, total = 0, 0, 0, 0
    symbolic_correct, semantic_correct, cluster_correct = 0, 0, 0
    S_sy, S_se, S_sc, S_label = [], [], [], []
    # for (id, json_file) in tqdm.tqdm(enumerate(json_file_paths)):
    for json_file in json_file_paths:
        # print(json_file)
        with open(json_file) as f:
            data = json.load(f)
        symbolic_scores, semantic_scores, cluster_scores, syntax_scores, gts = (
            [],
            [],
            [],
            [],
            [],
        )
        if "prediction" not in data or len(data["prediction"]) == 0:
            print("skip")
            continue
        components = [data["prediction"][key] for key in data["prediction"].keys()]
        #### autoformalize the problem

        for i in range(10):
            name = f"a_{i}"
            semantic_score = data[name]["semantic_score"]
            symbolic_score = data[name]["symbolic_score"]
            semantic_scores.append(semantic_score)
            symbolic_scores.append(symbolic_score)
            # syntax_scores.append(data[name]["syntax"])
            syntax_scores.append(data[name].get("syntax", 1))
            # syntax_scores.append(1)
            # gts.append(data[f'a_{i}']['label'])
            if (
                i in data.get("equivalence_oracle", [])
                or data[f"a_{i}"].get("label", 0) == 1
            ):
                gts.append(1)
            else:
                gts.append(0)
        # print(semantic_scores)
        # print(syntax_scores)
        # print(semantic_scores)
        # print(symbolic_scores)
        semantic_scores = torch.softmax(
            torch.tensor(semantic_scores) * 3, dim=0
        ).tolist()
        symbolic_scores = torch.softmax(
            torch.tensor(symbolic_scores) * 4, dim=0
        ).tolist()
        # print(semantic_scores)
        S_sy.append(symbolic_scores)
        S_se.append(semantic_scores)
        S_sc.append(syntax_scores)
        S_label.append(gts)
    return S_sy, S_se, S_sc, S_label


def calc_linear(S_sy, S_se, S_sc, S_label):
    x_values = []
    y_values = []
    best_alpha = 0
    best_alpha_last = 0
    best_correct = 0
    for alpha in range(0, 51):
        alpha = alpha / 50
        correct = 0
        for i in range(len(S_sy)):
            # scores = [a*b*c for (a,b,c) in zip(S_sy[i], S_se[i], S_sc[i])]
            scores = [alpha * a + (1 - alpha) * b for (a, b) in zip(S_sy[i], S_se[i])]
            index_of_max_value = max(enumerate(scores), key=lambda pair: pair[1])[0]
            if S_label[i][index_of_max_value] == 1:
                correct += 1
        # print(f"alpha: {alpha}; synthesis pred: {correct/len(S_sy)}")
        if correct > best_correct:
            best_alpha = alpha
            best_correct = correct
        if correct == best_correct:
            best_alpha_last = alpha
        x_values.append(alpha)
        y_values.append(correct / len(S_sy))
    # Convert x_values and y_values to a dictionary
    data = {"x_values": x_values, "y_values": y_values}
    # Write the dictionary to a JSON file
    with open("linear_output.json", "w") as f:
        json.dump(data, f, indent=4)


def calc_logistic(S_sy, S_se, S_sc, S_label):
    x_values = []
    y_values = []
    best_alpha = 0
    best_alpha_last = 0
    best_correct = 0
    for alpha in range(0, 51):
        alpha = alpha / 50
        correct = 0
        for i in range(len(S_sy)):
            # scores = [a*b*c for (a,b,c) in zip(S_sy[i], S_se[i], S_sc[i])]
            scores = [
                alpha * math.log(a) + (1 - alpha) * math.log(b)
                for (a, b) in zip(S_sy[i], S_se[i])
            ]
            index_of_max_value = max(enumerate(scores), key=lambda pair: pair[1])[0]
            if S_label[i][index_of_max_value] == 1:
                correct += 1
        # print(f"alpha: {alpha}; synthesis pred: {correct/len(S_sy)}")
        if correct > best_correct:
            best_alpha = alpha
            best_correct = correct
        if correct == best_correct:
            best_alpha_last = alpha
        x_values.append(alpha)
        y_values.append(correct / len(S_sy))
    # Convert x_values and y_values to a dictionary
    data = {"x_values": x_values, "y_values": y_values}
    # Write the dictionary to a JSON file
    with open("logistic_output.json", "w") as f:
        json.dump(data, f, indent=4)


def calc_power(S_sy, S_se, S_sc, S_label):
    x_values = []
    y_values = []
    best_alpha = 0
    best_alpha_last = 0
    best_correct = 0
    for alpha in range(0, 51):
        alpha = alpha / 50
        correct = 0
        for i in range(len(S_sy)):
            # scores = [a*b*c for (a,b,c) in zip(S_sy[i], S_se[i], S_sc[i])]
            scores = [
                alpha * (a**2) + (1 - alpha) * (b**2)
                for (a, b) in zip(S_sy[i], S_se[i])
            ]
            index_of_max_value = max(enumerate(scores), key=lambda pair: pair[1])[0]
            if S_label[i][index_of_max_value] == 1:
                correct += 1
        # print(f"alpha: {alpha}; synthesis pred: {correct/len(S_sy)}")
        if correct > best_correct:
            best_alpha = alpha
            best_correct = correct
        if correct == best_correct:
            best_alpha_last = alpha
        x_values.append(alpha)
        y_values.append(correct / len(S_sy))
    # Convert x_values and y_values to a dictionary
    data = {"x_values": x_values, "y_values": y_values}
    # Write the dictionary to a JSON file
    with open("power_output.json", "w") as f:
        json.dump(data, f, indent=4)


def main():
    parser = argparse.ArgumentParser(
        description="Process JSON files for a specific node."
    )
    parser.add_argument(
        "--root_dir_list",
        default="../../dataset/miniF2F/informal/",
        type=str,
        help="Comma-separated list of root directories",
    )
    parser.add_argument(
        "--suffix", default="", type=str, help="Comma-separated list of suffix"
    )

    args = parser.parse_args()
    root_dir_list = args.root_dir_list.split(",")
    suffix = args.suffix.split(",")
    json_file_paths = []
    for root_dir in root_dir_list:
        json_file_paths += get_json_files(root_dir, suffix)
    json_file_paths = sorted(json_file_paths)
    print(f"Totally have {len(json_file_paths)} to do")

    S_sy, S_se, S_sc, S_label = get_scores(json_file_paths)

    calc_linear(S_sy, S_se, S_sc, S_label)
    calc_logistic(S_sy, S_se, S_sc, S_label)
    calc_power(S_sy, S_se, S_sc, S_label)


if __name__ == "__main__":
    main()
