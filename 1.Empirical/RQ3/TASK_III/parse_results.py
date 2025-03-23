import pandas as pd
import json
import sys
import os
from tqdm import tqdm

def get_ccpatch_metrics():
    fp = open("../../RQ1/taxonomy_cve_lists.json")
    type_cves = json.load(fp)
    fp.close()

    file_path = 'results_tgpatch.xlsx'
    df = pd.read_excel(file_path)
    
    df_dict_cc = df.to_dict(orient='records')  

    tp_v = 0
    fp_v = 0
    fn_v = 0

    tp_f = 0
    fp_f = 0
    fn_f = 0
    results = {}
    tp_data = []

    for data in df_dict_cc:
        for typ in type_cves:
            if typ not in ['Functional Change', 'Fixing Change', 'Equivalent Change']:
                continue
            if typ not in results:
                results[typ] = {}            
            if data['CVE'] not in type_cves[typ]:
                continue
            if data['TP/FP'] == "TP":
                try:
                    results[typ]['tg_TP'] += 1
                except:
                    results[typ]['tg_TP'] = 1
            if 'FIRE' in data['TOOL']:
                if 'FIRE' not in results[typ]:
                    results[typ]['FIRE'] = {}
                if data['TP/FP'] == "TP":
                    try:
                        results[typ]['FIRE']['tg_TP'] += 1
                    except:
                        results[typ]['FIRE']['tg_TP'] = 1
                else:
                    try:
                        results[typ]['FIRE']['tg_FP'] += 1
                    except:
                        results[typ]['FIRE']['tg_FP'] = 1
            
            if 'VUDDY' in data['TOOL']:
                if 'VUDDY' not in results[typ]:
                    results[typ]['VUDDY'] = {}
                if data['TP/FP'] == "TP":
                    try:
                        results[typ]['VUDDY']['tg_TP'] += 1
                    except:
                        results[typ]['VUDDY']['tg_TP'] = 1
                else:
                    try:
                        results[typ]['VUDDY']['tg_FP'] += 1
                    except:
                        results[typ]['VUDDY']['tg_FP'] = 1

    file_path = 'results_ccpatch.xlsx'
    df = pd.read_excel(file_path)
    
    df_dict_cc = df.to_dict(orient='records') 

    for data in df_dict_cc:
        for typ in type_cves:
            if typ not in ['Functional Change', 'Fixing Change', 'Equivalent Change']:
                continue
            if typ not in results:
                results[typ] = {}            
            if data['CVE'] not in type_cves[typ]:
                continue
            if data['TP/FP'] == "TP":
                try:
                    results[typ]['cc_TP'] += 1
                except:
                    results[typ]['cc_TP'] = 1
            if 'FIRE' in data['TOOL']:
                if 'FIRE' not in results[typ]:
                    results[typ]['FIRE'] = {}
                if data['TP/FP'] == "TP":
                    try:
                        results[typ]['FIRE']['cc_TP'] += 1
                    except:
                        results[typ]['FIRE']['cc_TP'] = 1
                else:    
                    try:
                        results[typ]['FIRE']['cc_FP'] += 1
                    except:
                        results[typ]['FIRE']['cc_FP'] = 1
            
            if 'VUDDY' in data['TOOL']:
                if 'VUDDY' not in results[typ]:
                    results[typ]['VUDDY'] = {}
                if data['TP/FP'] == "TP":
                    try:
                        results[typ]['VUDDY']['cc_TP'] += 1
                    except:
                        results[typ]['VUDDY']['cc_TP'] = 1
                else:
                    try:
                        results[typ]['VUDDY']['cc_FP'] += 1
                    except:
                        results[typ]['VUDDY']['cc_FP'] = 1
    for typ in results:
        for tool in results[typ]:
            if tool == "cc_TP" or tool == "tg_TP":
                continue
            print(typ, tool)
            results[typ][tool]['tg_pre'] = results[typ][tool]['tg_TP'] / (results[typ][tool]['tg_TP']+results[typ][tool]['tg_FP'])
            results[typ][tool]['tg_rec'] = results[typ][tool]['tg_TP'] / results[typ]['tg_TP']
            results[typ][tool]['tg_f1'] = 2*results[typ][tool]['tg_pre']*results[typ][tool]['tg_rec'] / (results[typ][tool]['tg_rec']+results[typ][tool]['tg_pre'])
            results[typ][tool]['cc_pre'] = results[typ][tool]['cc_TP'] / (results[typ][tool]['cc_TP']+results[typ][tool]['cc_FP'])
            results[typ][tool]['cc_rec'] = results[typ][tool]['cc_TP'] / results[typ]['cc_TP']
            results[typ][tool]['cc_f1'] = 2*results[typ][tool]['cc_pre']*results[typ][tool]['cc_rec'] / (results[typ][tool]['cc_rec']+results[typ][tool]['cc_pre'])
    
    fp = open("results.json","w")
    json.dump(results, fp, indent=4)
    fp.close()

if __name__ == "__main__":
    get_ccpatch_metrics()
        