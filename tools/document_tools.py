from __future__ import annotations

import re
from datetime import date
from typing import Any

from tools.file_tools import ok


DATE_PATTERNS = [
    re.compile(r"\d{4}-\d{1,2}-\d{1,2}"),
    re.compile(r"\d{1,2}\s*月\s*\d{1,2}\s*日"),
]
ACTION_KEYWORDS = ("截止", "DDL", "提交", "作业", "报告", "考试", "面试", "网申", "简历", "材料", "报名")


def organize_document(
    title: str,
    content: str,
    max_items: int = 12,
) -> dict[str, Any]:
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    headings = [line.lstrip("#").strip() for line in lines if line.startswith("#")]
    action_lines = [
        line
        for line in lines
        if any(keyword.lower() in line.lower() for keyword in ACTION_KEYWORDS)
        or any(pattern.search(line) for pattern in DATE_PATTERNS)
    ]
    bullets = [
        line.lstrip("-*0123456789.、 ").strip()
        for line in lines
        if line.startswith(("-", "*")) or re.match(r"^\d+[.、]", line)
    ]
    summary = []
    for item in headings + action_lines + bullets:
        if item not in summary:
            summary.append(item)
        if len(summary) >= max_items:
            break
    dates = []
    for line in lines:
        for pattern in DATE_PATTERNS:
            dates.extend(match.group(0).replace(" ", "") for match in pattern.finditer(line))
    markdown = [f"# {title} 整理结果", "", f"- 整理日期：{date.today().isoformat()}", ""]
    markdown.append("## 关键信息")
    if summary:
        markdown.extend(f"- {item}" for item in summary)
    else:
        markdown.append("- 未提取到明显标题、日期或行动项。")
    markdown.append("")
    markdown.append("## 可能的 DDL / 日期")
    if dates:
        markdown.extend(f"- {item}" for item in sorted(set(dates)))
    else:
        markdown.append("- 未发现明确日期。")
    return ok({"title": title, "summary": summary, "dates": sorted(set(dates)), "markdown": "\n".join(markdown)})
