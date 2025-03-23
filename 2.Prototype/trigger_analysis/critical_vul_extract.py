import json

def find_called_functions(cg, llm_methods):
    methods = []
    for method in cg["pre"]["points"]:
        for llm_method in llm_methods:
            if llm_method in method:
                methods.append(method)

    for method in cg["post"]["points"]:
        for llm_method in llm_methods:
            if llm_method in method:
                methods.append(method)            
                
    pre_result = set(methods)
    post_result = set(methods)
    
    def recursive_search(status, method):
        if method in visited:
            return
        
        visited.add(method)
        
        for edge in cg[status]['edges']:
            if edge[0] == method:  
                called_method = edge[1]
                if called_method not in visited:
                    if status == "pre":
                        pre_result.add(called_method)
                    else:
                        post_result.add(called_method)
                    recursive_search(status, called_method)
            if edge[1] == method:
                calling_method = edge[0]
                if calling_method not in visited:
                    if status == "pre":
                        pre_result.add(calling_method)
                    else:
                        post_result.add(calling_method)
                    recursive_search(status, calling_method)
    for status in ["pre", "post"]:
        visited = set()
        for method in methods:
            recursive_search(status, method)
    return pre_result, post_result


def filter_call_data(cg, called_methods):
    pre_call_methods, post_call_methods = called_methods
    
    pre_filtered_points = pre_call_methods
    post_filtered_points = post_call_methods
    
    pre_filtered_edges = [
        edge for edge in cg['pre']['edges'] 
        if edge[0] in pre_call_methods or edge[1] in pre_call_methods
    ]
    
    post_filtered_edges = [
        edge for edge in cg['post']['edges'] 
        if edge[0] in post_call_methods or edge[1] in post_call_methods
    ]
    
    return {
        "pre": {
            "points": list(pre_filtered_points),
            "edges": pre_filtered_edges
        },
        "post": {
            "points": list(post_filtered_points),
            "edges": post_filtered_edges
        }
    }


if __name__ == "__main__":
    pass
    
