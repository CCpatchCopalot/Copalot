We assessed Copalot using the ground truth, and compared its performance with baseline approaches. See [RQ4 results](results.json).
- The raw results of `PRIMEVUL` is shown in [prime_vul_results](prime_vul_results), the raw results of `VMUD` is shown in [vmud_results.json](vmud_results.json), the raw results of `GPT-4O` is shown in [results-4o](resutls_4o), and the raw results of `Copalot` is shown in [results_copalot](results_copalot)
- For `VMUD` and `PRIMEVUL`, just run `python get_baseline_results.py` to get the function-level effectiveness of them.
- For other baseline and `Copalot`:
    - To get the patch-level results and the function-level effectiveness, just run in the following steps:
        1. modify the result directory path in the line 7 of `get_diff.py` and run `python get_diff.py` to format the results.
        2. modify the repository directory and result directory path in the line 25 and 27 of `get_results_post.py` and run `python get_results_post.py` to get the characterics of the generated patch.
        3. run `python get_baseline_results.py` to get the function-level effectiveness of them.
    - To get the statement-level effectiveness, just modify the repository directory and result directory path in the line 25 and 27 of `get_baseline_results_stmt_level.py` and run `python get_baseline_results_stmt_level.py`
