#!/usr/bin/env python3
"""Render grant and SSH source-to-destination edges as Graphviz DOT."""

import json
import sys
from pathlib import Path


def values(value):
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    if isinstance(value, str):
        return [value]
    return []


def dot_quote(value):
    return json.dumps(value, ensure_ascii=True)


def main():
    if len(sys.argv) != 3:
        raise SystemExit(
            f"usage: {Path(sys.argv[0]).name} GRANTS.json SSH.json"
        )

    grants_policy = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    ssh_policy = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    node_ids = {}
    node_labels = {}
    node_styles = {}
    edges = []

    def node_for(selector):
        if selector not in node_ids:
            node_id = f"n{len(node_ids)}"
            node_ids[selector] = node_id
            if selector == "*" or selector.startswith(("group:", "tag:", "autogroup:")):
                label = selector
            else:
                label = f"Sensitive selector {1 + sum(v.startswith('Sensitive selector ') for v in node_labels.values())}"
            node_labels[node_id] = label
            if selector.startswith("group:"):
                node_styles[node_id] = {
                    "color": "#15803d",
                    "fillcolor": "#dcfce7",
                    "fontcolor": "#14532d",
                }
            elif selector.startswith("tag:"):
                node_styles[node_id] = {
                    "color": "#2563eb",
                    "fillcolor": "#dbeafe",
                    "fontcolor": "#1e3a8a",
                }
            elif label.startswith("Sensitive selector "):
                node_styles[node_id] = {
                    "color": "#d97706",
                    "fillcolor": "#fef3c7",
                    "fontcolor": "#78350f",
                }
            else:
                node_styles[node_id] = {
                    "color": "#64748b",
                    "fillcolor": "#f1f5f9",
                    "fontcolor": "#334155",
                }
        return node_ids[selector]

    for rule in grants_policy.get("grants", []):
        for source in values(rule.get("src")):
            for destination in values(rule.get("dst")):
                edges.append((node_for(source), node_for(destination), "grant"))

    for rule in ssh_policy.get("ssh", []):
        for source in values(rule.get("src")):
            for destination in values(rule.get("dst")):
                edges.append((node_for(source), node_for(destination), "ssh"))

    print("digraph tailscale_policy {")
    print('  graph [rankdir="LR", nodesep="0.65", ranksep="1.0", bgcolor="transparent", label="Tailscale access relationships", labelloc="t", fontname="DejaVu Sans", fontsize="16"];')
    print('  node [shape="box", style="rounded,filled", fontname="DejaVu Sans", fontsize="14", margin="0.18,0.12", penwidth="1.2"];')
    print('  edge [fontname="DejaVu Sans", fontsize="12", arrowsize="0.8", penwidth="1.4"];')
    for node_id, label in node_labels.items():
        style = ", ".join(
            f"{key}={dot_quote(value)}" for key, value in node_styles[node_id].items()
        )
        print(f"  {dot_quote(node_id)} [label={dot_quote(label)}, {style}];")
    for source, destination, label in edges:
        color = "#2563eb" if label == "grant" else "#ea580c"
        print(
            f"  {dot_quote(source)} -> {dot_quote(destination)} "
            f"[label={dot_quote(label)}, color={dot_quote(color)}, "
            f"fontcolor={dot_quote(color)}];"
        )
    print("}")


if __name__ == "__main__":
    main()
