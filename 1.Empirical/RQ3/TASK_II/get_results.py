import pandas as pd
import json

df = pd.read_excel("./patch_transfer.xlsx")
sheet_data = df.to_dict(orient='records')

results = {}
results['all'] = {}
results['all']['git'] = {}
results['all']['tsbport'] = {}
results['all']['count'] = 0
results['Equivalent Change'] = {}
results['Equivalent Change']['git'] = {}
results['Equivalent Change']['tsbport'] = {}
results['Equivalent Change']['count'] = 0
results['Fixing Change'] = {}
results['Fixing Change']['git'] = {}
results['Fixing Change']['tsbport'] = {}
results['Fixing Change']['count'] = 0
results['Functional Change'] = {}
results['Functional Change']['git'] = {}
results['Functional Change']['tsbport'] = {}
results['Functional Change']['count'] = 0

fp = open("../../RQ1/taxonomy_cve_lists.json")
type_cves = json.load(fp)
fp.close()

cnt = 0

for data in sheet_data:
    if str(data['CVE_ID']) =="nan":
        continue
    if str(data['cherry pick origin compile'] )== "nan":
        continue
    try:
        results['all']['git']['cr_raw'] +=  data['cherry pick origin compile']
    except:
        results['all']['git']['cr_raw'] =  data['cherry pick origin compile']

    try:
        results['all']['git']['fr_raw'] +=  data['cherry pick origin fix']
    except:
        results['all']['git']['fr_raw'] =  data['cherry pick origin fix']

    try:
        results['all']['git']['cr_cc'] +=  data['cherry pick ccpatch compile']
    except:
        results['all']['git']['cr_cc'] =  data['cherry pick ccpatch compile']

    try:
        results['all']['git']['fr_cc'] +=  data['cherry pick ccpatch fix']
    except:            
        results['all']['git']['fr_cc'] =  data['cherry pick ccpatch fix']

    try:
        results['all']['tsbport']['cr_raw'] +=  data['tsbport origin compile']
    except:
        results['all']['tsbport']['cr_raw'] =  data['tsbport origin compile']

    try:
        results['all']['tsbport']['fr_raw'] +=  data['tsbport origin fix']
    except:
        results['all']['tsbport']['fr_raw'] =  data['tsbport origin fix']
    results['all']['count'] += 1


    cnt += 1
    try:
        results['all']['tsbport']['cr_cc'] +=  data['tsbport ccpatch compile']
    except:
        results['all']['tsbport']['cr_cc'] =  data['tsbport ccpatch compile']

    try:
        results['all']['tsbport']['fr_cc'] +=  data['tsbport ccpatch fix']
    except:
        results['all']['tsbport']['fr_cc'] =  data['tsbport ccpatch fix']
            

    if data['CVE_ID'] in type_cves['Equivalent Change']:        
        
        try:
            results['Equivalent Change']['git']['cr_raw'] +=  data['cherry pick origin compile']
        except:
            results['Equivalent Change']['git']['cr_raw'] =  data['cherry pick origin compile']

    
        try:
            results['Equivalent Change']['git']['fr_raw'] +=  data['cherry pick origin fix']
        except:
            results['Equivalent Change']['git']['fr_raw'] =  data['cherry pick origin fix']

    
        try:
            results['Equivalent Change']['git']['cr_cc'] +=  data['cherry pick ccpatch compile']
        except:
            results['Equivalent Change']['git']['cr_cc'] =  data['cherry pick ccpatch compile']

    
        try:
            results['Equivalent Change']['git']['fr_cc'] +=  data['cherry pick ccpatch fix']
        except:            
            results['Equivalent Change']['git']['fr_cc'] =  data['cherry pick ccpatch fix']

    
        try:
            results['Equivalent Change']['tsbport']['cr_raw'] +=  data['tsbport origin compile']
        except:
            results['Equivalent Change']['tsbport']['cr_raw'] =  data['tsbport origin compile']
    
        try:
            results['Equivalent Change']['tsbport']['fr_raw'] +=  data['tsbport origin fix']
        except:
            results['Equivalent Change']['tsbport']['fr_raw'] =  data['tsbport origin fix']
    

        try:
            results['Equivalent Change']['tsbport']['cr_cc'] +=  data['tsbport ccpatch compile']
        except:
            results['Equivalent Change']['tsbport']['cr_cc'] =  data['tsbport ccpatch compile']

        try:
            results['Equivalent Change']['tsbport']['fr_cc'] +=  data['tsbport ccpatch fix']
        except:
            results['Equivalent Change']['tsbport']['fr_cc'] =  data['tsbport ccpatch fix']
                
        results['Equivalent Change']['count'] += 1


    if data['CVE_ID'] in type_cves['Fixing Change']:
        
        try:
            results['Fixing Change']['git']['cr_raw'] +=  data['cherry pick origin compile']
        except:
            results['Fixing Change']['git']['cr_raw'] =  data['cherry pick origin compile']

    
        try:
            results['Fixing Change']['git']['fr_raw'] +=  data['cherry pick origin fix']
        except:
            results['Fixing Change']['git']['fr_raw'] =  data['cherry pick origin fix']

    
        try:
            results['Fixing Change']['git']['cr_cc'] +=  data['cherry pick ccpatch compile']
        except:
            results['Fixing Change']['git']['cr_cc'] =  data['cherry pick ccpatch compile']

    
        try:
            results['Fixing Change']['git']['fr_cc'] +=  data['cherry pick ccpatch fix']
        except:            
            results['Fixing Change']['git']['fr_cc'] =  data['cherry pick ccpatch fix']

    
        try:
            results['Fixing Change']['tsbport']['cr_raw'] +=  data['tsbport origin compile']
        except:
            results['Fixing Change']['tsbport']['cr_raw'] =  data['tsbport origin compile']
    
        try:
            results['Fixing Change']['tsbport']['fr_raw'] +=  data['tsbport origin fix']
        except:
            results['Fixing Change']['tsbport']['fr_raw'] =  data['tsbport origin fix']
    

        try:
            results['Fixing Change']['tsbport']['cr_cc'] +=  data['tsbport ccpatch compile']
        except:
            results['Fixing Change']['tsbport']['cr_cc'] =  data['tsbport ccpatch compile']

        try:
            results['Fixing Change']['tsbport']['fr_cc'] +=  data['tsbport ccpatch fix']
        except:
            results['Fixing Change']['tsbport']['fr_cc'] =  data['tsbport ccpatch fix']

        results['Fixing Change']['count'] += 1

    if data['CVE_ID'] in type_cves['Functional Change']:
        
        print(data['CVE_ID'])
        try:
            results['Functional Change']['git']['cr_raw'] +=  data['cherry pick origin compile']
        except:
            results['Functional Change']['git']['cr_raw'] =  data['cherry pick origin compile']

    
        try:
            results['Functional Change']['git']['fr_raw'] +=  data['cherry pick origin fix']
        except:
            results['Functional Change']['git']['fr_raw'] =  data['cherry pick origin fix']

    
        try:
            results['Functional Change']['git']['cr_cc'] +=  data['cherry pick ccpatch compile']
        except:
            results['Functional Change']['git']['cr_cc'] =  data['cherry pick ccpatch compile']

    
        try:
            results['Functional Change']['git']['fr_cc'] +=  data['cherry pick ccpatch fix']
        except:            
            results['Functional Change']['git']['fr_cc'] =  data['cherry pick ccpatch fix']

    
        try:
            results['Functional Change']['tsbport']['cr_raw'] +=  data['tsbport origin compile']
        except:
            results['Functional Change']['tsbport']['cr_raw'] =  data['tsbport origin compile']
    
        try:
            results['Functional Change']['tsbport']['fr_raw'] +=  data['tsbport origin fix']
        except:
            results['Functional Change']['tsbport']['fr_raw'] =  data['tsbport origin fix']
    

        try:
            results['Functional Change']['tsbport']['cr_cc'] +=  data['tsbport ccpatch compile']
        except:
            results['Functional Change']['tsbport']['cr_cc'] =  data['tsbport ccpatch compile']

        try:
            results['Functional Change']['tsbport']['fr_cc'] +=  data['tsbport ccpatch fix']
        except:
            results['Functional Change']['tsbport']['fr_cc'] =  data['tsbport ccpatch fix']

        results['Functional Change']['count'] += 1

for typ in results:
    for tool in results[typ]:
        if tool == "count":
            continue
        print(typ, tool, results[typ][tool]["fr_raw"], results[typ][tool]["fr_cc"], results[typ][tool]["cr_raw"], results[typ][tool]["cr_cc"])
        results[typ][tool]["cr_raw"] = round(results[typ][tool]["cr_raw"] / results[typ]['count'], 2)
        results[typ][tool]["cr_cc"] = round(results[typ][tool]["cr_cc"] / results[typ]['count'], 2)
        results[typ][tool]["fr_raw"] = round(results[typ][tool]["fr_raw"] / results[typ]['count'], 2)
        results[typ][tool]["fr_cc"] = round(results[typ][tool]["fr_cc"] / results[typ]['count'], 2)
        if results[typ][tool]["fr_raw"] == 0:
            results[typ][tool]['fr_ratio'] = "nan"
        else:            
            results[typ][tool]['fr_ratio'] = round((results[typ][tool]["fr_cc"] - results[typ][tool]["fr_raw"]) / results[typ][tool]["fr_raw"], 2)
        if results[typ][tool]["cr_raw"] == 0:
            results[typ][tool]['cr_ratio'] = "nan"
        else:
            results[typ][tool]['cr_ratio'] = round((results[typ][tool]["cr_cc"] - results[typ][tool]["cr_raw"]) / results[typ][tool]["cr_raw"], 2)

fp = open("results.json", "w")
json.dump(results, fp, indent=4)
fp.close()