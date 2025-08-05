import argparse
import json
import os

import numpy as np


def check_labeled(file_path):
    k = 10
    with open(file_path) as f:
        data = json.load(f)
    labels = []
    # if 'largest_components' in data:
    #     return False
    for i in range(k):
        name = f"a_{i}"
        if "label" in data[name] and "syntax" in data[name]:
            labels.append(int(data[name]["label"]) * int(data[name]["syntax"]))
    if len(labels) >= 10:
        return True
    else:
        return False


def get_json_files(root_dir):
    json_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                # if check_labeled(file_path):
                json_files.append(file_path)
    return json_files


def main(cata, json_file_paths, suffix=""):
    pass1, pass10, correct = 0, 0, 0
    largest_components_list = []
    cluster_size_list = []
    human_check_list = []
    auto_check_list = []
    total = len(json_file_paths)
    for json_file in json_file_paths:
        # print(json_file)
        with open(json_file) as f:
            data = json.load(f)
        pred = f"prediction_{suffix}"
        if suffix == "":
            pred = "prediction"
        if pred not in data or len(data[pred]) == 0:
            print(f"skip {json_file}")
            continue
        components = [data[pred][key] for key in data[pred].keys()]
        largest_components_list.append(len(components[0]))
        cluster_size_list.append(len(components))
        human_check = 10
        auto_check = len(components)
        for i in range(10):
            name = f"a_{i}"
            if (
                i in data.get("equivalence_oracle", [])
                or data[name].get("label", 0) == 1
            ):
                human_check = i + 1
                break
        human_check_list.append(human_check)
        for i in range(len(components)):
            for j in components[i]:
                if (
                    j in data.get("equivalence_oracle", [])
                    or data[f"a_{j}"].get("label", 0) == 1
                ):
                    auto_check = i + 1
                    break
            if auto_check != len(components):
                break
        auto_check_list.append(auto_check)

    largest_components_avg = np.mean(largest_components_list)
    largest_components_var = np.var(largest_components_list)
    cluster_size_avg = np.mean(cluster_size_list)
    cluster_size_var = np.var(cluster_size_list)
    save_human_check = sum(a - b for a, b in zip(human_check_list, auto_check_list))
    print(f"{cata}: total_promble:{total};")
    print(
        f"largest_components_avg: {largest_components_avg}; largest_components_var: {largest_components_var};"
    )
    print(
        f"cluster_size_avg: {cluster_size_avg}; cluster_size_var: {cluster_size_var};"
    )
    print(f"pure_human_check: {np.sum(human_check_list)};")
    print(f"auto_human_check: {np.sum(auto_check_list)};")
    print(f"save_human_check: {save_human_check};\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process JSON files for a specific node."
    )
    parser.add_argument(
        "--dataset", default="miniF2F", type=str, help="MATH or miniF2F"
    )
    parser.add_argument(
        "--root_dir_list",
        default="../dataset/miniF2F/informal/",
        type=str,
        help="Comma-separated list of root directories",
    )

    args = parser.parse_args()
    root_dir_list = args.root_dir_list.split(",")
    dataset = args.dataset

    if dataset == "miniF2F":
        json_file_paths = []
        for path in root_dir_list:
            json_file_paths += get_json_files(path)
        print(f"Totally have {len(json_file_paths)} to do in miniF2F")
        print("All data result:")
        main("All type", json_file_paths)

        print("Reduce by category")
        for cata in ["imo", "amc", "aime", "induction", "algebra", "numbertheory"]:
            problem_list = [path for path in json_file_paths if cata in path]
            main(cata, problem_list)

    if dataset == "MATH":
        json_file_paths = []
        for path in root_dir_list:
            json_file_paths += get_json_files(path)
        print(f"Totally have {len(json_file_paths)} to do in MATH")
        math_level_dict = {}
        math_category_dict = {}
        for json_file in json_file_paths:
            with open(json_file) as f:
                data = json.load(f)
            probelm_category = json_file.split("/")[-2]
            probelm_name = json_file.split("/")[-1]
            problem_level = data.get("level", 0)
            if problem_level not in math_level_dict:
                math_level_dict[problem_level] = []
            math_level_dict[problem_level].append(json_file)

            if probelm_category not in math_category_dict:
                math_category_dict[probelm_category] = []
            math_category_dict[probelm_category].append(json_file)

        print("All data result:")
        main("All type", json_file_paths)

        print("Reduce by level")
        for level in sorted(math_level_dict.keys()):
            main(f"{level}", math_level_dict[level])

        print("Reduce by category")
        for cata in math_category_dict.keys():
            main(cata, math_category_dict[cata])

    # json_file_paths+=get_json_files(root_dir)
    # print("All type in one")
    # main("All type in one", json_file_paths)
