#!/usr/bin/env python3
r"""
Post-processor for BML --no-tree LaTeX output.

Rewrites \begin{bidtable}...\end{bidtable} blocks into multi-column
xltabular tables: one column per bidding level plus a justified
X-column for descriptions that fills the remaining linewidth.
"""

import re
import sys
from pathlib import Path


class Node:
    def __init__(self, bid: str, desc: str, level: int):
        self.bid = bid
        self.desc = desc
        self.level = level
        self.children = []


def parse_line(line: str):
    """Parse a single line from a BML no-tree bidtable."""
    line = line.rstrip()

    # Remove trailing row separator \\
    if line.endswith("\\\\"):
        line = line[:-2].rstrip()

    # Extract trailing structural markers \+ and \-
    markers = []
    while True:
        if line.endswith("\\+"):
            markers.append("+")
            line = line[:-2].rstrip()
        elif line.endswith("\\-"):
            markers.append("-")
            line = line[:-2].rstrip()
        else:
            break

    plus_count = markers.count("+")
    minus_count = markers.count("-")

    # Continuation of previous description: starts with \>
    if line.startswith("\\>"):
        return {
            "bid": None,
            "desc": line[2:].strip(),
            "plus_count": plus_count,
            "minus_count": minus_count,
            "is_continuation": True,
        }

    # Bid row: split on first \>
    if "\\>" in line:
        bid, desc = line.split("\\>", 1)
        return {
            "bid": bid.strip(),
            "desc": desc.strip(),
            "plus_count": plus_count,
            "minus_count": minus_count,
            "is_continuation": False,
        }

    # Bid with no description
    return {
        "bid": line.strip(),
        "desc": "",
        "plus_count": plus_count,
        "minus_count": minus_count,
        "is_continuation": False,
    }


def parse_bidtable(content: str) -> Node:
    """Parse a bidtable environment into a Node tree."""
    root = Node("", "", 0)
    stack = [root]
    current_depth = 0
    last_node = root

    for raw_line in content.splitlines():
        if not raw_line.strip():
            continue

        parsed = parse_line(raw_line)

        if parsed["is_continuation"]:
            # Append to the description of the last real node
            if last_node.desc:
                last_node.desc += "\n" + parsed["desc"]
            else:
                last_node.desc = parsed["desc"]
        else:
            # The no-tree depth 0 corresponds to tree level 1 (child of root).
            level = current_depth + 1
            node = Node(parsed["bid"], parsed["desc"], level)

            # Extend stack if needed
            while len(stack) <= level:
                stack.append(None)
            stack[level] = node

            parent = stack[level - 1]
            parent.children.append(node)
            last_node = node

        current_depth += parsed["plus_count"]
        current_depth -= parsed["minus_count"]

    return root


def max_bid_level(node: Node) -> int:
    """Maximum bidding level in the tree."""
    m = node.level
    for child in node.children:
        m = max(m, max_bid_level(child))
    return m


def flatten_rows(node: Node, num_bid_cols: int):
    """Yield (columns, desc) for each row in tree order."""
    # Skip the artificial empty root
    if node.level > 0:
        cols = [""] * num_bid_cols
        col_idx = node.level - 1
        if 0 <= col_idx < num_bid_cols:
            cols[col_idx] = node.bid

        desc = node.desc.replace("\n", " \\newline ")
        yield cols, desc

    for child in node.children:
        yield from flatten_rows(child, num_bid_cols)


def generate_xltabular(root: Node) -> str:
    """Generate an xltabular replacement for a bidtable tree."""
    md = max_bid_level(root)
    num_bid_cols = max(1, md)

    # One narrow left-aligned column per bid level, then a justified X column.
    # Full grid borders (vertical + horizontal lines) and extra row spacing.
    col_spec = "|" + "l|" * num_bid_cols + "X|"

    lines = [
        "\\begingroup",
        "\\renewcommand{\\arraystretch}{1.4}",
        f"\\begin{{xltabular}}{{\\linewidth}}{{{col_spec}}}",
        "\\hline",
    ]

    for cols, desc in flatten_rows(root, num_bid_cols):
        # BML already escapes & as \& in descriptions.
        row = " & ".join(cols + [desc]) + " \\\\"
        lines.append(row)
        lines.append("\\hline")

    lines.extend([
        "\\end{xltabular}",
        "\\endgroup",
    ])
    return "\n".join(lines)


def process_tex(tex: str) -> str:
    """Replace all bidtable environments in the LaTeX source."""
    # Add xltabular package if missing
    if "\\usepackage{xltabular}" not in tex:
        tex = tex.replace(
            "\\usepackage{graphicx}",
            "\\usepackage{graphicx}\n\\usepackage{xltabular}",
        )

    def repl(match: re.Match) -> str:
        body = match.group(1)
        root = parse_bidtable(body)
        return generate_xltabular(root)

    return re.sub(
        r"\\begin\{bidtable\}(.*?)\\end\{bidtable\}",
        repl,
        tex,
        flags=re.DOTALL,
    )


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.tex> <output.tex>", file=sys.stderr)
        sys.exit(1)

    in_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    tex = in_path.read_text(encoding="utf-8")
    tex = process_tex(tex)
    out_path.write_text(tex, encoding="utf-8")


if __name__ == "__main__":
    main()
