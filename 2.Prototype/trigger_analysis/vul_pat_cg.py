
import os
import json
import requests
import openai
import time
import httpx
from volcenginesdkarkruntime import Ark
sys.path.append("../")
from config import OPENAI_API_KEY

def clean_text(text):
    return str(text).encode("utf-8", errors="replace").decode("utf-8")

def extract_vuln_functions(desc, cg, pat):
    client = openai.ChatCompletion

    try:
        response = client.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": f"You are a professional and cautious C/C++ security analyst. \
                    Here is the vulnerability report, which includes the vulnerability description and type: {clean_text(desc)} \
                    I will provide you its patch, which may contain both critical and uncritical changes. Your task is to carefully understand the vulnerability and then rank the provided functions based on their relevance to the vulnerability fix.\
                    Here is the diff hunks: {clean_text(pat)}  \
                    Here is the call relation changes: {clean_text(cg)} \
                    Output format: Ranked list of critical function names in descending order of importance."
                },
            ],
            api_key=OPENAI_API_KEY,
            timeout=httpx.Timeout(1800)
        )

        answer = response["choices"][0]["message"]["content"]
        functions = [each.strip() for each in answer.split(",")]
        return functions

    except Exception as e:
        print(f"Error occurred when extracting functions by LLM: {e}")
        return []

def extract_vuln_patch(desc, pat, taint_pats):
    client = openai.ChatCompletion

    try:
        response = client.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": f"You are a professional and cautious C/C++ security analyst. \
                    Here is the vulnerability report, which includes the vulnerability description and type: {clean_text(desc)} \
                    I will provide you its patch, which may contain both critical and uncritical changes. Your task is to carefully understand the vulnerability and then rank the provided statement sequences based on their relevance to the vulnerability fix.\
                    Here is the statement sequences extracted by inter-procedural taint-analysis: {clean_text(taint_pats)} \
                    Output format: Ranked list of sequence numbers in descending order of importance."
                },
            ],
            api_key=OPENAI_API_KEY,
            timeout=httpx.Timeout(1800)
        )

        return response["choices"][0]["message"]["content"]

    except Exception as e:
        print(f"Error occurred when extracting patch sequences by LLM: {e}")
        return ""