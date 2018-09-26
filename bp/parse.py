#!/usr/bin/env python

import json

f = open("p2p.json", "r")
data = f.read()
json_obj = json.loads(data)
producers = json_obj["producers"]
metas = json_obj['meta']

for nodes in producers:
    if not nodes.has_key("input"):
        continue

    input = nodes["input"]
    if not input.has_key("nodes"):
        continue
    ns = input["nodes"]
    for n in ns:
        if not n.has_key("p2p_endpoint"):
            continue
        if len(n["p2p_endpoint"]) <=0:
            continue
        if "http" in n["p2p_endpoint"]:
           continue
        print "p2p-peer-address = ",n["p2p_endpoint"]
