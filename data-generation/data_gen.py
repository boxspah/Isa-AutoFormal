import argparse
import json  
import os
import time
import json
import math
from tqdm import tqdm
import re
import logging  
import logging.handlers
import multiprocessing
import time
from PathManager import *
from datetime import datetime

parser = argparse.ArgumentParser(description='Generate answer for problem')
parser.add_argument('--exp_name', default="", type=str, help='Exp name')
parser.add_argument('--version_name', default="a", type=str, help='Version name')
parser.add_argument('--data', default="test", choices=['train', 'test'], type=str, help='dataset')
parser.add_argument('--api_id', default=1, type=int, help='API key id')
parser.add_argument('--category', default='algebra', type=str, help='category of problems')
parser.add_argument('--iter', default=10, type=int, help='ieration number of data generation')
args = parser.parse_args()

import utils.utils as utils
utils.logging_init(os.path.join("./data/logs/Auto_%s-%s_%s_%s.log" %(args.exp_name, args.version_name, args.data, args.category)))
import utils.gpt_utils as gpt_utils
import utils.auto_utils as auto_utils
import retrieval.auto_retrieval as auto_retrieval
import retrieval.inauto_retrieval as inauto_retrieval

DEBUG = False
def setup_logger(idx, queue):
    global logger
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info_log_path = f"./logs/{current_datetime}_info_{idx}.log"
    logger = logging.getLogger(f'logger_{idx}')
    logger.setLevel(logging.DEBUG)  # 设置最低的日志级别
    logger.propagate = False
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # set up info handler
    info_handler = logging.FileHandler(info_log_path)  
    info_handler.setLevel(logging.INFO)  
    info_handler.setFormatter(formatter)  
    # set up error handler
    error_handler = logging.handlers.QueueHandler(queue)  
    error_handler.setLevel(logging.ERROR)  
    error_handler.setFormatter(formatter)
    # set up stream handler
    stream_handler = logging.StreamHandler()  
    stream_handler.setFormatter(formatter)  
    stream_handler.setLevel(logging.INFO)

    # add handlers
    logger.addHandler(info_handler)
    logger.addHandler(error_handler)
    logger.addHandler(stream_handler)

    if DEBUG:
        debug_log_path = f"./logs/{current_datetime}_debug_{idx}.log"
        # set up debug handler
        debug_handler = logging.FileHandler(debug_log_path)
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(formatter)
        logger.addHandler(debug_handler)

def get_json_files(root_dir):
    json_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                # if check_labeled(file_path):
                json_files.append(file_path)
    return json_files

problem_auto_criteria = """Translate the natural language problem into the Isabelle version.
                            """
problem_inauto_criteria = """Translate the math problem formulated with Isabelle back to a natural language problem.
                            """
proof_auto_criteria = """As a mathematician familiar with Isabelle, your task is to translate the natural language proof into an Isabelle language version. 
                        Your translation should be structured and clearly written, meeting the following criteria:      
                        \n- Each step of the natural language proof should be translated and be included as comments enclosed in \"(*\" and \"*)\".      
                        \n- Do NOT prove any step, each method after 'by' should be replaced by \"sledgehammer\".
                        """
                        
# save_folder_path = os.path.join('./data/task_'+args.data+'_'+args.exp_name, args.category)
# if not os.path.exists(save_folder_path):
#     os.makedirs(save_folder_path)

# folder_path = './dataset_process/MATH/%s/' %(args.data) + args.category  
# # Get a list of all files in the folder  
# files = os.listdir(folder_path)  

# for k in range(args.iter):
#     tmp_name = args.version_name + '_' + str(k)
#     # Filter the list to only include JSON files  
#     json_files = [file for file in files if file.endswith('.json')]  
    
#     for json_file in tqdm(json_files):
#         #### load and store the contents of each JSON file  
#         n = json_file.replace('.json', '') 
#         file_name = 'problem_%s' % (n)
#         save_file_path = os.path.join(save_folder_path, file_name+'.json')
#         if not os.path.exists(save_file_path):
#             with open(os.path.join(folder_path, json_file), 'r') as file:  
#                 json_data = json.load(file)  
#                 natural_problem = json_data['problem']
#                 solution = auto_utils.normalize_answer(json_data['solution'])
#                 natural_solution = [t for t in solution.split('\n') if t != '']
#             natural_answer = auto_utils.parse_answer(natural_solution)
#             thy_series = {'natural problem': natural_problem, 
#                         'natural solution': natural_solution, 
#                         'natural answer': natural_answer}
#             with open(save_file_path, 'w') as file:  
#                 json.dump(thy_series, file, indent=4)
#         else:
#             with open(save_file_path) as file:
#                 thy_series = json.load(file)
#                 natural_problem = thy_series['natural problem']
#                 natural_solution = thy_series['natural solution']
#                 natural_answer = thy_series['natural answer']
#         thy = thy_series.get(tmp_name, {})      
#         #### autoformalize the problem
#         print('='*100)
#         print('start to autoformalize the problem...%s' %(file_name))
#         if 'formal problem' in thy:
#             print('skip')
#             formal_problem = thy['formal problem']
#         else:
#             t0 = time.time()
#             prompt = f" Natural language version: \"{natural_problem} The final Answer is ${natural_answer}$\". Translate the natural language version to an Isabelle version:"
#             prob_examples = auto_retrieval.prob_retrieval(prompt, k=8)
#             formal_problem = gpt_utils.gpt4_response(problem_auto_criteria + prompt, prob_examples)
#             formal_problem = auto_utils.normalize_statement(formal_problem)
#             print(prompt)
#             print(formal_problem)
#             t1 = time.time()
#             print('success! In (%s)s' % (t1-t0))
#             thy['formal problem'] = formal_problem
#             with open(save_file_path, 'w') as file:  
#                 thy_series.update({tmp_name: thy})
#                 json.dump(thy_series, file, indent=4)

#         #### autoformalize the solution
#         # print('='*100)
#         # print('start to autoformalize the solution...')
#         if 'formal solution' in thy:
#             print('skip')
#         else:
#             # print('number of lines: %s, number of chars: %s' %(len(natural_solution), len('\n'.join(natural_solution))))
#             natural_version = "(* ### Problem\n " + natural_problem + " The final Answer is " + natural_answer + "\n ### Proof\n " + '\n '.join(natural_solution) + '\n *)\n'
#             formal_solution = natural_version + '\n' + formal_problem + '\n proof- \n' + '  show ?thesis sledgehammer'
#             # print(formal_solution)
#             thy['formal solution'] = formal_solution
#             with open(save_file_path, 'w') as file:  
#                 thy_series.update({tmp_name: thy})
#                 json.dump(thy_series, file, indent=4)
        
#         #### informalize the problem
#         print('='*100)
#         print('start to informalize the problem...')
#         if 'informal problem' in thy: 
#             print('skip')
#             informal_problem = thy['informal problem']
#         else:
#             t0 = time.time()
#             prompt = f"Isabelle version: \"{formal_problem}\". Translate the Isabelle version to a natural language version:"
#             prob_examples = inauto_retrieval.prob_retrieval(prompt, k=8)
#             informal_problem = gpt_utils.gpt4_response(problem_inauto_criteria + prompt, prob_examples)
#             print(prompt)
#             print(informal_problem)
#             t1 = time.time()
#             print('success! In (%s)s' % (t1-t0))   
#             thy['informal problem'] = informal_problem 
#             with open(save_file_path, 'w') as file:  
#                 thy_series.update({tmp_name: thy})
#                 json.dump(thy_series, file, indent=4)
            
def process_file(file_path, dataset):
    k = 10
    with open(file_path, 'r') as f:  
        thy_data = json.load(f)
    for i in range(k):
        t0 = time.time()
        name = f"a_{i}_gpt3.5"
        if name in thy_data.keys():
            logger.info(f"skip {name}")
            continue
        logger.info('='*100)
        logger.info(f'start to autoformalize the problem...{name}')
        thy_data[name] = {}

        natural_problem, natural_solution = process_natural(thy_data, dataset)
        prompt = f"Natural language version: \"{natural_problem}\". Translate the natural language version to an Isabelle version:"
        prob_examples = auto_retrieval.prob_retrieval(prompt, k=8)
        formal_problem = gpt_utils.gpt4_response(problem_auto_criteria + prompt, prob_examples)
        formal_problem = auto_utils.normalize_statement(formal_problem)
        pattern = r' +'
        # 将所有连续的空白字符替换为单个空格
        formal_problem = re.sub(pattern, ' ', formal_problem)
        match = re.search(r'theorem[\s\S]*?shows "[\s\S]*?"', formal_problem)
        if match:
            extracted_part = match.group(0)
            # 将第一行修改为 'theorem'
            lines = extracted_part.split("\n")
            lines[0] = "theorem"

            # 删除最后一行的 'proof'
            if lines[-1].strip() == "proof":
                lines.pop()
            lines = [s.strip() for s in lines]
            formal_problem = "\n".join(lines)
        logger.info(prompt)
        logger.info(formal_problem)
        thy_data[name]['formal problem'] = formal_problem
        t1 = time.time()
        logger.info('success! In (%s)s' % (t1-t0))
        # time.sleep(1)

        #### autoformalize the solution
        natural_version = "(* ### Problem\n " + natural_problem + "\n ### Proof\n " + natural_solution + '\n *)\n'
        formal_solution = natural_version + '\n' + formal_problem + '\n proof- \n' + '  show ?thesis sledgehammer'
        # print(formal_solution)
        thy_data[name]['formal solution'] = formal_solution

        #### informalize the problem
        t0 = time.time()
        prompt = f"Isabelle version: \"{formal_problem}\". Translate the Isabelle version to a natural language version:"
        prob_examples = inauto_retrieval.prob_retrieval(prompt, k=8)
        informal_problem = gpt_utils.gpt4_response(problem_inauto_criteria + prompt, prob_examples)
        logger.info(prompt)
        logger.info(informal_problem)
        t1 = time.time()
        logger.info('success! In (%s)s' % (t1-t0))   
        thy_data[name]['informal problem'] = informal_problem
        with open(file_path, 'w') as f:
            json.dump(thy_data, f, indent=4)
        # with open(save_file_path, 'w') as file:  
        #     thy_series.update({tmp_name: thy})
        #     json.dump(thy_series, file, indent=4)
    
    # already processed
    # if dataset == "miniF2F":
    #     process_oracle(file_path, thy_data)
    with open(file_path, 'w') as f:
        json.dump(thy_data, f, indent=4)

def process_natural(thy_data, dataset):
    if dataset == "miniF2F":
        natural_problem = thy_data['informal_statement']
        natural_solution = thy_data['informal_proof']
        #### autoformalize the problem
        match = re.match(r'(.*) Show that it is (\d+)\.', natural_problem)
        if match:
            informal_statement = match.group(1)
            number = match.group(2)
            natural_problem = f"{informal_statement} The final Answer is ${number}$"
    if dataset == "MATH":
        natural_problem = thy_data['natural problem']
        if isinstance(natural_problem, list):
            natural_problem = '\n'.join(natural_problem)
        natural_solution = thy_data['natural solution']
        if isinstance(natural_solution, list):
            natural_solution = '\n'.join(natural_solution)
        natural_answer = thy_data['natural answer']
        natural_problem = f"{natural_problem} The final Answer is ${natural_answer}$"
    
    return natural_problem, natural_solution

def process_oracle(file_path, thy_data):
    oracle_path = file_path.replace('/informal/', '/isabelle/').replace('.json', '.thy')
    with open(oracle_path, 'r') as f:
        oracle_data = f.read()
    match = re.search(r'theorem[\s\S]*?shows "[\s\S]*?"', oracle_data)
    if match:
        extracted_part = match.group(0)
        # 将第一行修改为 'theorem'
        lines = extracted_part.split('\n')
        lines[0] = 'theorem'
        
        # 删除最后一行的 'proof'
        if lines[-1].strip() == 'proof':
            lines.pop()
        lines = [s.strip() for s in lines]
        oracle_data = '\n'.join(lines)
    thy_data['oracle'] = oracle_data

def process_batch(path_manager, queue, dataset, idx):
    idx=idx+1
    gpt_utils.set_api_key(idx)
    setup_logger(idx, queue)
    logger.info(f"Worker {idx} starting") 
    retry = 0
    file_path = ""
    while True:
        if retry == 0 or retry > 1:
            file_path = path_manager.get_next_path()
            retry = 0
        if file_path:
            try:
                logger.info(f"processing {file_path} in worker {idx}")
                process_file(file_path, dataset)
                retry = 0
            except Exception as e:
                logger.error(f"Some uncaught error in {file_path}")
                logger.error(e)
                retry += 1
        else:
            logger.info(f"No more file to process in worker:{idx}, quiting now!")
            break


def main():  
    parser = argparse.ArgumentParser(description="Process JSON files for a specific node.")
    parser.add_argument("--dataset", default="miniF2F", type=str, help="MATH or miniF2F")
    parser.add_argument("--root_dir_list", default="../dataset/miniF2F/informal/", type=str, help="Comma-separated list of root directories")
    parser.add_argument("--num_process", default=1, type=int, help="Set concurrency (same with number of api keys)")
    args = parser.parse_args()
    # root_dir_list = ['./informal']
    root_dir_list = args.root_dir_list.split(",")
    dataset = args.dataset
    dataset = "MATH"
    root_dir_list = root_dir_list = [
        "../dataset/MATH/batch/task_test_gpt-4/0",
        "../dataset/MATH/batch/task_test_gpt-4/15",
        "../dataset/MATH/batch/task_test_gpt-4/17",
        "../dataset/MATH/batch/task_test_gpt-4/48",
    ]
    num_process = args.num_process
    num_process = 1  
    
    json_file_paths = []
    for root_dir in root_dir_list:
        json_file_paths += get_json_files(root_dir)
    # json_file_paths = json_file_paths[:2]
    # json_file_paths = ["../dataset/MATH/batch/task_test_gpt-4/0/counting_and_probability/problem_472.json"]
    print(f"Totally have {len(json_file_paths)} to do")
    # set concurrency (same with number of api keys)
    # return

    manager = multiprocessing.Manager()  
    path_manager = PathManager(json_file_paths, manager)

    queue = manager.Queue(-1)
    # Create the file
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = f"./logs/{current_datetime}_error.log"
    # set up listener
    listener = logging.handlers.QueueListener(queue, logging.FileHandler(filename))
    listener.start()
    Parallel(n_jobs=num_process, temp_folder='/datadisk/tmp')(delayed(process_batch)(path_manager,queue,dataset,idx) for idx in range(num_process))

    listener.stop()

if __name__ == '__main__':
    main()