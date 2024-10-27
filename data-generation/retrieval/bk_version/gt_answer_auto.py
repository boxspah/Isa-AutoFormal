import argparse
import json  
import os
import time
import json
import utils.gpt_utils as gpt_utils
import utils.auto_utils as auto_utils
import AutoMath.autoformalize.retrieval.auto_retrieval as auto_retrieval
import math
from tqdm import tqdm

parser = argparse.ArgumentParser(description='Generate answer for problem')
parser.add_argument('--exp_name', default="", type=str, help='Exp name')
parser.add_argument('--data', default="test", choices=['train', 'test'], type=str, help='dataset')
parser.add_argument('--api_id', default=1, type=int, help='API key id')
parser.add_argument('--category', default='algebra', type=str, help='category of problems')
args = parser.parse_args()

import utils.utils as utils
utils.logging_init(os.path.join("../data/logs/Auto%s_%s_%s.log" %(args.exp_name, args.data, args.category)))

gpt_utils.set_api_key(args.api_id)

problem_auto_criteria = """Translate the natural language problem into the Isabelle version. 
                            """
proof_auto_criteria = """As a mathematician familiar with Isabelle, your task is to translate the natural language proof into an Isabelle language version. 
                        Your translation should be structured and clearly written, meeting the following criteria:      
                        \n- Each step of the natural language proof should be translated and be included as comments enclosed in \"(*\" and \"*)\".      
                        \n- Do NOT prove any step, each method after 'by' should be replaced by \"sledgehammer\".
                        """

save_folder_path1 = os.path.join('../data/gt-probs_'+args.data+args.exp_name, args.category)
if not os.path.exists(save_folder_path1):
    os.makedirs(save_folder_path1)

save_folder_path2 = os.path.join('../data/gt-proofs_'+args.data+args.exp_name, args.category)
if not os.path.exists(save_folder_path2):
    os.makedirs(save_folder_path2)

folder_path = './dataset_process/MATH/%s/' %(args.data) + args.category  
# Get a list of all files in the folder  
files = os.listdir(folder_path)  
  
# Filter the list to only include JSON files  
json_files = [file for file in files if file.endswith('.json')]  
  
# Load and store the contents of each JSON file  
for json_file in tqdm(json_files):
    n = json_file.replace('.json', '') 
    file_name = 'problem_%s' % (n)
    with open(os.path.join(folder_path, json_file), 'r') as file:  
        json_data = json.load(file)  
        natural_problem = json_data['problem']
        solution = auto_utils.normalize_answer(json_data['solution'])
        natural_solution = [t for t in solution.split('\n') if t != '']
    #### autoformalize the problem
    print('='*100)
    print('start to autoformalize the problem...%s' %(file_name))
    tmp_file_path = os.path.join(save_folder_path1, file_name+'.thy')
    if os.path.exists(tmp_file_path):
        print('skip')
        natural_answer = auto_utils.parse_answer(natural_solution)
        with open(tmp_file_path, 'r') as file:  
            symbolic_problem = file.read()
    else:
        t0 = time.time()
        natural_answer = auto_utils.parse_answer(natural_solution)
        prompt = f" Natural language version: \"{natural_problem} The final Answer is ${natural_answer}$\". Translate the natural language version to an Isabelle version:"
        prob_examples = auto_retrieval.prob_retrieval(prompt, k=8)
        symbolic_problem = gpt_utils.gpt4_response_problem(problem_auto_criteria + prompt, prob_examples)
        symbolic_problem = (symbolic_problem).replace('”','"').replace('“', '"') 
        print(prompt)
        print(symbolic_problem)
        t1 = time.time()
        print('success! In (%s)s' % (t1-t0))
        with open(tmp_file_path, 'w') as file:  
            file.write(symbolic_problem)

    #### autoformalize the solution
    print('='*100)
    print('start to autoformalize the solution...')
    tmp_file_path = os.path.join(save_folder_path2, file_name+'.thy')
    if os.path.exists(tmp_file_path):
        print('skip')
        continue
    print('number of lines: %s, number of chars: %s' %(len(natural_solution), len('\n'.join(natural_solution))))
    # if len(natural_solution) < 10:
    #     natural_version = "(* \n ### Problem\n" + '\n' + natural_problem + " The final Answer is " + natural_answer + '\n' + "\n ### Proof\n" + '\n'.join(natural_solution) + '\n *)\n'
    #     prompt = proof_auto_criteria + '\n' + "Natural language version: \n" + natural_version + '\n' + "Isabelle version: \n" + symbolic_problem + '\n proof- \n'
    #     # retrieval
    #     sol_examples = retrieval.sol_retrieval(natural_version, k=2)
    #     symbolic_solution = gpt_utils.gpt4_response_solution(prompt, sol_examples)
    # else:
    #     natural_version = "(* ### Problem\n " + natural_problem + " The final Answer is " + natural_answer + "\n ### Proof\n " + '\n '.join(natural_solution) + '\n *)\n'
    #     symbolic_solution = ''
    #     chunk = 5
    #     num_lines = len(natural_solution)
    #     K = math.ceil(num_lines / chunk)
    #     message = []
    #     for k in range(K):
    #         if k == 0:
    #             time.sleep(1)
    #             tmp_version = "(* \n ### Problem\n" + '\n' + natural_problem + " The final Answer is " + natural_answer + '\n' \
    #                                         + "\n ### Proof\n" + '\n'.join(natural_solution[k*chunk:(k+1)*chunk]) + '\nThis is an end END.' + '\n *)\n'
    #             prompt = proof_auto_criteria + '\n' + "Natural language version: \n" + tmp_version + '\n' + "Isabelle version: \n" + symbolic_problem + '\n proof-'
    #             # retrieval
    #             sol_examples = retrieval.sol_retrieval(tmp_version, k=2)
    #             answer = gpt_utils.gpt4_response_solution(prompt, sol_examples)
    #         if k > 0:
    #             prompt = "Continue the translation according to the criteria" + "\n (*"     \
    #                                         + "\n ### Proof\n" + '\n'.join(natural_solution[k*chunk:(k+1)*chunk]) + '\nThis is an end END.' + '\n *)' # + symbolic_solution
    #             answer = gpt_utils.gpt4_response_longsolution(prompt, sol_examples+message)
    #         tmp_natural_solution = '\n'.join(natural_solution[k*chunk:(k+1)*chunk]) 
    #         answer = auto_utils.normalize_proof(tmp_natural_solution, answer, remove_lastline=True) ### remove the last line 'This is an end END.'
    #         symbolic_solution = symbolic_solution + '\n' + answer
    #         message = [{"role": "user", "content": prompt}, {"role": "assistant", "content": answer}]
    # natural_solution = '\n'.join(natural_solution)
    # symbolic_solution = auto_utils.normalize_proof(natural_solution, symbolic_solution, remove_lastline=False)
    # formal = natural_version + '\n' + symbolic_problem + '\n proof- \n' + symbolic_solution
    formal = natural_version + '\n' + symbolic_problem + '\n proof- \n' + '  show ?thesis sledgehammer'
    print(prompt)
    print(formal)
    with open(tmp_file_path, 'w') as file:  
        file.write(formal)  