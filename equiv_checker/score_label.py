import copy
import os
import json
import tqdm
import torch
from torch import Tensor
import re
from transformers import BertTokenizer, BertModel, AutoTokenizer, AutoModel
from scipy.spatial.distance import cosine
import matplotlib.pyplot as plt
import argparse

# tokenizer = BertTokenizer.from_pretrained('AnReu/math_pretrained_bert')
# model = BertModel.from_pretrained('AnReu/math_pretrained_bert')
tokenizer = AutoTokenizer.from_pretrained('intfloat/e5-mistral-7b-instruct')
model = AutoModel.from_pretrained('intfloat/e5-mistral-7b-instruct')

def last_token_pool(last_hidden_states: Tensor,
                 attention_mask: Tensor) -> Tensor:
    left_padding = (attention_mask[:, -1].sum() == attention_mask.shape[0])
    if left_padding:
        return last_hidden_states[:, -1]
    else:
        sequence_lengths = attention_mask.sum(dim=1) - 1
        batch_size = last_hidden_states.shape[0]
        return last_hidden_states[torch.arange(batch_size, device=last_hidden_states.device), sequence_lengths]


def get_json_files(root_dir):
    json_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                json_files.append(file_path)
    return json_files

def main(json_file_paths, suffix=""):  
    for (id, json_file) in tqdm.tqdm(enumerate(json_file_paths)):
    # for json_file in json_file_paths:
        # print(json_file)
        with open(json_file, 'r') as f:
            data = json.load(f)

        pred = f"prediction_{suffix}"
        if pred not in data or len(data[pred]) == 0: print(f"skip {json_file}"); continue
        components = [data[pred][key] for key in data[pred].keys()]
        if "informal_statement" in data:
            natural_problem = data['informal_statement']
            match = re.match(r'(.*) Show that it is (\d+)\.', natural_problem)
            if match:
                informal_statement = match.group(1)
                number = match.group(2)
                natural_problem = f"{informal_statement} The final Answer is ${number}$"
        else:
            natural_problem = data['natural problem']+" The final Answer is $"+data['natural answer']+ "$"
        #### autoformalize the problem
        
        origin_problem = natural_problem
        for i in range(10):
            name = f'a_{i}_{suffix}'
            # print(f"working on {id}: {json_file} {name}")
            if name not in data: 
                data[name] = copy.deepcopy(data[f'a_{i}_deepseek'])
            # else:
            #     continue
            informal_problem = data[name]['informal problem']
            for c in components:
                if i in c:
                    symbolic_score = len(c) / 10.0
                    break
            texts = [origin_problem, informal_problem]
            inputs = tokenizer(texts, padding=True, truncation=True, return_tensors='pt')
            
            # Tokenize the input texts
            max_length = 8192
            inputs = tokenizer(texts, max_length=max_length, padding=True, truncation=True, return_tensors='pt')

            with torch.no_grad():
                # embeddings = model(**inputs, output_hidden_states=True, return_dict=True).pooler_output
                outputs = model(**inputs)
                embeddings = last_token_pool(outputs.last_hidden_state, inputs['attention_mask'])

            semantic_score = 1 - cosine(embeddings[0], embeddings[1])
            data[name]["semantic_score"] = semantic_score
            data[name]["symbolic_score"] = symbolic_score
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=4)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Process JSON files for a specific node.")
    parser.add_argument("--root_dir_list", default="../dataset/miniF2F/informal/", type=str, help="Comma-separated list of root directories")
    args = parser.parse_args()
    root_dir_list = args.root_dir_list.split(",")
    json_file_paths = []
    for path in root_dir_list:
        json_file_paths += get_json_files(path)
    print(f"Totally have {len(json_file_paths)} to do in {root_dir_list}")
    main(json_file_paths, suffix="")
