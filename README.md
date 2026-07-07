# AmoyClaw Demo

AmoyClaw 是一个面向大学生学习、求职、校园生活与 DDL 管理的轻量级 Agent demo。这个版本优先保证可运行、可测试、可演示：不用 API Key 也能通过离线 demo controller 跑通长期记忆、课程资料读取、作业管理、复习计划、实习筛选、校园美食抽签、文档整理、导出和安全路径限制。

提交版说明见：[docs/submission_checklist.md](docs/submission_checklist.md)

## 已实现

- Streamlit 对话界面和管理界面
- SQLite 长期记忆：用户画像、课程、作业、笔记、通用记忆、工具日志
- TXT/Markdown 课程文件读取，限制在 `data/courses/`
- 作业新增、查询、更新
- 关键词笔记保存与检索
- 一周复习计划生成，按考试日期、课程难度和每日可用时间分配
- 实习 / 工作机会保存和筛选，支持匹配度、关键词、截止日期
- 校园地点与美食偏好记忆，支持“吃什么”抽签决策
- 学习任务和求职机会合并 DDL 紧急度排序
- 文档内容整理，提取关键信息和可能 DDL
- Markdown/TXT 导出到 `data/outputs/`
- 工具注册、Pydantic 参数校验、工具调用日志
- 越界路径、危险文件类型、敏感信息保存的基础拦截

## 快速启动

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

打开页面后，先点侧边栏的 `初始化示例数据`，再到 `对话` 页依次点击示例请求即可演示。

## 推荐演示流程

```text
我是人工智能专业大三学生，计算机视觉考试在 7 月 10 日，我喜欢先做例题再复习概念，请记住。
读取 data/courses/computer_vision.md，提取考试重点并保存为笔记。
添加“完成计算机网络实验报告”，截止 7 月 8 日。
列出未来 7 天未完成的任务。
根据我的三门考试和每天可用时间，生成一周计划并导出。
帮我筛选未来 14 天截止、匹配度 75 以上的 Python 实习。
标记“南门沙茶面”好吃，适合想吃热乎的时候。
今天吃什么，帮我抽签。
梳理 DDL 的紧急程度。
整理文档：课程要求 7 月 9 日提交实验报告，7 月 12 日前完成网申材料，请导出。
读取 ../../etc/passwd。
```

## 项目结构

```text
agent/      demo controller、工具注册、模型客户端预留
memory/     SQLite schema、数据库封装、长期记忆管理
tools/      文件、作业、笔记、复习计划、导出工具
            以及求职、校园生活、DDL、文档整理工具
data/       课程资料、导出结果和本地 SQLite 数据库
tests/      核心工具与 controller 的 pytest
docs/       演示提示词和后续记录
```

## 测试

```bash
python scripts/quick_check.py
python -m pytest -q
python -m compileall -q .
```

当前提交版验证结果：`14 passed`。

## 后续扩展

真实 LLM Function Calling 已经预留在 `agent/model_client.py` 和 `agent/tool_registry.py`。配置 `.env` 后，可以在下一阶段把 `DemoAgentController` 替换为真正的模型工具调用循环，让模型自己决定调用学习、求职、生活和文档工具。
