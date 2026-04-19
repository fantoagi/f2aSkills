#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import subprocess

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DATA_DIR = SKILL_DIR / "data"
RUNS_DIR = DATA_DIR / "runs"

sys.path.insert(0, str(SCRIPT_DIR))
from diagram_renderers import render_vertical_flow, render_three_stage_relation

# regex to find code blocks
CODE_BLOCK_RE = re.compile(r"```(text|mermaid)[\s\S]*?```")

def parse_frontmatter(text: str) -> Tuple[Dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    block = text[4:end]
    body = text[end + 5:]
    data: Dict[str, str] = {}
    for line in block.splitlines():
        if not line.strip() or line.strip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data, body

def fetch_feishu_doc(url: str) -> str:
    """Use lark-cli to fetch feishu doc content."""
    # Use lark-cli to get doc content, relying on its auth context
    try:
        # Check if it's wiki
        if "/wiki/" in url:
            token_match = re.search(r'/wiki/([a-zA-Z0-9]+)', url)
            if not token_match:
                raise ValueError(f"Invalid wiki URL: {url}")
            wiki_token = token_match.group(1)

            # 1. get node
            cmd = ["lark-cli", "wiki", "spaces", "get_node", "--params", json.dumps({"token": wiki_token}), "--as", "user"]
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            node_data = json.loads(res.stdout)

            if "node" not in node_data:
                raise ValueError(f"Failed to resolve wiki node: {res.stdout}")

            obj_token = node_data["node"]["obj_token"]
            doc_id = obj_token
        else:
            # docx / doc
            token_match = re.search(r'/(?:docx|doc)/([a-zA-Z0-9]+)', url)
            if not token_match:
                raise ValueError(f"Invalid doc URL: {url}")
            doc_id = token_match.group(1)

        # 2. fetch content
        cmd = ["lark-cli", "docs", "+fetch", "--doc", doc_id, "--as", "user"]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return res.stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"lark-cli fetch failed: {e.stderr or e.stdout}")

def extract_nodes_from_flow_block(block: str) -> List[str]:
    """Simple extractor for vertical text flow."""
    lines = block.splitlines()
    nodes = []
    for line in lines[1:-1]: # skip ```text and ```
        line = line.strip()
        if not line or line == "↓" or line == "->":
            continue
        nodes.append(line)
    return nodes

def process_content(body: str, output_dir: Path, base_name: str, core_only: bool) -> Tuple[str, List[str], List[Dict[str, Any]]]:
    replaced_blocks = []
    generated_images = []

    # 1. Replace multi-step flow blocks
    def flow_replacer(match: re.Match) -> str:
        block = match.group(0)
        # heuristic: if it looks like a simple vertical flow
        if "↓" in block and "```text" in block:
            nodes = extract_nodes_from_flow_block(block)
            if len(nodes) >= 2:
                img_name = f"{base_name}_flow_{len(replaced_blocks)+1}.png"
                img_path = output_dir / img_name
                render_vertical_flow(img_path, "流程图", nodes)

                generated_images.append(str(img_path))
                replaced_blocks.append({"type": "vertical_flow", "original": block, "nodes": nodes})
                return f"![](./{img_name})"
        return block

    body = CODE_BLOCK_RE.sub(flow_replacer, body)

    # 2. Replace specific hardcoded relation patterns if needed (like article 04)
    # This is a bit heuristic but fits the MVP needs for known relation blocks
    relation_needle = "所以可以把这一层理解成：\n\n- Prompt 决定怎么交代任务\n- tools 决定能不能接上真实世界\n"
    if relation_needle in body:
        img_name = f"{base_name}_relation.png"
        img_path = output_dir / img_name
        render_three_stage_relation(
            img_path,
            "Prompt 和 MCP / tools 的分工",
            "Prompt", "负责把任务交代清楚\n\n- 目标是什么\n- 边界在哪里\n- 输出长什么样",
            "MCP / tools", "负责把能力接到外部世界\n\n- 读文档\n- 查数据\n- 调接口\n- 写回结果",
            "Agent\n从会说到能做"
        )
        generated_images.append(str(img_path))
        replaced_blocks.append({"type": "relation", "original": relation_needle})
        body = body.replace(relation_needle, relation_needle + f"\n![](./{img_name})\n")

    return body, generated_images, replaced_blocks

def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", value).strip("-")
    return value[:60] or "article"

def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare content for WeChat Draft Publisher")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source-file", help="Local Markdown file to process")
    group.add_argument("--feishu-doc", help="Feishu Wiki or Doc URL to fetch")

    parser.add_argument("--title", help="Override title")
    parser.add_argument("--cover", help="Cover image path")
    parser.add_argument("--output-file", help="Output file path (default: *_wechat.md)")
    parser.add_argument("--core-diagrams-only", action="store_true", default=True, help="Only convert core diagrams")
    args = parser.parse_args()

    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")

    try:
        # 1. Input resolution
        if args.source_file:
            source_path = Path(args.source_file).resolve()
            if not source_path.exists():
                raise FileNotFoundError(f"Source file not found: {source_path}")
            raw_text = source_path.read_text(encoding="utf-8")
            base_name = source_path.stem
            source_mode = "local"
            source_ref = str(source_path)
            out_dir = source_path.parent
        else:
            raw_text = fetch_feishu_doc(args.feishu_doc)
            base_name = "feishu_doc"
            source_mode = "feishu"
            source_ref = args.feishu_doc
            out_dir = Path.cwd()

        # 2. Parse frontmatter
        fm, body = parse_frontmatter(raw_text)

        title = args.title or fm.get("title") or "未命名文章"
        cover = args.cover or fm.get("cover") or ""

        if source_mode == "feishu" and not args.title:
            # try to extract title from markdown H1 if not provided
            match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
            if match:
                title = match.group(1).strip()
                # remove H1 from body to avoid duplication with wechat title
                body = body.replace(match.group(0), "", 1).strip()

        # Determine output file
        if args.output_file:
            out_path = Path(args.output_file).resolve()
            out_dir = out_path.parent
        else:
            out_path = out_dir / f"{base_name}_wechat.md"

        # 3. Process Content & Images
        new_body, generated_images, replaced_blocks = process_content(body, out_dir, base_name, args.core_diagrams_only)

        # 4. Construct output
        new_fm = ["---"]
        new_fm.append(f"title: {title}")
        if cover:
            new_fm.append(f"cover: {cover}")
        # copy author or other safe fields
        for k, v in fm.items():
            if k not in ["title", "cover"]:
                new_fm.append(f"{k}: {v}")
        new_fm.append("---\n")

        final_text = "\n".join(new_fm) + "\n" + new_body
        out_path.write_text(final_text, encoding="utf-8")

        # 5. Record Run
        run_id = f"{timestamp}-{slugify(title)}"
        payload = {
            "run_id": run_id,
            "timestamp": dt.datetime.now().isoformat(),
            "source_mode": source_mode,
            "source_ref": source_ref,
            "output_markdown": str(out_path),
            "generated_images": generated_images,
            "replaced_blocks": replaced_blocks,
            "title": title,
            "cover": cover,
        }

        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        run_file = RUNS_DIR / f"{run_id}.json"
        run_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())