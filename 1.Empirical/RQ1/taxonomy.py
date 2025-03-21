import pandas as pd
import json

if __name__ == "__main__":
    cve_data = {}
    fp = open("../Benchmark/ccpatch_dataset.json")
    dataset = json.load(fp)
    fp.close()

    for cve in dataset:
        taxonomies = dataset[cve]["taxonomy"].split(",")
        for taxonomy in taxonomies:
            if taxonomy not in cve_data:
                cve_data[taxonomy] = []
            cve_data[taxonomy].append(cve)

    tax_nums = {}
    for taxonomy in cve_data:
        tax_nums[taxonomy] = len(cve_data[taxonomy])
    
    tax_nums_results = {}
    tax_nums_results['Functional Change'] = {}
    tax_nums_results['Functional Change']['Feature Modification'] = tax_nums['Feature Modification']
    tax_nums_results['Functional Change']['Feature Introduction'] = tax_nums['Feature Introduction']
    tax_nums_results['Functional Change']['sum'] = tax_nums['Functional Change']

    tax_nums_results['Fixing Change'] = {}
    tax_nums_results['Fixing Change']['Irrelevant Vulnerability Fix'] = tax_nums['Irrelevant Vulnerability Fix']
    tax_nums_results['Fixing Change']['Non-Security Bug Fix'] = tax_nums['Non-Security Bug Fix']
    tax_nums_results['Fixing Change']['sum'] = tax_nums['Fixing Change']

    tax_nums_results['Equivalent Change'] = {}
    tax_nums_results['Equivalent Change']['Local Equivalent Change'] = tax_nums['Local Equivalent Change']
    tax_nums_results['Equivalent Change']['Global Equivalent Change'] = tax_nums['Global Equivalent Change']
    tax_nums_results['Equivalent Change']['sum'] = tax_nums['Equivalent Change']

    fp = open("taxonomy_results.json", "w")
    json.dump(tax_nums_results, fp, indent=4)
    fp.close()

    fp = open("taxonomy_cve_list.json", "w")
    json.dump(cve_data, fp, indent=4)
    fp.close()