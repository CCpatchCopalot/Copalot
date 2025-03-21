import os
import sys
import json
from collections import defaultdict
from typing import List, Set, Dict


def func_path_extract(trigger_point: str, modified_point: dict, cache_dir: str):

    with open(os.path.join(cache_dir, "call.json"), "r") as fr:
        call = json.load(fr)
    if isinstance(trigger_point, str):
        trigger_file = trigger_point.split("#")[0]
        trigger_func = trigger_point.split("#")[1]
        trigger_line = trigger_point.split("#")[2]
    else:
        return None
    trigger_point = None
    
    trigger_file_func = trigger_file + "#" + trigger_func
    
    for pre_point in call["pre"]["points"]:
        if pre_point.endswith("/" + trigger_file_func):
            trigger_point = pre_point
            break

    all_paths = {}
    for pre_or_post, point_edge in call.items():
        all_paths[pre_or_post] = {}
        graph = {}
        for edge in point_edge["edges"]:
            source, target = edge[0], edge[1]
            if source not in graph:
                graph[source] = []
            graph[source].append(target)

        def dfs(start, end, path=None, visited=None):
            if path is None:
                path = []
            if visited is None:
                visited = set()
                
            path.append(start)
            visited.add(start)
            paths = []
            
            if start == end:
                paths.append(path[:])
            else:
                for next_node in graph.get(start, []):
                    if next_node not in visited:
                        paths.extend(dfs(next_node, end, path, visited))
                        
            path.pop()
            visited.remove(start)
            return paths
        
        for start in modified_point:
            paths = dfs(start, trigger_point)
            if paths:
                all_paths[pre_or_post][start] = [list(t) for t in {tuple(sublist) for sublist in paths}]
        
    
    with open(os.path.join(cache_dir, "path/func_path.json"), "w") as fw:
        json.dump(all_paths, fw, indent=4)
        
if __name__ == "__main__":
    pass