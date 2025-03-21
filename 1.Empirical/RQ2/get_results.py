import json
import os

def get_results():
    results_rq1 = {}

    fp = open("../RQ1/taxonomy_cve_lists.json")
    type_cves = json.load(fp)
    fp.close()

    fp = open("cvc_info.json")
    results = json.load(fp)
    fp.close()

    f = 0
    c = 0
    
    for type in type_cves:
        count_ratio = 0
        count_ratio_cso = 0
        count = 0
        usi_count = 0
        fmix_count = 0
        uso_ratio_count = 0
        results_rq1[type] = {}
        for cve in type_cves[type]:
            if cve not in results:
                continue            
            if results[cve]['fcvc'] + results[cve]['fuvc'] + results[cve]['fmix'] == 0:
                print(cve)
                continue
            if results[cve]['cso'] + results[cve]['cvci'] == 0:
                print(cve)
                continue
            if results[cve]['fuvc'] > 20:
                continue    
            count_ratio += 1
            try:
                results_rq1[type]['fus_ratio'] += round(results[cve]['fuvc'] / (results[cve]['fcvc'] + results[cve]['fuvc'] + results[cve]['fmix']), 2)
            except:                
                results_rq1[type]['fus_ratio'] = round(results[cve]['fuvc'] / (results[cve]['fcvc'] + results[cve]['fuvc'] + results[cve]['fmix']), 2)

            try:
                results_rq1[type]['fmix_ratio'] += round(results[cve]['fmix'] / (results[cve]['fcvc'] + results[cve]['fuvc'] + results[cve]['fmix']), 2)
            except:                
                results_rq1[type]['fmix_ratio'] = round(results[cve]['fmix'] / (results[cve]['fcvc'] + results[cve]['fuvc'] + results[cve]['fmix']), 2)
                
            try:
                results_rq1[type]['fmixus_ratio'] += round((results[cve]['fmix'] + results[cve]['fuvc']) / (results[cve]['fcvc'] + results[cve]['fuvc'] + results[cve]['fmix']), 2)
            except:                
                results_rq1[type]['fmixus_ratio'] = round((results[cve]['fmix'] + results[cve]['fuvc']) / (results[cve]['fcvc'] + results[cve]['fuvc'] + results[cve]['fmix']), 2)

            try:
                results_rq1[type]['usi_ratio'] += round((3*results[cve]['uvci']) / (3*results[cve]['uvci'] + results[cve]['cvci']), 2)
            except:                
                results_rq1[type]['usi_ratio'] = round(3*results[cve]['uvci'] / (3*results[cve]['uvci'] + results[cve]['cvci']), 2)

            if results[cve]['cso'] + results[cve]['uvco'] != 0:
                try:
                    results_rq1[type]['uso_ratio'] += round(4*results[cve]['uvco'] / (results[cve]['cso'] + results[cve]['uvco']), 2)
                except:                
                    results_rq1[type]['uso_ratio'] = round(4*results[cve]['uvco'] / (results[cve]['cso'] + results[cve]['uvco']), 2)
            uso_ratio_count += 1

            try:
                results_rq1[type]['cso_ratio'] += round((5*results[cve]['cso']) / (results[cve]['cso'] + results[cve]['cvci']), 2)
            except:                
                results_rq1[type]['cso_ratio'] = round((5*results[cve]['cso']) / (results[cve]['cso'] + results[cve]['cvci']), 2)
            count_ratio_cso += 1
            count += 1
            try:
                results_rq1[type]['fus'] += results[cve]['fuvc']
            except:
                results_rq1[type]['fus'] = results[cve]['fuvc']

            try:
                results_rq1[type]['fmix'] += results[cve]['fmix']
            except:
                results_rq1[type]['fmix'] = results[cve]['fmix']
            fmix_count += 1

            try:
                results_rq1[type]['fmixus'] += results[cve]['fmix'] + results[cve]['fuvc']
            except:
                results_rq1[type]['fmixus'] = results[cve]['fmix'] + results[cve]['fuvc']
                    
            try:
                results_rq1[type]['uso'] += 4*results[cve]['uvco']
            except:
                results_rq1[type]['uso'] = 4*results[cve]['uvco']

            try:
                results_rq1[type]['usi'] += results[cve]['uvci']
            except:
                results_rq1[type]['usi'] = results[cve]['uvci']

            try:
                results_rq1[type]['cso'] += 5*results[cve]['cso']
            except:
                results_rq1[type]['cso'] = 5*results[cve]['cso']

        if type == "Functional Change":
            print("Functional Change")
            print(results_rq1[type], count, count_ratio)
        elif type == "Feature Modification":
            print("Feature Modification")
            print(results_rq1[type], count, count_ratio)
        elif type == "Feature Introduction":
            print("Feature Introduction")
            print(results_rq1[type], count, count_ratio)

        for typ in results_rq1[type]:
            if 'ratio'in typ:
                if typ == "cso_ratio":
                    results_rq1[type][typ] = round(results_rq1[type][typ]/203, 2)
                elif typ == "uso_ratio":
                    results_rq1[type][typ] = round(results_rq1[type][typ]/203, 2)

                else:
                    results_rq1[type][typ] = round(results_rq1[type][typ]/203, 2)
            else:
                if typ == "fmix":
                    results_rq1[type][typ] = round(results_rq1[type][typ]/203, 2)
                elif type not in ['Feature Modification', 'Feature Introduction','Functional Change'] and typ == "usi":
                    
                    results_rq1[type][typ] = round(results_rq1[type][typ]/203, 2)
                else:
                    results_rq1[type][typ] = round(results_rq1[type][typ]/203, 2)
       
    fp = open("results.json", "w")
    json.dump(results_rq1, fp, indent=4)
    fp.close()
    return results_rq1

if __name__ == "__main__":
    results = get_results()
