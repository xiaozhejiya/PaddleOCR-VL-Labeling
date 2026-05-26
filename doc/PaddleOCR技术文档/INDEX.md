# PaddleOCR 技术文档索引

版本：v0.1
日期：2026-05-27
用途：本文件是 PaddleOCR-VL、PP-DocLayoutV3、训练数据格式和 K12 评估集相关任务的文档入口。

## 目录

- 1. 使用原则
- 2. 文档索引
- 3. 常见任务读取路径
- 4. 维护规则

---

## 1. 使用原则

```text
1. 涉及 PaddleOCR-VL / PP-DocLayoutV3 输入输出时，先读本文件。
2. 官方或准官方格式参考优先于平台设计文档。
3. 平台实现如何承接官方格式，进入后端或前端 INDEX.md 查找。
4. 本文件不复制官方格式细节，只维护读取路径。
```

---

## 2. 文档索引

| 文档 | 什么时候读 | 内容边界 |
|---|---|---|
| `doc/PaddleOCR技术文档/paddleocr_vl_official_reference.md` | 涉及 PaddleOCR-VL / PP-DocLayoutV3 输入输出、25 类、bbox/polygon、训练格式 | 官方或准官方格式参考 |
| `doc/PaddleOCR技术文档/k12_paddleocr_vl_workflow_v0.3.md` | 理解 PaddleOCR-VL pipeline、PP-DocLayoutV3、0.9B VLM、K12 结构化层关系 | OCR/VL 流程和模块边界 |
| `doc/PaddleOCR技术文档/k12_exam_paper_requirements_eval_focused.md` | 涉及 K12 数据集、评估集、训练集、标注验收 | 数据要求和评估集要求 |
| `doc/开发文档/后端/INDEX.md` | 涉及预标注保存、导出器、后台任务或 PP-DocLayoutV3 数据包生成 | 后端文档导航 |
| `doc/开发文档/前端/INDEX.md` | 涉及预标注展示、bbox / read_order 人工修正或标注工作台交互 | 前端文档导航 |
| `doc/开发文档/k12_annotation_platform_design.md` | 涉及平台主数据格式、标签关系和 K12 场景扩展 | 功能设计、主数据格式、标注工作流 |

---

## 3. 常见任务读取路径

PaddleOCR-VL 输入输出或 pipeline 任务：

```text
1. doc/PaddleOCR技术文档/paddleocr_vl_official_reference.md
2. doc/PaddleOCR技术文档/k12_paddleocr_vl_workflow_v0.3.md
3. doc/开发文档/后端/INDEX.md 中 PaddleOCR-VL 预标注任务路径
```

PP-DocLayoutV3 训练数据格式任务：

```text
1. doc/PaddleOCR技术文档/paddleocr_vl_official_reference.md 的训练数据格式章节
2. doc/开发文档/后端/INDEX.md 中导出器任务路径
3. 涉及人工标注时读取 doc/开发文档/前端/INDEX.md 中标注工作台任务路径
```

read_order、bbox、polygon 或四点/两点格式判断：

```text
1. doc/PaddleOCR技术文档/paddleocr_vl_official_reference.md
2. doc/PaddleOCR技术文档/k12_paddleocr_vl_workflow_v0.3.md
3. doc/开发文档/后端/INDEX.md 中导出器和 Export QC 路径
4. doc/开发文档/前端/INDEX.md 中标注工作台路径
```

K12 数据、评估集或验收任务：

```text
1. doc/PaddleOCR技术文档/k12_exam_paper_requirements_eval_focused.md
2. doc/开发文档/k12_annotation_platform_design.md
3. 涉及实现时再进入 doc/开发文档/后端/INDEX.md 或 doc/开发文档/前端/INDEX.md
```

预标注到人工标注闭环任务：

```text
1. doc/PaddleOCR技术文档/k12_paddleocr_vl_workflow_v0.3.md
2. doc/开发文档/后端/INDEX.md 中 PaddleOCR-VL 预标注任务路径
3. doc/开发文档/前端/INDEX.md 中标注工作台任务路径
```

---

## 4. 维护规则

```text
1. 新增 PaddleOCR / PP-DocLayoutV3 / 数据集参考文档时，在“文档索引”加入一行。
2. 官方格式、训练格式和 pipeline 参考更新写入对应技术文档，不写入本文件。
3. 平台如何保存、质检和导出写入后端设计文档。
4. 平台如何展示、编辑和确认预标注写入前端交互文档。
```
