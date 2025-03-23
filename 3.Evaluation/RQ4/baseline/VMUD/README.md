### Environment Setup:

1. **Joern :** we use the version of 1.1.1377. 

   The installation process for Joern can be found at https://docs.joern.io/installation.

   To install and run Joern, JDK 11 environment is required.

2. **doxygen:**  we use the version of 1.10. 

   The installation process for Joern can be found at https://github.com/doxygen/doxygen.

3. **Python**: The required libraries for the version include json, os, hashlib, re, sys, queue, xml, pickle and networkx.

4. **ctags:** The installation process for ctags can be found at https://github.com/universal-ctags/ctags.

### List of File:
- *pagerank.py*: python script to get the PageRank score of each modified function in the patch.
- *config.py*: configuration file for PageRank score generation.

### configuration for PageRank:
- *Doxygen_conf_location*: the absolute path to the directory of doxygen.
- *work_path*: the absolute path to the directory of joern-cli
- *error_log_file*:the path to the error log file
- *timeout_repo_list_file*: the file path to record repository information for timeouts
- *method_info_location*: the file path to record method information
- *no_define_location_prefix*: the directory path to store the call graph information
- *jump_threshold*: call graph jump threshold, the default is 3
- *subprocess_exec_max_time_sec*: the time limit for call graph generation, specified in seconds, the default is 4 hours
- *subprocess_exam_time_sec*: the polling frequency for call graph generation process, specified in seconds, the default is 1minute
- *file_num_threshold*: the scale of files involved in the call graph, the default is 5000
- *pagerank_location_prefix*: the directory path to store the PageRank score files.

### Input & Output of VMUD
- **Input:** CVE-ID, Project's path affected by CVE, patch commit file path (patch commit file can be obtained through git show + commit hash)
- **Output**: PageRank score of each modified function
- **generation step:** please place the [files](Copalot/3.Evaluation/RQ4/baseline/VMUD) into the *joern-cli* directory. Ensure that the directory includes executable files such as *joern*, *joern-parse*, and *joern-flow*. After complete the relevant entries in the configuration file, just run the following command:

```
python SignatureGenetation.py CVE_ID commit_file_location git_repo_location
```

- **CVE_ID**: the CVE-ID corresponding to the patch file.

- **commit_file_location**: the absolute path to the file storing GitHub commit content.

- **git_repo_location:** the absolute path to the directory of the GitHub repository corresponding to the CVE.