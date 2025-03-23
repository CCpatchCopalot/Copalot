import os
import json
import requests
import openai
import time
import httpx
from volcenginesdkarkruntime import Ark

import sys
sys.path.append("../")
from config import OPENAI_API_KEY

def get_cve_description(cve_id, cache_dir, retries=5, delay=50):
    cache_path = os.path.join(cache_dir, "desc.json")
    if not os.path.exists(cache_path):
        url = f"https://cve.circl.lu/api/cve/{cve_id}"
        for attempt in range(1, retries + 1):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    description = data.get("containers", "").get("cna", "").get("descriptions", "")[0].get("value", "")
                    return description
                else:
                    print(f"Attempt {attempt}: HTTP {response.status_code} error")
            except Exception as e:
                print(f"Attempt {attempt}: Request exception {e}")
            
            if attempt < retries:
                time.sleep(delay)
        return -1
    else:
        with open(cache_path, "r") as fr:
            data = json.load(fr)
            return data[cve_id]["desc"]

def extract_file_and_method_names(description):
    client = openai.ChatCompletion

    try:
        response = client.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": f"Please extract the function (method) mentioned in the CVE description without any other analysis and without any other output. If there are many functions, you should split them by \\n. The description is: {description}"
                },
            ],
            api_key=OPENAI_API_KEY,
            timeout=httpx.Timeout(1800)
        )

        return response["choices"][0]["message"]["content"]

    except Exception as e:
        print(f"Error occurred when extracting function names: {e}")
        return ""

def desc_func_reg(cve_id, cache_dir):
    description = get_cve_description(cve_id, cache_dir)
    if description == -1:
        return -1
    else:
        llm_result = extract_file_and_method_names(description).strip()
        return description, llm_result

    
if __name__ == "__main__":
    pass