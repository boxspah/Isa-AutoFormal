import argparse
import itertools
import json
import logging
import logging.handlers
import multiprocessing
import os
import re
from datetime import datetime

import networkx as nx
from tqdm import tqdm

from .PathManager import PathManager, Parallel, delayed
from .utils import isa_utils, all_exceptions as E

init_port = isa_utils.init_port
DEBUG = isa_utils.DEBUG


def setup_logger(idx, queue):
    global logger
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info_log_path = f"./logs/{current_datetime}_info_{idx}.log"
    logger = logging.getLogger(f"logger_{idx}")
    logger.setLevel(logging.DEBUG)  # 设置最低的日志级别
    logger.propagate = False
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

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


def largest_connected_component(
    formal_statements, origin_oracle, checker, file_path, suffix
):
    G = nx.Graph()
    for i in range(len(formal_statements)):
        G.add_node(i)
    # iterate each node pair
    pairs = list(itertools.combinations(range(len(formal_statements)), 2))
    proofs = {}
    memory_heuristics = []
    for i in range(len(formal_statements)):
        striped_statement = [item.strip() for item in formal_statements[i].split(",")]
        formal_statements[i] = ",".join(striped_statement)
    # try:
    with open(file_path) as f:
        data = json.load(f)
    if f"prediction_{suffix}" in data.keys():
        logger.info(f"processed prediction {file_path} with suffix {suffix}")
        origin_connected_subgraphs = [
            value for value in data[f"prediction_{suffix}"].values()
        ]
        for node_list in origin_connected_subgraphs:
            G.add_edges_from(
                [(node_list[i], node_list[i + 1]) for i in range(len(node_list) - 1)]
            )
    else:
        logger.info(f"no prediction in {file_path} with suffix {suffix}")
        for i, j in tqdm(pairs):
            logger.info("=" * 100)
            logger.info(f"{file_path} {(i, j)}")
            # check the equivalence
            if nx.has_path(G, i, j):
                logger.info(f"{file_path} {(i, j)}: already connected")
                G.add_edge(i, j)
            else:
                logger.info(f"{formal_statements[i]} \n {formal_statements[j]}")
                # check existing proofs
                msg = None
                for u, v in proofs.keys():
                    if (
                        formal_statements[u] == formal_statements[i]
                        and formal_statements[v] == formal_statements[j]
                    ):
                        flag, msg = proofs[(u, v)]
                    elif (
                        formal_statements[u] == formal_statements[j]
                        and formal_statements[v] == formal_statements[i]
                    ):
                        flag, msg = proofs[(u, v)]
                    else:
                        continue
                if msg is not None:
                    logger.info(f"{file_path} {(i, j)}: using existing proof")
                    if flag:
                        G.add_edge(i, j)
                    continue
                try:
                    flag, msg = isa_utils.check_equivalence_simplify(
                        formal_statements[i],
                        formal_statements[j],
                        checker,
                        memory_heuristics,
                    )
                    for m in msg.split("\n"):
                        if "using tactic" in m and m.split("using tactic:")[1].strip():
                            memory_heuristics.append(
                                m.split("using tactic:")[1].strip()
                            )
                except (
                    E.ThmFormatException,
                    E.SimplifyException,
                    E.ConcException,
                ) as e:
                    flag = False
                    msg = str(e)
                    logger.error(msg)
                except Exception as e:
                    flag = False
                    msg = str(e)
                    logger.error(f"uncaught error in {file_path} {i, j}: {msg}")
                    if "Isabelle" in msg or "Spark" in msg:
                        # raise e
                        isa_utils.researt_isa(checker)
                proofs[(i, j)] = (flag, msg)
                logger.info(f"{file_path} {(i, j)}: {msg}")
                if flag:
                    G.add_edge(i, j)
                    continue
                try:
                    flag, msg = isa_utils.check_equivalence(
                        formal_statements[i],
                        formal_statements[j],
                        checker,
                        memory_heuristics,
                    )
                    for m in msg.split("\n"):
                        if "using tactic" in m and m.split("using tactic:")[1].strip():
                            memory_heuristics.append(
                                m.split("using tactic:")[1].strip()
                            )
                except (
                    E.ThmFormatException,
                    E.SimplifyException,
                    E.ConcException,
                ) as e:
                    flag = False
                    msg = str(e)
                    logger.error(msg)
                except Exception as e:
                    flag = False
                    msg = str(e)
                    logger.error(f"uncaught error in {file_path} {i, j}: {msg}")
                    if "Isabelle" in msg or "Spark" in msg:
                        # raise e
                        isa_utils.researt_isa(checker)
                proofs[(i, j)] = (flag, msg)
                logger.info(f"{file_path} {(i, j)}: {msg}")
                if flag:
                    G.add_edge(i, j)
                    continue

    connected_components = sorted(nx.connected_components(G), key=len, reverse=True)
    logger.info(f"connected_components in {file_path} : {connected_components}")
    connected_subgraphs = [list(c) for c in connected_components]
    equivalence_oracle = []
    striped_statement = [item.strip() for item in origin_oracle.split(",")]
    origin_oracle = ",".join(striped_statement)
    # get oracles
    oracles = []
    for i in range(len(formal_statements)):
        if data[f"a_{i}"]["label"] == 1:
            oracles.append(formal_statements[i])
    logger.info(f"oracles in {file_path} : {len(oracles)}")

    oracles.append(origin_oracle)
    for i in range(len(formal_statements)):
        logger.info("=" * 100)
        for oracle in oracles:
            logger.info(f"{file_path} {i}, oracle")
            logger.info(f"{formal_statements[i]} \n {oracle}")
            if i in equivalence_oracle:
                logger.info(f"{file_path} {i}, oracle: already in equivalence_oracle")
                break
            if i not in equivalence_oracle:
                try:
                    flag, msg = isa_utils.check_equivalence_simplify(
                        formal_statements[i], oracle, checker, memory_heuristics
                    )
                    for m in msg.split("\n"):
                        if "using tactic" in m and m.split("using tactic:")[1].strip():
                            memory_heuristics.append(
                                m.split("using tactic:")[1].strip()
                            )
                except (
                    E.ThmFormatException,
                    E.SimplifyException,
                    E.ConcException,
                ) as e:
                    flag = False
                    msg = str(e)
                    logger.error(f"{file_path} {i}, oracle: {msg}")
                except Exception as e:
                    flag = False
                    msg = str(e)
                    logger.error(f"uncaught error in {file_path} {i}, oracle: {msg}")
                    if "Isabelle" in msg or "Spark" in msg:
                        # raise e
                        isa_utils.researt_isa(checker)
                logger.info("simplify check: " + msg)
                if flag:
                    equivalence_oracle.extend(
                        [
                            elem
                            for subgraph in connected_subgraphs
                            if i in subgraph
                            for elem in subgraph
                        ]
                    )
                    if not any(i in subgraph for subgraph in connected_subgraphs):
                        equivalence_oracle.append(i)
                    continue

                try:
                    flag, msg = isa_utils.check_equivalence(
                        formal_statements[i], oracle, checker, memory_heuristics
                    )
                    for m in msg.split("\n"):
                        if "using tactic" in m and m.split("using tactic:")[1].strip():
                            memory_heuristics.append(
                                m.split("using tactic:")[1].strip()
                            )
                except (
                    E.ThmFormatException,
                    E.SimplifyException,
                    E.ConcException,
                ) as e:
                    flag = False
                    msg = str(e)
                    logger.error(f"{file_path} {i}, oracle: {msg}")
                except Exception as e:
                    flag = False
                    msg = str(e)
                    logger.error(f"uncaught error in {file_path} {i}, oracle: {msg}")
                    if "Isabelle" in msg or "Spark" in msg:
                        # raise e
                        isa_utils.researt_isa(checker)
                logger.info("normal check: " + msg)
                if flag:
                    equivalence_oracle.extend(
                        [
                            elem
                            for subgraph in connected_subgraphs
                            if i in subgraph
                            for elem in subgraph
                        ]
                    )
                    if not any(i in subgraph for subgraph in connected_subgraphs):
                        equivalence_oracle.append(i)
                    continue
    return connected_subgraphs, equivalence_oracle


def process_batch(path_manager, queue, idx, method, suffix):
    setup_logger(idx, queue)
    logger.info(f"Worker {idx} starting")
    checker = isa_utils.start_isa(port=init_port + idx)
    retry = 0
    file_path = ""
    while True:
        if retry == 0 or retry > 1:
            file_path = path_manager.get_next_path()
            retry = 0
        if file_path:
            for suf in suffix:
                try:
                    logger.info(f"processing {file_path} in worker {idx}")
                    if method == "naive":
                        naive_process_file(file_path, suf, checker)
                    else:
                        process_file(file_path, suf, checker)
                    retry = 0
                except Exception as e:
                    logger.error(f"Some uncaught error in {file_path}")
                    logger.error(e)
                    isa_utils.researt_isa(checker)
                    retry += 1
        else:
            logger.info(f"No more file to process in worker:{idx}, quiting now!")
            break
    checker.exit()


def process_file(file_path, suffix, checker):
    k = 10
    with open(file_path) as f:
        data = json.load(f)
    formal_statements = []
    for i in range(k):
        name = f"a_{i}_{suffix}"
        formal_statements.append(data[name]["formal problem"])
    oracle = data.get("oracle", "")
    logger.info(f"processing {file_path} with suffix {suffix}")
    if f"prediction_{suffix}" in data.keys():
        logger.info(f"processed prediction {file_path} with suffix {suffix}")
        return
    largest_components, equivalence_oracle = largest_connected_component(
        formal_statements, oracle, checker, file_path, suffix
    )
    if largest_components:
        largest_components_list = [list(s) for s in largest_components]
        data[f"prediction_{suffix}"] = {
            f"{index}": sublist for index, sublist in enumerate(largest_components_list)
        }
    logger.info(
        f"prediction in {file_path} with suffix {suffix}: " + str(largest_components)
    )
    if equivalence_oracle:
        data[f"equivalence_oracle_{suffix}"] = equivalence_oracle
    logger.info(
        f"equivalence_oracle in {file_path} with suffix {suffix}: "
        + str(equivalence_oracle)
    )

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)


def naive_process_file(file_path, suffix, checker):
    k = 10
    with open(file_path) as f:
        data = json.load(f)
    memory_heuristics = []
    for i in range(k):
        name = f"a_{i}_{suffix}"
        logger.info("=" * 100)
        logger.info(f"{file_path} {name}")
        formal_statements = data[name]["formal problem"]
        try:
            flag, msg = isa_utils.naive_check(
                formal_statements, checker, memory_heuristics
            )
            for m in msg.split("\n"):
                if "using tactic" in m and m.split("using tactic:")[1].strip():
                    memory_heuristics.append(m.split("using tactic:")[1].strip())
        except (E.ThmFormatException, E.SimplifyException, E.ConcException) as e:
            flag = False
            msg = str(e)
            logger.error(msg)
        except Exception as e:
            flag = False
            msg = str(e)
            logger.error(f"uncaught error in {file_path} {i}: {msg}")
            if "Isabelle" in msg or "Spark" in msg:
                # raise e
                isa_utils.researt_isa(checker)
        if flag:
            data[name]["naive_label"] = 1
        else:
            data[name]["naive_label"] = 0

    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)


def check_labeled(file_path):
    k = 10
    with open(file_path) as f:
        data = json.load(f)
    labels = []
    for i in range(k):
        name = f"a_{i}"
        if "label" in data[name] and "syntax" in data[name]:
            labels.append(int(data[name]["label"]) * int(data[name]["syntax"]))
    if len(labels) >= 10:
        return True
    else:
        return False


def check_not_processed(file_path, suffix):
    with open(file_path) as f:
        data = json.load(f)
    for suf in suffix:
        if f"prediction_{suf}" not in data.keys():
            return True
    return False


def check_processed(file_path, suffix):
    with open(file_path) as f:
        data = json.load(f)
    for suf in suffix:
        if f"prediction_{suf}" in data.keys():
            return True
    return False


def check_oracle_syntax(file_path):
    with open(file_path) as f:
        data = json.load(f)
    oracle = data.get("oracle", "")
    pattern = r" +"
    # 将所有连续的空白字符替换为单个空格
    oracle = re.sub(pattern, " ", oracle)
    match = re.search(r'theorem[\s\S]*?shows "[\s\S]*?"', oracle)
    if match:
        return True
    else:
        return False


def check_oracle(file_path):
    k = 10
    with open(file_path) as f:
        data = json.load(f)
    labels = []
    for i in range(k):
        name = f"a_{i}"
        if "label" in data[name] and data[name]["label"] == 1:
            return True
    if "oracle" in data:
        return check_oracle_syntax(file_path)
    return False


def get_json_files(root_dir, suffix=[]):
    json_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                if not check_oracle(file_path):
                    continue
                if check_not_processed(file_path, suffix) or not check_oracle_syntax(
                    file_path
                ):
                    json_files.append(file_path)
    return json_files


def calculate_group_sizes(total_length, num_groups):
    base_size = total_length // num_groups
    remaining = total_length % num_groups
    group_sizes = [
        base_size + 1 if i < remaining else base_size for i in range(num_groups)
    ]
    return group_sizes


def get_group_content(data_list, node_num, total_nodes):
    total_length = len(data_list)
    group_sizes = calculate_group_sizes(total_length, total_nodes)

    start_index = sum(group_sizes[:node_num])
    end_index = start_index + group_sizes[node_num]

    group_content = data_list[start_index:end_index]
    return group_content


def main():
    parser = argparse.ArgumentParser(
        description="Process JSON files for a specific node."
    )
    parser.add_argument(
        "--root_dir_list",
        default="../dataset/miniF2F/informal/",
        type=str,
        help="Comma-separated list of root directories",
    )
    parser.add_argument(
        "--total_node", default=1, type=int, help="Total number of nodes"
    )
    parser.add_argument("--node_num", default=0, type=int, help="Current node number")
    parser.add_argument(
        "--num_process", default=12, type=int, help="Number of processes"
    )
    parser.add_argument("--method", default="naive", type=str, help="naive or symbolic")
    parser.add_argument(
        "--suffix",
        default="gpt3.5,deepseek",
        type=str,
        help="Comma-separated list of suffix",
    )

    args = parser.parse_args()
    root_dir_list = args.root_dir_list.split(",")
    suffix = args.suffix.split(",")
    method = args.method
    json_file_paths = []
    for root_dir in root_dir_list:
        json_file_paths += get_json_files(root_dir, suffix)
    json_file_paths = sorted(json_file_paths)
    json_file_paths = get_group_content(json_file_paths, args.node_num, args.total_node)
    print(f"Totally have {len(json_file_paths)} to do")

    # set concurrency
    num_process = args.num_process

    manager = multiprocessing.Manager()
    path_manager = PathManager(json_file_paths, manager)

    queue = manager.Queue(-1)
    # Create the file
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = f"./logs/{current_datetime}_error.log"
    # set up listener
    listener = logging.handlers.QueueListener(queue, logging.FileHandler(filename))
    listener.start()
    Parallel(n_jobs=num_process, temp_folder="/datadisk/tmp")(
        delayed(process_batch)(path_manager, queue, idx, method, suffix)
        for idx in range(num_process)
    )

    listener.stop()


if __name__ == "__main__":
    main()
