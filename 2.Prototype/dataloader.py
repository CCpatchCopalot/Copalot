import pandas as pd
from tqdm import tqdm

class DataLoader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.df = pd.read_excel(file_path, header=0)
    
    def load_data(self):
        results = []
        
        for index, row in self.df.iterrows():
            cve_id = row.get('CVE_ID', '')
            commits = [commit.strip() for commit in row.get("patch", "").split("\n")]
            repo_name, pre_commit, post_commit, repohost = self.process_commits(commits)

            tool_results = row.get('TOOL_R2', '')
            results.append({
                "CVE_ID": cve_id,
                "repo_name": repo_name,
                "pre_commit": pre_commit.strip().replace("\n","").replace("\r","").replace("\t","").replace(" ","").replace("#7553","").replace("?expanded=1",""),
                "post_commit": post_commit.strip().replace("\n","").replace("\r","").replace("\t","").replace(" ","").replace("#7553","").replace("?expanded=1",""),
                "repohost": repohost,
                "tool_results":tool_results
            })
            
        return results        
    def process_commits(self, commits):
        first_commit, last_commit = commits[0], commits[-1]
        if "ghostscript" in first_commit:
            repohost = "ghostscript"
        elif "gitlab" in first_commit:
            repohost = "gitlab"
        else:
            repohost = "github"
        
        if repohost == "gitlab":
            base_url = "https://gitlab.com/"
        elif repohost == "ghostscript":
            return "ghostscript@@ghostscript", first_commit.split("=")[-1], first_commit.split("=")[-1], repohost
        else:
            base_url = "https://github.com/"
        
        if repohost == "gitlab":
            split_token = "/-/commit/"
        elif repohost == "ghostscript":
            split_token = None
        else:
            split_token = "/commit/"
        
        repo_name = first_commit.replace(base_url, "").split(split_token)[0].replace("/", "@@")
        pre_commit = first_commit.split(split_token)[1].split("#diff")[0]
        post_commit = last_commit.split(split_token)[1].split("#diff")[0]
        return repo_name, pre_commit, post_commit, repohost