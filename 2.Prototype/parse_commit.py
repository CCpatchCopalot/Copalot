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
from diffparser import gitdiff
from ast_parser import ASTParser
import ast_parser
from common import Language
import format


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

