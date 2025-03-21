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

from trigger_analysis.vul_pat_cg import extract_vuln_functions
from trigger_analysis.critical_vul_extract import find_called_functions, filter_call_data

def export_joern_graph(
    pre_dir: str,
    post_dir: str,
    need_cdg: bool,
    language: Language,
    multiprocess: bool = True,
    overwrite: bool = True,
):
    logger.info(f"🔄 Generate pre-patch, post-patch CPG PDG")
    worker_args = [
        (f"{pre_dir}/code", pre_dir, language, overwrite, need_cdg),
        (f"{post_dir}/code", post_dir, language, overwrite, need_cdg),
    ]
    if multiprocess:
        cpu_heater.multiprocess(
            joern.export_with_preprocess_and_merge,
            worker_args,
            max_workers=2,
            show_progress=False,
        )
    else:
        joern.export_with_preprocess_and_merge(*worker_args[0])
        joern.export_with_preprocess_and_merge(*worker_args[1])
    logger.info(f"✅ Generate pre-patch, post-patch CPG PDG Complete")


def write2file(file_path: str, content: str):
    with open(file_path, "w") as f:
        f.write(content)


def get_pre_post_methods(
    patch, pre_post_projects: tuple[Project, Project], signature: str
):
    pre_project, post_project = pre_post_projects

    pre_method = pre_project.get_method(signature)
    if signature in patch.change_method_map_dict.keys():
        post_method = post_project.get_method(
            patch.change_method_map_dict[signature][0]
        )
    else:
        post_method = post_project.get_method(signature)
    if pre_method is None:
        logger.warning(f"❌ Pre-Patch Method not exists: {signature}")
        return
    if post_method is None:
        logger.warning(f"❌ Post-Patch Method not exists: {signature}")
        return
    return pre_method, post_method


def init_method_dir(pre_post_methods: tuple[Method, Method], cache_dir: str):
    pre_method, post_method = pre_post_methods
    method_dir = f"{cache_dir}/method/{pre_method.signature_r}"
    dot_dir = f"{cache_dir}/method/{pre_method.signature_r}/dot"

    os.makedirs(method_dir, exist_ok=True)
    os.makedirs(dot_dir, exist_ok=True)

    pre_method.method_dir, post_method.method_dir = (method_dir,) * 2
    pre_method.write_code(method_dir)
    post_method.write_code(method_dir)
    pre_method.write_dot(dot_dir)
    post_method.write_dot(dot_dir)

    return method_dir


def init_single_method_dir(method, cache_dir):
    method_dir = f"{cache_dir}/method/{method.signature_r}"
    dot_dir = f"{cache_dir}/method/{method.signature_r}/dot"

    os.makedirs(dot_dir, exist_ok=True)
    os.makedirs(method_dir, exist_ok=True)

    method.method_dir = method_dir
    method.write_code(method_dir)
    method.write_dot(dot_dir)

    return method_dir


def worker_fn(pre_project: Project, ref_id, cnt):
    if cnt > 3:
        return None
    callees = pre_project.get_callee(ref_id)
    return callees, cnt + 1, ref_id


def get_callgraph(patch, project):
    edges = set()
    points = set()
    step = 0
    worker_list = []
    for method_signature in patch.changed_methods:
        points.add(method_signature)
        worker_list.append((project, method_signature, step))

    while worker_list != []:
        results = cpu_heater.multithreads(
            worker_fn, worker_list, max_workers=512, show_progress=False
        )
        worker_list = []
        for res in results:
            if res is None:
                continue
            callee, cnt, ref_id = res
            if cnt > 3:
                continue
            for point in callee:
                points.add(ref_id)
                points.add(point["callee_method_name"])
                point["caller_method_name"] = ref_id
                edges.add(
                    (
                        ref_id,
                        point["callee_method_name"],
                        point["callee_linenumber"],
                        point["method_line_number"],
                    )
                )
                if point["callee_method_name"] in points:
                    continue
                worker_list.append((project, point["callee_method_name"], cnt))

    return points, edges


def get_pre_post_call(patch, pre_post_projects, cache_dir):
    pre_project, post_project = pre_post_projects
    worker_list = []
    points, edges = get_callgraph(patch, pre_project)
    call = {}
    call["pre"] = {}
    call["pre"]["points"] = list(points)
    call["pre"]["edges"] = list(edges)
    points, edges = get_callgraph(patch, post_project)
    call["post"] = {}
    call["post"]["points"] = list(points)
    call["post"]["edges"] = list(edges)

    return call

def save_desc_info(cache_dir, cve_id, pre_methodsigs, post_methodsigs):
    result = desc_func_reg(cve_id, cache_dir)
    if isinstance(result, tuple) and len(result) == 2:
        desc, llm_func = result
    else:
        raise ValueError("desc_func_reg did not return a tuple with two elements")

    cache_json = os.path.join(cache_dir, "desc_func.json")
    desc_info = {}
    desc_info[cve_id] = {}
    desc_info[cve_id]["pre"] = pre_methodsigs
    desc_info[cve_id]["post"] = post_methodsigs
    desc_info[cve_id]["desc_function"] = llm_func
    desc_info[cve_id]["desc"] = desc   
    with open(cache_json, "w") as fw:
        json.dump(desc_info, fw, indent = 4)
    return desc_info

def get_clustring(repo_path, pre_commit, post_commit, cveid, trigger_point = None):
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
    logger.info(f"✅ analysis Patch finished")
    try:
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
    try:
        export_joern_graph(
            pre_dir,
            post_dir,
            need_cdg=True,
            language=Language.C,
            overwrite=False,
            multiprocess=True,
        )
    except Exception as e:
        logger.error(f"❌ Failed to generate CPG PDG for pre-patch, post-patch, target")
        error_code[cveid]['summary'] = "Failed to generate CPG PDG for pre-patch, post-patch, target"
        error_code[cveid]['details'] = str(e)
        error_code[cveid]['results'] = 'FAILED'
        return error_code

    logger.info(f"🔄 Parsing Project Joern Graph")
    assert patch is not None
    patch.pre_analysis_project.load_joern_graph(f"{pre_dir}/cpg", f"{pre_dir}/pdg")
    patch.post_analysis_project.load_joern_graph(
        f"{post_dir}/cpg", pdg_dir=f"{post_dir}/pdg"
    )
    logger.info(f"✅ Parsing Project Joern Graph")

    pre_post_projects = (patch.pre_analysis_project, patch.post_analysis_project)
    
    logger.info(f"🔄 Get suspected trigger method")
    pre_methodsigs = []
    post_methodsigs = []
    for file in pre_post_projects[0].files:
        for method in file.methods:
            pre_methodsigs.append(method.signature)
    for file in pre_post_projects[1].files:
        for method in file.methods:
            post_methodsigs.append(method.signature)
    
    desc_info = save_desc_info(local_cache_dir, cveid.split("_")[0], pre_methodsigs, post_methodsigs)
    logger.info(f"✅ Get suspected trigger method")
    patch_content = patch.patch_content

    if not os.path.exists(f"{local_cache_dir}/sub_call.json"): 
        try:
            logger.info(f"🔄 Get callgraph")
            callgraph = get_pre_post_call(patch, pre_post_projects, cache_dir)
            
            fp = open(f"{cache_dir}/call.json", "w")
            json.dump(callgraph, fp, indent=4)
            fp.close()

            fp = open(f"{local_cache_dir}/call.json", "w")
            json.dump(callgraph, fp, indent=4)
            fp.close()
            logger.info(f"✅ Get callgraph")
            critical_funcs = extract_vuln_functions(desc_info[cveid.split("_")[0]]["desc"], callgraph, patch_content)
            critical_related_func = find_called_functions(callgraph, critical_funcs)
            sub_call = filter_call_data(callgraph, critical_related_func)
            with open(os.path.join(cache_dir, "sub_call.json"), "w") as fw:
                json.dump(sub_call, fw, indent = 4)
            with open(os.path.join(local_cache_dir, "sub_call.json"), "w") as fw:
                json.dump(sub_call, fw, indent = 4)
        except Exception as e:
            logger.error(e)
            logger.error(f"❌ Get callgraph failed")        
            error_code[cveid]['summary'] = "Get callgraph failed"
            error_code[cveid]['details'] = str(e)
            error_code[cveid]['results'] = 'FAILED'
            return error_code
    else:
        with open(f"{local_cache_dir}/sub_call.json", "r") as f:
            sub_call = json.load(f)
    
    taint_path = {'pre':[], 'post':[]}
    vis = {'pre':{}, 'post':{}}
    worker_list = []
    try:
        for method_signature in patch.changed_methods:
            taint_path_per, vis = taint_analysis_all(patch, pre_post_projects, method_signature, sub_call, cache_dir, vis)
            taint_path['pre'].extend(taint_path_per['pre'])
            taint_path['post'].extend(taint_path_per['post'])
            taint_path.update(taint_path_per)
            worker_list.append((patch, pre_post_projects, method_signature, sub_call, cache_dir, vis))
        results = cpu_heater.multithreads(taint_analysis_all, worker_list, max_workers=512, show_progress=False)

        for result in results: 
            taint_path_per, vis = result
            taint_path['pre'].extend(taint_path_per['pre'])
            taint_path['post'].extend(taint_path_per['post'])
    except Exception as e:
        logger.error(f"❌ Taint analysis failed")    
        error_code[cveid]['summary'] = "Taint analysis failed"
        error_code[cveid]['details'] = str(e)
        error_code[cveid]['results'] = 'FAILED'
        return error_code

    fp = open(f"{cache_dir}/taint_path.json", "w")
    json.dump(taint_path, fp, indent=4)
    fp.close()

    fp = open(f"{local_cache_dir}/taint_path.json", "w")
    json.dump(taint_path, fp, indent=4)
    fp.close()
    path_dir = os.path.join(cache_dir, "path")
    if not os.path.exists(path_dir):
        os.makedirs(path_dir)
    
    modified_point = None
    modified_points = []
    for method_signature in patch.changed_methods:
        modified_points.append(method_signature)
    for method_signature in patch.added_methods:
        modified_points.append(method_signature)
    for method_signature in patch.deleted_methods:
        modified_points.append(method_signature)
    modified_points = list(set(modified_points))
    
    func_path_extract(trigger_point, modified_points, cache_dir)
    
    if len(patch.changed_methods) == 1:
        logger.info(f"✅ Determined as a single method")
        result = slicing_single_method(
            patch, list(patch.changed_methods)[0], pre_post_projects, cache_dir
        )
        if result is not None:
            pre_slice_results, post_slice_results = result
            pre_line_results, pre_call_edges = pre_slice_results
            post_line_results, post_call_edges = post_slice_results
            assert pre_call_edges is not None
            assert pre_line_results is not None
            assert post_line_results is not None
            assert post_call_edges is not None

            fp = open(f"{cache_dir}/graph_cluster.json", "w")
            json.dump(
                {
                    "pre": {
                        "nodes": list(pre_line_results),
                        "edges": list(pre_call_edges),
                    },
                    "post": {
                        "nodes": list(post_line_results),
                        "edges": list(post_call_edges),
                    },
                },
                fp,
                indent=4,
            )
            fp.close()
    else:
        slicing_multi_method(patch, pre_post_projects, cache_dir, callgraph)
    error_code[cveid]['results'] = 'SUCCESS'
    return error_code

def clone_repo(repo_name, repo_dir, repohost=None):
    repo_path = os.path.join(repo_dir, repo_name)
    if not os.path.exists(repo_path):
        if repohost == "gitlab":
            clone_url = f"https://gitlab.com/{repo_name.replace('@@', '/')}.git"
        elif repohost == "ghostscript":
            clone_url = f"git://git.ghostscript.com/ghostpdl.git"
        else:
            clone_url = f"https://github.com/{repo_name.replace('@@', '/')}.git"
        subprocess.run(["git", "clone", clone_url, repo_path], check=True)
        
if __name__ == "__main__":
    pass