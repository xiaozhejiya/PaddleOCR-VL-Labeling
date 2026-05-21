# K12 试卷数据采集与标注平台功能设计文档

版本：v0.2  
日期：2026-05-20  
适用范围：K12 试卷识别与解析项目的数据采集、预标注、人工标注、质检、版本管理、训练数据导出与评估集交付。

---

## 1. 背景与目标

本项目需要构建 K12 试卷识别与结构化解析数据集。数据规模较大，且标注对象不只是普通 OCR 文本框，还包含题目区域、选项区域、图片选项、公式、表格、跨页题、题目归属关系、来源授权、难度分层和质检状态。

现有 PaddleOCR-VL-1.5 / X-AnyLabeling 可以作为文档解析和预标注底座，但其官方输出更偏向通用文档块级解析，不直接覆盖 K12 题目级结构化标注需求。因此需要开发一层 K12 数据采集与标注平台。

本文涉及 PaddleOCR-VL / PP-DocLayoutV3 官方输入输出、25 个官方 layout 类别、bbox / quad / polygon 几何表示、`read_order` 和 COCOInstSegDataset 训练格式时，以本项目中的参考文档为准：

```text
paddleocr_vl_official_reference.md
```

平台目标：

```text
1. 管理真实试卷原始数据、授权信息和数据划分。
2. 调用 PaddleOCR-VL-1.5 进行预标注，但不修改其输入输出协议。
3. 在 PaddleOCR-VL 原始结果旁增加 K12 专用标注层。
4. 支持可扩展标签、可扩展关系、可扩展属性。
5. 支持自动质检、人工复核、可视化检查和数据锁定。
6. 支持多目标导出：K12 Question JSON、PP-DocLayoutV3 训练数据、Element Table、统计报告等。
7. 通过多版本、多备份、只读原始数据策略，避免原始数据和模型原始输出被误改。
```

---

## 2. 核心设计原则

### 2.1 不修改 PaddleOCR-VL-1.5 / 0.9B 的输入输出

平台只通过官方或稳定接口调用 PaddleOCR-VL-1.5：

```text
输入：PDF / 图片
输出：官方 res.json / markdown / visualization / block result / pipeline post-processing result
```

平台不直接修改：

```text
1. PaddleOCR-VL-1.5 的 pipeline 输入格式。
2. PaddleOCR-VL-1.5-0.9B 的 region crop 输入格式。
3. PaddleOCR-VL-1.5-0.9B 的 prompt / generation 输出格式。
4. 官方 res.json 的原始内容。
5. PaddleOCR-VL pipeline 后处理结果。
```

如果未来需要调整模型推理参数、prompt 或中间结果 hook，应通过独立 `model_run_config` 记录，不覆盖历史结果。

工程上必须把 PaddleOCR-VL-1.5 理解为三段：

```text
1. Layout Analysis：整页 layout 检测、实例轮廓、阅读顺序。
2. VLM Recognition：局部 crop / region 输入 0.9B VLM，输出文本、公式、表格、图表、印章等识别结果。
3. Pipeline Post-processing：按阅读顺序合并 region 结果，生成 res.json、Markdown、Word、HTML、XLSX、多页重构结果等。
```

平台可以消费这三段产生的结果，但第一阶段不修改任何一段的官方输入输出协议。

### 2.2 原始数据不可变

以下数据应视为不可变资产：

```text
1. 原始 PDF / 图片。
2. 原始采集元数据。
3. 原始授权证明或来源记录。
4. PaddleOCR-VL 每次运行产生的原始 res.json。
5. PaddleOCR-VL 每次运行产生的 markdown / visualization / crop 等输出。
6. 如果单独导出或运行 PP-DocLayoutV3，则其原始 boxes / polygon_points / order 输出。
7. PaddleOCR-VL `restructure_pages()` 产生的多页重构结果。
```

人工标注、质检结果、关系修正和导出结果必须存放在新增层，不得直接覆盖原始文件。

### 2.3 平台主格式采用扩展 JSON

平台可以直接存 JSON，但这份 JSON 应是项目自有的 K12 扩展主格式，而不是原封不动的 PaddleOCR-VL 官方 `res.json` 或 COCO 标注。

推荐关系：

```text
PaddleOCR-VL raw res.json
  作为只读输入和可追溯来源

K12 Extended Annotation JSON
  作为平台主数据格式

Exporters
  从平台主数据格式导出不同目标格式
```

### 2.4 多导出器，而不是单一数据格式

同一份人工标注资产应能导出为：

```text
1. K12 Question JSON
2. PP-DocLayoutV3 训练数据
3. Element Table
4. Question Assembler 训练数据
5. eval/train manifest
6. 质检报告和统计报告
7. overlay 可视化结果
```

导出格式不是主数据格式。导出结果可以删除和重建，平台主数据和原始数据不能被导出流程反向覆盖。

### 2.5 标签、属性、关系都要可扩展

平台不能把标签写死在代码里。应通过标签注册表和关系注册表扩展：

```text
labels.json
relations.json
attribute_schemas.json
export_profiles.json
```

新增标签时，原则上只需要更新配置和导出映射，不需要修改核心存储结构。

---

## 3. 功能范围

### 3.1 平台需要实现

```text
1. 数据导入：PDF / 图片 / 扫描件 / 手机拍摄件。
2. 来源台账：授权、来源、学科、年级、试卷类型、采集方式。
3. 原始数据备份：hash、版本、只读存储。
4. PaddleOCR-VL 预标注：保存每次运行配置和原始输出。
5. 官方 layout 候选保存：保留 PP-DocLayoutV3 boxes / polygon_points / order。
6. K12 区域标注：题目、大题、选项、图片、公式、表格等。
7. 几何标注：支持 bbox，并能自动派生四点 quad / polygon；复杂区域预留人工 quad / polygon。
8. K12 关系标注：题目-元素、选项-图片、跨页题等。
9. 标注版本管理：保存历史版本、差异和操作者。
10. 自动质检：schema、bbox/quad/polygon、标签、关系、跨页、数据泄漏。
11. 人工复核：抽检、双人复核、高风险样本复核。
12. 数据锁定：评估集锁定后禁止训练使用和误修改。
13. 多格式导出：PP-DocLayoutV3、K12 JSON、统计报告等。
14. 可视化：overlay、hard case、cross-page、option image。
```

### 3.2 平台第一阶段不需要实现

```text
1. 不直接训练 PaddleOCR-VL-1.5-0.9B。
2. 不直接修改 PaddleOCR-VL 源码。
3. 不把整页图片端到端训练成完整 K12 JSON。
4. 不重做完整 X-AnyLabeling 的所有基础画框能力。
5. 不把官方 res.json 改造成训练数据后覆盖原文件。
```

---

## 4. 总体架构

```text
Raw Asset Store
  原始 PDF / 图片 / 授权材料 / hash

PaddleOCR-VL Run Store
  每次 PaddleOCR-VL 运行配置和原始输出，只读保存

K12 Annotation Store
  人工标注区域、关系、属性、版本、质检状态

QC Engine
  自动检查 schema、bbox、关系、跨页、泄漏、统计分布

Review Workflow
  标注任务分配、复核、仲裁、锁定

Export Engine
  PP-DocLayoutV3 / K12 Question JSON / Element Table / reports

Visualization Engine
  overlay、错误样例、跨页题、图片选项样例
```

推荐平台内部采用分层数据模型：

```text
Layer 0: raw asset
Layer 1: PaddleOCR-VL raw pipeline output
Layer 2: optional PP-DocLayoutV3 raw layout candidates
Layer 3: K12 region annotations
Layer 4: K12 relation annotations
Layer 5: QC / review / lock status
Layer 6: exported datasets and reports
```

---

## 5. 推荐目录结构

```text
data/
  raw/
    papers/
      paper_001/
        original.pdf
        pages/
          paper_001_p001.jpg
          paper_001_p002.jpg
        source/
          authorization.pdf
          source_record.json

  paddleocr_vl_runs/
    run_20260520_001/
      config.json
      outputs/
        paper_001_p001.res.json
        paper_001_p001.md
        paper_001_p001_vis.jpg
      layout_candidates/
        paper_001_p001.layout.json
      restructure_pages/
        paper_001.restructured.res.json
      checksums.json

  annotations/
    k12/
      paper_001/
        paper_001_p001.annotation.v001.json
        paper_001_p001.annotation.v002.json
        paper_001_p001.annotation.latest.json

  manifests/
    eval_dataset_manifest.csv
    train_dataset_manifest.csv
    source_license_report.csv

  exports/
    pp_doclayout_v3/
      export_20260520_001/
        images/
        images_mask/
        annotations/
          instance_train.json
          instance_val.json
        export_config.json
        export_report.md

    k12_question_json/
      export_20260520_001/
        questions.jsonl
        export_report.md

  visualizations/
    eval_overlay/
    eval_hard_cases/
    eval_cross_page/
    eval_option_image/

  backups/
    snapshots/
    checksums/
```

---

## 6. 平台主数据格式

### 6.1 页面级主 JSON

建议每页一份 K12 扩展主 JSON。该文件可以引用 PaddleOCR-VL 原始输出，但不内联覆盖。

```json
{
  "schema_version": "k12_annotation_v0.1",
  "project_id": "k12_paddleocr_vl",
  "paper_id": "paper_001",
  "page_id": "paper_001_p001",
  "page_index": 1,
  "split": "eval",
  "lock_status": "unlocked",
  "image": {
    "asset_id": "asset_7b1f",
    "path": "data/raw/papers/paper_001/pages/paper_001_p001.jpg",
    "width": 2480,
    "height": 3508,
    "sha256": "..."
  },
  "source": {
    "source_type": "teacher_authorized",
    "authorization_id": "auth_001",
    "subject": "math",
    "grade": "grade_8",
    "exam_type": "midterm",
    "capture_method": "scanner",
    "visual_difficulty": "medium"
  },
  "paddleocr_vl_runs": [
    {
      "run_id": "run_20260520_001",
      "model_name": "PaddleOCR-VL-1.5",
      "pipeline_version": "v1.5",
      "run_config_path": "data/paddleocr_vl_runs/run_20260520_001/config.json",
      "raw_res_json_path": "data/paddleocr_vl_runs/run_20260520_001/outputs/paper_001_p001.res.json",
      "markdown_path": "data/paddleocr_vl_runs/run_20260520_001/outputs/paper_001_p001.md",
      "visualization_path": "data/paddleocr_vl_runs/run_20260520_001/outputs/paper_001_p001_vis.jpg",
      "layout_candidate_json_path": "data/paddleocr_vl_runs/run_20260520_001/layout_candidates/paper_001_p001.layout.json",
      "created_at": "2026-05-20T10:00:00+08:00",
      "readonly": true
    }
  ],
  "active_paddleocr_vl_run_id": "run_20260520_001",
  "k12_annotations": [],
  "relations": [],
  "qc": {
    "status": "pending",
    "auto_checks": [],
    "review_records": []
  },
  "history": []
}
```

### 6.2 标注对象结构

所有标注对象使用统一结构，便于新增标签。

```json
{
  "id": "ann_000001",
  "type": "question_block",
  "label_namespace": "k12",
  "geometry": {
    "bbox_xyxy": [120, 326, 2260, 1040],
    "quad": [[120, 326], [2260, 326], [2260, 1040], [120, 1040]],
    "polygon": [[120, 326], [2260, 326], [2260, 1040], [120, 1040]],
    "mask_ref": null
  },
  "read_order": 3,
  "attributes": {
    "question_number": "1",
    "question_type": "single_choice",
    "is_cross_page": false
  },
  "content": {
    "text": "",
    "latex": "",
    "table_html": "",
    "crop_ref": ""
  },
  "source_refs": [
    {
      "type": "paddleocr_vl_block",
      "run_id": "run_20260520_001",
      "block_id": "block_0003"
    },
    {
      "type": "pp_doclayout_v3_box",
      "run_id": "run_20260520_001",
      "box_id": "box_0003"
    }
  ],
  "provenance": {
    "created_by": "human",
    "created_at": "2026-05-20T10:30:00+08:00",
    "updated_by": "annotator_001",
    "updated_at": "2026-05-20T10:35:00+08:00"
  },
  "status": "draft"
}
```

几何字段约定：

```text
bbox_xyxy
  页面坐标系中的轴对齐矩形框，格式 [xmin, ymin, xmax, ymax]，用于快速空间计算和显示。
  这对应 PP-DocLayoutV3 推理结果中的 coordinate，本质是两个对角点，不是四点。

quad
  四点表示，格式 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]。
  普通矩形可以由 bbox 自动生成 quad；倾斜和透视区域可由人工调整 quad。

polygon
  多点轮廓，四点是 polygon 的特例。导出 PP-DocLayoutV3 COCO segmentation 时优先使用 polygon；若 polygon 缺失，则由 quad 或 bbox 生成。

mask_ref
  为未来像素级 mask 或更精细实例分割预留。MVP 可为空。
```

平台内部必须允许同一个对象同时保存 `bbox_xyxy`、`quad` 和 `polygon`。MVP 标注界面可以先只让标注员画 bbox，然后自动生成矩形 quad / polygon；后续再增加人工 quad / polygon 调整能力。

### 6.3 关系对象结构

关系独立于区域对象保存，不把复杂关系硬塞进某个框里。

```json
{
  "id": "rel_000001",
  "type": "option_image_belongs_to_option",
  "from_id": "ann_000020",
  "to_id": "ann_000015",
  "attributes": {
    "option_label": "A",
    "confidence": 1.0
  },
  "provenance": {
    "created_by": "human",
    "created_at": "2026-05-20T10:40:00+08:00"
  },
  "status": "reviewed"
}
```

---

## 7. 标签与关系扩展机制

### 7.1 标签注册表

标签不应写死在代码中，应由配置文件维护。

```json
{
  "schema_version": "label_registry_v0.1",
  "labels": [
    {
      "name": "question_block",
      "namespace": "k12",
      "display_name": "整题区域",
      "geometry_types": ["bbox", "quad", "polygon"],
      "exportable_to_pp_doclayout_v3": true,
      "default_color": "#E45756",
      "attributes_schema": {
        "question_number": "string",
        "question_type": "string",
        "is_cross_page": "boolean"
      }
    },
    {
      "name": "option_image",
      "namespace": "k12",
      "display_name": "选项图片",
      "geometry_types": ["bbox", "quad", "polygon"],
      "exportable_to_pp_doclayout_v3": true,
      "default_color": "#54A24B",
      "attributes_schema": {
        "option_label": "string"
      }
    }
  ]
}
```

新增标签时，只需要：

```text
1. 在 labels.json 增加标签定义。
2. 在 annotation UI 中自动加载。
3. 在 exporter profile 中决定是否导出。
4. 在 QC rules 中按需添加规则。
```

### 7.2 官方 PP-DocLayoutV3 标签与 K12 扩展标签

标签注册表必须区分两个命名空间：

```text
paddle.layout.*
  PaddleOCR / PP-DocLayoutV3 官方 layout 类别，用于保留官方输出、对齐预标注和导出官方格式。

k12.*
  本项目新增的题目级、选项级、关系装配相关语义标签。
```

PP-DocLayoutV3 官方 25 类应作为内置基础标签保留：

```text
abstract
algorithm
aside_text
chart
content
display_formula
doc_title
figure_title
footer
footer_image
footnote
formula_number
header
header_image
image
inline_formula
number
paragraph_title
reference
reference_content
seal
table
text
vertical_text
vision_footnote
```

这些标签不应被 K12 语义标签覆盖。比如官方 `number` 更接近页码或通用编号，不应直接等同于 K12 的 `question_number`。

### 7.3 第一批 K12 建议标签

```text
section_title
question_block
subquestion_block
question_number
subquestion_number
stem_block
option_label
option_block
option_image
stem_figure
formula
table
answer_area
analysis_block
material_block
noise_or_erasure
page_header
page_footer
```

其中，与官方标签含义接近的 K12 标签也应独立保留：

```text
k12.section_title      不直接等同于 paddle.layout.paragraph_title
k12.question_number    不直接等同于 paddle.layout.number
k12.option_image       不直接等同于 paddle.layout.image
k12.stem_figure        不直接等同于 paddle.layout.image
k12.formula            可由 display_formula / inline_formula 预标注辅助生成
k12.table              可由 paddle.layout.table 预标注辅助生成
```

### 7.4 第一批建议关系

```text
question_contains_element
question_belongs_to_section
option_belongs_to_question
option_image_belongs_to_option
formula_belongs_to_stem
formula_belongs_to_option
table_belongs_to_stem
figure_belongs_to_stem
subquestion_belongs_to_question
page_span_belongs_to_question
cross_page_continuation
```

---

## 8. PaddleOCR-VL 预标注集成

### 8.1 调用方式

平台通过独立任务调用 PaddleOCR-VL：

```text
input image/pdf
  -> PaddleOCR-VL official pipeline
  -> raw res.json / markdown / visualization / optional layout candidate json
  -> immutable run store
  -> optional conversion to initial K12 annotation suggestions
```

平台运行配置必须完整保存，至少包括：

```text
pipeline_version
layout_detection_model_name / layout_detection_model_dir
layout_threshold
layout_nms
layout_unclip_ratio
layout_merge_bboxes_mode
layout_shape_mode
merge_layout_blocks
markdown_ignore_labels
format_block_content
use_doc_orientation_classify
use_doc_unwarping
use_layout_detection
use_chart_recognition
use_ocr_for_image_block
vl_rec_backend / vl_rec_server_url
restructure_pages 参数，若执行多页重构
```

这些参数会影响 `parsing_res_list`、几何形状、阅读顺序和 Markdown/JSON 输出，必须进入 `run_config` 和导出报告。

### 8.2 预标注结果处理

PaddleOCR-VL 原始输出只读保存。平台可以从 `parsing_res_list` 抽取初始候选框：

```text
block_bbox
block_label
block_content
block_id
block_order
```

如果能通过官方 API 或单独运行 PP-DocLayoutV3 获取 layout analysis 输出，还应保存：

```text
cls_id
label
score
coordinate
polygon_points
order
```

其中 `coordinate` 是 `[xmin, ymin, xmax, ymax]`，`polygon_points` 是实例轮廓点列表，`order` 是 layout reading order。该结果仍然只作为预标注候选，不直接作为 K12 金标。

这些候选框可以转成 `source_refs` 或 `suggested_annotations`，但人工确认前不应直接当作金标。

推荐状态流：

```text
paddleocr_vl_block
  -> suggestion
  -> human_confirmed annotation
  -> reviewed annotation
  -> locked annotation
```

### 8.3 不覆盖规则

```text
1. 重新跑 PaddleOCR-VL 时生成新的 run_id。
2. 新 run_id 不覆盖旧 run_id。
3. 人工标注引用具体 run_id 和 block_id。
4. 如果模型输出变化，只新增对齐结果，不改历史标注。
```

### 8.4 后处理结果处理

PaddleOCR-VL 的 `res.json` 是 pipeline post-processing 后的页面级结果，不是 0.9B VLM 原始输出，也不是 PP-DocLayoutV3 训练标注。平台应分开保存：

```text
1. PaddleOCR-VL save_to_json() 结果。
2. PaddleOCR-VL save_to_markdown() 结果。
3. PaddleOCR-VL save_to_img() 可视化结果。
4. 可选的 PP-DocLayoutV3 boxes / polygon_points / order 结果。
5. 可选的 restructure_pages() 多页重构结果。
```

对于 PDF，逐页 predict 的原始结果和 `restructure_pages()` 结果都应作为独立 artifact 保存。K12 跨页题仍以平台的 `page_spans` 和 `cross_page_continuation` 关系为准，不直接依赖 PaddleOCR-VL 的多页后处理结果。

---

## 9. 标注工作流

### 9.1 数据导入

```text
1. 上传原始 PDF / 图片。
2. 计算 sha256。
3. 写入 source manifest。
4. 渲染或切分页面。
5. 生成 paper_id / page_id / asset_id。
6. 保存原始文件和页面图像。
```

### 9.2 预标注

```text
1. 选择 PaddleOCR-VL 运行配置。
2. 批量推理。
3. 保存 raw res.json 和可视化图。
4. 生成 block-level suggestions。
5. 初始化页面 annotation JSON。
```

### 9.3 人工标注

标注员需要完成：

```text
1. 校对大题标题和题号。
2. 以 bbox 为基础标注 question_block，并自动生成矩形 quad / polygon；倾斜或透视区域可人工调整 quad / polygon。
3. 标注 option_block 和 option_label。
4. 标注 option_image、stem_figure、formula、table。
5. 标注 answer_area、noise_or_erasure 等干扰区域。
6. 建立题目、选项、图片、公式、表格之间的关系。
7. 标记跨页题 page_spans。
```

### 9.4 复核与仲裁

```text
普通样本：按比例抽检。
hard 样本：100% 可视化复核。
图片选项题：100% 复核。
跨页题：100% 复核。
材料题 / 综合题：100% 复核。
冲突样本：进入仲裁队列。
```

### 9.5 数据锁定

评估集锁定后：

```text
1. 禁止直接编辑 locked annotation。
2. 如需修正，创建新 revision 并记录原因。
3. 禁止从 locked eval 数据生成训练增强样本。
4. 导出时记录 lock version 和 checksum。
```

---

## 10. 自动质检设计

### 10.1 基础 schema 检查

```text
1. JSON 是否合法。
2. schema_version 是否支持。
3. page_id / paper_id / image path 是否存在。
4. annotation id 是否唯一。
5. relation from_id / to_id 是否存在。
```

### 10.2 几何检查

```text
1. bbox / polygon 是否越界。
2. bbox 面积是否为正。
3. polygon 是否闭合或可解释。
4. quad 是否为四点，点序是否可解释，面积是否为正。
5. bbox、quad、polygon 三者是否明显不一致。
6. question_block 是否严重重叠。
7. option_block 是否在对应 question_block 内或有合理交叠。
8. option_image 是否在 option_block 内或有 owner 关系。
```

### 10.3 K12 结构检查

```text
1. 每个 question_block 是否有 question_number 或 review_flag。
2. 选择题是否存在 option_label / option_block。
3. 非选择题 options 是否为空。
4. option_image 是否有 owner。
5. 跨页题是否有多个 page_spans。
6. 大题标题与题目是否有 section 关系。
7. material_block 是否绑定到题组或子题。
```

### 10.4 数据集检查

```text
1. train / eval 是否按 paper_id 或 exam_id 隔离。
2. eval 是否含增强样本。
3. eval 是否含合成样本。
4. 同一试卷是否跨 split。
5. 数据来源和授权字段是否缺失。
6. easy / medium / hard 分布是否异常。
7. 学科、年级、采集方式分布是否异常。
```

---

## 11. PP-DocLayoutV3 训练数据导出

### 11.1 导出目标

导出给 PP-DocLayoutV3 的数据格式应对齐官方 PaddleX Layout Analysis 模块：

```text
COCOInstSegDataset + read_order
```

目录结构：

```text
dataset/
  images/
  images_mask/
  annotations/
    instance_train.json
    instance_val.json
```

其中 `images_mask` 在官方示例中与 `images` 内容一致。平台导出时可以复制图片，也可以在工程内部用硬链接/软链接实现，但交付包中必须保证 PaddleX `check_dataset` 能正常读取。

导出给 PP-DocLayoutV3 的 annotation 只包含 layout analysis / instance segmentation / reading order 所需信息：

```text
image
images
categories
annotations
category_id
bbox            COCO 格式 [x, y, width, height]
segmentation    COCO polygon segmentation
area
iscrowd
read_order
```

不导出以下业务字段：

```text
answer
analysis
knowledge_points
option ownership relation
cross-page merge decision
source authorization detail
review comment
```

这些字段保留在 K12 主 JSON 或其他导出格式中。

### 11.2 导出输入

导出器读取：

```text
1. K12 Extended Annotation JSON
2. labels.json，包含官方 25 类和 K12 扩展类
3. export_profile_pp_doclayout_v3.json，包含标签筛选和 category_id 映射
4. split manifest
5. image asset
6. paddleocr_vl_official_reference.md 中记录的官方格式约束
```

### 11.3 标签筛选

由 export profile 控制哪些标签导出：

```json
{
  "export_name": "pp_doclayout_v3_k12_v0.1",
  "target_format": "COCOInstSegDataset_with_read_order",
  "base_labels": "pp_doclayout_v3_25_classes",
  "include_labels": [
    "paddle.layout.text",
    "paddle.layout.table",
    "paddle.layout.image",
    "paddle.layout.display_formula",
    "paddle.layout.inline_formula",
    "k12.section_title",
    "k12.question_block",
    "k12.subquestion_block",
    "k12.question_number",
    "k12.option_label",
    "k12.option_block",
    "k12.option_image",
    "k12.stem_figure",
    "k12.answer_area",
    "k12.table",
    "k12.formula",
    "k12.noise_or_erasure"
  ],
  "category_mapping": {
    "paddle.layout.text": 23,
    "paddle.layout.table": 22,
    "paddle.layout.image": 15,
    "paddle.layout.display_formula": 6,
    "paddle.layout.inline_formula": 16,
    "k12.section_title": 101,
    "k12.question_block": 102,
    "k12.subquestion_block": 103,
    "k12.question_number": 104,
    "k12.option_label": 105,
    "k12.option_block": 106,
    "k12.option_image": 107,
    "k12.stem_figure": 108,
    "k12.answer_area": 109,
    "k12.table": 110,
    "k12.formula": 111,
    "k12.noise_or_erasure": 112
  }
}
```

如果只训练 K12 语义容器，可以只包含 `k12.*` 标签；如果希望保留官方 layout 能力，应包含官方 25 类或其子集。无论选择哪种 profile，`category_id` 必须稳定，不能随导出批次改变。

### 11.4 COCO annotation 转换规则

平台标注：

```json
{
  "id": "ann_000001",
  "type": "question_block",
  "geometry": {
    "bbox_xyxy": [120, 326, 2260, 1040],
    "quad": [[120, 326], [2260, 326], [2260, 1040], [120, 1040]],
    "polygon": [[120, 326], [2260, 326], [2260, 1040], [120, 1040]]
  },
  "read_order": 3
}
```

导出为：

```json
{
  "id": 1,
  "image_id": 1,
  "category_id": 102,
  "bbox": [120, 326, 2140, 714],
  "segmentation": [[120, 326, 2260, 326, 2260, 1040, 120, 1040]],
  "area": 1527960,
  "iscrowd": 0,
  "read_order": 3
}
```

几何转换优先级：

```text
1. 有 polygon：使用 polygon 展平成 COCO segmentation。
2. 无 polygon 但有 quad：使用 quad 展平成 COCO segmentation。
3. 无 polygon / quad 但有 bbox_xyxy：由 bbox 生成四点矩形 segmentation，并在 export_report 中标记 fallback。
```

### 11.5 read_order 规则

```text
1. 优先使用人工标注 read_order。
2. 如果缺失，可根据页面阅读顺序自动估算，但必须标记 auto_generated。
3. 同一页导出时 read_order 应为非负整数。
4. 同一页 read_order 建议从 0 开始连续。
5. 自动估算结果必须进入 QC 报告。
6. 导出前应按每张 image 重新检查 read_order 是否连续，不连续则失败或进入人工修正队列。
```

### 11.6 导出前校验

```text
1. include_labels 均存在于 labels.json。
2. 每个导出实例都有合法 polygon 或 bbox。
3. category_id 唯一且稳定。
4. image_id 与文件路径一致。
5. train / val split 不泄漏同一 paper_id。
6. locked eval 数据默认不得导出为训练集。
7. `categories` 中的 id / name 与 export profile 一致。
8. 每张图的 read_order 连续且从 0 开始。
```

### 11.7 PaddleX check_dataset

PP-DocLayoutV3 训练数据导出后，平台应提供一键校验入口或命令提示：

```bash
python main.py -c paddlex/configs/modules/layout_analysis/PP-DocLayoutV3.yaml \
  -o Global.mode=check_dataset \
  -o Global.dataset_dir=./dataset/doclayoutv3_examples
```

导出报告应记录：

```text
1. check_dataset 是否执行。
2. check_dataset_result.json 路径。
3. 样本数、类别数、类别分布。
4. 失败样本和失败原因。
5. 可视化样例路径。
```

---

## 12. K12 Question JSON 导出

K12 Question JSON 由区域和关系装配生成，不直接由 PaddleOCR-VL 原始 res.json 生成。

导出流程：

```text
K12 annotations
  -> question_block
  -> attach section
  -> attach stem / options / formula / table / figure
  -> resolve page_spans
  -> build question JSON
```

推荐输出结构：

```json
{
  "question_id": "paper_001_q001",
  "paper_id": "paper_001",
  "section_id": "sec_001",
  "section_title": "一、选择题",
  "question_number": "1",
  "question_type": "single_choice",
  "is_cross_page": false,
  "page_spans": [
    {
      "page_id": "paper_001_p001",
      "bbox_xyxy": [120, 326, 2260, 1040],
      "source_annotation_ids": ["ann_000001"]
    }
  ],
  "content": {
    "stem": {
      "text": "",
      "source_annotation_ids": []
    },
    "options": []
  },
  "review_flags": []
}
```

---

## 13. 备份与版本管理

### 13.1 文件不可变策略

```text
1. 原始文件按 sha256 建立 asset_id。
2. 同 hash 文件只存一份，多个 paper/page 可引用同一 asset。
3. raw 目录只允许追加，不允许覆盖。
4. PaddleOCR-VL run 目录只允许追加，不允许覆盖。
5. 每次人工保存生成新的 annotation revision。
```

### 13.2 标注版本策略

```text
paper_001_p001.annotation.v001.json
paper_001_p001.annotation.v002.json
paper_001_p001.annotation.v003.json
paper_001_p001.annotation.latest.json
```

`latest.json` 可以是指针文件或冗余副本，但历史版本不能删除。

每个版本记录：

```text
revision_id
parent_revision_id
created_by
created_at
change_summary
change_reason
qc_status
review_status
```

### 13.3 备份策略

```text
1. 每日生成 annotation snapshots。
2. 每次导出保存 export_config、source revision、checksums。
3. 每周生成 raw asset checksum report。
4. 删除只做 soft delete，保留 tombstone。
5. 重要版本复制到独立 backup 目录或对象存储。
```

### 13.4 回滚策略

```text
1. 回滚不覆盖当前版本。
2. 回滚操作创建一个新 revision，内容来自历史版本。
3. 回滚原因必须写入 history。
4. locked eval 的回滚需要管理员或仲裁角色批准。
```

---

## 14. 权限与角色

建议角色：

```text
admin
data_manager
annotator
reviewer
exporter
viewer
```

权限建议：

```text
annotator: 创建和编辑 draft annotation
reviewer: 审核 annotation，标记 reviewed
data_manager: 修改 manifest 和来源字段
exporter: 创建 export job
admin: 锁定数据集、回滚版本、管理标签注册表
viewer: 只读查看
```

---

## 15. MVP 建议

### 15.1 第一阶段必须做

```text
1. 原始图片/PDF 导入和 hash 保存。
2. source manifest 管理。
3. PaddleOCR-VL 批量预标注和 raw output 保存。
4. 页面级 K12 扩展 JSON。
5. 可配置标签注册表。
6. 内置 PP-DocLayoutV3 官方 25 类标签和 K12 扩展标签命名空间。
7. 支持 bbox / quad / polygon 几何字段，第一阶段至少支持 bbox 标注并自动生成四点 polygon。
8. question_block / option_block / option_image / stem_figure 标注。
9. 简单关系标注：option_image belongs to option。
10. 基础 QC：bbox/quad/polygon 越界、id 唯一、option owner、cross-page 检查。
11. PP-DocLayoutV3 COCOInstSegDataset + read_order 导出。
12. K12 Question JSON 初版导出。
```

### 15.2 第二阶段增强

```text
1. 跨页题专用标注界面。
2. 双人复核和仲裁。
3. overlay 批量可视化。
4. 统计报告自动生成。
5. Question Assembler 训练数据导出。
6. 自动 read_order 估算和人工修正。
7. 标签属性 schema 校验。
8. PaddleX check_dataset 一键校验。
```

### 15.3 第三阶段增强

```text
1. 多模型 run 对比。
2. 主动学习：优先分配高不确定样本。
3. 自动错误聚类。
4. 训练集增强配置管理。
5. 与训练任务和评估任务联动。
```

---

## 16. 验收标准

MVP 可按以下标准验收：

```text
1. 任意原始图片导入后能生成稳定 page_id 和 asset_id。
2. PaddleOCR-VL 原始 res.json 能只读保存，并能追溯 run_id。
3. PaddleOCR-VL run_config 能记录 layout_shape_mode、layout_nms、layout_unclip_ratio、layout_merge_bboxes_mode、merge_layout_blocks 等关键参数。
4. 人工标注不会覆盖 raw res.json。
5. 能新增一个自定义标签，无需修改主 JSON 结构。
6. 能保存官方 PP-DocLayoutV3 25 类标签，并与 K12 扩展标签分命名空间。
7. 能标注 question_block、option_block、option_image，并保存 bbox / quad / polygon。
8. 能建立 option_image belongs to option 等关系。
9. 能保存多个 annotation revision，并能回滚生成新 revision。
10. 能导出 PP-DocLayoutV3 COCOInstSegDataset + read_order 训练数据。
11. 能导出 K12 Question JSON。
12. 导出报告能列出源 revision、样本数、标签分布和 checksum。
13. locked eval 数据不能被误导出到训练集。
```

---

## 17. 关键结论

平台设计不应试图替代 PaddleOCR-VL-1.5，也不应修改 PaddleOCR-VL-1.5-0.9B 的输入输出。

推荐路线是：

```text
PaddleOCR-VL 负责通用文档解析、VLM 识别和 pipeline 后处理
K12 平台负责数据治理、人工标注、关系标注、质检和多格式导出
PP-DocLayoutV3 导出器负责从 K12 主 JSON 中筛选 layout 标签并转换为 COCOInstSegDataset + read_order
Question Assembler 导出器负责从 K12 主 JSON 中生成题目级结构化结果
```

这样可以同时满足：

```text
1. 不污染官方模型输入输出。
2. 支持未来新增标签和属性。
3. 保留 PaddleOCR-VL pipeline 后处理结果，避免把 res.json 误认为 VLM 原始输出。
4. 保留 PP-DocLayoutV3 官方 25 类和 K12 扩展类之间的清晰边界。
5. 支持从 bbox 自动生成四点 polygon，并预留人工 quad / 多点 polygon，便于导出 COCO segmentation。
6. 支持后续微调 PP-DocLayoutV3。
7. 支持 K12 Question JSON 交付。
8. 保留完整数据 lineage 和回滚能力。
9. 最大限度避免原始数据被误修改。
```
