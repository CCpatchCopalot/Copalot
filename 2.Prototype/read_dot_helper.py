import sys

import json
import sys
import networkx as nx
from loguru import logger

if len(sys.argv) < 2:
    logger.error("Usage: python read_dot_helper.py <dot_file>", file=sys.stderr)
    sys.exit(1)

dot_file = sys.argv[1]

try:
    graph = nx.nx_agraph.read_dot(dot_file)
    graph_data = nx.node_link_data(graph)
    json_data = json.dumps(graph_data)
    sys.exit(0)
except Exception as e:
    sys.exit(1)
