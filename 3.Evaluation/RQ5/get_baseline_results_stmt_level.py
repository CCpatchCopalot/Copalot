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
from difftools import git_diff_code, parse_diff


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../2.Prototype')))
from dataloader import DataLoader
from diffparser import gitdiff
from ast_parser import ASTParser
import ast_parser
from common import Language
import format

encoding_format = "ISO-8859-1"
repo_dir = "/path/to/repo/dir"
diff_cache = "./cache"
results_dir = "/path/to/results"
ccpatch_dir = "../../1.Empirical/Benchmark/ccpatch"

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


def get_cvco(repo_path, pre_commit, post_commit, cc_diff_path, res_diff_path, method_info, all_info):
    cc_patch_stmt_i = []
    cc_patch_stmt_o = []
    all_patch_stmt_i = []
    all_patch_stmt_o = []
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
        
        for pre_method in pre_methods:
            for line in method['delete']:
                if int(line)>= pre_method.start_point[0] and int(line) <= pre_method.end_point[0] :
                    cc_patch_stmt_i.append(method['delete'][line])
            
        for ccpost_method in ccpost_methods:
            for line in method['add']:
                if int(line)>= ccpost_method.start_point[0] and int(line) <= ccpost_method.end_point[0] :
                    cc_patch_stmt_i.append(method['add'][line])

        for line in method['delete']:
            if method['delete'][line] not in cc_patch_stmt_i:
                cc_patch_stmt_o.append(method['delete'][line])

        for line in method['add']:
            if method['add'][line] not in cc_patch_stmt_i:
                cc_patch_stmt_o.append(method['add'][line])

    for method in all_info:
        old_file_path = method['oldFileName'][2:]
        new_file_path = method['newFileName'][2:]
        original_pre = get_file_from_commit(repo_path, pre_commit+"^", old_file_path)
        original_post = apply_diff_in_memory(repo_path, pre_commit+"^", old_file_path, res_diff_path)
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
        for pre_method in pre_methods:
            for line in method['delete']:
                if int(line)>= pre_method.start_point[0] and int(line) <= pre_method.end_point[0] :
                    print(line)
                    all_patch_stmt_i.append(method['delete'][line])

        for post_method in post_methods:
            for line in method['add']:
                if int(line)>= post_method.start_point[0] and int(line) <= post_method.end_point[0] :
                    print(line)
                    all_patch_stmt_i.append(method['add'][line])
                    
        for line in method['delete']:
            if method['delete'][line] not in all_patch_stmt_i:
                all_patch_stmt_o.append(method['delete'][line])

        for line in method['add']:
            if method['add'][line] not in all_patch_stmt_i:
                all_patch_stmt_o.append(method['add'][line])

    
    
    return all_patch_stmt_i, all_patch_stmt_o, cc_patch_stmt_i, cc_patch_stmt_o


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
        
    res_diff_path = f"{results_dir}/{cveid}/ccpatch.diff"
    if not os.path.exists(res_diff_path):
        res_diff_path = f"{results_dir}/{cveid}/ccpatch_before_refine.diff"
    info = readCommit(repo_path, res_diff_path,  pre_commit, post_commit, True)

    fp = open(f"{diff_cache}/{cve_id}_method_info.json", "w")
    json.dump(info, fp, indent=4)
    fp.close()

    fp = open(f"{diff_cache}/{cve_id}_method_info.json")
    method_info = json.load(fp)
    fp.close()
    fp = open("method_info.json", "w")
    json.dump(method_info, fp, indent=4)
    fp.close()
    
    cc_diff_path = f"{ccpatch_dir}/{repo_name.split('@@')[-1]}/{cve_id}.diff"
    all_info = readCommit(repo_path, cc_diff_path,  pre_commit, post_commit, False)
    fp = open("method_info_cc.json", "w")
    json.dump(info, fp, indent=4)
    fp.close()
    all_patch_stmt_i, all_patch_stmt_o, cc_patch_stmt_i, cc_patch_stmt_o = get_cvco(repo_path, pre_commit, post_commit, cc_diff_path, res_diff_path, all_info, method_info)
    tp_i = 0
    tp = 0
    tp_o = 0
    fp_i = 0
    fp_o = 0
    fp = 0
    p_i = 0
    p_o = 0
    p = 0

    for line in all_patch_stmt_i:
        if line in cc_patch_stmt_i:
            tp_i += 1
            tp += 1
        else:
            fp_i += 1
            fp += 1
    
    for line in all_patch_stmt_o:
        if line in cc_patch_stmt_o:
            tp_o += 1
            tp += 1
        else:
            fp_o += 1
            fp += 1
    
    p = len(cc_patch_stmt_o) + len(cc_patch_stmt_i)
    p_i = len(cc_patch_stmt_i)
    p_o = len(cc_patch_stmt_o)
    cvc_info[cve_id] = {}
    cvc_info[cve_id]['p'] = p
    cvc_info[cve_id]['p_i'] = p_i
    cvc_info[cve_id]['p_o'] = p_o
    cvc_info[cve_id]['tp'] = tp
    cvc_info[cve_id]['tp_i'] = tp_i
    cvc_info[cve_id]['tp_o'] = tp_o
    cvc_info[cve_id]['fp'] = fp
    cvc_info[cve_id]['fp_i'] = fp_i
    cvc_info[cve_id]['fp_o'] = fp_o
    
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

        ccpatch_path = f"../0.dataset/ccpatch/{repo_name.split('@@')[-1]}/{cve_id}.diff"
        if not os.path.exists(ccpatch_path):
            no_cc.add(cve_id)
            continue
        worker_list.append((meta,))


    results = cpu_heater.multiprocess(work_fn, worker_list, max_workers=8, show_progress=True)
    for res in results:
        if res is None:
            continue
        for cve_id in res:
            cvc_info[cve_id] = res[cve_id]

    p = 0
    p_i = 0
    p_o = 0

    tp = 0
    tp_i = 0
    tp_o = 0

    fp = 0
    fp_i = 0
    fp_o = 0

    print(cvc_info)
    for cve_id in cvc_info:
        p += cvc_info[cve_id]['p']
        tp += cvc_info[cve_id]['tp']
        fp += cvc_info[cve_id]['fp']
        p_i += cvc_info[cve_id]['p_i']
        tp_i += cvc_info[cve_id]['tp_i']
        fp_i += cvc_info[cve_id]['fp_i']
        p_o += cvc_info[cve_id]['p_o']
        tp_o += cvc_info[cve_id]['tp_o']
        fp_o += cvc_info[cve_id]['fp_o']

    prec = tp / (tp+fp)
    rec = tp*3 / p
    f1 = 2*prec*rec / (prec+rec)

    prec_i = tp_i / (tp_i+fp_i)
    rec_i = tp_i*3 / p_i
    f1_i = 2*prec_i*rec_i / (prec_i+rec_i)

    prec_o = tp_o / (tp_o+fp_o)
    rec_o = tp_o*3 / p_o
    f1_o = 2*prec_o*rec_o / (prec_o+rec_o)

    print(prec, rec, f1)
    print(prec_i, rec_i, f1_i)
    print(prec_o, rec_o, f1_o)

    fp = open("cvc_info_results_stmt_w_o_seq.json", "w")
    json.dump(cvc_info, fp, indent=4)
    fp.close()
        
if __name__ == "__main__":
    main()