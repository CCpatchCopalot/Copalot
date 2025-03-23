from calendar import c
import json
import os
from threading import local
from tqdm import tqdm
import subprocess
import json
import cpu_heater
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
import fcntl
import signal
import hunkmap
import re
from callgraph_formatted import process_graph

def get_up_down_path(target, path_dict):
    up_node_path = []
    up_edge_path = []
    down_node_path = []
    down_edge_path = []
    get_target = False
    for i, edge in enumerate(path_dict['edge_path']):
        if edge['callee'] == target:
            get_target = True
            up_node_path.append(edge['caller'])
            up_node_path.append(edge['callee'])
            up_edge_path.append(edge)
        elif get_target:
            up_node_path.append(edge['caller'])
            up_edge_path.append(edge)
        else:
            down_node_path.append(edge['caller'])
            down_edge_path.append(edge)
        if i == len(path_dict['edge_path']) - 1:
            down_node_path.append(edge['callee'])
    
    split_path_dict = {
        "up": {
            "node_path": up_node_path,
            "edge_path": up_edge_path
        },
        "down": {
            "node_path": down_node_path,
            "edge_path": down_edge_path
        }
    }
    return split_path_dict

class FileLockManager:
    def __init__(self, file_path):
        self.file_path = file_path

    def __enter__(self):
        self.file = open(self.file_path, "w")
        fcntl.flock(self.file, fcntl.LOCK_EX)
        return self.file

    def __exit__(self, exc_type, exc_value, traceback):
        fcntl.flock(self.file, fcntl.LOCK_UN)
        self.file.close()

def get_formal_params(code, language):
    identifiers = []
    parser = ASTParser(code, language)
    parameters = parser.query_all(
        "(parameter_list  ( parameter_declaration (identifier)@name ))(pointer_declarator(identifier))@name"
    )
    if parameters is None:
        return identifiers
    
    parameters.sort(key=lambda x: x.start_point[0])
    for parameter in parameters:
        if parameter is None or parameter.text is None:
            continue
        identifiers.append(parameter.text.decode().replace("*", "").replace(" ",""))

    return identifiers

def match_args_formal_params(code, args_list, language):
    identifiers = get_formal_params(code, language)
    param_arg_pairs = zip(identifiers, args_list)
    arg_param_mapping = {}
    for param, arg in param_arg_pairs:
        arg_param_mapping[param] = arg
    
    return arg_param_mapping

  
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
        logger.warning(f"❌ Pre-Patch Method 不存在: {signature}")
        return
    if post_method is None:
        logger.warning(f"❌ Post-Patch Method 不存在: {signature}")
        return
    return pre_method, post_method


def get_local_variable(code, language, start_line):
    identifiers = {}
    parser = ASTParser(code, language)
    local_variables = parser.query_all(
        "(declaration  (identifier)@name)(declaration  (pointer_declarator(identifier)@name)) (declaration (init_declarator (identifier)@name))"
    )
    if local_variables is None:
        return identifiers

    local_variables.sort(key=lambda x: x.start_point[0])
    for variable in local_variables:
        if variable is None or variable.text is None:
            continue
        try:
            identifiers[variable.text.decode().replace("*", "").replace(" ","")] = [start_line + variable.start_point[0]]
        except:
            identifiers[variable.text.decode().replace("*", "").replace(" ","")].append(start_line + variable.start_point[0])

    return identifiers


def get_arguments(code, line_number, function_name, language):
    parser = ASTParser(code, language)
    arguments = parser.query_all(
        f"((call_expression)@name@{line_number})"
    )
    if arguments is None:
        return []
    args = []
    
    arguments.sort(key=lambda x: x.start_point[0])
    for argument in arguments:
        child = argument.child_by_field_name("function")
        if child is None or child.text is None:
            continue
        if child.text.decode() == function_name:
            arguments_node = argument.child_by_field_name("arguments")
            if arguments_node is None:
                continue
            for arg in arguments_node.children:
                if arg.type != "," and arg.type != "(" and arg.type != ")":
                    assert arg.text is not None
                    arg_value = arg.text.decode("utf-8").replace("*", "").replace(" ","")
                    args.append(arg_value)
    
    return args

def get_all_function_calls(code, language):
    parser = ASTParser(code, language)
    calls = parser.query_all(
        "(call_expression (identifier)@name)"
    )
    if calls is None:
        return []
    call_functions = []
    for call in calls:
        if call is None or call.text is None:
            continue
        call_functions.append(call.text.decode())
    return call_functions

def get_source(target_method:Method, up_path, flag):
    target = target_method.signature
    if target_method is None:
        logger.error(f"Method {target} not found in project")
        return None
    
    criterial_identifiers = target_method.diff_identifiers
    criterial_lines = target_method.diff_lines
    if len(criterial_lines) == 0 and not flag:
        logger.warning(f" Method {target} has no diff lines, maybe it's a method has pure add or delete lines")
        if target_method.counterpart is None:
            logger.error(f"❌ Method {target} has no counterpart")
            return None
        if not flag:
            conterpart_source = get_source( target_method.counterpart, up_path, flag=True)
            source = {}
            if conterpart_source is not None:
                line_map, pre_post_hunk_map, pre_post_add_lines, re_post_del_lines = (
                    hunkmap.method_map(target_method, target_method.counterpart)
                )
                post_pre_line_map = {v: k for k, v in line_map.items()}
                for line in conterpart_source:
                    if line-target_method.counterpart.start_line+1 not in post_pre_line_map.keys():
                        continue
                    source[post_pre_line_map[line-target_method.counterpart.start_line+1]] = {}
                    if line-target_method.counterpart.start_line+1 not in conterpart_source:
                        continue
                    for identifier in conterpart_source[line-target_method.counterpart.start_line+1]:
                        source[post_pre_line_map[line-target_method.counterpart.start_line+1]][identifier] = []
                        for sline in conterpart_source[line-target_method.counterpart.start_line+1][identifier]:
                            if sline-target_method.counterpart.start_line+1 not in post_pre_line_map.keys():
                                continue
                            source[post_pre_line_map[line-target_method.counterpart.start_line+1]][identifier].append(post_pre_line_map[sline-target_method.counterpart.start_line+1])
                    
            return source
        else:
            logger.error(f"❌ Method {target} has no diff lines, it's not a patch method")
            return None

    no_criterial_identifiers_lines = set()
    for line in criterial_lines:
        if line in criterial_identifiers.keys() and len(criterial_identifiers[line]) != 0:
            continue
        else:
            no_criterial_identifiers_lines.add(line)

    other_criterial_identifiers = target_method.identifier_by_lines(no_criterial_identifiers_lines, pure=True)
    criterial_identifiers.update(other_criterial_identifiers)
    parameters = get_formal_params(target_method.code, target_method.language)
    local_variables = get_local_variable(target_method.code, target_method.language, target_method.start_line)
    calls = get_all_function_calls(target_method.code, target_method.language)

    flipped_edge_path = up_path['edge_path'][::-1]
    source_lines = {}
    for line in criterial_identifiers:
        source_lines[line] = {}
        for identifier in criterial_identifiers[line]:
            identifier = identifier.strip().replace("!","").replace("*", "").replace(" ","").replace("~", "").replace("&", "")
            if identifier in calls:
                continue
            source_lines[line][identifier] = []
            if identifier in local_variables.keys():
                source_lines[line][identifier] = local_variables[identifier]
            else:                
                if flipped_edge_path == []:
                    try:
                        source_lines[line][identifier].append(target_method.start_line)
                    except:
                        source_lines[line][identifier] = [target_method.start_line]
                else:
                    for edge in flipped_edge_path:
                        assert target_method.file.project is not None
                        find_source = False
                        caller_method = target_method.file.project.get_method(edge['caller'])
                        assert caller_method is not None
                        for source_tgt_pair in edge['source_tgt_pairs']:
                            args = get_arguments(caller_method.code, int(source_tgt_pair[0])-caller_method.start_line, edge['callee'].split("#")[1], caller_method.language)
                            arg_param_mapping = match_args_formal_params(target_method.code, args, target_method.language)
                            caller_fp = get_local_variable(caller_method.code, caller_method.language, caller_method.start_line)
                            if identifier in arg_param_mapping and arg_param_mapping[identifier] in caller_fp.keys():
                                try:
                                    source_lines[line][identifier].extend(caller_fp[arg_param_mapping[identifier]])
                                except:
                                    source_lines[line][identifier] = caller_fp[arg_param_mapping[identifier]]
                                find_source = True

                        if find_source:
                            break
                    if source_lines[line][identifier] == []:
                        try:
                            source_lines[line][identifier].append(target_method.start_line)
                        except:
                            source_lines[line][identifier] = [target_method.start_line]
    
    return source_lines
                    

def remove_adjacent_duplicates(data):
    result = []
    for i in range(len(data)):
        if i == 0 or data[i]['lineNumber'] != data[i - 1]['lineNumber']:
            result.append(data[i])
    
    return result

def taint_analysis(target_method: Method, source, cpg_path: str, role:str, timeout=30 * 60 * 1000):
    up_taint_path = {}
    down_taint_path = {}
    taint_path = {}
    all_taint_path = []

    for line in source:
        taint_path[line] = {}
        up_taint_path[line] = {}
        down_taint_path[line] = {}
        for identifier in source[line]:
            taint_path[line][identifier] = []
            up_taint_path[line][identifier] = []
            down_taint_path[line][identifier] = []
            times = 0
            if not os.path.exists(f"{target_method.method_dir}/{line}_{identifier}_{role}_up.json"):
                times += 1
                if times >= 5:
                    break
                src_lines = "|".join(map(str, list(set(source[line][identifier]))))
                cmd = f'joern --script ./scripts/source.sc --param cpgFile=\"{cpg_path}\" --param identifier_name=\"{identifier}\" --param src_lines=\"{src_lines}\" --param dst_lines={line} --param file=\"{target_method.method_dir}/{line}_{identifier}_{role}_up.json\"'
                with FileLockManager(cpg_path.replace(".bin", ".lock")) as lock:
                    p = subprocess.Popen(
                        cmd,
                        stderr=subprocess.STDOUT,
                        stdout=subprocess.PIPE,
                        shell=True,
                        close_fds=True,
                        start_new_session=True,
                    )
                    try:
                        out, _ = p.communicate(timeout=timeout)
                        p.wait()
                        logger.info(out.decode('utf-8'))
                    except subprocess.TimeoutExpired:
                        p.kill()
                        p.terminate()
                        os.killpg(p.pid, signal.SIGTERM)
            try:
                with open(f"{target_method.method_dir}/{line}_{identifier}_{role}_up.json", "r") as fp:
                    lines = fp.read()
                    paths = parse_taint_path(lines)
            except:
                return None, None
                
            if len(paths) == 0:
                continue
            else:
                true_source = False
                min_lines = line
                for path in paths:
                    if path[0]['lineNumber'] in source[line][identifier]:
                        true_source = True
                        break
                    if path[0]['lineNumber'] < min_lines:
                        min_lines = path[0]['lineNumber']
                if true_source:
                    up_taint_path[line][identifier].extend(paths)
                else:
                    for path in paths:
                        if path[0]['lineNumber'] == min_lines:
                            up_taint_path[line][identifier].append(path)    
    
            times = 0
            if not os.path.exists(f"{target_method.method_dir}/{line}_{identifier}_{role}_down.json"):
                cmd = f'joern --script ./scripts/sink.sc --param cpgFile=\"{cpg_path}\" --param identifier_name=\"{identifier}\" --param src_line={line} --param dst_line={target_method.end_line} --param file=\"{target_method.method_dir}/{line}_{identifier}_{role}_down.json\"'
                with FileLockManager(cpg_path.replace(".bin", ".lock")) as lock:
                    p = subprocess.Popen(
                        cmd,
                        stderr=subprocess.STDOUT,
                        stdout=subprocess.PIPE,
                        shell=True,
                        close_fds=True,
                        start_new_session=True,
                    )
                    try:
                        out, _ = p.communicate(timeout=timeout)
                        p.wait()
                        logger.info(out.decode('utf-8'))
                    except subprocess.TimeoutExpired:
                        p.kill()
                        p.terminate()
                        os.killpg(p.pid, signal.SIGTERM)
            
            try:
                with open(f"{target_method.method_dir}/{line}_{identifier}_{role}_down.json", "r") as fp:
                    lines = fp.read()
                    paths = parse_taint_path(lines)
            except:
                return None, None
            if len(paths) == 0:
                cmd = f'joern --script ./scripts/sink_var.sc --param cpgFile=\"{cpg_path}\" --param identifier_name=\"{identifier}\" --param src_line={line} --param dst_line={target_method.end_line} --param file=\"{target_method.method_dir}/{line}_{identifier}_{role}_down.json\"'
                with FileLockManager(cpg_path.replace(".bin", ".lock")) as lock:
                    p = subprocess.Popen(
                        cmd,
                        stderr=subprocess.STDOUT,
                        stdout=subprocess.PIPE,
                        shell=True,
                        close_fds=True,
                        start_new_session=True,
                    )
                    try:
                        out, _ = p.communicate(timeout=timeout)
                        p.wait()
                        logger.info(out.decode('utf-8'))
                    except subprocess.TimeoutExpired:
                        p.kill()
                        p.terminate()
                        os.killpg(p.pid, signal.SIGTERM)
                with open(f"{target_method.method_dir}/{line}_{identifier}_{role}_down.json", "r") as fp:
                    lines = fp.read()
                    paths = parse_taint_path(lines)
            if len(paths) == 0:
                    continue
            else:
                max_lines = line
                for path in paths:
                    if path[-1]['lineNumber'] > max_lines:
                        max_lines = path[-1]['lineNumber']
                for path in paths:
                    if path[-1]['lineNumber'] == max_lines:
                        down_taint_path[line][identifier].append(path)
            
            for up_path in up_taint_path[line][identifier]:
                for down_path in down_taint_path[line][identifier]:
                    deduplicate_path = remove_adjacent_duplicates(up_path+down_path)
                    if deduplicate_path not in taint_path[line][identifier]:
                        taint_path[line][identifier].append(deduplicate_path)
                    if deduplicate_path not in all_taint_path:
                        all_taint_path.append(deduplicate_path)

    return taint_path, all_taint_path

def parse_taint_path(text):
    table_pattern = re.compile(r'┌.*?└.*?\n', re.DOTALL)
    table_blocks = table_pattern.findall(text)
    
    all_tables = []
    
    for block in table_blocks:
        lines = block.splitlines()
        header = None
        for line in lines:
            if 'nodeType' in line and 'file' in line:
                header = [h.strip() for h in line.strip('│').split('│')]
                break

        if header is None:
            continue
        try:
            idx_lineNumber = header.index("line")
            idx_method = header.index("method")
            idx_file = header.index("file")
            idx_code = header.index("tracked")
        except ValueError:
            continue

        table_entries = []
        for line in lines:
            if '─' in line or ('nodeType' in line and 'file' in line):
                continue
            if line.startswith('│'):
                cells = [cell.strip() for cell in line.strip('│').split('│')]
                if len(cells) < max(idx_lineNumber, idx_method, idx_file, idx_code) + 1:
                    continue
                try:
                    line_num = int(cells[idx_lineNumber])
                except ValueError:
                    continue

                entry = {
                    "lineNumber": line_num,
                    "method": cells[idx_method],
                    "file": cells[idx_file],
                    "tracked": cells[idx_code]  
                }
                table_entries.append(entry)
        

        all_tables.append(table_entries)
    
    return all_tables

def mapping_work_fn(path, pre_project, post_project, role, taint_path):
    conterpart_path = []
    for node in path:
        post_method = post_project.get_method(f"{node['file']}#{node['method']}")
        pre_method = pre_project.get_method(f"{node['file']}#{node['method']}")
        if post_method is None or pre_method is None:
            break

        line_map, pre_post_hunk_map, pre_post_add_lines, re_post_del_lines = (
                hunkmap.method_map(pre_method, post_method)
            )
        post_pre_line_map = {v: k for k, v in line_map.items()}

        if role == 'pre':
            if node['lineNumber']-post_method.start_line+1 in post_pre_line_map.keys():
                conterpart_node = {
                    'lineNumber': post_pre_line_map[node['lineNumber']-post_method.start_line+1]+pre_method.start_line-1,
                    'method': node['method'],
                    'file': node['file'],
                    'tracked': node['tracked']
                }
                conterpart_path.append(conterpart_node)
        else:
            if node['lineNumber']-pre_method.start_line+1 in line_map.keys():
                conterpart_node = {
                    'lineNumber': line_map[node['lineNumber']-pre_method.start_line+1]+post_method.start_line-1,
                    'method': node['method'],
                    'file': node['file'],
                    'tracked': node['tracked']
                }
                if conterpart_node not in conterpart_path:
                    conterpart_path.append(conterpart_node)
    if conterpart_path not in taint_path and conterpart_path != []:
        taint_path.append(conterpart_path)
    return taint_path

def mapping_taint_path(target_method:Method, pre_post_project:tuple[Project, Project], role:str):
    pre_post_role_mapping = {'pre': 'post', 'post': 'pre'}
    pre_project, post_project = pre_post_project
    if not os.path.exists(f"{target_method.method_dir}/{pre_post_role_mapping[role]}_taint_path.json"):
        logger.error(f"❌ {pre_post_role_mapping[role]}_taint_path.json not found")
        return None
    
    if not os.path.exists(f"{target_method.method_dir}/{role}_taint_path.json"):
        logger.error(f"❌ {role}_taint_path.json not found")
        return None
    
    with open(f"{target_method.method_dir}/{role}_taint_path.json", "r") as fp:
        taint_path = json.load(fp)

    with open(f"{target_method.method_dir}/{pre_post_role_mapping[role]}_taint_path.json", "r") as fp:
        counterpart_taint_path = json.load(fp)

    work_list = []
    for path in  tqdm(counterpart_taint_path):
        work_list.append((path, pre_project, post_project, role, taint_path))
    
    results = cpu_heater.multithreads(mapping_work_fn, work_list, 256, show_progress=True)
    for res in results:
        taint_path.extend(res)
    
    with open(f"{target_method.method_dir}/{role}_taint_path.json", "w") as fp:
        json.dump(taint_path, fp)
    
    return taint_path

def taint_work_fn(pre_method, call_path, role, cache_dir):
    source_lines = get_source(pre_method, call_path, flag=False)
    _ , all_taint_path= taint_analysis(pre_method, source_lines, f"{cache_dir}/{role}/cpg.bin", role)
    return all_taint_path, role, call_path

def taint_analysis_all(patch:Patch, pre_post_project:tuple[Project, Project], method_signature:str, graph_data, cache_dir:str, vis):
    pre_project, post_project = pre_post_project
    pre_post_methods: None | tuple[Method, Method] = get_pre_post_methods(
        patch, pre_post_project, method_signature
    )
    assert pre_post_methods is not None
    method_dir = init_method_dir(pre_post_methods, cache_dir)
    pre_method, post_method = pre_post_methods
    assert pre_method is not None and post_method is not None

    pre_method.counterpart = post_method
    post_method.counterpart = pre_method
    if not os.path.exists(f"{cache_dir}/format_callgraph_{method_signature.split('#')[-1]}.json"):
        formatted_callgraph = {
            "pre": process_graph(graph_data.get('pre', {}), "pre", method_signature),
            "post": process_graph(graph_data.get('post', {}), "post", method_signature)
        }
        if formatted_callgraph['pre'] == [] or formatted_callgraph['post'] == []:
            formatted_callgraph['pre'] = [{'node_path': [method_signature], 'edge_path': []}]
            formatted_callgraph['post'] = [{'node_path': [method_signature], 'edge_path': []}]

        fp = open(f"{cache_dir}/format_callgraph_{method_signature.split('#')[-1]}.json", "w")
        json.dump(formatted_callgraph, fp)
        fp.close()
    else:
        fp = open(f"{cache_dir}/format_callgraph_{method_signature.split('#')[-1]}.json", "r")
        formatted_callgraph = json.load(fp)
        fp.close()
    taint_path = {}
    work_list = []

    for role in ['pre', 'post']:
        taint_path[role] = []
        for call_path in  formatted_callgraph[role]:
            if str(call_path) in vis[role]:
                continue
            if role == 'pre':
                source_lines = get_source(pre_method, call_path, flag=False)
                if os.path.exists(f"{cache_dir}/{role}/cpg.lock"):
                    os.system(f"rm {cache_dir}/{role}/cpg.lock")
                _ , all_taint_path= taint_analysis(pre_method, source_lines, f"{cache_dir}/{role}/cpg.bin", role)
            else:
                source_lines = get_source(post_method, call_path, flag=False)
                if os.path.exists(f"{cache_dir}/{role}/cpg.lock"):
                    os.system(f"rm {cache_dir}/{role}/cpg.lock")
                _ , all_taint_path= taint_analysis(post_method, source_lines, f"{cache_dir}/{role}/cpg.bin", role)
            
            if all_taint_path is None:
                continue
            taint_path[role].extend(all_taint_path)
            vis[role][str(call_path)] = True
    
    fp = open(f"{pre_method.method_dir}/pre_taint_path.json", "w")
    json.dump(taint_path['pre'], fp)
    fp.close()

    fp = open(f"{post_method.method_dir}/post_taint_path.json", "w")
    json.dump(taint_path['post'], fp)
    fp.close()
    return taint_path, vis



def init_method_dir(pre_post_methods: tuple[Method, Method], cache_dir: str):
    pre_method, post_method = pre_post_methods
    method_dir = f"{cache_dir}/method/{pre_method.signature_r}"
    dot_dir = f"{cache_dir}/method/{pre_method.signature_r}/dot"

    os.makedirs(method_dir, exist_ok=True)
    os.makedirs(dot_dir, exist_ok=True)

    pre_method.method_dir, post_method.method_dir = (method_dir,) * 2
    pre_method.write_code(method_dir)
    post_method.write_code(method_dir)

    return method_dir

def clone_repo(repo_name, repo_dir, is_gitlab=False):
    repo_path = os.path.join(repo_dir, repo_name)
    if not os.path.exists(repo_path):
        logger.info(f"Cloning repo: {repo_name} from {'GitLab' if is_gitlab else 'GitHub'}")
        if is_gitlab:
            clone_url = f"https://gitlab.com/{repo_name.replace('@@', '/')}.git"
        else:
            clone_url = f"https://github.com/{repo_name.replace('@@', '/')}.git"
        
        subprocess.run(["git", "clone", clone_url, repo_path], check=True)

if __name__ == "__main__":
    pass