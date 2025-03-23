import difflib
import json
import os
from re import L
import os
import subprocess
from openai import timeout
import pandas as pd
from tqdm import tqdm
import json
import cpu_heater
import format_code
import hunkmap
import joern
import networkx as nx
import pandas as pd
import tqdm
from codefile import CodeFile, create_code_tree
from json2dot import convert_to_dot
from loguru import logger
from networkx import core_number
from patch import Patch
from project import Method, Project
from tqdm import tqdm
from cg_path import func_path_extract
from ast_parser import ASTParser
from common import Language, Mode
from dataloader import DataLoader
from trigger_analysis.desc_func_reg import desc_func_reg
from taint_analysis import taint_analysis_all
from parse_commit import readCommit
import code_transformation
from recovery import CodeMapper
from clang-tidy import checking

from trigger_analysis.vul_pat_cg import extract_vuln_functions
from trigger_analysis.vul_pat_cg import extract_vuln_patch
from trigger_analysis.vul_pat_cg import extract_vuln_patch_without_taint
from trigger_analysis.critical_vul_extract import find_called_functions, filter_call_data
from collections import defaultdict
import bisect
from diffparser import gitdiff


def process_string(s):
    lines = s.strip().split('\n')
    base_lines = []
    base_indices = []
    
    for i, line in enumerate(lines):
        if not line.startswith(('+', '-')):
            base_lines.append(line)
            base_indices.append(i)
    
    gap_dict = defaultdict(list)
    for i, line in enumerate(lines):
        if line.startswith(('+', '-')):
            pos = bisect.bisect_left(base_indices, i) - 1
            gap_pos = pos + 1
            gap_dict[gap_pos].append(line)
    
    return tuple(base_lines), gap_dict

def merge_string_lists(list1, list2):
    """合并两个字符串列表"""
    all_strings = list1 + list2
    grouped = defaultdict(lambda: defaultdict(list))
    
    for s in all_strings:
        base_key, gaps = process_string(s)
        for gap_pos, lines in gaps.items():
            seen = set()
            unique_lines = []
            for line in lines:
                if line not in seen:
                    seen.add(line)
                    unique_lines.append(line)
            grouped[base_key][gap_pos].extend(unique_lines)
    
    merged = []
    for base_key, gaps in grouped.items():
        base_lines = list(base_key)
        total_gaps = len(base_lines) + 1
        merged_lines = []
        
        for gap_pos in range(total_gaps):
            if gap_pos in gaps:
                merged_lines.extend(gaps[gap_pos])
            if gap_pos < len(base_lines):
                merged_lines.append(base_lines[gap_pos])
        
        merged_str = '\n'.join(merged_lines) + '\n'
        merged.append(merged_str)
    
    return merged

def save_desc_info(cache_dir, cve_id):
    result = desc_func_reg(cve_id, cache_dir)
    if isinstance(result, tuple) and len(result) == 2:
        desc, llm_func = result
    else:
         desc, llm_func = "",""

    cache_json = os.path.join(cache_dir, "desc_func.json")
    desc_info = {}
    desc_info[cve_id] = {}
    desc_info[cve_id]["desc_function"] = llm_func
    desc_info[cve_id]["desc"] = desc   
    return desc_info

def recovery(meta, local_cache_dir, cveid):
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
    res_diff_path = f"{local_cache_dir}/ccpatch_before_refine.diff"
    method_info = readCommit(repo_path, res_diff_path,  pre_commit, post_commit, True)
    diff = ""
    for info in method_info:        
        old_file_path = method['oldFileName'][2:]
        new_file_path = method['newFileName'][2:]
        pa = get_file_from_commit(repo_path, pre_commit+"^", old_file_path)
        pb = get_file_from_commit(repo_path, post_commit, new_file_path)
        pb_formatted = format.format(pb, Language.C, True, True, False, True)
        pc = apply_diff_in_memory(repo_path, pre_commit+"^", old_file_path, cc_diff_path)
        mapper = CodeMapper(pb, pb_formatted)
        pc_recovered = mapper.transform_to_original(pc)
        pc = checking(pa, pc_recovered, pb.split("\n"), info['add'])
        diff_per = gitdiff(pa, pc)
        diff += diff_per
    
    return diff  


    
def construct_taint_path(cveid, repo_path, pre_commit, post_commit):
    patch = None
    language = Language.C
    cache_dir = f"./cache/{cveid}"
    local_cache_dir = f"./results_cache/{cveid}"
    os.makedirs(local_cache_dir, exist_ok=True)
    error_code = {}
    error_code[cveid] = {}
    try:
        patch = Patch(repo_path, pre_commit.replace(" ","").replace("\n",""), post_commit.replace(" ","").replace("\n",""), language)
    except Exception as e:
        os.system(f"git config --global --add safe.directory {repo_path}")
        patch = Patch(repo_path, pre_commit.replace(" ","").replace("\n",""), post_commit.replace(" ","").replace("\n",""),  language)
        try:
            patch = Patch(repo_path, pre_commit.replace(" ","").replace("\n",""), post_commit.replace(" ","").replace("\n",""),  language)
        except Exception as e:
            logger.error(e)
            logger.error(f"❌ Failed to initialize Patch")
            error_code[cveid]['summary'] = "Failed to initialize Patch"
            error_code[cveid]['details'] = str(e)
            error_code[cveid]['results'] = 'FAILED'
            return error_code
        
    logger.info(f"🔄 analysis {cveid}...")
    logger.info(f"✅ Parsing Patch Completed")

    pre_taint_path_codes = []
    post_taint_path_codes = []
    try:
        if len(patch.pre_analysis_files) > 10 or len(patch.post_analysis_files) > 10 or len(patch.pre_analysis_files) == 10 or len(patch.post_analysis_files) == 10:
            pre_code_files = patch.pre_modify_files
            post_code_files = patch.post_modify_files
        else:
            pre_code_files = patch.pre_analysis_files
            post_code_files = patch.post_analysis_files
    except Exception as e:
        logger.error(f"❌ Failed to obtain pre-patch and post-patch code files")
        error_code[cveid]['summary'] = "Failed to obtain pre-patch and post-patch code files"
        error_code[cveid]['details'] = str(e)
        error_code[cveid]['results'] = 'FAILED'
        return error_code

    logger.info(f"{cveid} pre-patch code files: {len(pre_code_files)}")
    pre_dir = os.path.join(cache_dir, "pre")
    post_dir = os.path.join(cache_dir, "post")
    create_code_tree(pre_code_files, pre_dir)
    create_code_tree(post_code_files, post_dir)
    logger.info(f"✅ Building the patch-related directory tree is complete")
    pre_post_projects = (patch.pre_analysis_project, patch.post_analysis_project)
    try:
        logger.info(f"🔄 merge all taint paths")
        for path in taint_path['pre']:
            taint_path_code = ""
            sort_path = sorted(path, key=lambda x: x["lineNumber"])
            for i, node in enumerate(sort_path):
                if i > 0 and sort_path[i-1]['lineNumber'] == node['lineNumber']:
                    continue
                change_method_signature = f"{node['file']}#{node['method']}"
                target_method = patch.pre_analysis_project.get_method(change_method_signature)
                if target_method is None:
                    continue
                
                if change_method_signature in patch.changed_methods_line_map and node['lineNumber'] in patch.changed_methods_line_map[change_method_signature]['delete']:
                    taint_path_code += f"-   {target_method.lines[node['lineNumber']]}\n"
                else:
                    try:
                        taint_path_code += f"{target_method.lines[node['lineNumber']]}\n"
                    except:
                        continue
            if taint_path_code not in pre_taint_path_codes:
                pre_taint_path_codes.append(taint_path_code)

        for path in taint_path['post']:
            taint_path_code = ""
            sort_path = sorted(path, key=lambda x: x["lineNumber"])
            for i, node in enumerate(sort_path):
                if i > 0 and sort_path[i-1]['lineNumber'] == node['lineNumber']:
                    continue
                change_method_signature = f"{node['file']}#{node['method']}"
                target_method = patch.post_analysis_project.get_method(change_method_signature)
                if target_method is None:
                    continue
                
                if change_method_signature in patch.changed_methods_line_map and node['lineNumber'] in patch.changed_methods_line_map[change_method_signature]['add']:
                    taint_path_code += f"+   {target_method.lines[node['lineNumber']]}\n"
                else:
                    try:
                        taint_path_code += f"{target_method.lines[node['lineNumber']]}\n"
                    except:
                        continue
            if taint_path_code not in post_taint_path_codes:
                post_taint_path_codes.append(taint_path_code)
        result = merge_string_lists(pre_taint_path_codes, post_taint_path_codes)
        logger.info(f"✅ merge all taint paths")
    except Exception as e:
        logger.error(f"❌ merge all taint paths failed {cveid}")
        error_code[cveid]['summary'] = "merge all taint paths failed"
        error_code[cveid]['details'] = str(e)
        error_code[cveid]['results'] = 'FAILED'
        return error_code
    try:
        logger.info(f"🔄 Get ccpatch")
        desc_info = save_desc_info(local_cache_dir, cveid.split("_")[0])
        patch_content = patch.patch_content
        if result != []:
            taint = extract_vuln_patch(desc_info[cveid.split("_")[0]]['desc'], patch_content, result)
        else:
            taint = extract_vuln_patch_without_taint(desc_info[cveid.split("_")[0]]['desc'], patch_content)
        fp = open(f"{local_cache_dir}/ccpatch_before_refine.diff", "w")
        fp.write(taint)
        fp.close()
        taint = recovery(meta, local_cache_dir, cveid)
        fp = open(f"{local_cache_dir}/ccpatch.diff", "w")
        fp.write(taint)
        fp.close()
        logger.info(f"✅ Get ccpatch")
    except Exception as e:
        logger.error(f"❌ Get ccpatch")
        error_code[cveid]['summary'] = "Get ccpatch"
        error_code[cveid]['details'] = str(e)
        error_code[cveid]['results'] = 'FAILED'
        return error_code
    error_code[cveid]['summary'] = ""
    error_code[cveid]['details'] = ""
    error_code[cveid]['results'] = 'SUCESS'
    return error_code


if __name__ == "__main__":
    pass
