import os
import json
from tqdm import tqdm
import re
import numpy as np
import networkx as nx
import itertools  
import time
import argparse

def check_labeled(file_path):
    k = 10
    with open(file_path, 'r') as f:  
        data = json.load(f)  
    labels = []
    # if 'largest_components' in data:
    #     return False
    for i in range(k):
        name = f"a_{i}"
        if 'label' in data[name] and 'syntax' in data[name]:
            labels.append(int(data[name]['label'])*int(data[name]['syntax']))   
    if len(labels) >= 10:
        return True
    else:
        return False

def get_json_files(root_dir):
    json_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                # if check_labeled(file_path):
                json_files.append(file_path)
    return json_files

def naive_majority_voting(formal_statements):
    # with open(json_file, 'r') as f:
    #     data = json.load(f)
    G = nx.Graph()
    for i in range(len(formal_statements)):
        G.add_node(i)
    for i in range(len(formal_statements)):
        formal_statements[i] = re.sub(r'\s', '', formal_statements[i])
    pairs = list(itertools.combinations(range(len(formal_statements)), 2))  
    for i, j in pairs:
        if nx.has_path(G, i, j):
            G.add_edge(i, j)
        else:
            if formal_statements[i] == formal_statements[j]:
                G.add_edge(i, j)
    connected_components = sorted(nx.connected_components(G), key=len, reverse=True)
    connected_subgraphs = [list(c) for c in connected_components]
    symbolic_scores = [0]*10
    # print(connected_subgraphs)
    # time.sleep(10000)
    for index in range(len(connected_subgraphs)):
        for c in connected_subgraphs[index]:
            symbolic_scores[c] = len(connected_subgraphs[index])/10
    max_value = max(symbolic_scores)
    index_of_max_value = symbolic_scores.index(max_value)
    # print(symbolic_scores)
    select_index = []
    select_index.append(index_of_max_value)
    if len(connected_subgraphs)>1:
        select_index.append(connected_subgraphs[1][0])
    if len(connected_subgraphs)>2:
        select_index.append(connected_subgraphs[2][0])
    return select_index

def main(cata, json_file_paths, suffix=""):  
    pass1, pass10, total = 0, 0, 0
    naive1, naive2, naive3 = 0, 0, 0
    naive_pred1, naive_pred2, naive_pred3 = 0, 0, 0
    pred = f"prediction_{suffix}"
    if suffix == "":
        pred = "prediction"
    for json_file in json_file_paths:
        # print(json_file)
        with open(json_file, 'r') as f:
            data = json.load(f)
        first_name = f"a_0_{suffix}"
        if suffix == "":
            first_name = "a_0"
        if 'naive_label' not in data[first_name]:
            print(f"skip {json_file}")
            continue
        syntax_scores, gts = [], []
        for i in range(10):
            name = f"a_{i}_{suffix}"
            if suffix == "":
                name = f"a_{i}"
            syntax_scores.append(data[name].get('syntax', 1))
            equiv = f'equivalence_oracle_{suffix}'
            if suffix == "":
                equiv = 'equivalence_oracle'
            if i in data.get(equiv, []) or data[name].get('label', 0) == 1:
                gts.append(1)
            else:
                gts.append(0)

        gts = [g*s for (g,s) in zip(gts, syntax_scores)]
        
        naive_num = 0
        for i in range(10):
            name = f"a_{i}_{suffix}"
            if suffix == "":
                name = f"a_{i}"
            equiv = f'equivalence_oracle_{suffix}'
            if suffix == "":
                equiv = 'equivalence_oracle'
            if data[name].get('naive_label', 0) == 1:
                naive_num += 1
                if i in data.get(equiv, []) or data[name].get('label', 0) == 1:
                    if syntax_scores[i] == 1:
                        if naive_num == 1:
                            naive1 += 1
                            naive2 += 1
                            naive3 += 1
                            break
                        elif naive_num == 2:
                            naive2 += 1
                            naive3 += 1
                            break
                        else:
                            naive3 += 1
                            break
                    # print(json_file)
            if naive_num > 3:
                break
        
        if gts[0]*syntax_scores[0] == 1:
            pass1 += 1
        if sum([a*b for (a,b) in zip(gts, syntax_scores)]) >= 1:
            pass10 += 1
        pred = f
        if "prediction" not in data or len(data["prediction"]) == 0: print(f"skip {json_file}"); continue
        components = [data["prediction"][key] for key in data["prediction"].keys()]
        formal_statements = []
        for i in range(10):
            name = f"a_{i}_{suffix}"
            if suffix == "":
                name = f"a_{i}"
            formal_statements.append(data[name].get('formal problem', ''))
        select_index = naive_majority_voting(formal_statements)
        
        if gts[select_index[0]]*syntax_scores[select_index[0]] == 1:
            naive_pred1 += 1
            naive_pred2 += 1
            naive_pred3 += 1
        elif len(select_index)>1 and gts[select_index[1]]*syntax_scores[select_index[1]] == 1:
            naive_pred2 += 1
            naive_pred3 += 1
        elif len(select_index)>2 and gts[select_index[2]]*syntax_scores[select_index[2]] == 1:
            naive_pred3 += 1
        total += 1
    print(f"{cata}: total_promble:{total};")
    print(f"pass@1: {pass1/total}; pass@10: {pass10/total};")
    # print(f"synthesis pred: {correct/total}")
    print(f"atp only pred@1: {naive1/total};")
    print(f"atp only pred@2: {naive2/total};")
    print(f"atp only pred@3: {naive3/total};")
    print(f"naive majority pred@1: {naive_pred1/total};")
    print(f"naive majority pred@2: {naive_pred2/total};")
    print(f"naive majority pred@3: {naive_pred3/total};")
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Process JSON files for a specific node.")
    parser.add_argument("--dataset", default="miniF2F", type=str, help="MATH or miniF2F")
    parser.add_argument("--root_dir_list", default="../dataset/miniF2F/informal/", type=str, help="Comma-separated list of root directories")

    args = parser.parse_args()
    root_dir_list = args.root_dir_list.split(",")
    dataset = args.dataset

    if dataset == "miniF2F":
        json_file_paths = []
        for path in root_dir_list:
            json_file_paths += get_json_files(path)
        # json_file_paths = json_file_paths[8:]
        print(f"Totally have {len(json_file_paths)} to do in miniF2F")
        print("All data result:")
        main("All type", json_file_paths)
        exit()
        for cata in ['imo', 'amc', 'aime', 'induction', 'algebra', 'numbertheory']:
            problem_list = [path for path in json_file_paths if cata in path]
            main(cata, problem_list)

    if dataset == "MATH":
        json_file_paths=[]
        for path in root_dir_list:
            json_file_paths += get_json_files(path)
        print(f"Totally have {len(json_file_paths)} to do in MATH")
        math_level_dict = {}
        math_category_dict = {}
        for json_file in json_file_paths:
            with open(json_file, 'r') as f:
                data = json.load(f)
            probelm_category = json_file.split('/')[-2]
            probelm_name = json_file.split('/')[-1]
            problem_level = data.get('level', 0)
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
