import os
import json


def get_json_files(root_dir):
    json_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".json"):
                file_path = os.path.join(root, file)
                # if check_labeled(file_path):
                json_files.append(file_path)
    return json_files


if __name__ == "__main__":
    for part in ["test", "train"]:
        root_dir = f"./batch/task_{part}_gpt-4/"
        count = 0
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if file.endswith(".json"):
                    file_path = os.path.join(root, file)
                    # print(root,file)
                    origin_data_path = os.path.join(
                        f"../../MATH/{part}/",
                        root.split("/")[-1],
                        file.replace("problem_", ""),
                    )
                    if not os.path.exists(origin_data_path):
                        print(origin_data_path)
                    else:
                        with open(file_path) as f:
                            data = json.load(f)
                        with open(origin_data_path) as f:
                            origin_data = json.load(f)
                        data["level"] = origin_data["level"]
                        data["type"] = origin_data["type"]
                        with open(file_path, "w") as f:
                            json.dump(data, f, indent=4)
                    count += 1
        print(f"{count} files in {part} set.")
