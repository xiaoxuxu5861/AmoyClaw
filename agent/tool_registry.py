from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from pydantic import BaseModel, Field, ValidationError

from memory.memory_manager import MemoryManager
from tools.assignment_tools import add_assignment, list_assignments, update_assignment
from tools.campus_tools import add_campus_place, decide_food, list_campus_places
from tools.career_tools import add_career_opportunity, filter_career_opportunities, update_career_status
from tools.deadline_tools import analyze_deadlines
from tools.document_tools import organize_document
from tools.export_tools import export_report
from tools.file_tools import read_course_file
from tools.note_tools import save_note, search_notes
from tools.study_plan_tools import create_study_plan


def _model_dump(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def _json_schema(model: type[BaseModel]) -> dict[str, Any]:
    if hasattr(model, "model_json_schema"):
        return model.model_json_schema()
    return model.schema()


class ReadCourseFileArgs(BaseModel):
    path: str


class SaveNoteArgs(BaseModel):
    course: str
    title: str
    content: str
    tags: list[str] = Field(default_factory=list)


class SearchNotesArgs(BaseModel):
    keyword: str
    course: str | None = None


class AddAssignmentArgs(BaseModel):
    course: str
    title: str
    deadline: str | None = None
    priority: int = 3


class ListAssignmentsArgs(BaseModel):
    status: str = "todo"
    due_within_days: int | None = None


class UpdateAssignmentArgs(BaseModel):
    assignment_id: int
    status: str | None = None
    deadline: str | None = None


class CreateStudyPlanArgs(BaseModel):
    course_names: list[str]
    start_date: str
    end_date: str
    weekday_hours: float
    weekend_hours: float


class ExportReportArgs(BaseModel):
    filename: str
    content: str
    format: str = "md"
    overwrite: bool = False


class AddCareerOpportunityArgs(BaseModel):
    title: str
    organization: str | None = None
    opportunity_type: str = "internship"
    location: str | None = None
    work_mode: str | None = None
    deadline: str | None = None
    status: str = "saved"
    fit_score: int | None = None
    tags: list[str] = Field(default_factory=list)
    source: str | None = None
    notes: str | None = None
    target_keywords: list[str] = Field(default_factory=list)


class FilterCareerOpportunitiesArgs(BaseModel):
    keyword: str | None = None
    opportunity_type: str | None = None
    status: str | None = None
    min_fit_score: int | None = None
    due_within_days: int | None = None


class UpdateCareerStatusArgs(BaseModel):
    opportunity_id: int
    status: str


class AddCampusPlaceArgs(BaseModel):
    name: str
    category: str = "food"
    location: str | None = None
    tags: list[str] = Field(default_factory=list)
    rating: int = 4
    price_level: int = 2
    mood: str | None = None
    notes: str | None = None


class ListCampusPlacesArgs(BaseModel):
    keyword: str | None = None
    category: str | None = None
    mood: str | None = None
    max_price_level: int | None = None


class DecideFoodArgs(BaseModel):
    mood: str | None = None
    max_price_level: int | None = None


class AnalyzeDeadlinesArgs(BaseModel):
    include_career: bool = True
    status: str = "todo"


class OrganizeDocumentArgs(BaseModel):
    title: str
    content: str
    max_items: int = 12


class RememberFactArgs(BaseModel):
    category: str
    content: str
    importance: int = 3


class RecallMemoryArgs(BaseModel):
    query: str
    category: str | None = None


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    args_model: type[BaseModel]
    handler: Callable[..., dict[str, Any]]


class ToolRegistry:
    def __init__(self, memory: MemoryManager | None = None) -> None:
        self.memory = memory or MemoryManager()
        self.tools: dict[str, ToolSpec] = {
            "read_course_file": ToolSpec("read_course_file", "读取 data/courses/ 内的 TXT/Markdown 文件", ReadCourseFileArgs, read_course_file),
            "save_note": ToolSpec("save_note", "保存课程学习笔记", SaveNoteArgs, save_note),
            "search_notes": ToolSpec("search_notes", "关键词检索课程笔记", SearchNotesArgs, search_notes),
            "add_assignment": ToolSpec("add_assignment", "新增课程作业", AddAssignmentArgs, add_assignment),
            "list_assignments": ToolSpec("list_assignments", "查询作业列表", ListAssignmentsArgs, list_assignments),
            "update_assignment": ToolSpec("update_assignment", "更新作业状态或截止日期", UpdateAssignmentArgs, update_assignment),
            "create_study_plan": ToolSpec("create_study_plan", "根据考试日期和可用时间生成复习计划", CreateStudyPlanArgs, create_study_plan),
            "export_report": ToolSpec("export_report", "导出 Markdown/TXT 报告到 data/outputs/", ExportReportArgs, export_report),
            "add_career_opportunity": ToolSpec("add_career_opportunity", "保存实习、校招、兼职或项目机会", AddCareerOpportunityArgs, add_career_opportunity),
            "filter_career_opportunities": ToolSpec("filter_career_opportunities", "按关键词、类型、截止日期和匹配度筛选机会", FilterCareerOpportunitiesArgs, filter_career_opportunities),
            "update_career_status": ToolSpec("update_career_status", "更新求职机会状态", UpdateCareerStatusArgs, update_career_status),
            "add_campus_place": ToolSpec("add_campus_place", "保存校园餐厅、窗口或地点偏好", AddCampusPlaceArgs, add_campus_place),
            "list_campus_places": ToolSpec("list_campus_places", "查询校园地点偏好", ListCampusPlacesArgs, list_campus_places),
            "decide_food": ToolSpec("decide_food", "根据校园美食记忆抽签决定吃什么", DecideFoodArgs, decide_food),
            "analyze_deadlines": ToolSpec("analyze_deadlines", "合并学习任务和求职机会，按紧急程度排序", AnalyzeDeadlinesArgs, analyze_deadlines),
            "organize_document": ToolSpec("organize_document", "整理文本资料，提取关键信息和可能 DDL", OrganizeDocumentArgs, organize_document),
            "remember_fact": ToolSpec("remember_fact", "保存明确、稳定、未来有用的信息", RememberFactArgs, self._remember_fact),
            "recall_memory": ToolSpec("recall_memory", "检索用户画像、课程、任务和长期记忆", RecallMemoryArgs, self._recall_memory),
        }

    def schemas_for_llm(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": spec.name,
                    "description": spec.description,
                    "parameters": _json_schema(spec.args_model),
                },
            }
            for spec in self.tools.values()
        ]

    def execute_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        spec = self.tools.get(name)
        if not spec:
            result = {"success": False, "data": None, "error": f"未知工具：{name}"}
            self.memory.log_tool(name, arguments, result, "error")
            return result
        try:
            parsed = spec.args_model(**arguments)
            kwargs = _model_dump(parsed)
            if name in {
                "save_note",
                "search_notes",
                "add_assignment",
                "list_assignments",
                "update_assignment",
                "create_study_plan",
                "add_career_opportunity",
                "filter_career_opportunities",
                "update_career_status",
                "add_campus_place",
                "list_campus_places",
                "decide_food",
                "analyze_deadlines",
            }:
                kwargs["memory"] = self.memory
            result = spec.handler(**kwargs)
        except ValidationError as exc:
            result = {"success": False, "data": None, "error": f"参数校验失败：{exc}"}
        except Exception as exc:  # pragma: no cover - final safety net
            result = {"success": False, "data": None, "error": f"工具异常：{exc}"}
        status = "success" if result.get("success") else "error"
        self.memory.log_tool(name, arguments, result, status)
        return result

    def _remember_fact(self, category: str, content: str, importance: int = 3) -> dict[str, Any]:
        try:
            return {"success": True, "data": self.memory.remember_fact(category, content, importance), "error": None}
        except ValueError as exc:
            return {"success": False, "data": None, "error": str(exc)}

    def _recall_memory(self, query: str, category: str | None = None) -> dict[str, Any]:
        return {"success": True, "data": self.memory.recall_memory(query, category), "error": None}
