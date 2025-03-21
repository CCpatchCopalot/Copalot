from config import excel_path, joern_path
from function_clustering import get_clustring
from merge_taint_path import construct_taint_path

if __name__ == "__main__":
    ## phase1 critical function extraction
    joern.set_joern_env(joern_path)
    repo_dir = "./repo_cache"
    errors = {}
    loader = DataLoader(file_path = excel_path)
    cve_metas = loader.load_data()
    work_list = []
    workers = []
    for meta in tqdm(reversed(cve_metas), total=len(cve_metas)):
        repohost = meta.get("repohost", None)
        repo_name = meta.get("repo_name", None)
        pre_commit = meta.get("pre_commit", None).strip().replace(" ","").replace(" \\n","").replace("\n","").replace("\t","").replace("?w=1", "").replace("\\n","")
        post_commit = meta.get("post_commit", None).strip().replace(" ","").replace(" \\n","").replace("\n","").replace("\t","").replace("?w=1", "").replace("\\n",""
        cve_id = meta.get("CVE_ID", None)
        if repo_name == None:
            errors[cve_id + "__NoneRepo"] = {}
            errors[cve_id + "__NoneRepo"]['results'] = "FAILED"
            errors[cve_id + "__NoneRepo"]['summary'] = "no suce repo"
            errors[cve_id + "__NoneRepo"]['details'] = "no suce repo"
            continue
            
        clone_repo(repo_name, repo_dir, repohost)
        if not os.path.exists(os.path.join(repo_dir, f"{repo_name}_{cve_id}")):
            os.makedirs(os.path.join(repo_dir, f"{repo_name}_{cve_id}"))
            os.system(f"cp -r {os.path.join(repo_dir, repo_name, '.git')} {os.path.join(repo_dir, f'{repo_name}_{cve_id}')}")
        repo_path = os.path.join(repo_dir,  f'{repo_name}_{cve_id}')
        os.system(f"git config --global --add safe.directory {repo_path}")
        os.system(f"rm -rf {repo_path}/.git/config.lock")

        cveid = f"{cve_id}_{pre_commit}_{post_commit}"
        if os.path.exists(f"./results_cache/{cveid}/taint_path.json"):
            fp = open(f"./results_cache/{cveid}/taint_path.json", "r")
            taint_path = json.load(fp)
            fp.close()
            if taint_path != {} and taint_path['pre'] != [] and taint_path['post'] != []:
                continue
                
        workers.append(cveid)
        work_list.append((repo_path, pre_commit, post_commit, cveid))
    results = cpu_heater.multiprocess(get_clustring, work_list, max_workers=64, show_progress=True)
    done = []
    for ret in results:
        for cveid in ret:
            if ret[cveid]['results'] == 'FAILED':
                errors[cveid] = ret[cveid]
            done.append(cveid)

    for cveid in workers:
        if cveid not in done and cveid not in errors:
            errors[cveid] = {}
            errors[cveid]['results'] = "FAILED"
            errors[cveid]['summary'] = "TIMEOUT"
            errors[cveid]['details'] = "TIMEOUT"
        
    ## phase2&3 critical statements extraction&recovery
    for meta in tqdm(reversed(cve_metas), total=len(cve_metas)):        
        repohost = meta.get("repohost", None)
        repo_name = meta.get("repo_name", None)
        if repo_name.endswith("@@"):
            repo_name = repo_name[:-2]
        pre_commit = meta.get("pre_commit", None).strip().replace(" ","").replace(" \\n","").replace("\n","").replace("\t","").replace("?w=1", "").replace("\\n","")
        post_commit = meta.get("post_commit", None).strip().replace(" ","").replace(" \\n","").replace("\n","").replace("\t","").replace("?w=1", "").replace("\\n","")
        cve_id = meta.get("CVE_ID", None)

        if repo_name == None:
            errors[cve_id + "__NoneRepo"] = {}
            errors[cve_id + "__NoneRepo"]['results'] = "FAILED"
            errors[cve_id + "__NoneRepo"]['summary'] = "no such repo"
            errors[cve_id + "__NoneRepo"]['details'] = "no such repo"
            continue

        if not os.path.exists(os.path.join(repo_dir, f"{repo_name}_{cve_id}")):
            os.makedirs(os.path.join(repo_dir, f"{repo_name}_{cve_id}"))
            os.system(f"cp -r {os.path.join(repo_dir, repo_name, '.git')} {os.path.join(repo_dir, f'{repo_name}_{cve_id}')}")
        repo_path = os.path.join(repo_dir,  f'{repo_name}_{cve_id}')
        os.system(f"git config --global --add safe.directory {repo_path}")
        os.system(f"rm -rf {repo_path}/.git/config.lock")

        cveid = f"{cve_id}_{pre_commit}_{post_commit}"
        if pre_commit == "660b513d99bced8783a4a5984ac2f742c74ebbdd":
            pre_commit = "ad6d7cf88d6673167ca1f517248af9409a9f1be1"
        if post_commit == "660b513d99bced8783a4a5984ac2f742c74ebbdd":
            post_commit = "ad6d7cf88d6673167ca1f517248af9409a9f1be1"   
        if not os.path.exists(f"./results_cache/{cveid}/taint_path.json"):
            taint_path = {
                "pre": [],
                "post": []
            }
        else:            
            fp = open(f"./results_cache/{cveid}/taint_path.json", "r")
            taint_path = json.load(fp)
            fp.close()
            
    
        workers.append(cveid)

        worklist.append((cveid, repo_path, pre_commit, post_commit))


    results = cpu_heater.multiprocess(construct_taint_path, worklist, max_workers=16, show_progress=True, timeout=600)

    done = []
    for ret in results:
        for cveid in ret:
            if ret[cveid]['results'] == 'FAILED':
                errors[cveid] = ret[cveid]
            done.append(cveid)

    for cveid in workers:
        if cveid not in done and cveid not in errors:
            errors[cveid] = {}
            errors[cveid]['results'] = "FAILED"
            errors[cveid]['summary'] = "TIMEOUT"
            errors[cveid]['details'] = "TIMEOUT"
        
    fp = open("error_cve.json", "w")
    json.dump(errors, fp, indent=4)
    fp.close()