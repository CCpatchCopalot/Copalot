import platform
import os

version = "3.1.0" 
pf = platform.platform()
if "Windows" in pf:  
    gitBinary = r"path\to\git.exe"
    diffBinary = r"path\to\diff.exe"
else:  
    gitBinary = "git"
    diffBinary = "diff"
    javaBinary = "java"


CTAGS_PATH = "/path/to/ctags"
joern_path = "/path/to/joern/joern-cli"
excel_path = "/path/to/dataset"
LLM_KEY = "api_key"

encoding_format = "ISO-8859-1"
timeout_repo_list_file="timeoutRepo.json"
jump_threshold=3
subprocess_exec_max_time_sec=4*60*60
subprocess_exam_time_sec=60
file_num_threshold=100
warning_info="min_dir contains too many files"