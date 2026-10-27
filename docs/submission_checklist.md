# AmoyClaw 提交说明

## 一句话介绍

AmoyClaw 是一个面向大学生的轻量级校园 Agent demo，覆盖学习复习、DDL 管理、实习筛选、校园生活决策和文档整理。
界面模型状态显示为 `MiniMax 在线`，已预留 MiniMax-M3 OpenAI-compatible 接入配置。

## 启动方式

```powershell
cd X:\0001FileSync\Program\AmoyClaw
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

打开浏览器：

```text
http://localhost:8501
```

## 现场演示顺序

1. 左侧点击 `初始化示例数据`。
2. 进入 `对话` 页，依次点击短命令按钮。
3. 进入 `DDL` 页，展示学习任务和求职截止日期的统一排序。
4. 进入 `求职` 页，展示实习机会筛选。
5. 进入 `校园生活` 页，展示校园美食记忆和吃什么抽签。
6. 进入 `文件与输出` 页，展示课程文件读取、文档整理和导出结果。
7. 点击 `安全测试`，展示路径越界被拒绝。

## 已完成验收点

- Streamlit 可视化界面。
- MiniMax 在线模型状态展示和 OpenAI-compatible 客户端预留。
- SQLite 长期记忆，重启后仍可读取。
- 课程 TXT/Markdown 文件读取。
- 作业新增、查询和 DDL 紧急度排序。
- 实习 / 工作机会保存和筛选。
- 校园地点记忆和吃什么抽签。
- 文档整理和 Markdown 导出。
- 工具调用日志。
- `data/courses/` 路径安全限制。
- pytest 核心测试。

## 提交前自检

```powershell
python scripts/quick_check.py
python -m pytest -q
python -m compileall -q .
```

当前验证结果：`14 passed`。

## 说明

当前版本为了保证课堂演示稳定，Agent 决策层使用 demo controller；工具、数据库、文件读取、导出和安全拦截都是真实执行。`agent/model_client.py` 和 `agent/tool_registry.py` 已预留 MiniMax / OpenAI-compatible Function Calling 扩展位置。
