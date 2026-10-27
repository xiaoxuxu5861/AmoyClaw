from __future__ import annotations

import html
import json
from pathlib import Path

import streamlit as st

from agent.controller import DemoAgentController
from config import (
    COURSES_DIR,
    DB_PATH,
    MODEL_DISPLAY_NAME,
    MODEL_STATUS_LABEL,
    OPENAI_BASE_URL,
    OUTPUTS_DIR,
    ensure_dirs,
)
from memory.memory_manager import MemoryManager
from tools.assignment_tools import add_assignment
from tools.campus_tools import add_campus_place, decide_food
from tools.career_tools import add_career_opportunity, filter_career_opportunities
from tools.deadline_tools import analyze_deadlines
from tools.document_tools import organize_document
from tools.export_tools import export_report
from tools.file_tools import SUPPORTED_EXTENSIONS, list_course_files, read_course_file


ensure_dirs()


@st.cache_resource
def get_memory() -> MemoryManager:
    return MemoryManager()


def get_controller() -> DemoAgentController:
    memory = get_memory()
    return DemoAgentController(memory=memory)


def render_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Gabarito:wght@500;700;800&family=Noto+Serif+SC:wght@500;700&display=swap');
        :root {
            --ink: #1d211b;
            --muted: #63685f;
            --paper: #f7f5ec;
            --panel: #fffdf6;
            --line: #c9cdbd;
            --moss: #2f6957;
            --brick: #a64a35;
            --blue: #315d85;
            --gold: #bd8d2f;
            --shadow: rgba(29, 33, 27, .11);
        }
        .stApp {
            background:
                linear-gradient(90deg, rgba(47,105,87,.07) 1px, transparent 1px),
                linear-gradient(180deg, rgba(166,74,53,.045) 1px, transparent 1px),
                var(--paper);
            background-size: 30px 30px;
            color: var(--ink);
        }
        [data-testid="stHeader"] {
            background: rgba(247, 245, 236, .86);
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(201, 205, 189, .7);
        }
        .block-container {
            padding-top: 2.15rem;
            padding-bottom: 3rem;
            max-width: 1400px;
        }
        h1, h2, h3, [data-testid="stMarkdownContainer"] h1 {
            font-family: 'Gabarito', 'Noto Serif SC', serif;
            letter-spacing: 0;
        }
        h1 {
            font-size: clamp(2.35rem, 4vw, 4.15rem);
            line-height: .98;
            margin-bottom: .35rem;
        }
        h2, h3 { color: var(--ink); }
        p, li, label, span { letter-spacing: 0; }
        section[data-testid="stSidebar"] {
            background: #ecefe6;
            border-right: 1px solid var(--line);
        }
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: var(--muted);
        }
        .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
            border-radius: 6px;
            border: 1px solid var(--ink);
            color: var(--ink);
            background: #fffdf5;
            box-shadow: 2px 2px 0 var(--ink);
            min-height: 2.55rem;
            font-weight: 700;
            transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease, color .12s ease;
        }
        .stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {
            transform: translate(1px, 1px);
            box-shadow: 1px 1px 0 var(--ink);
            border-color: var(--brick);
            color: var(--brick);
        }
        div[data-testid="stMetric"] {
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: .78rem .9rem;
            background: rgba(255,253,246,.78);
            box-shadow: 0 10px 24px var(--shadow);
        }
        div[data-testid="stChatMessage"] {
            border-radius: 8px;
            border: 1px solid var(--line);
            background: rgba(255,253,246,.82);
            box-shadow: 0 10px 24px rgba(29, 33, 27, .06);
        }
        [data-testid="stDataFrame"] {
            border: 1px solid var(--line);
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 12px 28px rgba(29, 33, 27, .06);
        }
        [data-testid="stTextInput"] input,
        [data-testid="stTextArea"] textarea,
        [data-baseweb="select"] > div {
            border-radius: 6px !important;
            border-color: var(--line) !important;
            background-color: rgba(255,253,246,.92) !important;
        }
        .stTabs [role="tablist"] {
            gap: .35rem;
            border-bottom: 1px solid var(--line);
        }
        .stTabs [role="tab"] {
            border-radius: 6px 6px 0 0;
            padding: .55rem .9rem;
            font-weight: 700;
        }
        .stTabs [aria-selected="true"] {
            color: var(--brick);
            border-bottom: 3px solid var(--brick);
        }
        .small-label {
            color: #5f655b;
            font-size: .86rem;
            margin-bottom: .2rem;
        }
        .app-kicker {
            color: var(--brick);
            font-family: 'Gabarito', 'Noto Serif SC', serif;
            font-size: .82rem;
            font-weight: 800;
            letter-spacing: .08em;
            text-transform: uppercase;
        }
        .app-title-row {
            border-bottom: 4px solid var(--ink);
            padding-bottom: .8rem;
            margin-bottom: 1rem;
        }
        .app-subtitle {
            max-width: 900px;
            color: var(--muted);
            font-size: 1.02rem;
            line-height: 1.65;
        }
        .briefing {
            display: grid;
            grid-template-columns: 1.2fr repeat(5, minmax(120px, 1fr));
            gap: 1px;
            border: 1px solid var(--ink);
            background: var(--ink);
            border-radius: 8px;
            overflow: hidden;
            margin: 1.1rem 0 1.35rem;
            box-shadow: 5px 5px 0 rgba(29,33,27,.16);
        }
        .briefing-cell {
            background: rgba(255,253,246,.94);
            min-height: 86px;
            padding: .85rem .95rem;
        }
        .briefing-cell.primary {
            background: #eef0e6;
        }
        .briefing-label {
            color: var(--muted);
            font-size: .72rem;
            font-weight: 800;
            letter-spacing: .08em;
            text-transform: uppercase;
        }
        .briefing-value {
            color: var(--ink);
            font-family: 'Gabarito', 'Noto Serif SC', serif;
            font-size: 1.6rem;
            font-weight: 800;
            line-height: 1.15;
            margin-top: .35rem;
        }
        .briefing-note {
            color: var(--muted);
            font-size: .82rem;
            margin-top: .25rem;
        }
        .section-rule {
            display: flex;
            align-items: center;
            gap: .75rem;
            margin: .25rem 0 .9rem;
        }
        .section-rule span {
            color: var(--muted);
            font-family: 'Gabarito', 'Noto Serif SC', serif;
            font-size: .76rem;
            font-weight: 800;
            letter-spacing: .08em;
            text-transform: uppercase;
        }
        .section-rule:after {
            content: "";
            height: 1px;
            flex: 1;
            background: var(--line);
        }
        .chat-tools {
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: .8rem .9rem .95rem;
            background: rgba(255,253,246,.64);
            margin-bottom: 1.15rem;
        }
        .status-pill {
            display: inline-block;
            border: 1px solid var(--ink);
            border-radius: 999px;
            padding: .25rem .65rem;
            background: #fffdf5;
            color: var(--ink);
            font-size: .78rem;
            font-weight: 800;
            margin-right: .3rem;
        }
        @media (max-width: 980px) {
            .briefing { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .briefing-cell { min-height: 78px; }
        }
        @media (max-width: 640px) {
            .block-container { padding-left: 1rem; padding-right: 1rem; }
            .briefing { grid-template-columns: 1fr; }
            h1 { font-size: 2.25rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def seed_demo_data(memory: MemoryManager) -> None:
    memory.upsert_profile("major", "人工智能")
    memory.upsert_profile("grade", "大3")
    memory.upsert_profile("study_preference", "先做例题再复习概念")
    memory.upsert_profile("available_hours_weekday", "3")
    memory.upsert_profile("available_hours_weekend", "5")
    memory.add_course("计算机视觉", exam_date="2026-07-10", difficulty=4, notes="视觉课程示例")
    memory.add_course("机器学习", exam_date="2026-07-13", difficulty=5, notes="需要多刷推导题")
    memory.add_course("计算机网络", exam_date="2026-07-15", difficulty=3, notes="实验报告和协议题")
    if not memory.list_assignments(status="todo"):
        memory.add_assignment("计算机网络", "完成计算机网络实验报告", "2026-07-08", priority=4)
        memory.add_assignment("机器学习", "整理 SVM 和神经网络错题", "2026-07-09", priority=5)
    if not memory.list_career_opportunities():
        memory.add_career_opportunity(
            title="Python 数据分析实习",
            organization="厦门某科技公司",
            opportunity_type="internship",
            location="厦门",
            deadline="2026-07-12",
            fit_score=86,
            tags=["Python", "数据", "可转正"],
            notes="需要熟悉 Pandas 和可视化，适合 AI 专业学生。",
        )
        memory.add_career_opportunity(
            title="AI 算法实习生",
            organization="远程实验室项目",
            opportunity_type="internship",
            location="远程",
            deadline="2026-07-18",
            fit_score=78,
            tags=["AI", "算法", "远程"],
            notes="需要整理简历项目经历。",
        )
    memory.add_campus_place("南门沙茶面", category="food", location="南门", tags=["面", "热乎"], rating=5, price_level=2, mood="想吃热乎的")
    memory.add_campus_place("二食堂轻食窗口", category="food", location="二食堂", tags=["清淡", "健康", "快"], rating=4, price_level=2, mood="赶时间或想清淡")
    memory.add_campus_place("西区麻辣香锅", category="food", location="西区", tags=["辣", "多人"], rating=4, price_level=3, mood="想吃辣")


def run_prompt(prompt: str) -> None:
    st.session_state.messages.append({"role": "user", "content": prompt})
    response = get_controller().handle(prompt)
    st.session_state.messages.append(
        {"role": "assistant", "content": response.answer, "trace": response.tool_trace}
    )


def section_rule(label: str) -> None:
    st.markdown(f"<div class='section-rule'><span>{html.escape(label)}</span></div>", unsafe_allow_html=True)


def compact_tags(value: object) -> str:
    if not value:
        return ""
    if isinstance(value, list):
        return " / ".join(str(item) for item in value)
    text = str(value)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return text
    if isinstance(parsed, list):
        return " / ".join(str(item) for item in parsed)
    return text


def render_app_header(memory: MemoryManager) -> None:
    deadlines = analyze_deadlines(include_career=True, memory=memory)
    ddl_items = deadlines["data"]["items"] if deadlines["success"] else []
    urgent_count = sum(1 for item in ddl_items if item["urgency_score"] >= 75)
    todo_count = len(memory.list_assignments(status="todo"))
    career_count = len(memory.list_career_opportunities())
    place_count = len(memory.list_campus_places(category="food"))
    output_count = len([path for path in OUTPUTS_DIR.glob("*") if path.is_file() and path.name != ".gitkeep"])
    model_state = MODEL_STATUS_LABEL

    st.markdown(
        """
        <div class="app-title-row">
          <div class="app-kicker">Campus agent cockpit</div>
          <h1>AmoyClaw</h1>
          <div class="app-subtitle">把课程、DDL、实习投递、校园地点和文档整理放进同一个可演示的 Agent 工作台。</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    cells = [
        ("MODEL", model_state, MODEL_DISPLAY_NAME),
        ("DDL", str(len(ddl_items)), f"{urgent_count} high urgency"),
        ("TASKS", str(todo_count), "unfinished assignments"),
        ("CAREER", str(career_count), "saved opportunities"),
        ("FOOD", str(place_count), "campus picks"),
        ("OUTPUTS", str(output_count), "exported files"),
    ]
    html_cells = []
    for index, (label, value, note) in enumerate(cells):
        primary = " primary" if index == 0 else ""
        html_cells.append(
            "<div class='briefing-cell{primary}'>"
            "<div class='briefing-label'>{label}</div>"
            "<div class='briefing-value'>{value}</div>"
            "<div class='briefing-note'>{note}</div>"
            "</div>".format(
                primary=primary,
                label=html.escape(label),
                value=html.escape(value),
                note=html.escape(note),
            )
        )
    st.markdown("<div class='briefing'>" + "".join(html_cells) + "</div>", unsafe_allow_html=True)


def deadline_view(items: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "分数": item.get("urgency_score"),
            "类型": "求职" if item.get("type") == "career" else "课程",
            "事项": item.get("title"),
            "关联": item.get("context") or "",
            "截止": item.get("deadline") or "未设置",
            "剩余": "未知" if item.get("days_left") is None else f"{item.get('days_left')} 天",
            "判断": item.get("reason"),
            "下一步": item.get("next_action"),
        }
        for item in items
    ]


def career_view(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "匹配": row.get("fit_score"),
            "机会": row.get("title"),
            "组织": row.get("organization") or "",
            "类型": row.get("opportunity_type"),
            "地点": row.get("location") or "",
            "截止": row.get("deadline") or "未设置",
            "状态": row.get("status"),
            "标签": compact_tags(row.get("tags")),
        }
        for row in rows
    ]


def place_view(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "地点": row.get("name"),
            "位置": row.get("location") or "",
            "评分": row.get("rating"),
            "价格": row.get("price_level"),
            "适合": row.get("mood") or "",
            "标签": compact_tags(row.get("tags")),
        }
        for row in rows
    ]


def task_view(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "ID": row.get("id"),
            "任务": row.get("title"),
            "课程": row.get("course") or "",
            "截止": row.get("deadline") or "未设置",
            "状态": row.get("status"),
            "优先级": row.get("priority"),
        }
        for row in rows
    ]


def file_view(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    return [
        {
            "文件": row.get("name"),
            "路径": row.get("relative_path"),
            "大小": f"{round(int(row.get('size') or 0) / 1024, 1)} KB",
        }
        for row in rows
    ]


def render_chat() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    section_rule("command deck")
    commands = [
        ("记住画像", "我是人工智能专业大三学生，计算机视觉考试在 7 月 10 日，我喜欢先做例题再复习概念，请记住。"),
        ("读课程资料", "读取 data/courses/computer_vision.md，提取考试重点并保存为笔记。"),
        ("新增任务", "添加“完成计算机网络实验报告”，截止 7 月 8 日。"),
        ("列任务", "列出未来 7 天未完成的任务。"),
        ("导出计划", "根据我的三门考试和每天可用时间，生成一周计划并导出。"),
        ("筛实习", "帮我筛选未来 14 天截止、匹配度 75 以上的 Python 实习。"),
        ("记美食", "标记“南门沙茶面”好吃，适合想吃热乎的时候。"),
        ("抽今天吃啥", "今天吃什么，帮我抽签。"),
        ("排 DDL", "梳理 DDL 的紧急程度。"),
        ("整理文档", "整理文档：课程要求 7 月 9 日提交实验报告，7 月 12 日前完成网申材料，请导出。"),
        ("安全测试", "读取 ../../etc/passwd。"),
    ]
    cols = st.columns(4)
    for index, (label, prompt) in enumerate(commands):
        if cols[index % 4].button(label, key=f"prompt_{index}", help=prompt, width="stretch"):
            run_prompt(prompt)
            st.rerun()
    clear_col, state_col = st.columns([1, 3])
    if clear_col.button("清空对话", width="stretch"):
        st.session_state.messages = []
        st.rerun()
    state_col.markdown(
        "<span class='status-pill'>MiniMax 在线</span><span class='status-pill'>工具真实执行</span><span class='status-pill'>数据库持久化</span>",
        unsafe_allow_html=True,
    )

    section_rule("conversation")
    for item in st.session_state.messages:
        with st.chat_message(item["role"]):
            st.markdown(item["content"])
            trace = item.get("trace") or []
            if trace:
                with st.expander("工具调用轨迹", expanded=False):
                    st.json(trace)

    prompt = st.chat_input("输入学习、求职、DDL、校园生活或文档整理请求")
    if prompt:
        run_prompt(prompt)
        st.rerun()


def render_memory(memory: MemoryManager) -> None:
    section_rule("memory")
    left, right = st.columns([1, 1])
    with left:
        st.subheader("用户画像")
        profile = memory.get_profile_dict()
        if profile:
            st.dataframe([{"key": key, "value": value} for key, value in profile.items()], width="stretch")
        with st.form("profile_form", clear_on_submit=True):
            key = st.text_input("记忆键", placeholder="available_hours_weekday")
            value = st.text_input("记忆值", placeholder="3")
            submitted = st.form_submit_button("保存画像")
            if submitted and key and value:
                try:
                    memory.upsert_profile(key, value)
                    st.success("已保存")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))
    with right:
        st.subheader("课程")
        courses = memory.list_courses()
        if courses:
            course_rows = [
                {
                    "课程": row.get("name"),
                    "教师": row.get("teacher") or "",
                    "考试": row.get("exam_date") or "未设置",
                    "难度": row.get("difficulty"),
                    "备注": row.get("notes") or "",
                }
                for row in courses
            ]
            st.dataframe(course_rows, width="stretch", hide_index=True)
        with st.form("course_form", clear_on_submit=True):
            name = st.text_input("课程名", placeholder="机器学习")
            exam_date = st.date_input("考试日期", value=None)
            difficulty = st.slider("难度", 1, 5, 3)
            notes = st.text_area("备注", height=80)
            submitted = st.form_submit_button("保存课程")
            if submitted and name:
                memory.add_course(name, exam_date=exam_date.isoformat() if exam_date else None, difficulty=difficulty, notes=notes)
                st.success("已保存")
                st.rerun()


def render_tasks(memory: MemoryManager) -> None:
    section_rule("assignments")
    left, right = st.columns([0.95, 1.35])
    with left:
        st.subheader("新增任务")
        courses = [course["name"] for course in memory.list_courses()] or ["未分类课程"]
        if courses == ["未分类课程"] and not memory.get_course("未分类课程"):
            memory.add_course("未分类课程")
        with st.form("assignment_form", clear_on_submit=True):
            course = st.selectbox("课程", courses)
            title = st.text_input("任务", placeholder="完成实验报告")
            deadline = st.date_input("截止日期", value=None)
            priority = st.slider("优先级", 1, 5, 3)
            submitted = st.form_submit_button("新增")
            if submitted and title:
                result = add_assignment(course, title, deadline.isoformat() if deadline else None, priority, memory)
                if result["success"]:
                    st.success("已新增")
                    st.rerun()
                else:
                    st.error(result["error"])
    with right:
        st.subheader("未完成任务")
        tasks = memory.list_assignments(status="todo")
        if tasks:
            st.dataframe(
                task_view(tasks),
                width="stretch",
                hide_index=True,
                column_config={"优先级": st.column_config.ProgressColumn("优先级", min_value=1, max_value=5)},
            )
        else:
            st.info("暂无未完成任务")


def render_deadlines(memory: MemoryManager) -> None:
    section_rule("deadline radar")
    st.subheader("DDL 紧急程度")
    result = analyze_deadlines(include_career=True, memory=memory)
    items = result["data"]["items"] if result["success"] else []
    metric_cols = st.columns(3)
    urgent_count = sum(1 for item in items if item["urgency_score"] >= 75)
    career_count = sum(1 for item in items if item["type"] == "career")
    metric_cols[0].metric("待处理 DDL", len(items))
    metric_cols[1].metric("高紧急", urgent_count)
    metric_cols[2].metric("求职相关", career_count)
    if items:
        st.dataframe(
            deadline_view(items),
            width="stretch",
            hide_index=True,
            column_config={"分数": st.column_config.ProgressColumn("分数", min_value=0, max_value=110)},
        )
    else:
        st.info("当前没有可分析的作业或求职截止日期")


def render_career(memory: MemoryManager) -> None:
    section_rule("career board")
    left, right = st.columns([0.9, 1.3])
    with left:
        st.subheader("保存机会")
        with st.form("career_form", clear_on_submit=True):
            title = st.text_input("岗位 / 机会", placeholder="Python 数据分析实习")
            organization = st.text_input("公司 / 组织", placeholder="厦门某科技公司")
            opportunity_type = st.selectbox("类型", ["internship", "job", "project", "competition"])
            location = st.text_input("地点", placeholder="厦门 / 远程")
            deadline = st.date_input("截止日期", value=None, key="career_deadline")
            fit_score = st.slider("匹配度", 0, 100, 70)
            tags_text = st.text_input("标签", placeholder="Python, 数据, 可转正")
            notes = st.text_area("备注", height=90)
            submitted = st.form_submit_button("保存机会")
            if submitted and title:
                result = add_career_opportunity(
                    title=title,
                    organization=organization or None,
                    opportunity_type=opportunity_type,
                    location=location or None,
                    deadline=deadline.isoformat() if deadline else None,
                    fit_score=fit_score,
                    tags=[item.strip() for item in tags_text.split(",") if item.strip()],
                    notes=notes,
                    memory=memory,
                )
                if result["success"]:
                    st.success("已保存机会")
                    st.rerun()
                else:
                    st.error(result["error"])
    with right:
        st.subheader("机会筛选")
        filter_cols = st.columns(4)
        keyword = filter_cols[0].text_input("关键词", placeholder="Python")
        min_fit = filter_cols[1].number_input("最低匹配度", min_value=0, max_value=100, value=0)
        due_days = filter_cols[2].number_input("未来天数", min_value=0, max_value=365, value=30)
        opp_type = filter_cols[3].selectbox("类型筛选", ["全部", "internship", "job", "project", "competition"])
        result = filter_career_opportunities(
            keyword=keyword or None,
            opportunity_type=None if opp_type == "全部" else opp_type,
            min_fit_score=min_fit if min_fit else None,
            due_within_days=due_days if due_days else None,
            memory=memory,
        )
        rows = result["data"] if result["success"] else []
        if rows:
            st.dataframe(
                career_view(rows),
                width="stretch",
                hide_index=True,
                column_config={"匹配": st.column_config.ProgressColumn("匹配", min_value=0, max_value=100)},
            )
        else:
            st.info("暂无符合条件的机会")


def render_campus(memory: MemoryManager) -> None:
    section_rule("campus life")
    left, right = st.columns([0.9, 1.3])
    with left:
        st.subheader("记住校园地点")
        with st.form("place_form", clear_on_submit=True):
            name = st.text_input("地点 / 店名", placeholder="南门沙茶面")
            location = st.text_input("位置", placeholder="南门")
            tags_text = st.text_input("标签", placeholder="面, 热乎, 便宜")
            rating = st.slider("评分", 1, 5, 4)
            price_level = st.slider("价格等级", 1, 5, 2)
            mood = st.text_input("适合场景", placeholder="想吃热乎的")
            notes = st.text_area("备注", height=80)
            submitted = st.form_submit_button("保存地点")
            if submitted and name:
                result = add_campus_place(
                    name=name,
                    category="food",
                    location=location or None,
                    tags=[item.strip() for item in tags_text.split(",") if item.strip()],
                    rating=rating,
                    price_level=price_level,
                    mood=mood or None,
                    notes=notes,
                    memory=memory,
                )
                if result["success"]:
                    st.success("已记住")
                    st.rerun()
                else:
                    st.error(result["error"])
    with right:
        st.subheader("吃什么抽签")
        cols = st.columns([1, 1, 1])
        mood = cols[0].text_input("心情 / 口味", placeholder="辣 / 清淡 / 热乎")
        max_price = cols[1].selectbox("预算", ["不限", "便宜优先"])
        if cols[2].button("抽签", width="stretch"):
            result = decide_food(mood=mood or None, max_price_level=1 if max_price == "便宜优先" else None, memory=memory)
            if result["success"]:
                picked = result["data"]["picked"]
                st.success(f"今天吃：{picked['name']}，{result['data']['reason']}")
            else:
                st.error(result["error"])
        places = memory.list_campus_places(category="food")
        if places:
            st.dataframe(
                place_view(places),
                width="stretch",
                hide_index=True,
                column_config={
                    "评分": st.column_config.ProgressColumn("评分", min_value=1, max_value=5),
                    "价格": st.column_config.ProgressColumn("价格", min_value=1, max_value=5),
                },
            )
        else:
            st.info("还没有保存校园美食地点")


def render_files(memory: MemoryManager) -> None:
    section_rule("documents")
    left, middle, right = st.columns([1, 1, 1])
    with left:
        st.subheader("课程文件")
        uploaded = st.file_uploader("上传 TXT/Markdown", type=["txt", "md", "markdown"])
        if uploaded:
            filename = Path(uploaded.name).name
            if Path(filename).suffix.lower() not in SUPPORTED_EXTENSIONS:
                st.error("仅支持 TXT/Markdown")
            else:
                target = COURSES_DIR / filename
                target.write_bytes(uploaded.getvalue())
                st.success(f"已保存到 data/courses/{filename}")
                st.rerun()
        files = list_course_files()
        if files:
            selected = st.selectbox("选择文件", [item["relative_path"] for item in files])
            if st.button("读取文件", width="stretch"):
                result = read_course_file(selected)
                if result["success"]:
                    st.code(result["data"]["content"][:4000], language="markdown")
                else:
                    st.error(result["error"])
            st.dataframe(file_view(files), width="stretch", hide_index=True)
        else:
            st.info("data/courses/ 里还没有课程文件")
    with middle:
        st.subheader("文档整理")
        doc_title = st.text_input("整理标题", value="校园文档")
        doc_content = st.text_area("粘贴 TXT/Markdown 内容", height=220, placeholder="例如：7 月 9 日提交实验报告，7 月 12 日前完成网申材料...")
        export_digest = st.checkbox("同时导出 Markdown", value=True)
        if st.button("整理文档", width="stretch"):
            if not doc_content.strip():
                st.warning("请先粘贴内容")
            else:
                result = organize_document(doc_title, doc_content)
                if result["success"]:
                    st.markdown(result["data"]["markdown"])
                    if export_digest:
                        exported = export_report("amoyclaw_document_digest.md", result["data"]["markdown"], overwrite=True)
                        if exported["success"]:
                            st.success(f"已导出：{exported['data']['filename']}")
                        else:
                            st.error(exported["error"])
    with right:
        st.subheader("输出文件")
        outputs = sorted(OUTPUTS_DIR.glob("*"))
        real_outputs = [path for path in outputs if path.is_file() and path.name != ".gitkeep"]
        if real_outputs:
            for path in real_outputs:
                with st.expander(path.name):
                    content = path.read_text(encoding="utf-8")
                    st.code(content[:5000], language="markdown" if path.suffix == ".md" else "text")
                    st.download_button("下载", data=content, file_name=path.name, width="stretch")
        else:
            st.info("生成复习计划后会出现在这里")


def render_logs(memory: MemoryManager) -> None:
    section_rule("tool trace")
    logs = memory.list_tool_logs(limit=80)
    if logs:
        rows = [
            {
                "ID": row.get("id"),
                "工具": row.get("tool_name"),
                "状态": row.get("status"),
                "时间": row.get("created_at"),
                "参数": row.get("arguments"),
                "结果": row.get("result"),
            }
            for row in logs
        ]
        st.dataframe(rows, width="stretch", hide_index=True)
    else:
        st.info("暂无工具日志")


def main() -> None:
    st.set_page_config(page_title="AmoyClaw Demo", page_icon=None, layout="wide")
    render_css()
    memory = get_memory()

    with st.sidebar:
        st.title("AmoyClaw")
        st.caption("Campus Agent Demo")
        st.markdown(
            "<span class='status-pill'>Memory</span><span class='status-pill'>Tools</span><span class='status-pill'>Safety</span>",
            unsafe_allow_html=True,
        )
        status_cols = st.columns(2)
        status_cols[0].metric("SQLite", "Ready")
        status_cols[1].metric("模型", MODEL_STATUS_LABEL)
        st.caption(f"数据库：{DB_PATH.relative_to(Path.cwd())}")
        st.caption(f"模型：{MODEL_DISPLAY_NAME}")
        st.caption(f"端点：{OPENAI_BASE_URL}")
        if st.button("初始化示例数据", width="stretch"):
            seed_demo_data(memory)
            st.success("示例数据已写入")
            st.rerun()
        st.divider()
        st.caption("演示顺序建议")
        st.markdown("`对话` → `DDL` → `求职` → `校园生活` → `文件与输出`")

    render_app_header(memory)

    tabs = st.tabs(["对话", "记忆", "DDL", "求职", "校园生活", "任务", "文件与输出", "日志"])
    with tabs[0]:
        render_chat()
    with tabs[1]:
        render_memory(memory)
    with tabs[2]:
        render_deadlines(memory)
    with tabs[3]:
        render_career(memory)
    with tabs[4]:
        render_campus(memory)
    with tabs[5]:
        render_tasks(memory)
    with tabs[6]:
        render_files(memory)
    with tabs[7]:
        render_logs(memory)


if __name__ == "__main__":
    main()
