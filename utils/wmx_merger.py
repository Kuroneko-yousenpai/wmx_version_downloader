import math
import os
import re
import sys
import time
from loguru import logger


def is_last_file(root, files, all_files):
    return os.path.join(root, files[-1]) == all_files[-1]

def check_imports(str_l: str):
    pattern = re.compile(r'^\s*import\s+.*;', re.MULTILINE)
    return bool(pattern.match(str_l))

def copy_contents_to_file(start_path, output_file, is_include_names: bool = False, is_rm_imports: bool = False, sort_by="name"):
    all_files = [os.path.join(root, file) for root, dirs, files in os.walk(start_path) for file in files if file.endswith('.as')]

    if sort_by == "name":
        all_files.sort(key=lambda x: os.path.basename(x).lower())
    elif sort_by == "size":
        all_files.sort(key=lambda x: os.path.getsize(x))
    elif sort_by == "date":
        all_files.sort(key=lambda x: os.path.getmtime(x))
    elif sort_by == "type":
        all_files.sort(key=lambda x: os.path.splitext(x)[1].lower())

    is_first_file = True
    for file_path in all_files:
        file_buffer = []
        if is_include_names:
            if is_first_file:
                file_buffer.append(f"{os.path.basename(file_path)}\n\n")
                is_first_file = False
            else:
                file_buffer.append(f"\n{os.path.basename(file_path)}\n\n")
        with open(file_path, "r", encoding="utf-8") as f:
            if is_rm_imports:
                for line in f:
                    if check_imports(line):
                        continue
                    file_buffer.append(line)
                root, file = os.path.split(file_path)
                if not is_last_file(root, [file], all_files):
                    file_buffer.append("\n")
                output_file.write(''.join(file_buffer))
            else:
                f_content = f.read()
                file_buffer.append(f_content)
                root, file = os.path.split(file_path)
                if not is_last_file(root, [file], all_files):
                    file_buffer.append("\n")
                output_file.write(''.join(file_buffer))

def get_valid_directory(prompt):
    while True:
        directory = input(prompt)
        normalized_directory = os.path.normpath(directory)
        if os.path.isdir(normalized_directory):
            return normalized_directory
        logger.error(f"Directory not found: {directory}. Please enter a valid path!")

def get_valid_filename(prompt):
    while True:
        filename = input(prompt)
        # Remove non-ASCII characters
        safe_filename = filename.encode("ascii", "ignore").decode()
        if safe_filename.strip():
            if not safe_filename.lower().endswith(".txt"):
                return f"{safe_filename}.txt"
            return safe_filename
        logger.error("Filename cannot be empty. Please enter a valid name!")

def query_yes_no(question, default="yes"):
    valid = {"yes": True, "y": True, "yea": True,
             "no": False, "n": False, "nope": False}
    prompt_options = {"yes": " [Y/n] ", "no": " [y/N] ", None: " [y/n] "}
    prompt = prompt_options.get(default, " [y/n] ")
    while True:
        sys.stdout.write(question + prompt)
        choice = input().strip().lower()
        if not len(choice) > 0 and default is not None:
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' (or 'y'/'n')\n")

def create_file_tree(path, prefix=""):
    file_tree = ""
    if os.path.isdir(path):
        file_tree += prefix + os.path.basename(path) + "/\n"
        prefix += "    "
        for item in sorted(os.listdir(path)):
            file_tree += create_file_tree(os.path.join(path, item), prefix)
    else:
        file_tree += prefix + os.path.basename(path) + "\n"
    return file_tree

def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def main():
    start_folder = get_valid_directory("Enter the starting path: ")
    output_file_name = get_valid_filename("Enter the name for the result file: ")
    is_rm_imports = query_yes_no("Remove imports lines?", default="yes")
    is_include_names = query_yes_no("Include file names in the content?", default="no")
    prev_dir = os.path.dirname(start_folder)
    result_file_path = os.path.join(prev_dir, output_file_name)
    time_start = time.time()
    with open(result_file_path, "w") as res_file:
        copy_contents_to_file(start_folder, res_file, is_include_names, is_rm_imports)
    time_end = time.time()
    execution_time = time_end - time_start
    is_tree_need = query_yes_no("Make filetree?", default="no")
    if is_tree_need:
        file_tree = create_file_tree(start_folder)
        print(f"\nFile Tree:\n{file_tree}")
    file_size = convert_size(os.path.getsize(result_file_path))
    logger.info(f"Result path: {result_file_path} ; Size: {file_size}")
    logger.info(f"Successed in: {execution_time}")
    logger.success("Done, lol")


if __name__ == "__main__":
    LOGGER_LEVEL = "DEBUG"

    logger.remove()
    logger.add(sys.stdout,
               format="[<fg 255,185,255>{time:HH:mm:ss}</fg 255,185,255>] "
                      "[ <fg #FFA319>consollite</fg #FFA319> ] "
                      "[<level>{level}</level>] <fg #66FF66>{message}</fg #66FF66>",
               level=LOGGER_LEVEL,
               colorize=True)

    logger.level("TRACE", color="<fg #DCDCDC><b>")
    logger.level("DEBUG", color="<fg #66FF66><b>")
    logger.level("INFO", color="<fg #0064FF><b>")
    logger.level("SUCCESS", color="<fg #FF86FF><b>")
    logger.level("WARNING", color="<fg #FF9900><b>")
    logger.level("ERROR", color="<red><b>")
    logger.level("CRITICAL", color="<fg #FF1C1C><b>")

    main()