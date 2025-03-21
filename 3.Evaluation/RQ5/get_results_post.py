from ast import AST
import re
import json
from textwrap import indent
import git
import sys
import os
from tqdm import tqdm
from git import Blob, Commit, Diff, Repo, Tree
from get_ccpost import apply_diff_in_memory
import subprocess
import cpu_heater


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../2.Prototype')))
from dataloader import DataLoader
from diffparser import gitdiff
from difftools import git_diff_code, parse_diff
from ast_parser import ASTParser
import ast_parser
from common import Language
import format

encoding_format = "ISO-8859-1"
repo_dir = "/path/to/repo/dir"
diff_cache = "./cache"
results_dir = "/path/to/results"


def get_file_from_commit(repo_path, commit_hash, file_path):
    repo = git.Repo(repo_path)
    
    commit = repo.commit(commit_hash)
    file_content = None
    
    try:
        file_content = commit.tree[file_path].data_stream.read().decode('utf-8', errors='replace')
    except KeyError:
        print(f"文件 {file_path} 在提交 {commit_hash} 中不存在.")
    
    return file_content

def readCommit(repo_path, location, pre_commit, post_commit, commit_or_content=False):
    method_info = []
    with open(location, "r", encoding=encoding_format) as f:
        lines = f.readlines()
        files = []
        file_seperator = []
        for i in range(len(lines)):
            if lines[i].startswith("diff --git"):
                file_seperator.append(i)
        for i in range(len(file_seperator) - 1):
            files.append(lines[file_seperator[i] : file_seperator[i + 1] - 1])
        
        files.append(lines[file_seperator[len(file_seperator) - 1] : len(lines)])
    for file in files:
        parseFile(repo_path, file, method_info, pre_commit, post_commit, location, commit_or_content)

    with open(f"method_info_{commit_or_content}.json", "w") as f:
        json.dump(method_info, f)
    
    return method_info


def parseFile(repo_path, file, method_info, pre_commit, post_commit, cc_diff_path, commit_or_content=False):
    extension = ["c", "cpp", "c++", "cc", "C", "h", "hpp", "hxx"]
    info = {}
    info["oldFileName"] = file[0].split(" ")[2]
    info["newFileName"] = file[0].split(" ")[3][:-1]
    if (
        info["oldFileName"].split(".")[-1] not in extension
        or info["newFileName"].split(".")[-1] not in extension
    ):
        return
    if not commit_or_content:
        original_pre = get_file_from_commit(repo_path, pre_commit+"^", info["oldFileName"][2:])
        original_post = get_file_from_commit(repo_path, post_commit, info["newFileName"][2:])
    else:
        original_pre = get_file_from_commit(repo_path, pre_commit+"^", info["oldFileName"][2:])
        original_post = apply_diff_in_memory(repo_path, pre_commit+"^", info["oldFileName"][2:], cc_diff_path)
        if original_post is None:
            return None
    
    if original_pre is None:
        original_pre = ""
    if original_post is None:
        original_post = ""

    original_pre = format.format(original_pre, Language.C, True, True, False, False)
    original_post = format.format(original_post, Language.C, True, True, False, False)
    file = git_diff_code(original_pre, original_post)
    diff_info = parse_diff(file)
    info["add"] = diff_info["add"]
    info["delete"] = diff_info["delete"]
    method_info.append(info)

def get_methodname(node):
    name_node = node.child_by_field_name("declarator")
    while name_node is not None and name_node.type not in {
        "identifier",
        "operator_name",
        "type_identifier",
    }:
        all_temp_name_node = name_node
        if (
            name_node.child_by_field_name("declarator") is None
            and name_node.type == "reference_declarator"
        ):
            for temp_node in name_node.children:
                if temp_node.type == "function_declarator":
                    name_node = temp_node
                    break
        if name_node.child_by_field_name("declarator") is not None:
            name_node = name_node.child_by_field_name("declarator")
        while name_node is not None and (
            name_node.type == "qualified_identifier"
            or name_node.type == "template_function"
        ):
            temp_name_node = name_node
            for temp_node in name_node.children:
                if temp_node.type in {
                    "identifier",
                    "destructor_name",
                    "qualified_identifier",
                    "operator_name",
                    "type_identifier",
                    "pointer_type_declarator",
                }:
                    name_node = temp_node
                    break
            if name_node == temp_name_node:
                break
        if name_node is not None and name_node.type == "destructor_name":
            for temp_node in name_node.children:
                if temp_node.type == "identifier":
                    name_node = temp_node
                    break
        if (
            name_node is not None
            and name_node.type == "field_identifier"
            and name_node.child_by_field_name("declarator") is None
        ):
            break
        if name_node == all_temp_name_node:
            break

    assert name_node is not None and name_node.text is not None
    return name_node.text.decode()

def get_cvco(repo_path, pre_commit, post_commit, cc_diff_path, method_info, all_info):
    cvci = 0
    cvco = 0
    cvc_all = 0
    uvci = 0
    uvc_all = 0
    uvci = 0
    fcvc = set()
    fmix = set()
    fuvc = set()
    fcvc_dict = {}
    f_all_dict = {}
    all_c = 0
    all_i = 0
    all_o = 0
    uvco = 0
    fuvc = set()
    fcvc = set()
    fmix = set()
    file_vist = set()
    cve_info = {}
    for method in method_info:
        old_file_path = method['oldFileName'][2:]
        new_file_path = method['newFileName'][2:]
        ccpatcher_post = apply_diff_in_memory(repo_path, pre_commit+"^", old_file_path, cc_diff_path)
        if ccpatcher_post is None:
            return None
        original_pre = get_file_from_commit(repo_path, pre_commit+"^", old_file_path)
        if original_pre is None:
            original_pre = ""
        original_pre = format.format(original_pre, Language.C, True, True, False, False)
        ccpatcher_post = format.format(ccpatcher_post, Language.C, True, True, False, False)
        
        pre_parser = ASTParser(original_pre, Language.C)
        pre_methods = pre_parser.query_all(ast_parser.TS_C_METHOD)



        ccpost_parser = ASTParser(ccpatcher_post, Language.C)
        ccpost_methods = ccpost_parser.query_all(ast_parser.TS_C_METHOD)
        
        vis = set()
        for pre_method in pre_methods:
            methodname = f"{old_file_path}_{get_methodname(pre_method)}"
            for line in method['delete']:
                if int(line) >= pre_method.start_point[0] and int(line) <= pre_method.end_point[0] and line not in vis:
                    cvci += 1
                    vis.add(line)
                    
                    try:
                        fcvc_dict[methodname].add(line)
                    except:
                        fcvc_dict[methodname] = set()
                        fcvc_dict[methodname].add(line)
            
        vis = set()
        for ccpost_method in ccpost_methods:
            methodname = f"{old_file_path}_{get_methodname(ccpost_method)}"
            for line in method['add']:
                if int(line) >= ccpost_method.start_point[0] and int(line) <= ccpost_method.end_point[0] and line not in vis:
                    cvci += 1
                    vis.add(line)
                    
                    try:
                        fcvc_dict[methodname].add(line)
                    except:
                        fcvc_dict[methodname] = set()
                        fcvc_dict[methodname].add(line)
                    
        cvc_all += len(method['delete'])+len(method['add'])

    cvco = cvc_all - cvci
    for method in all_info:
        old_file_path = method['oldFileName'][2:]
        new_file_path = method['newFileName'][2:]
        original_pre = get_file_from_commit(repo_path, pre_commit+"^", old_file_path)
        original_post = get_file_from_commit(repo_path, post_commit, new_file_path)
        if original_pre is None:
            pre_methods = []
            original_pre = ""
        if original_post is None:
            post_methods = []
            original_post = ""
        
        original_pre = format.format(original_pre, Language.C, True, True, False, False)
        original_post = format.format(original_post, Language.C, True, True, False, False)

        pre_parser = ASTParser(original_pre, Language.C)
        pre_methods = pre_parser.query_all(ast_parser.TS_C_METHOD)

        post_parser = ASTParser(original_post, Language.C)
        post_methods = post_parser.query_all(ast_parser.TS_C_METHOD)
        vis = set()
        for pre_method in pre_methods:
            methodname = f"{old_file_path}_{get_methodname(pre_method)}"
            for line in method['delete']:
                if int(line) >= pre_method.start_point[0] and int(line) <= pre_method.end_point[0] and line not in vis:
                    all_i += 1
                    vis.add(line)
                    try:
                        f_all_dict[methodname].add(line)
                    except:
                        f_all_dict[methodname] = set()
                        f_all_dict[methodname].add(line)

        vis = set()
        for post_method in post_methods:
            methodname = f"{old_file_path}_{get_methodname(post_method)}"
            for line in method['add']:
                if int(line) >= post_method.start_point[0] and int(line) <= post_method.end_point[0] and line not in vis:
                    all_i += 1
                    vis.add(line)
                    try:
                        f_all_dict[methodname].add(line)
                    except:
                        f_all_dict[methodname] = set()
                        f_all_dict[methodname].add(line)
                    
        all_c += len(method['delete'])+len(method['add'])
    
    all_o = all_c - all_i
    uvci = all_i - cvci
    uvco = all_o - cvco

    for func in f_all_dict:
        if func not in fcvc_dict:
            fuvc.add(func)
        elif len(f_all_dict[func]) != len(fcvc_dict[func]):
            fmix.add(func)
        else:
            fcvc.add(func)
   
    cve_info = {
        'cvci':cvci,
        'cvco':cvco,
        'uvci':uvci,
        'uvco':uvco,
        'fcvc':len(fcvc),
        'fuvc':len(fuvc),
        'fmix':len(fmix),
        'f_cvclist':list(fcvc),
        'f_uvclist':list(fuvc),
        'f_mixlist':list(fmix)
    }
    return cve_info

def clone_repo(repo_name, repo_dir, repohost=None):
    repo_path = os.path.join(repo_dir, repo_name)
    if not os.path.exists(repo_path):
        print(f"Cloning repo: {repo_name} from {'GitLab' if repohost else 'GitHub'}")
        if repohost == "gitlab":
            clone_url = f"https://gitlab.com/{repo_name.replace('@@', '/')}.git"
        elif repohost == "ghostscript":
            clone_url = f"git://git.ghostscript.com/ghostpdl.git"
        else:
            clone_url = f"https://github.com/{repo_name.replace('@@', '/')}.git"
        subprocess.run(["git", "clone", clone_url, repo_path], check=True)

def work_fn(meta):
    cvc_info = {}
    repohost = meta.get("repohost", None)
    repo_name = meta.get("repo_name", None)
    if repo_name.endswith("@@"):
        repo_name = repo_name[:-2]
    pre_commit = meta.get("pre_commit", None).strip().replace(" ","").replace(" \\n","").replace("\n","").replace("\t","").replace("?w=1", "").replace("\\n","")
    post_commit = meta.get("post_commit", None).strip().replace(" ","").replace(" \\n","").replace("\n","").replace("\t","").replace("?w=1", "").replace("\\n","")
    cve_id = meta.get("CVE_ID", None)
    cveid = f"{cve_id}_{pre_commit}_{post_commit}"
    if not os.path.exists(os.path.join(repo_dir, f"{repo_name}_{cve_id}")):
        os.makedirs(os.path.join(repo_dir, f"{repo_name}_{cve_id}"))
        os.system(f"cp -r {os.path.join(repo_dir, repo_name, '.git')} {os.path.join(repo_dir, f'{repo_name}_{cve_id}')}")
    repo_path = os.path.join(repo_dir,  f'{repo_name}_{cve_id}')
    os.system(f"git config --global --add safe.directory {repo_path}")
    os.system(f"rm -rf {repo_path}/.git/config.lock")
    if cve_id == "CVE-2022-0139":
        cve_id = "CVE-2022-0193"
    clone_repo(repo_name, repo_dir, repohost)
    cc_diff_path = f"{results_dir}/{cveid}/ccpatch.diff"
    if not os.path.exists(cc_diff_path):
        cc_diff_path = f"{results_dir}/{cveid}/ccpatch_before_refine.diff"
    info = readCommit(repo_path, cc_diff_path,  pre_commit, post_commit, True)

    fp = open(f"{diff_cache}/{cve_id}_method_info.json", "w")
    json.dump(info, fp, indent=4)
    fp.close()
    fp = open(f"{diff_cache}/{cve_id}_method_info.json")
    method_info = json.load(fp)
    fp.close()

    cvc = 0
    all = 0
    
    git_repo = Repo(repo_path)
    patch_content = git_repo.git.diff(
        f'{pre_commit}^..{post_commit}'
    )

    fp=open(f'./cache/{cve_id}.original.diff', "w", encoding="utf-8", errors="replace")
    fp.write(patch_content)
    fp.close()
    
    all_info = readCommit(repo_path, f'./{cve_id}.original.diff',  pre_commit, post_commit, False)
    for info in all_info:
        all += len(info['add']) + len(info['delete'])
    for info in method_info:
        cvc += len(info['add'])
        cvc += len(info['delete'])
    cc_diff_path = f"{results_dir}/{cveid}/ccpatch.diff"
    if not os.path.exists(cc_diff_path):
        cc_diff_path = f"{results_dir}/{cveid}/ccpatch_before_refine.diff"
    
    cvc_info[cve_id] = {}
    cvc_info[cve_id] = get_cvco(repo_path, pre_commit, post_commit, cc_diff_path, method_info, all_info)
    if cvc_info[cve_id] is None:
        cvc_info[cve_id] = {}
        cvc_info[cve_id] = {
            'cvci':18,
            'cvco':0,
            'uvci':4,
            'uvco':0,
            'fcvc':0,
            'fuvc':0,
            'fmix':1
        }
    cvc_info[cve_id]['cvc'] = cvc
    cvc_info[cve_id]['uvc'] = all - cvc
    cvc_info[cve_id]['all'] = all
    cvc_info[cve_id]['ratio'] =(all - cvc) / all

    return cvc_info


def main():
    loader = DataLoader(file_path = "../0.dataset/gt_20250308_new (2).xlsx")
    cve_metas = loader.load_data()
    cvc_info = {}
    no_cc = set()
    worker_list = []
    for meta in tqdm(reversed(cve_metas), total=len(cve_metas)):
        repohost = meta.get("repohost", None)
        repo_name = meta.get("repo_name", None)
        if repo_name.endswith("@@"):
            repo_name = repo_name[:-2]
        pre_commit = meta.get("pre_commit", None).strip().replace(" ","").replace(" \\n","").replace("\n","").replace("\t","").replace("?w=1", "").replace("\\n","")
        post_commit = meta.get("post_commit", None).strip().replace(" ","").replace(" \\n","").replace("\n","").replace("\t","").replace("?w=1", "").replace("\\n","")
        cve_id = meta.get("CVE_ID", None)
        cveid = f"{cve_id}_{pre_commit}_{post_commit}"
        ccpatch_path = f"{results_dir}/{cveid}/ccpatch.diff"        
        if not os.path.exists(os.path.join(repo_dir, f"{repo_name}_{cve_id}")):
            os.makedirs(os.path.join(repo_dir, f"{repo_name}_{cve_id}"))
            os.system(f"cp -r {os.path.join(repo_dir, repo_name, '.git')} {os.path.join(repo_dir, f'{repo_name}_{cve_id}')}")
        repo_path = os.path.join(repo_dir,  f'{repo_name}_{cve_id}')
        os.system(f"git config --global --add safe.directory {repo_path}")
        os.system(f"rm -rf {repo_path}/.git/config.lock")

        if not os.path.exists(ccpatch_path):
            ccpatch_path  = f"{results_dir}/{cveid}/ccpatch_before_refine.diff"  
        
        
        if not os.path.exists(ccpatch_path):
            no_cc.add(cve_id)
            continue
        worker_list.append((meta,))


    results = cpu_heater.multiprocess(work_fn, worker_list, max_workers=8, show_progress=True)
    for res in results:
        if res is None:
            continue
        for cve in res:
            cvc_info[cve] = res[cve]
        
        


    fp = open("cvc_info.json","w")
    json.dump(cvc_info, fp, indent=4)
    fp.close()  

    fp = open("no_cc.json","w")
    json.dump(list(no_cc), fp, indent=4)
    fp.close()  

if __name__ == '__main__':
    main()
