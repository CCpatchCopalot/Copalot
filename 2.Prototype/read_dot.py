import json
import re
import subprocess
import time
import config
import networkx as nx
from loguru import logger
import sys

def read_dot_in_fix_mode(dot_file):
    start_time = time.time()
    timeout = 60
    while True:
        
        result = subprocess.run(
            ["python", "read_dot_helper.py", dot_file], capture_output=True, text=True
        )

        if result.returncode == 0:
            graph_data = json.loads(result.stdout)
            graph = nx.node_link_graph(graph_data)
            return graph
        else:
            logger.warning(f"Find error in the dot reading")
            error_str = result.stderr
            if error_str.startswith("Error: syntax error in line"):
                logger.error(error_str)
                match = re.search(
                    r"syntax error in line (\d+) near \'(.+?)\'", error_str
                )
                if match:
                    line_number = int(match.group(1))
                    token = match.group(2)
                    logger.info(
                        f"Try to fix of token: {token} in line: {line_number} of file: {dot_file}"
                    )
                    correct_result = correct_syntax_error(dot_file, line_number, token)
                    if not correct_result:
                        logger.error(f"Fix Failed")
                        logger.error(f"Dot Reading Exception: {dot_file}")
                    else:
                        pass
                else:
                    logger.error(f"Unhandled Error: {error_str}")
            else:
                logger.error(f"Dot Reading Exception: {dot_file} {error_str}")

            if time.time() - start_time > timeout:
                logger.error(f"Timeout in dot reading")
                logger.error(f"Dot Reading Exception: {dot_file}")
                return None


def correct_syntax_error(dot_file, line_number, token):
    """
    find the token in the given line number and add the escape character
    """
    pattern = rf"([A-Z]+(?:_[A-Z]+)?)=(?<!\\)(\")\{token}|(?<!\\)(\")\{token}"

    with open(dot_file, "r") as file:
        lines = file.readlines()
    target_line = lines[line_number - 1]

    index = None
    for match in re.finditer(pattern, target_line):
        if match.group(1):  
            continue
        if match.group(3): 
            index = match.start(3)  
            break

    if index is None:
        return False
    else:
        escaped_string = target_line[:index] + r"\"" + target_line[index + 1 :]
        lines[line_number - 1] = escaped_string
        with open(dot_file, "w") as file:
            file.writelines(lines)
        return True


if __name__ == "__main__":
    pass