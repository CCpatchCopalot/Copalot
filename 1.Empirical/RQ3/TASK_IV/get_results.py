import pandas as pd
import json
from collections import Counter
df = pd.read_excel("./fuzz_result.xlsx")
sheet_data = df.to_dict(orient='records')

results = {}
results['all'] = {}
results['all']['aflgo'] = {}
results['all']['beacon'] = {}
results['Equivalent Change'] = {}
results['Equivalent Change']['aflgo'] = {}
results['Equivalent Change']['beacon'] = {}
results['Fixing Change'] = {}
results['Fixing Change']['aflgo'] = {}
results['Fixing Change']['beacon'] = {}
results['Functional Change'] = {}
results['Functional Change']['aflgo'] = {}
results['Functional Change']['beacon'] = {}

fp = open("../../RQ1/taxonomy_cve_lists.json")
type_cves = json.load(fp)
fp.close()

cve_type_counter = Counter()

for data in sheet_data:
    if str(data['CVE']) =="nan":
        continue
    cve_type_counter['all'] += 1

    if data['aflgo-origin'] != -1 and str(data['aflgo-origin']) != "nan" and data['aflgo-ccpatch'] != -1 and str(data['aflgo-ccpatch']) != "nan":
        try:
            results['all']['aflgo']['rt_raw'] +=  data['aflgo-origin']
            results['all']['aflgo']['rt_cc'] += data['aflgo-ccpatch']
            results['all']['aflgo']['rt_count'] += 1
        except:
            results['all']['aflgo']['rt_raw'] = data['aflgo-origin']
            results['all']['aflgo']['rt_cc'] = data['aflgo-ccpatch']
            results['all']['aflgo']['rt_count'] = 1

    if data['aflgo-origin'] != -1 and str(data['aflgo-origin'] )!= "nan":
        try:
            results['all']['aflgo']['rr_raw'] +=  1
        except:
            results['all']['aflgo']['rr_raw'] =  1
    if data['aflgo-ccpatch'] != -1 and str(data['aflgo-ccpatch']) != "nan":
        try:
            results['all']['aflgo']['rr_cc'] +=  1
        except:
            results['all']['aflgo']['rr_cc'] =  1

    if data['beacon-origin'] != -1 and str(data['beacon-origin']) != "nan" and data['beacon-ccpatch'] != -1 and str(data['beacon-ccpatch']) != "nan":
        try:
            results['all']['beacon']['rt_raw'] +=  data['beacon-origin']
            results['all']['beacon']['rt_cc'] += data['beacon-ccpatch']
            results['all']['beacon']['rt_count'] += 1
        except:
            results['all']['beacon']['rt_raw'] = data['beacon-origin']
            results['all']['beacon']['rt_cc'] = data['beacon-ccpatch']
            results['all']['beacon']['rt_count'] = 1

    if data['beacon-origin'] != -1 and str(data['beacon-origin']) != "nan":
        try:
            results['all']['beacon']['rr_raw'] +=  1
        except:
            results['all']['beacon']['rr_raw'] =  1
    if data['beacon-ccpatch'] != -1 and str(data['beacon-ccpatch']) != "nan":
        try:
            results['all']['beacon']['rr_cc'] +=  1
        except:
            results['all']['beacon']['rr_cc'] =  1

    if data['CVE'] in type_cves['Equivalent Change']:
        cve_type_counter['Equivalent Change'] += 1

        if data['aflgo-origin'] != -1 and str(data['aflgo-origin']) != "nan" and data['aflgo-ccpatch'] != -1 and str(
                data['aflgo-ccpatch']) != "nan":
            try:
                results['Equivalent Change']['aflgo']['rt_raw'] += data['aflgo-origin']
                results['Equivalent Change']['aflgo']['rt_cc'] += data['aflgo-ccpatch']
                results['Equivalent Change']['aflgo']['rt_count'] += 1
            except:
                results['Equivalent Change']['aflgo']['rt_raw'] = data['aflgo-origin']
                results['Equivalent Change']['aflgo']['rt_cc'] = data['aflgo-ccpatch']
                results['Equivalent Change']['aflgo']['rt_count'] = 1

        if data['aflgo-origin'] != -1 and str(data['aflgo-origin'] )!= "nan":
            try:
                results['Equivalent Change']['aflgo']['rr_raw'] +=  1
            except:
                results['Equivalent Change']['aflgo']['rr_raw'] =  1
        if data['aflgo-ccpatch'] != -1 and str(data['aflgo-ccpatch']) != "nan":
            try:
                results['Equivalent Change']['aflgo']['rr_cc'] +=  1
            except:
                results['Equivalent Change']['aflgo']['rr_cc'] =  1

        if data['beacon-origin'] != -1 and str(data['beacon-origin']) != "nan" and data['beacon-ccpatch'] != -1 and str(
                data['beacon-ccpatch']) != "nan":
            try:
                results['Equivalent Change']['beacon']['rt_raw'] += data['beacon-origin']
                results['Equivalent Change']['beacon']['rt_cc'] += data['beacon-ccpatch']
                results['Equivalent Change']['beacon']['rt_count'] += 1
            except:
                results['Equivalent Change']['beacon']['rt_raw'] = data['beacon-origin']
                results['Equivalent Change']['beacon']['rt_cc'] = data['beacon-ccpatch']
                results['Equivalent Change']['beacon']['rt_count'] = 1
        if data['beacon-origin'] != -1 and str(data['beacon-origin']) != "nan":
            try:
                results['Equivalent Change']['beacon']['rr_raw'] +=  1
            except:
                results['Equivalent Change']['beacon']['rr_raw'] =  1
        if data['beacon-ccpatch'] != -1 and str(data['beacon-ccpatch']) != "nan":
            try:
                results['Equivalent Change']['beacon']['rr_cc'] +=  1
            except:
                results['Equivalent Change']['beacon']['rr_cc'] =  1

    if data['CVE'] in type_cves['Fixing Change']:
        cve_type_counter['Fixing Change'] += 1
        if data['aflgo-origin'] != -1 and str(data['aflgo-origin']) != "nan" and data['aflgo-ccpatch'] != -1 and str(
                data['aflgo-ccpatch']) != "nan":
            try:
                results['Fixing Change']['aflgo']['rt_raw'] += data['aflgo-origin']
                results['Fixing Change']['aflgo']['rt_cc'] += data['aflgo-ccpatch']
                results['Fixing Changee']['aflgo']['rt_count'] += 1
            except:
                results['Fixing Change']['aflgo']['rt_raw'] = data['aflgo-origin']
                results['Fixing Change']['aflgo']['rt_cc'] = data['aflgo-ccpatch']
                results['Fixing Change']['aflgo']['rt_count'] = 1
        if data['aflgo-origin'] != -1 and str(data['aflgo-origin'] )!= "nan":
            try:
                results['Fixing Change']['aflgo']['rr_raw'] +=  1
            except:
                results['Fixing Change']['aflgo']['rr_raw'] =  1
        if data['aflgo-ccpatch'] != -1 and str(data['aflgo-ccpatch']) != "nan":
            try:
                results['Fixing Change']['aflgo']['rr_cc'] +=  1
            except:
                results['Fixing Change']['aflgo']['rr_cc'] =  1

        if data['beacon-origin'] != -1 and str(data['beacon-origin']) != "nan" and data['beacon-ccpatch'] != -1 and str(
                data['beacon-ccpatch']) != "nan":
            try:
                results['Fixing Change']['beacon']['rt_raw'] += data['beacon-origin']
                results['Fixing Change']['beacon']['rt_cc'] += data['beacon-ccpatch']
                results['Fixing Change']['beacon']['rt_count'] += 1
            except:
                results['Fixing Change']['beacon']['rt_raw'] = data['beacon-origin']
                results['Fixing Change']['beacon']['rt_cc'] = data['beacon-ccpatch']
                results['Fixing Change']['beacon']['rt_count'] = 1
        if data['beacon-origin'] != -1 and str(data['beacon-origin']) != "nan":
            try:
                results['Fixing Change']['beacon']['rr_raw'] +=  1
            except:
                results['Fixing Change']['beacon']['rr_raw'] =  1
        if data['beacon-ccpatch'] != -1 and str(data['beacon-ccpatch']) != "nan":
            try:
                results['Fixing Change']['beacon']['rr_cc'] +=  1
            except:
                results['Fixing Change']['beacon']['rr_cc'] =  1

    if data['CVE'] in type_cves['Functional Change']:
        cve_type_counter['Functional Change'] += 1

        if data['aflgo-origin'] != -1 and str(data['aflgo-origin']) != "nan" and data['aflgo-ccpatch'] != -1 and str(
                data['aflgo-ccpatch']) != "nan":
            try:
                results['Functional Change']['aflgo']['rt_raw'] += data['aflgo-origin']
                results['Functional Change']['aflgo']['rt_cc'] += data['aflgo-ccpatch']
                results['Functional Change']['aflgo']['rt_count'] += 1
            except:
                results['Functional Change']['aflgo']['rt_raw'] = data['aflgo-origin']
                results['Functional Change']['aflgo']['rt_cc'] = data['aflgo-ccpatch']
                results['Functional Change']['aflgo']['rt_count'] = 1

        if data['aflgo-origin'] != -1 and str(data['aflgo-origin'] )!= "nan":
            try:
                results['Functional Change']['aflgo']['rr_raw'] +=  1
            except:
                results['Functional Change']['aflgo']['rr_raw'] =  1
        if data['aflgo-ccpatch'] != -1 and str(data['aflgo-ccpatch']) != "nan":
            try:
                results['Functional Change']['aflgo']['rr_cc'] +=  1
            except:
                results['Functional Change']['aflgo']['rr_cc'] =  1

        if data['beacon-origin'] != -1 and str(data['beacon-origin']) != "nan" and data['beacon-ccpatch'] != -1 and str(
                data['beacon-ccpatch']) != "nan":
            try:
                results['Functional Change']['beacon']['rt_raw'] += data['beacon-origin']
                results['Functional Change']['beacon']['rt_cc'] += data['beacon-ccpatch']
                results['Functional Change']['beacon']['rt_count'] += 1
            except:
                results['Functional Change']['beacon']['rt_raw'] = data['beacon-origin']
                results['Functional Change']['beacon']['rt_cc'] = data['beacon-ccpatch']
                results['Functional Change']['beacon']['rt_count'] = 1

        if data['beacon-origin'] != -1 and str(data['beacon-origin']) != "nan":
            try:
                results['Functional Change']['beacon']['rr_raw'] +=  1
            except:
                results['Functional Change']['beacon']['rr_raw'] =  1
        
        if data['beacon-ccpatch'] != -1 and str(data['beacon-ccpatch']) != "nan":
            try:
                results['Functional Change']['beacon']['rr_cc'] +=  1
            except:
                results['Functional Change']['beacon']['rr_cc'] =  1

print(cve_type_counter)
print(results)

for typ in results:
    for tool in results[typ]:
        results[typ][tool]["rt_raw"] = round(results[typ][tool]["rt_raw"] / results[typ][tool]["rt_count"], 2)
        results[typ][tool]["rt_cc"] = round(results[typ][tool]["rt_cc"] / results[typ][tool]["rt_count"], 2)
        results[typ][tool]["rr_raw"] = round(results[typ][tool]["rr_raw"] / cve_type_counter[typ], 2)
        results[typ][tool]["rr_cc"] = round(results[typ][tool]["rr_cc"] / cve_type_counter[typ], 2)
        results[typ][tool]['rr_ratio'] = round((results[typ][tool]["rr_cc"] - results[typ][tool]["rr_raw"]) / results[typ][tool]["rr_raw"], 2)
        results[typ][tool]['rt_ratio'] = abs(round((results[typ][tool]["rt_cc"] - results[typ][tool]["rt_raw"]) / results[typ][tool]["rt_raw"], 2))

fp = open("results.json", "w")
json.dump(results, fp, indent=4)
fp.close()