import os
import json
import tqdm
import torch
import re
# from scipy.spatial.distance import cosine
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline
import numpy as np
import argparse
import time


def get_json_files(root_dir):
    json_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                json_files.append(file_path)
    return json_files

def main(cata, json_file_paths, suffix=""):  
    T = 1
    pass1, pass10, correct1, total = 0, 0, 0, 0
    pass2, pass3 = 0, 0
    symbolic_correct1, semantic_correct1, cluster_correct = 0, 0, 0
    correct2, symbolic_correct2, semantic_correct2 = 0, 0, 0
    correct3, symbolic_correct3, semantic_correct3 = 0, 0, 0
    S_sy, S_se, S_sc, S_label = [], [], [], []
    pred = f"prediction_{suffix}"
    if suffix == "":
        pred = "prediction"
    for json_file in json_file_paths:
        with open(json_file, 'r') as f:
            data = json.load(f)
        if pred not in data or len(data[pred]) == 0: 
            continue
        symbolic_scores, semantic_scores, cluster_scores, syntax_scores, gts = [], [], [], [], []
        if pred not in data or len(data[pred]) == 0: 
            continue
        components = [data[pred][key] for key in data[pred].keys()]
        
        father_dict = {}

        # 遍历原始字典中的每个键值对
        for key, values in data[pred].items():
            for value in values:
                father_dict[value] = key
        
        equiv= f'equivalence_oracle_{suffix}'
        if suffix == "":
            equiv = 'equivalence_oracle'
        for i in range(10):
            name = f"a_{i}_{suffix}"
            if suffix == "":
                name = f"a_{i}"
            semantic_score = data[name].get("semantic_score",0.1)
            symbolic_score = data[name].get("symbolic_score",0.1)
            semantic_scores.append(semantic_score)
            symbolic_scores.append(symbolic_score)
            syntax_scores.append(data[name].get("syntax",1))
            if i in data.get(equiv, []) or data[name].get('label', 0) == 1:
                gts.append(1)
                # print(1)
            else:
                gts.append(0)
        gts = [g*s for (g,s) in zip(gts, syntax_scores)]
        # print(semantic_scores)
        semantic_scores=  torch.softmax(torch.tensor(semantic_scores) , dim=0).tolist()
        symbolic_scores=  torch.softmax(torch.tensor(symbolic_scores) , dim=0).tolist()
        S_sy.append(symbolic_scores)
        S_se.append(semantic_scores)
        S_sc.append(syntax_scores)
        S_label.append(gts)
        default_aplha = 0.8
        scores = [((default_aplha*a)+(1-default_aplha)*b)*c for (a,b,c) in zip(symbolic_scores, semantic_scores, syntax_scores)]
        for index, cluster in enumerate(components):
            cluster_score=0
            for c in cluster:
                cluster_score += semantic_scores[c]
            cluster_scores.append(cluster_score)
        index_of_max_value = max(enumerate(cluster_scores), key=lambda pair: pair[1])[0]
        index_of_max_value = components[index_of_max_value][0]
        if gts[index_of_max_value] == 1:
            cluster_correct += 1
            
        index_of_max_value = max(enumerate(scores), key=lambda pair: pair[1])[0]
        sorted_synthesis_indices = sorted(range(len(symbolic_scores)), key=lambda i: symbolic_scores[i], reverse=True)
        father_list=[]
        select_index = []
        select_index.append(index_of_max_value)
        father_list.append(father_dict[index_of_max_value])
        for i in range(10):
            if father_dict[sorted_synthesis_indices[i]] in father_list:
                continue
            else:
                select_index.append(sorted_synthesis_indices[i])
                father_list.append(father_dict[sorted_synthesis_indices[i]])
            
        if gts[index_of_max_value] == 1:
            correct1 += 1
            correct2 += 1
            correct3 += 1
        elif len(select_index) > 1 and gts[select_index[1]] == 1:
            correct2 += 1
            correct3 += 1
        elif len(select_index) > 2 and gts[select_index[2]] == 1:
            correct3 += 1

        max_value = max(symbolic_scores)
        index_of_max_value = symbolic_scores.index(max_value)
        sorted_symbolic_indices = sorted(range(len(symbolic_scores)), key=lambda i: symbolic_scores[i], reverse=True)
        father_list=[]
        select_index = []
        select_index.append(index_of_max_value)
        father_list.append(father_dict[index_of_max_value])
        for i in range(10):
            if father_dict[sorted_synthesis_indices[i]] in father_list:
                continue
            else:
                select_index.append(sorted_synthesis_indices[i])
                father_list.append(father_dict[sorted_synthesis_indices[i]])
        if gts[index_of_max_value] == 1:
            symbolic_correct1 += 1
            symbolic_correct2 += 1
            symbolic_correct3 += 1
        elif len(select_index) > 1 and gts[select_index[1]] == 1:
            symbolic_correct2 += 1
            symbolic_correct3 += 1
        elif len(select_index) > 2 and gts[select_index[2]] == 1:
            symbolic_correct3 += 1


        index_of_max_value = max(enumerate(semantic_scores), key=lambda pair: pair[1])[0]
        sorted_semantic_indices = sorted(range(len(semantic_scores)), key=lambda i: semantic_scores[i], reverse=True)
        if gts[index_of_max_value] == 1:
            semantic_correct1 += 1
        for i in range(2):
            if gts[sorted_semantic_indices[i]] == 1:
                semantic_correct2 += 1
                break
        for i in range(3):
            if gts[sorted_semantic_indices[i]] == 1:
                semantic_correct3 += 1
                break
        if gts[0]*syntax_scores[0] == 1:
            pass1 += 1
        if sum([a*b for (a,b) in zip(gts[:2], syntax_scores[:2])]) >= 1:
            pass2 += 1
        if sum([a*b for (a,b) in zip(gts[:3], syntax_scores[:3])]) >= 1:
            pass3 += 1
        if sum([a*b for (a,b) in zip(gts, syntax_scores)]) >= 1:
            pass10 += 1
        total += 1
        # print(components, gts, index_of_max_value)
    print(f"{cata}: total_promble:{total};")
    print(f"pass@1: {pass1/total}; pass@10: {pass10/total};")
    print(f"pass@2: {pass2/total}; pass@3: {pass3/total};")
    print(f"synthesis@1 pred: {correct1/total}")
    print(f"symbolic@1  pred: {symbolic_correct1/total}")
    print(f"semantic@1  pred: {semantic_correct1/total}")
    print(f"synthesis@2 pred: {correct2/total}")
    print(f"symbolic@2  pred: {symbolic_correct2/total}")
    print(f"semantic@2  pred: {semantic_correct2/total}")
    print(f"synthesis@3 pred: {correct3/total}")
    print(f"symbolic@3  pred: {symbolic_correct3/total}")
    print(f"semantic@3  pred: {semantic_correct3/total}")
    # if "All type" in cata:
    # calc_alpha(S_sy, S_se, S_sc, S_label, cata)

def calc_alpha(S_sy, S_se, S_sc, S_label, cata):
    # print("calculating alpha……")
    print(f"total problem in {cata}: {len(S_sy)}")
    print(f"calculating alpha in {cata}……")

    x_values = []
    y_values = []
    best_alpha = 0
    best_alpha_last = 0
    best_correct = 0
    for alpha in range(0, 51):
        alpha = alpha / 50
        correct = 0
        for i in range(len(S_sy)):
            scores = [alpha * a + (1-alpha) * b for (a,b) in zip(S_sy[i], S_se[i])]
            index_of_max_value = max(enumerate(scores), key=lambda pair: pair[1])[0]
            if S_label[i][index_of_max_value] == 1:
                correct += 1
        if correct > best_correct:
            best_alpha = alpha
            best_correct = correct
        if correct == best_correct:
            best_alpha_last = alpha
        x_values.append(alpha)
        y_values.append(correct/len(S_sy))
    plt.figure(figsize=(8, 4))
    plt.xlabel(r'Various values of $\alpha$',fontsize=20)  
    plt.ylabel('Accuracy of the combine prediction',fontsize=15)  
    model=make_interp_spline(x_values, y_values)
    
    #smooth the curve
    xs=np.linspace(0,1,200)
    ys=model(xs)
    # Compute the first derivative of y
    dydx = np.gradient(y_values, x_values)
    turning_points = np.where(np.diff(np.sign(dydx)))[0]
    # Auto set turning points
    turning_points_x = [x_values[i] for i in turning_points]
    turning_points_y = [y_values[i] for i in turning_points]
   
    ymin = min(y_values)
    
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.plot(xs, ys, linewidth=3.7)
    for i in range(len(turning_points_x)):
        plt.plot([turning_points_x[i], turning_points_x[i]], [0.35, turning_points_y[i]], color='gray', linestyle='--', linewidth=1.6)
    plt.scatter(turning_points_x,turning_points_y, color='red', label='Turning points',zorder=10)
    plt.savefig(f'./tmp/{cata}_alpha.pdf',format='pdf', bbox_inches='tight')
    plt.show()
    print(f"calculating alpha done: best alpha {(best_alpha+best_alpha_last)/2 }; combine pred: {best_correct/len(S_sy)}")
    plt.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Process JSON files for a specific node.")
    parser.add_argument("--dataset", default="miniF2F", type=str, help="MATH or miniF2F")
    parser.add_argument("--root_dir_list", default="../dataset/miniF2F/informal/", type=str, help="Comma-separated list of root directories")

    args = parser.parse_args()
    root_dir_list = args.root_dir_list.split(",")
    dataset = args.dataset
    if dataset == "miniF2F":
        # predict for miniF2F
        json_file_paths_miniF2F = []
        for path in root_dir_list:
            json_file_paths_miniF2F += get_json_files(path)
        print(f"Totally have {len(json_file_paths_miniF2F)} to do in miniF2F")
        print("Reduce by category")
        for cata in ['imo', 'amc', 'aime', 'induction', 'algebra', 'numbertheory']:
            problem_list = [path for path in json_file_paths_miniF2F if cata in path]
            main(f"miniF2F_{cata}", problem_list)
        print("All data result:")
        main("All type in miniF2F", json_file_paths_miniF2F)

    if dataset == "MATH":
        # predict for MATH
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
        
        print("Reduce by level")
        for level in sorted(math_level_dict.keys()):
            main(f"MATH_{level}", math_level_dict[level])
        
        print("Reduce by category")
        for cata in math_category_dict.keys():
            main(f"MATH_{cata}", math_category_dict[cata])

        print("All data result:")
        main("All type in MATH", json_file_paths)
