from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from agent.tool_registry import ToolRegistry
from memory.memory_manager import MemoryManager


CN_NUMBERS = {"一": "1", "二": "2", "三": "3", "四": "4", "五": "5"}


@dataclass
class ControllerResponse:
    answer: str
    tool_trace: list[dict[str, Any]] = field(default_factory=list)


class DemoAgentController:
    """A deterministic controller that demonstrates the MVP loop without an API key."""

    def __init__(self, memory: MemoryManager | None = None, registry: ToolRegistry | None = None) -> None:
        self.memory = memory or MemoryManager()
        self.registry = registry or ToolRegistry(self.memory)

    def handle(self, user_message: str) -> ControllerResponse:
        trace: list[dict[str, Any]] = []
        message = user_message.strip()
        if not message:
            return ControllerResponse("请先输入一个学习任务。", trace)

        if self._looks_like_profile_update(message):
            return self._handle_profile(message, trace)
        if "整理文档" in message or "梳理文档" in message or "资料整理" in message:
            return self._handle_document_organize(message, trace)
        if any(word in message for word in ("实习", "岗位", "校招", "找工作", "工作筛选")):
            if any(word in message for word in ("添加", "保存", "记录", "标记")):
                return self._handle_add_career(message, trace)
            return self._handle_filter_career(message, trace)
        if any(word in message for word in ("吃什么", "吃啥", "抽签", "好吃", "食堂", "餐厅")):
            if any(word in message for word in ("添加", "保存", "记录", "标记")):
                return self._handle_add_place(message, trace)
            return self._handle_decide_food(message, trace)
        if "读取" in message or "读一下" in message:
            return self._handle_file_request(message, trace)
        if "添加" in message and ("作业" in message or "任务" in message or "报告" in message):
            return self._handle_add_assignment(message, trace)
        if ("列出" in message or "查询" in message) and ("任务" in message or "作业" in message or "未完成" in message):
            return self._handle_list_assignments(message, trace)
        if any(word in message for word in ("DDL", "ddl", "截止", "紧急", "优先级")) and any(
            word in message for word in ("整理", "梳理", "排序", "分析")
        ):
            return self._handle_deadlines(message, trace)
        if "复习计划" in message or "一周计划" in message or "计划并导出" in message:
            return self._handle_study_plan(message, trace)
        return self._handle_recall_or_fallback(message, trace)

    def _execute(self, trace: list[dict[str, Any]], tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
        result = self.registry.execute_tool(tool_name, args)
        trace.append({"tool": tool_name, "arguments": args, "result": result})
        return result

    def _looks_like_profile_update(self, message: str) -> bool:
        return "我是" in message and ("专业" in message or "考试" in message or "喜欢" in message or "请记住" in message)

    def _handle_profile(self, message: str, trace: list[dict[str, Any]]) -> ControllerResponse:
        saved: list[str] = []
        major = self._match(r"我是(.+?)专业", message)
        if major:
            major = major.strip(" ，,。")
            self.memory.upsert_profile("major", major)
            saved.append(f"专业：{major}")
        grade = self._match(r"大([一二三四五12345])", message)
        if grade:
            grade_value = CN_NUMBERS.get(grade, grade)
            self.memory.upsert_profile("grade", f"大{grade_value}")
            saved.append(f"年级：大{grade_value}")
        preference = self._match(r"我喜欢(.+?)(?:，|,|。|请|$)", message)
        if preference:
            preference = preference.strip()
            self.memory.upsert_profile("study_preference", preference)
            saved.append(f"学习偏好：{preference}")
        hours = self._match(r"每天(?:有|可用)?\s*(\d+(?:\.\d+)?)\s*小时", message)
        if hours:
            self.memory.upsert_profile("available_hours_weekday", hours)
            saved.append(f"工作日可用时间：{hours} 小时")

        exam = re.search(r"([\u4e00-\u9fa5A-Za-z0-9_]+)考试在\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", message)
        if exam:
            course_name = exam.group(1).strip()
            exam_date = date(date.today().year, int(exam.group(2)), int(exam.group(3))).isoformat()
            course = self.memory.add_course(course_name, exam_date=exam_date, difficulty=4)
            trace.append({"tool": "memory.add_course", "arguments": {"name": course_name, "exam_date": exam_date}, "result": course})
            saved.append(f"{course_name}考试：{exam_date}")

        if saved:
            memory_text = "；".join(saved)
            self._execute(trace, "remember_fact", {"category": "profile", "content": memory_text, "importance": 4})
            return ControllerResponse(
                "已保存为长期记忆：\n"
                + "\n".join(f"- {item}" for item in saved)
                + "\n\n之后询问复习建议时，我会优先召回这些信息。",
                trace,
            )
        return ControllerResponse("我没有识别出可稳定保存的信息。可以补充专业、课程、考试日期或学习偏好。", trace)

    def _handle_file_request(self, message: str, trace: list[dict[str, Any]]) -> ControllerResponse:
        path = self._extract_path(message)
        if not path:
            return ControllerResponse("请提供 data/courses/ 下的 TXT 或 Markdown 文件路径。", trace)
        result = self._execute(trace, "read_course_file", {"path": path})
        if not result.get("success"):
            return ControllerResponse(f"读取被拒绝或失败：{result.get('error')}", trace)

        data = result["data"]
        content = str(data["content"])
        summary = self._summarize_course(content)
        course = self._infer_course_from_message(message) or self._infer_course_from_filename(data["filename"])
        if not self.memory.get_course(course):
            course_row = self.memory.add_course(course, difficulty=3)
            trace.append({"tool": "memory.add_course", "arguments": {"name": course}, "result": course_row})
        if "保存" in message or "笔记" in message:
            note = self._execute(
                trace,
                "save_note",
                {
                    "course": course,
                    "title": f"{course}资料重点",
                    "content": summary,
                    "tags": ["课程资料", "自动摘要"],
                },
            )
            note_text = f"\n已保存笔记 ID：{note['data']['id']}" if note.get("success") else f"\n保存笔记失败：{note.get('error')}"
        else:
            note_text = ""
        return ControllerResponse(f"已读取 {data['filename']}，提取到的重点如下：\n\n{summary}{note_text}", trace)

    def _handle_add_assignment(self, message: str, trace: list[dict[str, Any]]) -> ControllerResponse:
        title = self._match(r"[“\"](.+?)[”\"]", message) or self._match(r"添加(.+?)(?:，|,|截止|$)", message)
        title = (title or "未命名任务").replace("作业", "").strip(" ：:")
        deadline = self._parse_cn_date(message)
        course = self._infer_course_from_message(message) or self._infer_course_from_title(title)
        if not self.memory.get_course(course):
            course_row = self.memory.add_course(course, difficulty=3)
            trace.append({"tool": "memory.add_course", "arguments": {"name": course}, "result": course_row})
        result = self._execute(
            trace,
            "add_assignment",
            {"course": course, "title": title, "deadline": deadline, "priority": 3},
        )
        if not result.get("success"):
            return ControllerResponse(f"新增任务失败：{result.get('error')}", trace)
        data = result["data"]
        return ControllerResponse(f"已新增任务：{data['title']}；课程：{data['course']}；截止日期：{data.get('deadline') or '未设置'}。", trace)

    def _handle_add_career(self, message: str, trace: list[dict[str, Any]]) -> ControllerResponse:
        title = self._match(r"[“\"](.+?)[”\"]", message) or self._match(r"(?:添加|保存|记录|标记)(.+?)(?:，|,|截止|$)", message)
        title = (title or "未命名机会").strip(" ：:")
        opportunity_type = "job" if any(word in message for word in ("校招", "全职", "找工作")) else "internship"
        organization = self._match(r"(?:公司|组织|单位)[:：]\s*([^，,]+)", message)
        location = self._match(r"(?:地点|城市|在)[:：]?\s*([^，,。]+)", message)
        deadline = self._parse_cn_date(message)
        fit_match = self._match(r"匹配度\s*(\d+)", message)
        tags = self._extract_tags(message)
        result = self._execute(
            trace,
            "add_career_opportunity",
            {
                "title": title,
                "organization": organization,
                "opportunity_type": opportunity_type,
                "location": location,
                "deadline": deadline,
                "fit_score": int(fit_match) if fit_match else None,
                "tags": tags,
                "notes": message,
                "target_keywords": ["Python", "算法", "AI", "数据", "前端"],
            },
        )
        if not result.get("success"):
            return ControllerResponse(f"保存机会失败：{result.get('error')}", trace)
        item = result["data"]
        return ControllerResponse(
            f"已保存机会：#{item['id']} {item['title']}；类型：{item['opportunity_type']}；"
            f"截止：{item.get('deadline') or '未设置'}；匹配度：{item['fit_score']}。",
            trace,
        )

    def _handle_filter_career(self, message: str, trace: list[dict[str, Any]]) -> ControllerResponse:
        days_match = self._match(r"未来\s*(\d+)\s*天", message)
        min_fit_match = self._match(r"匹配度\s*(\d+)")
        keyword = None
        for item in ["Python", "算法", "AI", "数据", "前端", "产品", "运营", "厦门", "远程"]:
            if item.lower() in message.lower():
                keyword = item
                break
        opportunity_type = "job" if any(word in message for word in ("校招", "全职", "工作")) else None
        result = self._execute(
            trace,
            "filter_career_opportunities",
            {
                "keyword": keyword,
                "opportunity_type": opportunity_type,
                "min_fit_score": int(min_fit_match) if min_fit_match else None,
                "due_within_days": int(days_match) if days_match else None,
            },
        )
        rows = result.get("data") or []
        if not rows:
            return ControllerResponse("还没有筛到合适机会。可以先保存几个实习/校招岗位，再按关键词、截止日期或匹配度筛选。", trace)
        lines = [
            f"- #{row['id']} {row['title']}（{row.get('organization') or '未知组织'}，"
            f"{row.get('opportunity_type')}，截止 {row.get('deadline') or '未设置'}，匹配度 {row.get('fit_score')}）"
            for row in rows[:8]
        ]
        return ControllerResponse("筛选到这些机会：\n" + "\n".join(lines), trace)

    def _handle_add_place(self, message: str, trace: list[dict[str, Any]]) -> ControllerResponse:
        name = self._match(r"[“\"](.+?)[”\"]", message) or self._match(r"(?:添加|保存|记录|标记)(.+?)(?:好吃|，|,|$)", message)
        name = (name or "未命名地点").strip(" ：:")
        tags = self._extract_food_tags(message)
        mood = "、".join(tags) if tags else None
        location = self._match(r"(?:位置|地点|在)[:：]?\s*([^，,。]+)", message)
        rating = 5 if "特别" in message or "很好" in message else 4
        price_level = 1 if "便宜" in message else 3 if "贵" in message else 2
        result = self._execute(
            trace,
            "add_campus_place",
            {
                "name": name,
                "category": "food",
                "location": location,
                "tags": tags,
                "rating": rating,
                "price_level": price_level,
                "mood": mood,
                "notes": message,
            },
        )
        if not result.get("success"):
            return ControllerResponse(f"保存地点失败：{result.get('error')}", trace)
        place = result["data"]
        return ControllerResponse(
            f"已记住校园美食：{place['name']}；标签：{', '.join(tags) if tags else '暂无'}；"
            f"评分：{place['rating']}/5。下次犹豫吃什么时可以让我抽签。",
            trace,
        )

    def _handle_decide_food(self, message: str, trace: list[dict[str, Any]]) -> ControllerResponse:
        tags = self._extract_food_tags(message)
        mood = tags[0] if tags else None
        max_price = 1 if "便宜" in message else None
        result = self._execute(trace, "decide_food", {"mood": mood, "max_price_level": max_price})
        if not result.get("success"):
            return ControllerResponse(f"暂时抽不了：{result.get('error')}。你可以先标记一处好吃的地点。", trace)
        data = result["data"]
        picked = data["picked"]
        return ControllerResponse(
            f"今天抽到：{picked['name']}。\n"
            f"- 位置：{picked.get('location') or '未记录'}\n"
            f"- 理由：{data['reason']}\n"
            f"- 候选数量：{data['candidate_count']}",
            trace,
        )

    def _handle_deadlines(self, message: str, trace: list[dict[str, Any]]) -> ControllerResponse:
        result = self._execute(trace, "analyze_deadlines", {"include_career": True, "status": "todo"})
        if not result.get("success"):
            return ControllerResponse(f"DDL 分析失败：{result.get('error')}", trace)
        items = (result["data"] or {}).get("items", [])
        if not items:
            return ControllerResponse("当前没有未完成作业或待跟踪求职机会。", trace)
        lines = ["DDL 紧急程度排序："]
        for item in items[:10]:
            context = f" / {item['context']}" if item.get("context") else ""
            lines.append(
                f"- [{item['urgency_score']}] {item['title']}{context}："
                f"截止 {item.get('deadline') or '未设置'}；{item['reason']}；下一步：{item['next_action']}"
            )
        return ControllerResponse("\n".join(lines), trace)

    def _handle_document_organize(self, message: str, trace: list[dict[str, Any]]) -> ControllerResponse:
        content = self._match(r"(?:整理文档|梳理文档|资料整理)[:：]\s*(.+)", message)
        if not content:
            return ControllerResponse("可以把要整理的文档内容粘贴成：整理文档：<内容>。我会提取关键信息和可能的 DDL。", trace)
        organized = self._execute(trace, "organize_document", {"title": "校园文档", "content": content})
        if not organized.get("success"):
            return ControllerResponse(f"整理失败：{organized.get('error')}", trace)
        markdown = organized["data"]["markdown"]
        exported = None
        if "导出" in message:
            exported = self._execute(
                trace,
                "export_report",
                {"filename": "amoyclaw_document_digest.md", "content": markdown, "format": "md", "overwrite": True},
            )
        export_line = ""
        if exported:
            export_line = f"\n\n已导出到：{exported['data']['path']}" if exported.get("success") else f"\n\n导出失败：{exported.get('error')}"
        return ControllerResponse(markdown + export_line, trace)

    def _handle_list_assignments(self, message: str, trace: list[dict[str, Any]]) -> ControllerResponse:
        days_match = self._match(r"未来\s*(\d+)\s*天", message)
        days = int(days_match) if days_match else None
        result = self._execute(trace, "list_assignments", {"status": "todo", "due_within_days": days})
        if not result.get("success"):
            return ControllerResponse(f"查询任务失败：{result.get('error')}", trace)
        assignments = result["data"]
        if not assignments:
            return ControllerResponse("当前没有符合条件的未完成任务。", trace)
        lines = [
            f"- #{item['id']} {item['title']}（{item['course']}，截止 {item.get('deadline') or '未设置'}，优先级 {item['priority']}）"
            for item in assignments
        ]
        return ControllerResponse("未完成任务：\n" + "\n".join(lines), trace)

    def _handle_study_plan(self, message: str, trace: list[dict[str, Any]]) -> ControllerResponse:
        courses = self.memory.list_courses()
        if not courses:
            return ControllerResponse("还没有课程信息。请先添加课程或告诉我考试日期。", trace)
        start = date.today()
        end = start + timedelta(days=6)
        weekday_hours = float(self.memory.get_profile("available_hours_weekday") or 3)
        weekend_hours = float(self.memory.get_profile("available_hours_weekend") or max(weekday_hours, 5))
        course_names = [str(course["name"]) for course in courses]
        plan = self._execute(
            trace,
            "create_study_plan",
            {
                "course_names": course_names,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "weekday_hours": weekday_hours,
                "weekend_hours": weekend_hours,
            },
        )
        if not plan.get("success"):
            return ControllerResponse(f"生成计划失败：{plan.get('error')}", trace)
        markdown = self._format_plan_markdown(plan["data"])
        exported = None
        if "导出" in message or "输出" in message:
            exported = self._execute(
                trace,
                "export_report",
                {"filename": "amoyclaw_study_plan.md", "content": markdown, "format": "md", "overwrite": True},
            )
        export_line = ""
        if exported:
            export_line = f"\n\n已导出到：{exported['data']['path']}" if exported.get("success") else f"\n\n导出失败：{exported.get('error')}"
        return ControllerResponse(markdown + export_line, trace)

    def _handle_recall_or_fallback(self, message: str, trace: list[dict[str, Any]]) -> ControllerResponse:
        result = self._execute(trace, "recall_memory", {"query": message})
        recalled = result.get("data") or {}
        profile = self.memory.get_profile_dict()
        courses = self.memory.list_courses()
        if profile or courses:
            lines = ["我召回到这些信息，可以据此继续安排学习："]
            if profile:
                lines.append("用户画像：" + "；".join(f"{key}={value}" for key, value in profile.items()))
            if courses:
                course_text = "；".join(
                    f"{item['name']}考试{item.get('exam_date') or '未设置'}，难度{item.get('difficulty')}"
                    for item in courses
                )
                lines.append("课程：" + course_text)
            if any(recalled.get(key) for key in ("notes", "assignments", "memories", "career", "places")):
                lines.append("也找到了相关笔记、任务、机会或校园地点，可继续让我生成计划、筛岗位、抽签或排 DDL。")
            return ControllerResponse("\n".join(lines), trace)
        return ControllerResponse(
            "这是 demo controller，目前可以演示：保存画像、读取课程资料、添加/查询任务、复习计划、实习筛选、校园美食抽签、DDL 排序、文档整理和路径安全。",
            trace,
        )

    @staticmethod
    def _match(pattern: str, text: str) -> str | None:
        match = re.search(pattern, text)
        return match.group(1).strip() if match else None

    def _extract_path(self, message: str) -> str | None:
        match = re.search(r"(?:读取|读一下)\s*([^\s，。]+)", message)
        return match.group(1).strip("。") if match else None

    def _parse_cn_date(self, message: str) -> str | None:
        iso = re.search(r"\d{4}-\d{1,2}-\d{1,2}", message)
        if iso:
            return datetime.fromisoformat(iso.group(0)).date().isoformat()
        cn = re.search(r"(\d{1,2})\s*月\s*(\d{1,2})\s*日", message)
        if cn:
            return date(date.today().year, int(cn.group(1)), int(cn.group(2))).isoformat()
        return None

    @staticmethod
    def _extract_tags(message: str) -> list[str]:
        candidates = ["Python", "算法", "AI", "数据", "前端", "后端", "产品", "运营", "厦门", "远程", "可转正"]
        return [item for item in candidates if item.lower() in message.lower()]

    @staticmethod
    def _extract_food_tags(message: str) -> list[str]:
        candidates = ["便宜", "辣", "清淡", "夜宵", "快", "面", "米饭", "健康", "甜", "热乎", "多人"]
        return [item for item in candidates if item in message]

    def _infer_course_from_message(self, message: str) -> str | None:
        for course in self.memory.list_courses():
            if str(course["name"]) in message:
                return str(course["name"])
        known = ["计算机视觉", "计算机网络", "机器学习", "数据库", "操作系统", "人工智能"]
        for name in known:
            if name in message:
                return name
        return None

    @staticmethod
    def _infer_course_from_title(title: str) -> str:
        for name in ["计算机视觉", "计算机网络", "机器学习", "数据库", "操作系统", "人工智能"]:
            if name in title:
                return name
        return "未分类课程"

    @staticmethod
    def _infer_course_from_filename(filename: str) -> str:
        stem = Path(filename).stem.lower()
        mapping = {
            "computer_vision": "计算机视觉",
            "cv": "计算机视觉",
            "network": "计算机网络",
            "machine_learning": "机器学习",
        }
        return mapping.get(stem, Path(filename).stem.replace("_", " "))

    @staticmethod
    def _summarize_course(content: str) -> str:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        headings = [line.lstrip("#").strip() for line in lines if line.startswith("#")]
        bullet_like = [line.lstrip("-*0123456789. ").strip() for line in lines if line.startswith(("-", "*")) or re.match(r"^\d+[.、]", line)]
        selected = (headings + bullet_like + lines[:3])[:8]
        if not selected:
            selected = ["资料为空，未提取到有效内容。"]
        return "\n".join(f"- {item}" for item in selected)

    @staticmethod
    def _format_plan_markdown(plan: dict[str, Any]) -> str:
        lines = [
            "# AmoyClaw 一周复习计划",
            "",
            f"- 周期：{plan['start_date']} 至 {plan['end_date']}",
            f"- 工作日每日上限：{plan['weekday_hours']} 小时",
            f"- 周末每日上限：{plan['weekend_hours']} 小时",
            "",
        ]
        for day in plan["days"]:
            lines.append(f"## {day['date']}（合计 {day['total_hours']} 小时）")
            if not day["items"]:
                lines.append("- 无需安排复习。")
                continue
            for item in day["items"]:
                lines.append(f"- {item['course']}：{item['hours']} 小时；{item['goal']}")
            lines.append("")
        return "\n".join(lines).strip()
