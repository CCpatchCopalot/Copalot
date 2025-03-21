import json
import os
from tqdm import tqdm

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../2.Prototype')))
from dataloader import DataLoader
from diffparser import gitdiff
from difftools import git_diff_code, parse_diff
from ast_parser import ASTParser
import ast_parser
from common import Language
import format
from config import excel_path

def get_prime_vul():
    fp = open("../../1.Empirical/RQ2/cvc_info.json")
    cvc_info = json.load(fp)
    fp.close()

    fp = open("../../1.Empirical/RQ1/taxonomy_cve_lists.json")
    type_cves = json.load(fp)
    fp.close()

    cc = 0
    cc_1 = 0
    cc_2 = 0
    cc_3 = 0

    fp_all = 0
    fp_1 = 0
    fp_2 = 0
    fp_3 = 0

    p = 0
    p_1 = 0
    p_2 = 0
    p_3 = 0

    loader = DataLoader(file_path = excel_path)
    cve_metas = loader.load_data()
    for meta in tqdm(reversed(cve_metas), total=len(cve_metas)):
        repohost = meta.get("repohost", None)
        repo_name = meta.get("repo_name", None)
        pre_commit = meta.get("pre_commit", None).strip().replace(" ","").replace(" \\n","").replace("\n","").replace("\t","").replace("?w=1", "").replace("\\n","")
        post_commit = meta.get("post_commit", None).strip().replace(" ","").replace(" \\n","").replace("\n","").replace("\t","").replace("?w=1", "").replace("\\n","")
        # print(pre_commit, post_commit)
        cve = meta.get("CVE_ID", None)
        
        if cve not in cvc_info:
            continue
        
        # print(cveid)
        cveid = f"{cve}_{pre_commit}_{post_commit}"
        
        if not os.path.exists(f"./prime_vul_results/{cveid}.json"):
            continue
        
        p += len(set(cvc_info[cve]['f_mixlist']).union(set(cvc_info[cve]['f_cvclist'])))        
        if cve in type_cves['Equivalent Change']:
            p_3 += len(set(cvc_info[cve]['f_mixlist']).union(set(cvc_info[cve]['f_cvclist'])))
        if cve in type_cves['Fixing Change']:
            p_2 += len(set(cvc_info[cve]['f_mixlist']).union(set(cvc_info[cve]['f_cvclist'])))
        if cve in type_cves['Functional Change']:
            p_1 += len(set(cvc_info[cve]['f_mixlist']).union(set(cvc_info[cve]['f_cvclist'])))
        fp = open(f"./prime_vul_results/{cveid}.json")
        desc = json.load(fp)
        fp.close()

        func = desc[cve]['desc_function']

        flag_tp = True
        for true_func in set(cvc_info[cve]['f_mixlist']).union(set(cvc_info[cve]['f_cvclist'])):
            if func not in true_func:
                flag_tp = False

        flag_fp = False
        for false_func in cvc_info[cve]['f_uvclist']:
            if func in false_func:
                flag_fp = True

        

        if flag_tp:
            cc += 1
            if cve in type_cves['Equivalent Change']:
                cc_3 += 1
            if cve in type_cves['Fixing Change']:
                cc_2 += 1
            if cve in type_cves['Functional Change']:
                cc_1 += 1

        if flag_fp:
            fp_all += 1
            if cve in type_cves['Equivalent Change']:
                fp_3 += 1
            if cve in type_cves['Fixing Change']:
                fp_2 += 1
            if cve in type_cves['Functional Change']:
                fp_1 += 1

    
    prec = cc / (cc+fp_all)
    prec_1 = cc_1 / (cc_1+fp_1)
    prec_2 = cc_2 / (cc_2+fp_2)
    prec_3 = cc_3 / (cc_3+fp_3)

    rec = cc/p
    rec_1 = cc_1 / p_1
    rec_2 = cc_2 / p_2
    rec_3 = cc_3 / p_3

    f1 = 2*prec*rec / (prec + rec)
    results = {
        "CC1":cc_1,
        "CC2":cc_2,
        "CC3":cc_3,
        "CC":cc,
        "pref":prec,
        "recf":rec,
        "f1f":f1
    }
    fp = open("results_primevul.json", "w")
    json.dump(results, fp, indent=4)
    fp.close()



def get_vmud():
    fp = open("vmud_results.json")
    vmud_results = json.load(fp)
    fp.close()

    fp = open("../../1.Empirical/RQ2/cvc_info.json")
    cvc_info = json.load(fp)
    fp.close()

    fp = open("../../1.Empirical/RQ1/taxonomy_cve_lists.json")
    type_cves = json.load(fp)
    fp.close()

    loader = DataLoader(file_path = excel_path)
    cve_metas = loader.load_data()
    cc = 0
    cc_1 = 0
    cc_2 = 0
    cc_3 = 0
    fp_all = 0
    p = 0
    for meta in tqdm(reversed(cve_metas), total=len(cve_metas)):
        repohost = meta.get("repohost", None)
        repo_name = meta.get("repo_name", None)
        pre_commit = meta.get("pre_commit", None).strip().replace(" ","").replace(" \\n","").replace("\n","").replace("\t","").replace("?w=1", "").replace("\\n","")
        post_commit = meta.get("post_commit", None).strip().replace(" ","").replace(" \\n","").replace("\n","").replace("\t","").replace("?w=1", "").replace("\\n","")
        cve = meta.get("CVE_ID", None)
        
        if cve not in cvc_info:
            continue
        cveid = f"{cve}_{pre_commit}_{post_commit}"
        p += len(set(cvc_info[cve]['f_mixlist']).union(set(cvc_info[cve]['f_cvclist'])))
        
        flag_all = True
        for true_func in set(cvc_info[cve]['f_mixlist']).union(set(cvc_info[cve]['f_cvclist'])):
            flag_per = False
            for func in vmud_results[cve]:
                if true_func.split("/")[-1] in func:
                    flag_per = True
                    break
            if not flag_per:
                flag_all = False
                break

        flag_fp = True
        for false_func in cvc_info[cve]['f_uvclist']:
            flag_per = False
            for func in vmud_results[cve]:
                if true_func.split("/")[-1] in func:
                    flag_per = True
                    break
            if not flag_per:
                flag_fp = False
                break
                
        if flag_all:
            cc += 2
            if cve in type_cves['Equivalent Change']:
                cc_3 += 2
            if cve in type_cves['Fixing Change']:
                cc_2 += 2
            if cve in type_cves['Functional Change']:
                cc_1 += 2

        if flag_fp:
            fp_all += 1

    
    prec = cc / (cc+fp_all)
    rec = cc/p
    f1 = 2*prec*rec / (prec + rec)
    print(prec, rec, f1)
    results = {
        "CC1":cc_1,
        "CC2":cc_2,
        "CC3":cc_3,
        "CC":cc,
        "pref":prec,
        "recf":rec,
        "f1f":f1
    }
    fp = open("results_vmud.json", "w")
    json.dump(results, fp, indent=4)
    fp.close()


def get_gpt4o():
    fp = open("cvc_info_gpt4o.json")
    results_4o = json.load(fp)
    fp.close()

    fp = open("../../1.Empirical/RQ2/cvc_info.json")
    cvc_info = json.load(fp)
    fp.close()

    fp = open("../../1.Empirical/RQ1/taxonomy_cve_lists.json")
    type_cves = json.load(fp)
    fp.close()

    p = 0
    tp = 0
    fp = 0
    cc = 0
    cc_1 = 0
    cc_2 = 0
    cc_3 = 0

    for cve in cvc_info:
        if cve not in results_4o:
            continue
        
        
        cvc = set(cvc_info[cve]['f_mixlist']).union(set(cvc_info[cve]['f_cvclist']))
        cvc_4o = set(results_4o[cve]['f_mixlist']).union(set(results_4o[cve]['f_cvclist']))

        for func in cvc_4o:
            if func in cvc:
                tp += 1
            else:
                fp += 1
        p += len(cvc)

        if cvc == cvc_4o:
            cc += 1            
            if cve in type_cves['Equivalent Change']:
                cc_3 += 1
            if cve in type_cves['Fixing Change']:
                cc_2 += 1
            if cve in type_cves['Functional Change']:
                cc_1 += 1
    
    pre = tp / (tp+fp)
    rec = tp / p
    f1 = 2*pre*rec/(pre+rec)
    results = {
        "CC1":cc_1,
        "CC2":cc_2,
        "CC3":cc_3,
        "CC":cc,
        "pref":prec,
        "recf":rec,
        "f1f":f1
    }
    fp = open("results_4o_func_level.json", "w")
    json.dump(results, fp, indent=4)
    fp.close()


def get_ours():
    fp = open("cvc_info_copalot.json")
    results_4o = json.load(fp)
    fp.close()

    fp = open("../../1.Empirical/RQ2/cvc_info.json")
    cvc_info = json.load(fp)
    fp.close()

    fp = open("../../1.Empirical/RQ1/taxonomy_cve_lists.json")
    type_cves = json.load(fp)
    fp.close()

    p = 0
    tp = 0
    fp = 0
    cc = 0
    cc_1 = 0
    cc_2 = 0
    cc_3 = 0

    for cve in cvc_info:
        if cve not in results_4o:
            continue
        
        
        cvc = set(cvc_info[cve]['f_mixlist']).union(set(cvc_info[cve]['f_cvclist']))
        cvc_4o = set(results_4o[cve]['f_mixlist']).union(set(results_4o[cve]['f_cvclist']))

        for func in cvc_4o:
            if func in cvc:
                tp += 1
            else:
                fp += 1
        p += len(cvc)

        if cvc == cvc_4o:
            cc += 1            
            if cve in type_cves['Equivalent Change']:
                cc_3 += 1
            if cve in type_cves['Fixing Change']:
                cc_2 += 1
            if cve in type_cves['Functional Change']:
                cc_1 += 1
    
    pre = tp / (tp+fp)
    rec = tp / p
    f1 = 2*pre*rec/(pre+rec)
    fp = open("results_copalot_func_level.json", "w")
    json.dump(results, fp, indent=4)
    fp.close()



if __name__ == "__main__":
    get_prime_vul()
    get_vmud()
    get_gpt4o()
    get_ours()