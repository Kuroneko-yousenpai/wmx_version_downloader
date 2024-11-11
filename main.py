"""
  - Copyright 2024 Ruri Gokou (Kuroneko-yousenpai)
  - Email: Kuronekoyousenpai@gmail.com
  - Telegram: https://t.me/Kuroneko_yousenpai
  - VK: https://vk.com/kuroneko_yousenpai
"""

import os
import subprocess
import sys
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import re


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

def get_ldr_url():
    is_manual = not query_yes_no("[?] Use default VK game loader url?", default="yes")
    if not is_manual:
        loader_url = "https://markus.rmart.ru/engine/preloader/preloader.html"
        return loader_url
    while True:
        loader_url = input("[?] Enter preloader url: ")
        if re.match(r'^(?:https?://)?(?:www\.)?[\w.-]+\.[a-zA-Z]{2,}(?:/[\w.-]*)*$', loader_url):
            return loader_url
        else:
            print("[-] Invalid link, try again")

def get_lang(langs: list):
    is_manual = not query_yes_no("[?] Use default game lang?", default="yes")
    if not is_manual:
        cur_lang = 0
        return cur_lang

    print("[+] Choose game lang")
    for i, lang in enumerate(langs, start=1):
        print(f"{i} - {lang}")

    while True:
        try:
            cur_lang = int(input("[?] Enter lang num: "))
            if cur_lang in [1, 2, 3, 4]:
                if cur_lang < 4:
                    cur_lang -= 1
                else:
                    cur_lang = -1
                return cur_lang
            else:
                print("[-] Invalid value, try again")
        except ValueError:
            print("[-] Invalid lang! Please enter only a digit value")

def extract_base_url(html_url: str):
    parsed_url = urlparse(html_url)
    path_parts = parsed_url.path.split("/")
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{'/'.join(path_parts[:-1])}/"
    return base_url

def download_file(file_url: str, file_path: str, is_critical: bool = True) -> bool:
    response = requests.get(file_url)
    if response.status_code != 200 and is_critical:
        print("[-] File not found")
        return False
    base_name = os.path.basename(file_path)
    base_path = os.path.dirname(file_path)
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    with open(file_path, "wb") as f:
        f.write(response.content)
    print(f"[+] File {base_name} successfully downloaded")
    return True

def decompile_swf(file_name: str, swf_path: str, cur_path: str) -> str:
    jar_path = os.path.normpath(os.path.join(cur_path, "ffdec/ffdec.jar"))
    if file_name.find(".") != -1:
        file_name = file_name.split(".")[0]
    output_dir = os.path.join(os.getenv("LOCALAPPDATA"), "Temp", "swf_export", file_name)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    command = f"java -jar {jar_path} -export script {output_dir} {swf_path}"
    subprocess.run(command, shell=True)
    return output_dir

def search_pattern(folder_path, pattern: str):
    res_pattern = re.compile(pattern)

    results = set()
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".as"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    content = f.read()
                    pattern_matches = res_pattern.findall(content)
                    results.update(pattern_matches)
    return results

def search_main_patterns(folder_path):
    data_pattern = re.compile(r"data/lang/")
    ser_pattern = re.compile(r'(?:data/|serializers/)serializers\.xml')
    chat_pattern = re.compile(r'common/chat.xml')
    s_lang_pattern = re.compile(r'avatar.messages')
    smsg_pattern = re.compile(r'\+ "messages"')
    taunts_pattern = re.compile(r'\+ "taunts"')
    chat2_pattern = re.compile(r'\+ "chat_"')

    founded_arr = []
    const_pattern = re.compile(r'private\s+static\s+const\s+\S+\s*:\s*(String|Array)\s*=\s*("[^"]+"|\[[^\]]+\])') # noqa
    results = []
    is_data_found = False
    is_ser_found = False
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".as"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    content = f.read()
                    if data_pattern.search(content):
                        const_matches = const_pattern.findall(content)
                        for match in const_matches:
                            if match[1].startswith('"'):
                                founded_arr.append(match[1][1:-1])
                            else:
                                array_items = [item.strip()[1:-1] for item in match[1][1:-1].split(",")]
                                founded_arr.append(array_items)
                        chat_matches = chat_pattern.findall(content)
                        founded_arr.append(chat_matches[0])
                        s_lang_matches = s_lang_pattern.findall(content)
                        avatar_msg_f = f"{{social}}/{s_lang_matches[0]}"
                        founded_arr.append(avatar_msg_f)
                        smsg_matches = smsg_pattern.findall(content)
                        if len(smsg_matches):
                            founded_arr.append("messages")
                        taunts_matches = taunts_pattern.findall(content)
                        if len(taunts_matches):
                            founded_arr.append("taunts")
                        chat2_matches = chat2_pattern.findall(content)
                        if len(chat2_matches):
                            founded_arr.append("chat")
                        is_data_found = True
                    elif ser_pattern.search(content):
                        ser_matches = ser_pattern.findall(content)
                        founded_arr.append(ser_matches[0])
                        is_ser_found = True
                if is_ser_found and is_data_found:
                    break
        if is_data_found:
            break

    for i, element in enumerate(founded_arr):
        if "serializers.xml" in element and founded_arr.index(element) != 0:
            founded_arr.insert(0, founded_arr.pop(i))

    results = [[res] for res in founded_arr]

    return results

def extract_data_files(cfg_path: str):
    pattern = r'<library path="([^"]+)"(?:\s+\S+="[^"]+")*>'

    results = []
    with open(cfg_path, "r") as f:
        file_contents = f.read()
    matches = re.findall(pattern, file_contents)
    results.extend(matches)

    return results

def get_social(folder_name: str):
    socials = ["vkontakte", "mailru", "odnoklassniki"]
    match(folder_name):
        case "engine" | "wormix_vk_test":
            return socials[0] if len(socials) > 0 else None
        case "wormix_mm" | "wormix_mm_test":
            return socials[1] if len(socials) > 1 else None
        case "wormix_ok" | "wormix_ok_test":
            return socials[2] if len(socials) > 2 else None
        case _:
            return "vkontakte"

def get_lang_pathes(lang_path: str, lang_files: list, lang_folder: str):
    files = []
    for lang_f in lang_files:
        lang_f = f"{lang_f}_{lang_folder}.xml"
        lang_f_path = os.path.join(lang_path, lang_f)
        files.append(lang_f_path)
    return files

def main():
    print("Wormix Version Downloader v2.0", end="\n\n")

    html_url = get_ldr_url()

    game_langs = ["ru", "ua", "en", "all"]
    cur_lang = get_lang(game_langs)

    print("[+] Try to get new game version...")
    base_url = extract_base_url(html_url)
    social_folder = html_url.split("rmart.ru/")[-1].split("/")[0]
    main_folder = "versions"
    social = get_social(social_folder)
    if not base_url or not social_folder:
        print("[-] Main url are wrong")
        return
    cur_path = os.getcwd()
    response = requests.get(html_url)
    if response.status_code != 200:
        print("[-] Failed to fetch HTML content")
        return
    soup = BeautifulSoup(response.content, "html.parser")
    script_tags = soup.find_all("script")
    loader_name = "preloader.swf"
    for script_tag in script_tags:
        if script_tag.string:
            match = re.search(r"preloader_\d+.swf", script_tag.string)
            if match:
                loader_name = match.group(0)
                swf_url = f"{base_url}{loader_name}"
                file_path = os.path.normpath(os.path.join(cur_path, main_folder, loader_name))
                is_downloaded = download_file(swf_url, file_path)
                break
    else:
        print("[-] No preloader files found")
        return
    if not is_downloaded:
        print(f"[-] Loader file {loader_name} not found in folder")
        return
    ldr_path = os.path.join(cur_path, main_folder, loader_name)
    ldr_decomp_path = decompile_swf(loader_name, ldr_path, cur_path)
    print("[+] Loader successfully decompiled")
    print(f"[*] Output path: {ldr_decomp_path}", end="\n\n\n")
    ldr_results = []
    loader_patterns = [r'return\s+"(Wormix.*\.swf)";', r'return\s+"(https://.+\.rmart\.ru/.+?)";']
    for pattern in loader_patterns:
        results = search_pattern(ldr_decomp_path, pattern)
        ldr_results.extend([results])
    main_swf = ""
    main_project_url = ""
    for i, res_arr in enumerate(ldr_results):
        if i == 0:
            print("[*] Found SWF files:")
        else:
            print("\n[*] Found URLs:")
        for j, res_str in enumerate(res_arr):
            if i == 0 and j == 0:
                main_swf = res_str
            if i == 1 and j == 0:
                main_project_url = res_str
            print(res_str)
    print(f"[*] Warning! Will be downloaded only {main_swf} and used only main url")
    if len(main_swf) < 1 or len(main_project_url) < 1:
        if len(main_swf) < 1:
            print("[-] Main swf file not found")
        if len(main_project_url) < 1:
            print("[-] Project folder not found")
        return
    project_version = re.search(r"/([\w.]+)/$", main_project_url).group(1)
    main_swf_url = f"{main_project_url}{main_swf}"
    file_path = os.path.normpath(os.path.join(cur_path, main_folder, project_version, main_swf))
    is_downloaded = download_file(main_swf_url, file_path)
    if not is_downloaded:
        print(f"[-] Main swf file {main_swf_url} not found in folder")
        return
    main_swf_path = os.path.join(cur_path, main_folder, project_version, main_swf)
    main_decomp_path = decompile_swf(main_swf, main_swf_path, cur_path)
    print("[+] Main game engine swf successfully decompiled")
    print(f"[*] Output path: {main_decomp_path}", end="\n\n\n")

    main_results = search_main_patterns(main_decomp_path)
    if len(main_results) < 9:
        print("[-] Not all data configs found")
        return

    print(f"[+] Try to download files...", end="\n\n")

    ser_file_url = f"{main_project_url}{main_results[0][0]}"
    ser_path = os.path.normpath(os.path.join(cur_path, main_folder, project_version, main_results[0][0]))
    is_downloaded = download_file(ser_file_url, ser_path)
    if not is_downloaded:
        print("[-] Serializer not found")
        return

    cfgs_path = os.path.normpath(os.path.join(cur_path, main_folder, project_version, main_results[4][0]))
    rescfgs = [main_results[5][0], main_results[6][0], main_results[7][0]]
    all_data_files = []
    other_lang_files = []
    rm_indexes = []
    res_arr = []
    for i, el in enumerate(main_results):
        if any(substring in el[0] for substring in ["avatar.messages", "chat.xml", "messages", "taunts", "chat"]) and not isinstance(el[0], list):
            rm_indexes.append(i)
            if "avatar.messages" in el[0]:
                el = main_results[2][0].format(social=el[0])
                parts = el.split("/")
                lang_index = parts.index("lang")
                avatar_index = parts.index("avatar.messages")
                parts[lang_index], parts[avatar_index] = parts[avatar_index], parts[lang_index]
                el = "/".join(parts)[:-1]
                all_data_files.append(el)
            elif "chat.xml" in el[0]:
                el = f"{main_results[1][0]}{el[0]}"
                all_data_files.append(el)
            elif "messages" in el[0]:
                el = f"{main_results[2][0]}{el[0]}"
                all_data_files.append(el)
            else:
                el = el[0]
                other_lang_files.append(el)
            res_arr.append(el)
            if all(any(substring in el and substring != "chat" or substring == el for el in res_arr) for substring in ["avatar.messages", "chat.xml", "messages", "taunts", "chat"]):
                break
    main_results = [main_results[i] for i in range(len(main_results)) if i not in rm_indexes]
    del rm_indexes
    for rescfg_file in rescfgs:
        resconfig_url = f"{main_project_url}{main_results[4][0]}{rescfg_file}"
        rescfg_path = os.path.normpath(os.path.join(cfgs_path, rescfg_file))
        is_downloaded = download_file(resconfig_url, rescfg_path)
        if not is_downloaded:
            print("[-] Config not found")
            return
        data_files = extract_data_files(rescfg_path)
        all_data_files.extend(data_files)

    # Get real pathes
    for i, file_path in enumerate(all_data_files):
        if "{social}" in file_path:
            all_data_files[i] = file_path.format(social=social)

    # Get social lang files
    lang_indexes = []
    for i, data_f in enumerate(all_data_files):
        if any(substring in data_f for substring in ["avatar.messages", "messages"]):
            lang_indexes.append(i)
            if len(lang_indexes) > 1:
                break
    slang_files = [all_data_files.pop(i) for i in sorted(lang_indexes, reverse=True)]

    if cur_lang != -1:
        lang_paths = get_lang_pathes(main_results[3][0], main_results[-1][0], game_langs[cur_lang])
        all_data_files.extend(lang_paths)
        for slang in slang_files:
            lang_f = f"{slang}_{game_langs[cur_lang]}.xml"
            all_data_files.append(lang_f)
        other_lang_paths = get_lang_pathes(main_results[3][0], other_lang_files, game_langs[cur_lang])
        lang_paths.extend(other_lang_paths)
        # For lang/chat we need at least ru, ua or en lang files
        chat_index = other_lang_files.index("chat")
        for lang in game_langs[:-1]:
            if lang == game_langs[cur_lang]:
                continue
            c_lang_paths = get_lang_pathes(main_results[3][0], [other_lang_files[chat_index]], lang)
            lang_paths.extend(c_lang_paths)
        all_data_files.extend(lang_paths)
    else:
        for lang in game_langs[:-1]:
            lang_paths = get_lang_pathes(main_results[3][0], main_results[-1][0], lang)
            all_data_files.extend(lang_paths)
            for slang in slang_files:
                lang_f = f"{slang}_{lang}.xml"
                all_data_files.append(lang_f)
            other_lang_paths = get_lang_pathes(main_results[3][0], other_lang_files, lang)
            lang_paths.extend(other_lang_paths)
            all_data_files.extend(lang_paths)

    for i, data_f in enumerate(all_data_files):
        file_url = f"{main_project_url}/{data_f}"
        file_path = os.path.normpath(os.path.join(cur_path, main_folder, project_version, data_f))
        is_critical = False
        is_downloaded = download_file(file_url, file_path, is_critical=is_critical)
        if not is_downloaded and is_critical:
            break
    print("[+] Done, lol")


if __name__ == "__main__":
    # Default link to main VK game loader: https://markus.rmart.ru/engine/preloader/preloader.html
    main()