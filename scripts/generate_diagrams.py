#!/usr/bin/env python3
"""Generate the Mermaid architecture diagram in each workflow README from its JSON.

Every diagram is derived from the workflow export, so the two cannot drift. Run
with --check in CI to fail when a README is stale.

    python3 scripts/generate_diagrams.py           # rewrite READMEs in place
    python3 scripts/generate_diagrams.py --check    # exit 1 if any README is stale
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

ARCH_START = "<!-- ARCHITECTURE:START -->"
ARCH_END = "<!-- ARCHITECTURE:END -->"

# Mermaid lays sibling subgraphs out perpendicular to the flow direction, and
# GitHub scales a diagram down to the width of the README column. So a
# multi-island workflow drawn top-down spreads its islands sideways and the
# labels shrink into illegibility; drawn left-right the islands stack and the
# text stays readable. A single-island workflow has the opposite problem. Node
# count does not predict this — island count does. Measured on this repo:
#
#   rag_internal_knowledge_chatbot (3 islands)  TD 4777px wide -> 17% scale
#                                               LR 1215px wide -> 66% scale
#   daily_product_pricing_monitor  (1 island)   TD  802px wide -> 100% scale
#                                               LR 3423px wide -> 23% scale
DIRECTION_SINGLE_ISLAND = "TD"
DIRECTION_MULTI_ISLAND = "LR"

TRIGGER_TYPE_HINTS = ("trigger", "webhook")
SUBNODE_CONNECTION_PREFIX = "ai_"

# Node types whose main outputs carry a fixed meaning.
STATIC_OUTPUT_LABELS = {
    "if": ["true", "false"],
    "splitInBatches": ["done", "loop"],
    "compareDatasets": ["in A only", "same", "different", "in B only"],
}

DEFAULT_SENTIMENT_CATEGORIES = ["Positive", "Neutral", "Negative"]


def short_type(node: dict) -> str:
    """Last segment of the node type, so community nodes read like core ones."""
    return node["type"].rsplit(".", 1)[-1]


def is_trigger(node: dict) -> bool:
    t = short_type(node).lower()
    return any(hint in t for hint in TRIGGER_TYPE_HINTS)


def is_decision(node: dict) -> bool:
    return short_type(node) in {
        "if",
        "switch",
        "filter",
        "textClassifier",
        "sentimentAnalysis",
    }


def escape_label(text: str) -> str:
    """Mermaid node labels are quoted, so inner quotes need entities."""
    return (
        text.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def output_labels(node: dict, count: int) -> list[str | None]:
    """Human-readable label per main output index.

    n8n appends an error output as the last one when a node is configured with
    ``onError: continueErrorOutput``; ``continueRegularOutput`` folds failures
    into the normal output and adds nothing.
    """
    node_type = short_type(node)
    params = node.get("parameters", {})
    labels: list[str | None] = []

    if node_type in STATIC_OUTPUT_LABELS:
        labels = list(STATIC_OUTPUT_LABELS[node_type])
    elif node_type == "switch":
        rules = params.get("rules", {}).get("values", [])
        labels = [rule.get("outputKey") or f"output {i}" for i, rule in enumerate(rules)]
        if params.get("options", {}).get("fallbackOutput") == "extra":
            labels.append("fallback")
    elif node_type == "textClassifier":
        categories = params.get("categories", {}).get("categories", [])
        labels = [c.get("category") or f"category {i}" for i, c in enumerate(categories)]
        if params.get("options", {}).get("fallback") == "other":
            labels.append("other")
    elif node_type == "sentimentAnalysis":
        raw = params.get("options", {}).get("categories")
        labels = (
            [c.strip() for c in raw.split(",") if c.strip()]
            if raw
            else list(DEFAULT_SENTIMENT_CATEGORIES)
        )

    if node.get("onError") == "continueErrorOutput":
        # Everything before the error output is the success path. A node with no
        # other named outputs just reads success/error.
        if not labels:
            labels = ["success"]
        labels = labels + ["error"]

    labels = labels[:count] + [None] * max(0, count - len(labels))
    return labels


def build_graph(workflow: dict):
    """Return (nodes, main_edges, ai_edges) with sticky notes dropped."""
    nodes = [n for n in workflow.get("nodes", []) if short_type(n) != "stickyNote"]
    known = {n["name"] for n in nodes}
    by_name = {n["name"]: n for n in nodes}

    main_edges: list[tuple[str, str, str | None]] = []
    ai_edges: list[tuple[str, str, str]] = []

    for source, outputs in workflow.get("connections", {}).items():
        if source not in known:
            continue
        for connection_type, branches in outputs.items():
            branches = branches or []
            if connection_type == "main":
                labels = output_labels(by_name[source], len(branches))
                for index, branch in enumerate(branches):
                    for target in branch or []:
                        if target["node"] not in known:
                            continue
                        # A single-output node needs no label at all.
                        label = labels[index] if len(branches) > 1 else None
                        main_edges.append((source, target["node"], label))
            else:
                kind = connection_type
                if kind.startswith(SUBNODE_CONNECTION_PREFIX):
                    kind = kind[len(SUBNODE_CONNECTION_PREFIX) :]
                for branch in branches:
                    for target in branch or []:
                        if target["node"] in known:
                            ai_edges.append((source, target["node"], kind))

    return nodes, main_edges, ai_edges


def connected_components(names: list[str], edges) -> list[list[str]]:
    """Undirected components, each preserving the workflow's node order."""
    adjacency = defaultdict(set)
    for source, target, *_ in edges:
        adjacency[source].add(target)
        adjacency[target].add(source)

    seen: set[str] = set()
    components: list[list[str]] = []
    for name in names:
        if name in seen:
            continue
        stack, group = [name], []
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            group.append(current)
            stack.extend(n for n in adjacency[current] if n not in seen)
        components.append([n for n in names if n in set(group)])
    return components


def component_title(group: list[str], by_name: dict) -> str:
    """Name an island after what starts it, so nothing floats unexplained."""
    if any(short_type(by_name[n]) == "errorTrigger" for n in group):
        return "Error handling"

    triggers = [n for n in group if is_trigger(by_name[n])]
    if triggers:
        return " / ".join(triggers)

    # No trigger and no inbound path: helper or leftover nodes parked on the
    # canvas. Saying so is more useful than inventing a flow number for them.
    return "Unwired node" if len(group) == 1 else "Unwired fragment"


def render(workflow: dict) -> str:
    nodes, main_edges, ai_edges = build_graph(workflow)
    if not nodes:
        return ""

    names = [n["name"] for n in nodes]
    by_name = {n["name"]: n for n in nodes}
    node_id = {name: f"N{i}" for i, name in enumerate(names)}

    components = connected_components(names, main_edges + ai_edges)
    direction = (
        DIRECTION_SINGLE_ISLAND if len(components) == 1 else DIRECTION_MULTI_ISLAND
    )
    lines = [f"flowchart {direction}"]

    def declare(name: str, indent: str) -> str:
        node = by_name[name]
        label = f"{escape_label(name)}<br/><small>{escape_label(short_type(node))}</small>"
        if is_trigger(node):
            body = f'(["{label}"])'
        elif is_decision(node):
            body = f'{{{{"{label}"}}}}'
        else:
            body = f'["{label}"]'
        return f"{indent}{node_id[name]}{body}"

    if len(components) == 1:
        for name in names:
            lines.append(declare(name, "    "))
    else:
        # Islands are the norm here (error handlers, secondary triggers). Naming
        # each one keeps the reader from wondering why fragments float apart.
        for index, group in enumerate(components):
            title = escape_label(component_title(group, by_name))
            lines.append(f'    subgraph G{index} ["{title}"]')
            for name in group:
                lines.append(declare(name, "        "))
            lines.append("    end")

    for source, target, label in main_edges:
        arrow = f"-->|{escape_label(label)}|" if label else "-->"
        lines.append(f"    {node_id[source]} {arrow} {node_id[target]}")

    for source, target, kind in ai_edges:
        lines.append(f"    {node_id[source]} -.{escape_label(kind)}.-> {node_id[target]}")

    # Roles are conveyed with stroke only. Any fill or text colour would break
    # under whichever of GitHub's two themes it was not picked for.
    roles = defaultdict(list)
    for name in names:
        node = by_name[name]
        if node.get("disabled"):
            roles["disabled"].append(node_id[name])
        elif short_type(node) == "errorTrigger":
            roles["errorPath"].append(node_id[name])
        elif is_trigger(node):
            roles["trigger"].append(node_id[name])
    subnode_targets = {source for source, _, _ in ai_edges}
    for name in names:
        if name in subnode_targets and not by_name[name].get("disabled"):
            roles["aiSubnode"].append(node_id[name])

    if roles:
        lines.append("")
        for role, ids in roles.items():
            lines.append(f"    class {','.join(ids)} {role}")
        lines.append("    classDef trigger stroke-width:3px")
        lines.append("    classDef aiSubnode stroke-dasharray:5 3")
        lines.append("    classDef errorPath stroke-width:3px,stroke-dasharray:2 2")
        lines.append("    classDef disabled stroke-dasharray:1 4,opacity:0.45")

    return "\n".join(lines)


def build_section(workflow: dict) -> str:
    diagram = render(workflow)
    note = (
        "\n> Shapes: rounded = trigger, hexagon = branch point. "
        "Dashed borders mark AI sub-nodes; dotted edges are the model, memory "
        "and tool connections feeding an agent. Faded nodes are disabled in "
        "this export.\n"
    )
    return (
        f"{ARCH_START}\n## Architecture\n\n```mermaid\n{diagram}\n```\n{note}{ARCH_END}"
    )


def workflow_dirs() -> list[Path]:
    return sorted(
        d
        for d in REPO_ROOT.iterdir()
        if d.is_dir() and not d.name.startswith(".") and d.name != "scripts"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify READMEs are up to date instead of rewriting them",
    )
    args = parser.parse_args()

    stale: list[str] = []
    problems: list[str] = []
    written = 0

    for directory in workflow_dirs():
        readme = directory / "README.md"
        exports = sorted(directory.glob("*.json"))
        if not readme.exists() or not exports:
            problems.append(f"{directory.name}: missing README.md or workflow JSON")
            continue

        try:
            workflow = json.loads(exports[0].read_text())
        except json.JSONDecodeError as exc:
            problems.append(f"{exports[0]}: invalid JSON ({exc})")
            continue

        text = readme.read_text()
        pattern = re.compile(
            re.escape(ARCH_START) + r".*?" + re.escape(ARCH_END), re.DOTALL
        )
        if not pattern.search(text):
            problems.append(f"{readme}: no ARCHITECTURE markers")
            continue

        section = build_section(workflow)
        updated = pattern.sub(lambda _: section, text)
        if updated == text:
            continue

        if args.check:
            stale.append(directory.name)
        else:
            readme.write_text(updated)
            written += 1

    for problem in problems:
        print(f"ERROR: {problem}", file=sys.stderr)

    if args.check:
        for name in stale:
            print(f"STALE: {name}/README.md does not match its workflow JSON")
        if stale or problems:
            print(
                f"\n{len(stale)} stale diagram(s). "
                "Run: python3 scripts/generate_diagrams.py",
                file=sys.stderr,
            )
            return 1
        print(f"All {len(workflow_dirs())} diagrams match their workflow JSON.")
        return 0

    print(f"Updated {written} diagram(s).")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
