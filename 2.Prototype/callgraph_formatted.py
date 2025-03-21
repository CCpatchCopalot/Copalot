import json
from collections import defaultdict


def build_graph(graph_part):
    temp_graph = defaultdict(dict)
    nodes = set()
    
    edges = graph_part.get('edges', [])
    for edge in edges:
        source, target, src_line, tgt_line = edge
        nodes.add(source)
        nodes.add(target)
        key = (src_line, tgt_line)
        if target in temp_graph[source]:
            temp_graph[source][target].append(key)
        else:
            temp_graph[source][target] = [key]
    
    graph_dict = defaultdict(list)
    for source, mapping in temp_graph.items():
        for target, src_lines in mapping.items():
            graph_dict[source].append((target, src_lines))
    return graph_dict, nodes

def find_sources_and_sinks(graph_dict, nodes):
    indegree = {node: 0 for node in nodes}
    for src, edge_list in graph_dict.items():
        for tgt, _ in edge_list:
            indegree[tgt] += 1
    sources = [node for node in nodes if indegree[node] == 0]
    sinks = [node for node in nodes if node not in graph_dict or len(graph_dict[node]) == 0]
    return sources, sinks

def dfs_paths(graph_dict, current, node_path, edge_path, paths, sinks):
    node_path.append(current)
    if current in sinks:
        paths.append((node_path.copy(), edge_path.copy()))
    else:
        for (neighbor, src_lines) in graph_dict.get(current, []):
            if neighbor not in node_path:
                edge_path.append((current, neighbor, src_lines))
                dfs_paths(graph_dict, neighbor, node_path, edge_path, paths, sinks)
                edge_path.pop()
    node_path.pop()

def find_all_paths_containing_target(graph_dict, sources, sinks, target):
    valid_paths = []
    for src in sources:
        paths = []
        dfs_paths(graph_dict, src, [], [], paths, sinks)
        for node_path, edge_path in paths:
            if target in node_path:
                valid_paths.append({
                    "node_path": node_path,
                    "edge_path": [
                        {
                            "caller": caller,
                            "callee": callee,
                            "source_tgt_pairs": source_lines
                        }
                        for caller, callee, source_lines in edge_path
                    ]
                })
    return valid_paths

def process_graph(graph_part, part_name, target):
    graph_dict, nodes = build_graph(graph_part)
    sources, sinks = find_sources_and_sinks(graph_dict, nodes)
    return find_all_paths_containing_target(graph_dict, sources, sinks, target)
    
if __name__ == "__main__":
    pass
