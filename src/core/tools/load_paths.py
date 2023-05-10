import os

def load_paths(dir_path):
    buggy_code_path = []
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.endswith(".py"):
                buggy_code_path.append(os.path.join(root, file))

    # sort the buggy code path by the number in the file names
    buggy_code_path = sorted(buggy_code_path, key=lambda x: int(x.split("/")[-1].split(".")[0].split("_")[2]))
    return buggy_code_path