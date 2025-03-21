import config
import os
import json
from xml.dom import minidom
from queue import Queue
import subprocess
import time
import re
import sys
import networkx as nx


def modify_doxyfile(scan_dir_list, git_repo_location):
    dir_list = []
    for scan_dir in scan_dir_list:
        dir_list.append(scan_dir)
        for root, dirs, files in os.walk(scan_dir):
            for dir1 in dirs:
                write_dir = os.path.join(root, dir1).replace('\\', '/')
                if "/." not in write_dir:
                    dir_list.append(write_dir)
    os.system("cp " + config.Doxygen_conf_location + " " + git_repo_location)
    with open(git_repo_location + "/Doxyfile", "r") as f:
        lines = f.readlines()
        for i in range(len(dir_list)):
            if i != len(dir_list) - 1:
                lines.insert(119 + i, '"' + dir_list[i] + '" \\ \n')
            else:
                lines.insert(119 + i, '"' + dir_list[i] + '"\n')
    with open(git_repo_location + "/Doxyfile", "w") as f:
        f.writelines(lines)
    return True


def readCommit(location, git_repo_location, work_dir):
    method_info = []
    old_file_relative_name_list = []
    with open(location, "r", encoding=config.encoding_format) as f:
        lines = f.readlines()
        files = []
        file_seperator = []
        for i in range(len(lines)):
            if lines[i].startswith("diff --git"):
                file_seperator.append(i)
        for i in range(len(file_seperator) - 1):
            files.append(lines[file_seperator[i]: file_seperator[i + 1] - 1])
        files.append(lines[file_seperator[len(file_seperator) - 1]: len(lines)])
    for file in files:
        ret = parseFile(file, method_info, git_repo_location, work_dir)
        if ret is not None:
            old_file_relative_name_list.append(ret)
    with open(config.method_info_location, "w") as f:
        json.dump(method_info, f)
    return old_file_relative_name_list


def parseFile(file, method_info, git_repo_location, work_dir):
    extension = ["c", "cpp", "c++", "cc", "C"]
    info = {}
    info["oldFileName"] = file[0].split(" ")[2]
    info["newFileName"] = file[0].split(" ")[3][:-1]
    if (
            info["oldFileName"].split(".")[-1] not in extension
            or info["newFileName"].split(".")[-1] not in extension
    ):
        return None
    if (
            "test" in info["oldFileName"]
            or "test" in info["newFileName"]
            or "tst" in info["oldFileName"]
            or "tst" in info["newFileName"]
    ):
        return None
    pos = info["oldFileName"].find("/")
    old_file_relative_name = info["oldFileName"][pos + 1:]
    info["oldCommit"] = file[1].split(" ")[1].split("..")[0]
    info["newCommit"] = file[1].split(" ")[1].split("..")[1]
    old_name = info["oldCommit"] + "-" + info["oldFileName"].split("/")[-1]
    new_name = info["newCommit"] + "-" + info["newFileName"].split("/")[-1]
    info["add"] = []
    info["delete"] = []
    os.chdir(git_repo_location)
    os.system("git show " + info["oldCommit"] + " > " + work_dir + "temp/" + old_name)

    os.system("git show " + info["newCommit"] + " > " + work_dir + "temp/" + new_name)
    format_and_del_comment(work_dir + "temp/" + old_name)
    format_and_del_comment(work_dir + "temp/" + new_name)
    os.system("git diff -w " + work_dir + "temp/" + old_name + " " + work_dir + "temp/" + new_name + " > " + work_dir
              + "temp/" + info["oldCommit"] + "__split__" + new_name)
    with open(work_dir + "temp/" + info["oldCommit"] + "__split__" + new_name, "r") as f:
        file = f.readlines()
    add_line = 0
    delete_line = 0
    for line in file:
        if line.startswith("@@"):
            delete_line = int(line.split("-")[1].split(",")[0]) - 1
            add_line = int(line.split("+")[1].split(",")[0]) - 1
        elif line.startswith("+") and not line.startswith("+++"):
            add_line += 1
            info["add"].append(add_line)
        elif line.startswith("-") and not line.startswith("---"):
            delete_line += 1
            info["delete"].append(delete_line)
        else:
            add_line += 1
            delete_line += 1
    change_dict = {}
    change_dict["oldMethod"] = {}
    change_dict["newMethod"] = {}
    os.chdir(work_dir)
    os.system("./joern-parse " + work_dir + "temp/" + old_name)
    os.system("./joern --script metadata.sc --params cpgFile=cpg.bin")
    method_list = []
    with open("./method.json") as f:
        json_obj = json.load(f)
        for obj in json_obj:
            if "lineNumber" in obj.keys() and not obj["fullName"].endswith(":<global>"):
                if obj["lineNumber"] == obj["lineNumberEnd"] or obj["signature"] == "":
                    continue
                method_dict = {}
                method_dict["name"] = obj["signature"]
                method_dict["lineStart"] = obj["lineNumber"]
                method_dict["lineEnd"] = obj["lineNumberEnd"]
                method_list.append(method_dict)
                with open(
                        work_dir + "temp/" + old_name, "r", encoding=config.encoding_format
                ) as fp:
                    old_content = fp.readlines()
                if method_dict["lineStart"] in info["delete"]:
                    for i in range(
                            method_dict["lineStart"], method_dict["lineEnd"] + 1
                    ):
                        if i not in info["delete"]:
                            i_content = (
                                old_content[i - 1]
                                .replace(" ", "")
                                .replace("{", "")
                                .replace("}", "")
                                .replace("\t", "")
                                .replace("\n", "")
                            )
                            if i_content != "":
                                change_dict["oldMethod"][method_dict["name"]] = i
                                break
    delete_dict = {}
    for line in info["delete"]:
        for method in method_list:
            if method["lineStart"] <= line <= method["lineEnd"]:
                if method["name"] not in delete_dict.keys():
                    delete_dict[method["name"]] = [
                        method["lineStart"],
                        method["lineEnd"],
                    ]
                delete_dict[method["name"]].append(line)
    this_method_info_dict = {}
    this_method_info_dict["oldFile"] = old_name
    this_method_info_dict["deleteMethod"] = delete_dict
    os.system("rm cpg.bin")
    os.system("rm method.json")
    os.system("./joern-parse " + work_dir + "temp/" + new_name)
    os.system("./joern --script metadata.sc --params cpgFile=cpg.bin")
    method_list = []
    with open("./method.json") as f:
        json_obj = json.load(f)
        for obj in json_obj:
            if "lineNumber" in obj.keys() and not obj["fullName"].endswith(":<global>"):
                if obj["lineNumber"] == obj["lineNumberEnd"] or obj["signature"] == "":
                    continue
                method_dict = {}
                method_dict["name"] = obj["signature"]
                method_dict["lineStart"] = obj["lineNumber"]
                method_dict["lineEnd"] = obj["lineNumberEnd"]
                method_list.append(method_dict)
                with open(
                        work_dir + "temp/" + new_name, "r", encoding=config.encoding_format
                ) as fp:
                    new_content = fp.readlines()
                if method_dict["lineStart"] in info["add"]:
                    for i in range(
                            method_dict["lineStart"], method_dict["lineEnd"] + 1
                    ):
                        if i not in info["add"]:
                            i_content = (
                                new_content[i - 1]
                                .replace(" ", "")
                                .replace("{", "")
                                .replace("}", "")
                                .replace("\t", "")
                                .replace("\n", "")
                            )
                            if i_content != "":
                                change_dict["newMethod"][method_dict["name"]] = i
                                break
    add_dict = {}
    for line in info["add"]:
        for method in method_list:
            if method["lineStart"] <= line <= method["lineEnd"]:
                if method["name"] not in add_dict.keys():
                    add_dict[method["name"]] = [method["lineStart"], method["lineEnd"]]
                add_dict[method["name"]].append(line)
    this_method_info_dict["newFile"] = new_name
    this_method_info_dict["addMethod"] = add_dict
    this_method_info_dict["delete"] = info["delete"]
    this_method_info_dict["add"] = info["add"]
    new_old_map = {}
    old_new_map = {}
    delete_lines = info["delete"]
    add_lines = info["add"]
    delete = 1
    add = 1
    for i in range(1, 100000):
        while delete in delete_lines:
            delete += 1
        while add in add_lines:
            add += 1
        old_new_map[delete] = add
        new_old_map[add] = delete
        delete += 1
        add += 1
    change_method_map_dict = {}
    for key in change_dict["oldMethod"].keys():
        if key in this_method_info_dict["addMethod"]:
            continue
        for key1 in change_dict["newMethod"].keys():
            if (
                    old_new_map[change_dict["oldMethod"][key]]
                    == change_dict["newMethod"][key1]
            ):
                change_method_map_dict[key] = key1
    this_method_info_dict["change_method_map"] = change_method_map_dict
    for method in this_method_info_dict["addMethod"].keys():
        if method not in this_method_info_dict["deleteMethod"].keys():
            if this_method_info_dict["addMethod"][method][0] not in new_old_map.keys():
                if method in change_method_map_dict.values():
                    del this_method_info_dict["addMethod"][method][1:3]
                    continue
                if "pureAddMethod" not in this_method_info_dict.keys():
                    this_method_info_dict["pureAddMethod"] = []
                this_method_info_dict["pureAddMethod"].append(
                    {
                        method: [
                            this_method_info_dict["addMethod"][method][0],
                            this_method_info_dict["addMethod"][method][1],
                        ]
                    }
                )
                pass
            else:
                this_method_info_dict["deleteMethod"][method] = [
                    new_old_map[this_method_info_dict["addMethod"][method][0]]
                ]
        elif len(this_method_info_dict["addMethod"][method]) != 1:
            del this_method_info_dict["addMethod"][method][1]
    for method in this_method_info_dict["deleteMethod"].keys():
        if method not in this_method_info_dict["addMethod"].keys():
            if (
                    this_method_info_dict["deleteMethod"][method][0]
                    not in old_new_map.keys()
            ):
                if method in change_method_map_dict.keys():
                    del this_method_info_dict["deleteMethod"][method][1:3]
                    continue
                if "pureDeleteMethod" not in this_method_info_dict.keys():
                    this_method_info_dict["pureDeleteMethod"] = []
                this_method_info_dict["pureDeleteMethod"].append(
                    {
                        method: [
                            this_method_info_dict["deleteMethod"][method][0],
                            this_method_info_dict["deleteMethod"][method][1],
                        ]
                    }
                )
            else:
                this_method_info_dict["addMethod"][method] = [
                    old_new_map[this_method_info_dict["deleteMethod"][method][0]]
                ]
        elif len(this_method_info_dict["deleteMethod"][method]) != 1:
            del this_method_info_dict["deleteMethod"][method][1]
    os.system("rm cpg.bin")
    os.system("rm method.json")
    method_info.append(this_method_info_dict)
    return old_file_relative_name


def format_and_del_comment(src):
    with open(src, "r", encoding=config.encoding_format) as f:
        lines = f.readlines()
        i = 0
        while i < len(lines):
            if lines[i].endswith("\\\n"):
                temp = i
                while lines[i].endswith("\\\n"):
                    i += 1
                lines[temp] = lines[temp][:-2]
                for j in range(temp + 1, i):
                    lines[temp] += lines[j].rstrip()[:-1]
                    lines[j] = "\n"
                lines[temp] += lines[i]
                lines[i] = "\n"
            else:
                i += 1
    with open(src, "w", encoding=config.encoding_format) as f:
        f.writelines(lines)
    with open(src, "r", encoding=config.encoding_format) as f:
        file_contents = f.read()
    c_regex = re.compile(
        r'(?P<comment>//.*?$|[{}]+)|(?P<multilinecomment>/\*.*?\*/)|(?P<noncomment>\'(\\.|[^\\\'])*\'|"(\\.|[^\\"])*"|.[^/\'"]*)',
        re.DOTALL | re.MULTILINE,
    )
    file_contents = "".join(
        [
            c.group("noncomment")
            for c in c_regex.finditer(file_contents)
            if c.group("noncomment")
        ]
    )
    with open(src, "w", encoding=config.encoding_format) as f:
        f.write(file_contents)
    with open(src, "r", encoding=config.encoding_format) as f:
        lines = f.readlines()
        i = 0
        while i < len(lines):
            if (
                    lines[i].strip() == "\n"
                    or lines[i].strip() == "\r\n"
                    or lines[i].strip() == ""
                    or lines[i].strip().startswith("#")
            ):
                i += 1
            else:
                temp = i
                while (
                        i < len(lines)
                        and not lines[i].strip().endswith(";")
                        and not lines[i].strip().endswith("{")
                        and not lines[i].strip().endswith(")")
                        and not lines[i].strip().endswith("}")
                        and not lines[i].strip().endswith(":")
                        and not lines[i].strip().startswith("#")
                ):
                    i += 1
                if i < len(lines) and lines[i].strip().startswith("#"):
                    i -= 1
                if temp != i:
                    lines[temp] = lines[temp][:-1]
                for j in range(temp + 1, i + 1):
                    if j == len(lines):
                        break
                    lines[temp] += " "
                    lines[temp] += lines[j][:-1].strip()
                    lines[j] = "\n"
                if temp == i:
                    i += 1
    with open(src, "w", encoding=config.encoding_format) as f:
        f.writelines(lines)


def get_callgraph_sig(CVE_ID, commit_file_location, git_repo_location):
    suffix_list = ["c", "cc", "cxx", "cpp", "c++", "h"]
    doxygen_suffix_list = []
    for suffix in suffix_list:
        doxygen_suffix_list.append("_8" + suffix + ".xml")
    os.system("git config --global --add safe.directory " + git_repo_location)
    old_file_relative_name_list = readCommit(commit_file_location, git_repo_location, config.work_dir)
    with open("./old_file_relative_name_list.json", "w") as f:
        json.dump(old_file_relative_name_list, f)
    old_function_info = {}
    old_function_cnt = 0
    with open(config.method_info_location, "r") as f:
        file_list = json.load(f)
        for file in file_list:
            hyphen_pos = file["oldFile"].find("-")
            file_name = file["oldFile"][hyphen_pos + 1:]
            old_function_info[file_name] = {}
            for method_full_name in file["deleteMethod"].keys():
                if (method_full_name not in file["addMethod"].keys() and method_full_name not in file[
                    "change_method_map"].keys()):
                    continue
                method_name = method_full_name.split("(")[0].split(" ")[-2]
                if method_name in old_function_info[file_name].keys():
                    with open(config.error_log_file, "a") as f:
                        f.write(
                            "same function name in CVE:" + CVE_ID + ", function name is " + method_name + " and file name is" + file_name + "\n")
                        return
                if method_full_name in file["change_method_map"].keys():
                    old_function_info[file_name][method_name] = [file["deleteMethod"][method_full_name][0].__str__(),
                                                                 file["oldFile"] + "__split__" + file[
                                                                     "newFile"] + "__split__" + method_full_name + "__split__" +
                                                                 file["change_method_map"][method_full_name]]
                else:
                    old_function_info[file_name][method_name] = [file["deleteMethod"][method_full_name][0].__str__(),
                                                                 file["oldFile"] + "__split__" + file[
                                                                     "newFile"] + "__split__" + method_full_name]
                old_function_cnt += 1
            if "pureDeleteMethod" in file.keys():
                for pureDeleteMethod in file["pureDeleteMethod"]:
                    for method_full_name in pureDeleteMethod.keys():
                        method_name = method_full_name.split("(")[0].split(" ")[-2]
                        if method_name in old_function_info[file_name].keys():
                            with open(config.error_log_file, "a") as f:
                                f.write(
                                    "same function name in CVE:" + CVE_ID + ", function name is " + method_name + " and file name is" + file_name + "\n")
                                return
                        old_function_info[file_name][method_name] = [pureDeleteMethod[method_full_name][0].__str__(),
                                                                     "del__split__" + file[
                                                                         "oldFile"] + "__split__" + method_full_name]
                        old_function_cnt += 1
    commit_hash = commit_file_location.split("-")[-1].split(".")[0]
    os.chdir(git_repo_location)
    os.system("git reset --hard " + commit_hash + "~1")
    min_dir = ""
    if len(old_file_relative_name_list) == 1:
        pos = old_file_relative_name_list[0].rfind("/")
        min_dir = old_file_relative_name_list[0][:pos + 1]
    else:
        min_dir = LCP(old_file_relative_name_list)
        pos = min_dir.rfind("/")
        min_dir = min_dir[:pos + 1]
    min_dir = "/" + min_dir
    scan_dir = findLargestDir(git_repo_location, min_dir, suffix_list)
    scan_dir_list = []
    if scan_dir == config.warning_info:
        for old_file_relative_name in old_file_relative_name_list:
            pos = old_file_relative_name.rfind("/")
            scan_dir_list.append(git_repo_location + "/" + old_file_relative_name[:pos + 1])
        scan_dir_list = list(set(scan_dir_list))
    else:
        scan_dir_list.append(scan_dir)
    if not modify_doxyfile(scan_dir_list, git_repo_location):
        with open(config.error_log_file, "a") as f:
            f.write("same file name in CVE:" + CVE_ID + "\n")
            return
    os.chdir(git_repo_location)
    os.system("rm -rf codeclone")
    os.system("rm -rf xml")
    for old_file_relative_name in old_file_relative_name_list:
        format_and_del_comment(git_repo_location + "/" + old_file_relative_name)
    if not run_command_with_timeout("doxygen Doxyfile > /dev/null 2>&1", config.subprocess_exec_max_time_sec):
        with open(config.timeout_repo_list_file, "r") as f:
            timeout_repo_list = json.load(f)
            if git_repo_location not in timeout_repo_list:
                timeout_repo_list.append(git_repo_location)
        with open(config.timeout_repo_list_file, "w") as f:
            json.dump(timeout_repo_list, f)
        with open(config.error_log_file, "a") as f:
            f.write("doxygen operation in CVE:" + CVE_ID + " timeout \n")
        return
    call_graph_sig_direction_no_define(git_repo_location, doxygen_suffix_list, old_function_info, old_function_cnt,
                                       CVE_ID)


def call_graph_sig_direction_no_define(git_repo_location, doxygen_suffix_list, old_function_info, old_function_cnt,
                                       CVE_ID):
    old_function_refid_list = []
    old_function_doxygen_cnt = 0
    refid_to_signature_dict = {}
    function_refid_list = []
    define_refid_list = []
    implement_dict = {}
    implemented_dict = {}
    function_location_refid_dict = {}
    function_refid_location_dict = {}
    if not os.path.exists(git_repo_location + "/xml/index.xml"):
        with open(config.error_log_file, "a") as f:
            f.write("Can't generate index.xml in CVE:" + CVE_ID + "\n")
        return
    index_flag = False
    with open(git_repo_location + "/xml/index.xml", "rb") as f:
        content = f.read().decode(config.encoding_format)
    try:
        tree = minidom.parseString(content)
    except Exception as E:
        index_flag = True
        with open(config.error_log_file, "a") as f:
            f.write("Error when parsing index.xml in CVE:" + CVE_ID + "\n")
    if index_flag:
        return
    collection = tree.documentElement
    for compound in tree.getElementsByTagName("compound"):
        if compound.getAttribute("kind") == "file":
            compound_name = compound.getElementsByTagName("name")[0]
            file_name = compound_name.childNodes[0].data
            members = compound.getElementsByTagName("member")
            for member in members:
                if member.getAttribute("kind") == "function":
                    refid = member.getAttribute("refid")
                    function_refid_list.append(refid)
                elif member.getAttribute("kind") == "define":
                    refid = member.getAttribute("refid")
                    define_refid_list.append(refid)
    function_referenced_dict = {}
    define_referenced_dict = {}
    function_reference_dict = {}
    define_reference_dict = {}
    xml_file_list = os.listdir(git_repo_location + "/xml")
    for xml_file in xml_file_list:
        flag = False
        for suffix in doxygen_suffix_list:
            if xml_file.endswith(suffix):
                flag = True
        if flag:
            with open(git_repo_location + "/xml/" + xml_file, "rb") as f:
                content = f.read().decode(config.encoding_format)
            parse_flag = False
            try:
                tree = minidom.parseString(content)
            except Exception as E:
                parse_flag = True
                with open(config.error_log_file, "a") as f:
                    f.write("Error when parsing " + xml_file + " in CVE:" + CVE_ID + "\n")
            if parse_flag:
                continue
            current_file_name = \
                tree.getElementsByTagName("compounddef")[0].getElementsByTagName("compoundname")[0].childNodes[0].data
            collection = tree.documentElement
            for member in tree.getElementsByTagName("memberdef"):
                if member.getAttribute("kind") == "function":
                    member_id = member.getAttribute("id")
                    location = member.getElementsByTagName("location")[0]
                    name = member.getElementsByTagName("name")[0].childNodes[0].data
                    if (location.hasAttribute("bodyfile") and location.hasAttribute(
                            "bodystart") and not location.hasAttribute("declfile") and not location.hasAttribute(
                        "declline")) or (location.hasAttribute("declfile") and location.hasAttribute(
                        "bodyfile") and location.getAttribute("declfile") == location.getAttribute("bodyfile")):
                        function_location_refid_dict[
                            location.getAttribute("bodyfile") + "__split__" + location.getAttribute(
                                "bodystart")] = member_id
                        function_refid_location_dict[member_id] = location.getAttribute(
                            "bodyfile") + "__split__" + location.getAttribute("bodystart")
                    for file_name in old_function_info.keys():
                        if current_file_name == file_name:
                            for function_name in old_function_info[file_name].keys():
                                if function_name == name:
                                    if location.getAttribute("bodystart") == \
                                            old_function_info[file_name][function_name][0]:
                                        old_function_refid_list.append(member_id)
                                        refid_to_signature_dict[member_id] = \
                                            old_function_info[file_name][function_name][1]
                                        old_function_doxygen_cnt += 1
                    referenceds = member.getElementsByTagName("referencedby")
                    if len(referenceds) != 0:
                        if member_id not in function_referenced_dict.keys():
                            function_referenced_dict[member_id] = set()
                        for referenced in referenceds:
                            ref_id = referenced.getAttribute("refid")
                            if ref_id in function_refid_list or ref_id in define_refid_list:
                                function_referenced_dict[member_id].add(ref_id)
                                if ref_id in function_refid_list:
                                    if ref_id not in function_reference_dict.keys():
                                        function_reference_dict[ref_id] = set()
                                    function_reference_dict[ref_id].add(member_id)
                                elif ref_id in define_refid_list:
                                    if ref_id not in define_reference_dict.keys():
                                        define_reference_dict[ref_id] = set()
                                    define_reference_dict[ref_id].add(member_id)
                    references = member.getElementsByTagName("references")
                    for reference in references:
                        ref_id = reference.getAttribute("refid")
                        if member_id not in function_reference_dict.keys():
                            function_reference_dict[member_id] = set()
                        function_reference_dict[member_id].add(ref_id)
                        if ref_id in function_refid_list:
                            if ref_id not in function_referenced_dict.keys():
                                function_referenced_dict[ref_id] = set()
                            function_referenced_dict[ref_id].add(member_id)
                        elif ref_id in define_refid_list:
                            if ref_id not in define_referenced_dict.keys():
                                define_referenced_dict[ref_id] = set()
                            define_referenced_dict[ref_id].add(member_id)
                elif member.getAttribute("kind") == "define":
                    member_id = member.getAttribute("id")
                    initializer = member.getElementsByTagName("initializer")
                    if len(initializer) != 0:
                        init = initializer[0]
                        references = init.getElementsByTagName("ref")
                        for reference in references:
                            ref_id = reference.getAttribute("refid")
                            if member_id not in define_reference_dict:
                                define_reference_dict[member_id] = set()
                            define_reference_dict[member_id].add(ref_id)
                            if ref_id in function_refid_list:
                                if ref_id not in function_referenced_dict.keys():
                                    function_referenced_dict[ref_id] = set()
                                function_referenced_dict[ref_id].add(member_id)
                            elif ref_id in define_refid_list:
                                if ref_id not in define_referenced_dict.keys():
                                    define_referenced_dict[ref_id] = set()
                                define_referenced_dict[ref_id].add(member_id)
    xml_file_list = os.listdir(git_repo_location + "/xml")
    for xml_file in xml_file_list:
        flag = False
        for suffix in doxygen_suffix_list:
            if xml_file.endswith(suffix):
                flag = True
        if flag:
            with open(git_repo_location + "/xml/" + xml_file, "rb") as f:
                content = f.read().decode(config.encoding_format)
            parse_flag = False
            try:
                tree = minidom.parseString(content)
            except Exception as E:
                parse_flag = True
            if parse_flag:
                continue
            current_file_name = \
                tree.getElementsByTagName("compounddef")[0].getElementsByTagName("compoundname")[0].childNodes[0].data
            collection = tree.documentElement
            for member in tree.getElementsByTagName("memberdef"):
                if member.getAttribute("kind") == "function":
                    location = member.getElementsByTagName("location")[0]
                    if location.hasAttribute("declfile") and location.hasAttribute(
                            "declline") and location.hasAttribute("bodyfile") and location.hasAttribute(
                        "bodystart") and location.getAttribute("declfile") != location.getAttribute("bodyfile"):
                        member_id = member.getAttribute("id")
                        if location.getAttribute("bodyfile") + "__split__" + location.getAttribute(
                                "bodystart") in function_location_refid_dict.keys():
                            implemented_refid = function_location_refid_dict[
                                location.getAttribute("bodyfile") + "__split__" + location.getAttribute("bodystart")]
                            implement_dict[member_id] = implemented_refid
                            implemented_dict[implemented_refid] = member_id
    if old_function_doxygen_cnt != old_function_cnt:
        with open(config.error_log_file, "a") as f:
            f.write("Inconsistency between doxygen and joern in CVE:" + CVE_ID + "\n")
            return
    result_dict = {}
    vertices_set = set()
    edges_list = []
    modified_vertices_set = set()
    for old_function in old_function_refid_list:
        visited = set()
        visited.add(old_function)
        vertices_set.add(refid_to_signature_dict[old_function])
        modified_vertices_set.add(refid_to_signature_dict[old_function])
        queue1 = Queue(maxsize=0)
        queue1.put([old_function, old_function, 0])
        while not queue1.empty():
            cur = queue1.get()
            cnt = cur[2]
            ref_id = cur[1]
            last_ref_id = cur[0]
            if cnt > config.jump_threshold:
                continue
            if ref_id in old_function_refid_list and ref_id != old_function:
                continue
            if ref_id in function_refid_list:
                if ref_id in function_reference_dict.keys():
                    for callee in function_reference_dict[ref_id]:
                        if callee not in visited:
                            if callee in implement_dict.keys():
                                callee = implement_dict[callee]
                            visited.add(callee)
                            if last_ref_id in old_function_refid_list:
                                ref_vertices = refid_to_signature_dict[last_ref_id]
                            else:
                                ref_vertices = function_refid_location_dict[last_ref_id]
                            if callee in old_function_refid_list:
                                if cnt + 1 > config.jump_threshold:
                                    continue
                                queue1.put([callee, callee, cnt + 1])
                                vertices_set.add(refid_to_signature_dict[callee])
                                edges_list.append([ref_vertices, refid_to_signature_dict[callee]])
                            elif callee in function_refid_list:
                                if cnt + 1 > config.jump_threshold:
                                    continue
                                queue1.put([callee, callee, cnt + 1])
                                vertices_set.add(function_refid_location_dict[callee])
                                edges_list.append([ref_vertices, function_refid_location_dict[callee]])
                            elif callee in define_refid_list:
                                queue1.put([last_ref_id, callee, cnt])
            elif ref_id in define_refid_list:
                if ref_id in define_reference_dict.keys():
                    for callee in define_reference_dict[ref_id]:
                        if callee not in visited:
                            if callee in implement_dict.keys():
                                callee = implement_dict[callee]
                            visited.add(callee)
                            if last_ref_id in old_function_refid_list:
                                ref_vertices = refid_to_signature_dict[last_ref_id]
                            else:
                                ref_vertices = function_refid_location_dict[last_ref_id]
                            if callee in old_function_refid_list:
                                if cnt + 1 > config.jump_threshold:
                                    continue
                                queue1.put([callee, callee, cnt + 1])
                                vertices_set.add(refid_to_signature_dict[callee])
                                edges_list.append([ref_vertices, refid_to_signature_dict[callee]])
                            elif callee in function_refid_list:
                                if cnt + 1 > config.jump_threshold:
                                    continue
                                queue1.put([callee, callee, cnt + 1])
                                vertices_set.add(function_refid_location_dict[callee])
                                edges_list.append([ref_vertices, function_refid_location_dict[callee]])
                            elif callee in define_refid_list:
                                queue1.put([last_ref_id, callee, cnt])
    for old_function in old_function_refid_list:
        visited = set()
        visited.add(old_function)
        vertices_set.add(refid_to_signature_dict[old_function])
        modified_vertices_set.add(refid_to_signature_dict[old_function])
        queue1 = Queue(maxsize=0)
        queue1.put([old_function, old_function, 0])
        while not queue1.empty():
            cur = queue1.get()
            cnt = cur[2]
            ref_id = cur[1]
            last_ref_id = cur[0]
            if cnt > config.jump_threshold:
                continue
            if ref_id in old_function_refid_list and ref_id != old_function:
                continue
            if ref_id in function_refid_list:
                if ref_id in function_referenced_dict.keys():
                    for caller in function_referenced_dict[ref_id]:
                        if cnt + 1 > config.jump_threshold:
                            continue
                        if caller not in visited:
                            if caller in implement_dict.keys():
                                caller = implement_dict[caller]
                            visited.add(caller)
                            if last_ref_id in old_function_refid_list:
                                ref_vertices = refid_to_signature_dict[last_ref_id]
                            else:
                                ref_vertices = function_refid_location_dict[last_ref_id]
                            if caller in old_function_refid_list:
                                queue1.put([caller, caller, cnt + 1])
                                vertices_set.add(refid_to_signature_dict[caller])
                                edges_list.append([refid_to_signature_dict[caller], ref_vertices])
                            elif caller in function_refid_list:
                                queue1.put([caller, caller, cnt + 1])
                                vertices_set.add(function_refid_location_dict[caller])
                                edges_list.append([function_refid_location_dict[caller], ref_vertices])
                            elif caller in define_refid_list:
                                queue1.put([last_ref_id, caller, cnt + 1])
            elif ref_id in define_refid_list:
                if ref_id in define_referenced_dict.keys():
                    for caller in define_referenced_dict[ref_id]:
                        if caller not in visited:
                            if caller in implement_dict.keys():
                                caller = implement_dict[caller]
                            visited.add(caller)
                            if last_ref_id in old_function_refid_list:
                                ref_vertices = refid_to_signature_dict[last_ref_id]
                            else:
                                ref_vertices = function_refid_location_dict[last_ref_id]
                            if caller in old_function_refid_list:
                                queue1.put([caller, caller, cnt])
                                vertices_set.add(refid_to_signature_dict[caller])
                                edges_list.append([refid_to_signature_dict[caller], ref_vertices])
                            elif caller in function_refid_list:
                                queue1.put([caller, caller, cnt])
                                vertices_set.add(function_refid_location_dict[caller])
                                edges_list.append([function_refid_location_dict[caller], ref_vertices])
                            elif caller in define_refid_list:
                                queue1.put([last_ref_id, caller, cnt])
    write_dict = {}
    write_dict["vertices"] = list(vertices_set)
    write_dict["edges"] = list(set(tuple(sublist) for sublist in edges_list))
    write_dict["modified_function_vertices"] = list(modified_vertices_set)
    with open(config.no_define_location_prefix + CVE_ID + ".json", "w") as f:
        json.dump(write_dict, f)


def run_command_with_timeout(cmd, timeout_sec):
    proc = subprocess.Popen(cmd, shell=True)
    start_time = time.time()
    while True:
        if proc.poll() is not None:
            return True
        elapsed_time = time.time() - start_time
        if elapsed_time > timeout_sec:
            proc.kill()
            return False
        time.sleep(config.subprocess_exam_time_sec)


def LCP(old_file_relative_name_list):
    prefix = old_file_relative_name_list[0]
    for i in range(1, len(old_file_relative_name_list)):
        prefix = lcp(prefix, old_file_relative_name_list[i])
        if not prefix:
            break
    return prefix


def lcp(str1, str2):
    length, index = min(len(str1), len(str2)), 0
    while index < length and str1[index] == str2[index]:
        index += 1
    return str1[:index]


def findLargestDir(git_repo_location, min_dir, suffix_list):
    split_list = min_dir.split("/")
    length = len(split_list)
    for i in range(length, 0, -1):
        temp_dir = "/".join(split_list[:i])
        count = 0
        for _, _, files in os.walk(git_repo_location + temp_dir):
            for file in files:
                for suffix in suffix_list:
                    if file.endswith(suffix):
                        count += 1
        if count > config.file_num_threshold:
            if i == length:
                return config.warning_info
            else:
                return git_repo_location + "/".join(split_list[:i + 1])
    return git_repo_location


def pagerank_algorithm(CVEID, nodes, edges, modified_function_vertices):
    nodes_lst = nodes
    edges_lst = edges
    graph = nx.DiGraph()

    graph.add_nodes_from(nodes_lst)
    graph.add_edges_from(edges_lst)

    pagerank_scores = nx.pagerank(graph)

    write_dict = {}
    for nodeid, score in pagerank_scores.items():
        if nodeid in modified_function_vertices:
            write_dict[nodeid] = score
    with open(config.pagerank_location_prefix + CVEID + ".json", "w") as f:
        json.dump(write_dict, f)


def pageranMain(CVE_ID, commit_file_location, git_repo_location):
    get_callgraph_sig(CVE_ID, commit_file_location, git_repo_location)
    with open(config.no_define_location_prefix + CVE_ID + ".json", "r") as f:
        json_obj = json.load(f)
    nodes = json_obj["vertices"]
    edges = json_obj["edges"]
    modified_function_vertices = json_obj["modified_function_vertices"]
    pagerank_algorithm(CVE_ID, nodes, edges, modified_function_vertices)

if __name__ == "__main__":
    CVE_ID = sys.argv[1]
    commit_file_location = sys.argv[2]
    git_repo_location = sys.argv[3]
    get_callgraph_sig(CVE_ID, commit_file_location, git_repo_location)
    with open(config.no_define_location_prefix + CVE_ID + ".json", "r") as f:
        json_obj = json.load(f)
    nodes = json_obj["vertices"]
    edges = json_obj["edges"]
    modified_function_vertices = json_obj["modified_function_vertices"]
    pagerank_algorithm(CVE_ID, nodes, edges, modified_function_vertices)
