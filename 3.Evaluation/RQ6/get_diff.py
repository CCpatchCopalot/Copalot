import os
from tqdm import tqdm
import json

not_found = set()
wrong_answer = set()
results_path = "/path/to/results"
for file in tqdm(os.listdir(results_path)):
    if not os.path.exists(f"{results_path}/{file}/ccpatch_before_refine.diff"):
        not_found.add(file.split("_")[0])
    else:
        fp = open(f"{results_path}/{file}/ccpatch_before_refine.diff")
        lines = fp.readlines()
        fp.close()

        diff_lines = ""
        st = -1
        success = True
        for i, line in enumerate(lines):
            if line.startswith("```diff"):
                st = i+1
            elif line.startswith("```"):
                # print(st, i)
                # print(lines[st:i])
                if st != -1:
                    diff_lines += "".join(lines[st:i])
                    st = -1
                else:
                    wrong_answer.add(file.split("_")[0])
                    success = False
                    break
            elif line.startswith("diff --git "):
                if st != -1:
                    diff_lines += "".join(lines[st:i-1])
                st = i

        if st != -1:
            diff_lines += "".join(lines[st:len(lines)])
        if success and diff_lines != "":
            fp = open(f"{results_path}/{file}/ccpatch.diff", "w")
            fp.write(diff_lines)
            fp.close()
        else:
            wrong_answer.add(file.split("_")[0])


fp = open("not_found.json", "w")
json.dump(list(not_found), fp, indent=4)
fp.close()

fp = open("wrong_answer.json", "w")
json.dump(list(wrong_answer), fp, indent=4)
fp.close()
