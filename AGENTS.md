# Agent 文档索引

版本：v0.5
日期：2026-06-03
用途：本文件是 agent 读取项目文档的总入口。它只保留全局入口、二级索引路径和上下文控制规则，详细读取路径进入对应 `INDEX.md`。

## 目录

- 1. 使用原则
- 2. 项目一句话背景
- 3. 顶层索引
- 4. 常见任务入口
- 5. 上下文控制规则
- 6. 文档维护规则

---

## 1. 使用原则

```text
1. 先读本文件，再按任务进入对应二级 INDEX.md。
2. 根 AGENTS.md 不维护完整文档清单、完整任务路径或详细规则。
3. 如果二级 INDEX.md 与详细文档冲突，以详细文档为准。
4. 如果新增、重命名或删除文档，需要同步更新对应二级 INDEX.md。
5. 如果新增顶层文档类别，再更新本文件。
```

---

## 2. 项目一句话背景

本项目是一个通用文档数据采集与标注平台，当前第一个场景是 K12 试卷识别与结构化解析；平台需要兼容 PaddleOCR-VL / PP-DocLayoutV3 的官方输入输出，同时维护自己的可扩展标注、质检、版本和导出能力。

---

## 3. 顶层索引

| 文档 | 什么时候读 | 内容边界 |
|---|---|---|
| `doc/开发文档/mvp_implementation_plan.md` | 准备写代码、拆任务、判断 MVP 下一步 | MVP 阶段、开发顺序、验收标准 |
| `doc/开发文档/COMMIT_RULES.md` | 准备提交、编写提交信息、审查提交规范 | Git 提交标题、正文格式和验证说明 |
| `CLAUDE.md` | 使用 Claude Code 快速理解项目背景、命令和文档入口 | Claude Code 快捷入口；详细规则仍以二级 INDEX 和详细文档为准 |
| `doc/开发文档/后端/INDEX.md` | 后端、数据库、API、权限、安全、导出器任务 | 后端文档导航和后端任务读取路径 |
| `doc/开发文档/前端/INDEX.md` | 前端、路由、组件、标注工作台、i18n 任务 | 前端文档导航和前端任务读取路径 |
| `doc/PaddleOCR技术文档/INDEX.md` | PaddleOCR-VL、PP-DocLayoutV3、训练数据和评估集任务 | OCR/VL 技术参考导航 |
| `doc/开发文档/k12_annotation_platform_design.md` | 理解平台功能、标注格式、标签关系、版本和导出目标 | 平台功能设计和主数据格式 |

---

## 4. 常见任务入口

```text
后端编码 / 数据库 / API / 权限 / 安全：
1. doc/开发文档/mvp_implementation_plan.md
2. doc/开发文档/后端/INDEX.md

前端编码 / 路由 / 组件 / 标注工作台：
1. doc/开发文档/mvp_implementation_plan.md
2. doc/开发文档/前端/INDEX.md

PaddleOCR-VL / PP-DocLayoutV3 / read_order / 训练数据导出：
1. doc/PaddleOCR技术文档/INDEX.md
2. doc/开发文档/后端/INDEX.md

K12 数据、评估集或场景字段：
1. doc/PaddleOCR技术文档/INDEX.md
2. doc/开发文档/k12_annotation_platform_design.md

提交代码 / 编写 commit message：
1. doc/开发文档/COMMIT_RULES.md

跨前后端任务：
1. 先读相关二级 INDEX.md。
2. 再只打开被该 INDEX.md 指向的具体章节。
```

---

## 5. 上下文控制规则

```text
1. 不要一次性读取所有文档，除非任务明确要求全局审查。
2. 先用二级 INDEX.md 定位文档，再用详细文档目录定位章节。
3. 回答或编码时引用具体文档，不要在 AGENTS.md 中寻找详细规则。
4. 如果当前任务只涉及工程规范，不读取 K12 数据要求文档。
5. 如果当前任务只涉及数据集要求，不读取前后端目录结构和依赖细节。
6. 如果需要新增详细规则，写入对应详细文档，而不是扩写 AGENTS.md。
```

---

## 6. 文档维护规则

```text
1. 后端文档新增、移动或重命名时，更新 doc/开发文档/后端/INDEX.md。
2. 前端文档新增、移动或重命名时，更新 doc/开发文档/前端/INDEX.md。
3. PaddleOCR 技术文档新增、移动或重命名时，更新 doc/PaddleOCR技术文档/INDEX.md。
4. 提交规范变更时，更新 doc/开发文档/COMMIT_RULES.md，并检查本文件是否需要同步。
5. 新增顶层文档类别时，更新本文件的“顶层索引”。
6. 每个 Markdown 文档前部应有“目录”章节，方便 agent 快速定位。
7. 如果开发中发现重要需求、架构或数据格式未被文档覆盖，先补充对应详细文档，再进入实现。
```
