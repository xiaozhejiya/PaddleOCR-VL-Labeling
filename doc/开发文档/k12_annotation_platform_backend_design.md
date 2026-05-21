# 文档数据采集与标注平台后端设计文档

版本：v0.1  
日期：2026-05-21  
依据文档：

```text
k12_annotation_platform_design.md
paddleocr_vl_official_reference.md
k12_exam_paper_requirements_eval_focused.md
```

---

## 1. 后端目标

后端负责支撑文档类数据采集、PaddleOCR-VL 预标注、人工标注、关系管理、质检、版本管理、备份和多格式导出。

平台核心能力不绑定某一个垂直场景。K12 试卷标注是当前首个业务场景，应通过 `scenario_profile`、标签注册表、关系注册表、QC 规则和导出器扩展实现，而不是写死在平台核心逻辑中。

核心目标：

```text
1. 原始 PDF / 图片只读归档，避免被覆盖。
2. PaddleOCR-VL 原始输出只读保存，不修改官方输入输出。
3. 支持场景扩展标注 JSON，包括 bbox / quad / polygon。
4. 支持标签、属性、关系和导出 profile 可配置。
5. 支持 PP-DocLayoutV3 COCOInstSegDataset + read_order 导出。
6. 支持场景自定义导出器，例如 K12 Question JSON。
7. 支持自动质检、人工复核、版本回滚和评估集锁定。
8. 支持异步任务：OCR 预标注、导出、报告生成、备份、校验。
```

---

## 2. 技术选型建议

### 2.1 MVP 推荐

```text
后端框架：FastAPI
数据库：PostgreSQL
异步任务：Celery + Redis，或 RQ + Redis
文件存储：本地文件系统，后续可切换 MinIO / S3
鉴权：JWT + RBAC
结构化校验：Pydantic + JSON Schema
导出任务：Python exporter scripts
日志：structlog / logging + JSON log
```

### 2.2 为什么不用纯文件系统

纯文件系统适合保存原始图片、模型输出和导出结果，但不适合作为唯一后端状态源。原因：

```text
1. 标注状态、复核状态、锁定状态需要频繁查询。
2. 标注任务分配、多人协作和权限需要事务。
3. 版本、导出记录、QC 记录需要可追溯索引。
4. 需要按 document_id / split / label / status 快速筛选样本。
```

建议采用：

```text
PostgreSQL 保存元数据、状态、索引、权限、任务记录。
文件系统保存大文件、raw JSON、图片、导出包。
```

---

## 3. 总体架构

```text
Frontend
  标注画布 / 任务列表 / 复核界面 / 导出管理

API Server
  FastAPI REST API
  鉴权、权限、业务校验、元数据读写

Database
  PostgreSQL
  项目、资产、页面、标注、关系、版本、任务、QC、导出记录

Object Store
  raw assets
  paddleocr_vl_runs
  annotations snapshots
  exports
  visualizations
  backups

Worker
  PaddleOCR-VL predict
  PP-DocLayoutV3 candidate extraction
  QC jobs
  exporter jobs
  report generation
  backup jobs
```

后端原则：

```text
1. API Server 不直接执行长耗时推理和导出。
2. 长任务进入 job queue，由 worker 执行。
3. 所有 job 输出写入独立 artifact 目录。
4. artifact 写入后计算 checksum，并登记到数据库。
5. 数据锁定后，修改只能产生新 revision，不能覆盖旧 revision。
```

---

## 4. 场景扩展模型

平台后端按“核心平台 + 场景扩展”设计。

核心平台负责：

```text
1. 文件资产、页面、标注 revision、标签、关系、权限、任务、质检、导出框架。
2. 通用几何对象：bbox / quad / polygon / mask_ref。
3. 通用标注对象和关系对象。
4. 通用 QC：schema、geometry、dataset、export。
5. 通用导出：PP-DocLayoutV3、Element Table、通用 annotation JSON。
```

场景扩展负责：

```text
1. 定义业务标签，例如 k12.question_block 或 medical.finding_region。
2. 定义业务关系，例如 option_image_belongs_to_option。
3. 定义业务属性 schema。
4. 定义业务 QC 规则。
5. 定义业务导出器，例如 K12 Question JSON。
6. 定义统计报告字段。
```

建议增加 `scenario_profiles` 表或配置文件：

```text
scenario_id
name
label_set
relation_set
qc_rule_set
exporter_set
statistics_fields
created_at
updated_at
```

---

## 5. 数据分层

### 5.1 文件资产层

保存不可变或可重建文件：

```text
raw PDF / image
rendered page image
authorization document
PaddleOCR-VL res.json
PaddleOCR-VL markdown
PaddleOCR-VL visualization
PP-DocLayoutV3 candidate json
annotation revision json
export package
QC report
overlay visualization
backup snapshot
```

### 5.2 数据库元数据层

保存可查询状态：

```text
project
document
page
asset
source metadata
model run
annotation revision
annotation object index
relation object index
QC result
review record
export job
task assignment
lock status
```

### 5.3 JSON 主数据层

每页标注主数据以 revision JSON 保存，数据库保留索引和状态。这样既保留完整 JSON 可移植性，又能支持查询和协作。

推荐：

```text
annotation revision json 是标注事实载体。
数据库 annotation_objects 是从 revision json 抽取的索引表。
数据库 relation_objects 是从 revision json 抽取的索引表。
修改标注时创建新 revision，再重建索引。
```

---

## 6. 存储目录设计

```text
data/
  raw/
    assets/
      sha256_prefix/
        asset_id.original.ext
    documents/
      doc_001/
        source_record.json
        authorization/
        pages/
          doc_001_p001.jpg

  paddleocr_vl_runs/
    run_20260521_000001/
      config.json
      inputs.json
      outputs/
        doc_001_p001.res.json
        doc_001_p001.md
        doc_001_p001_vis.jpg
      layout_candidates/
        doc_001_p001.layout.json
      restructure_pages/
        doc_001.restructured.res.json
      checksums.json

  annotations/
    k12/
      doc_001/
        doc_001_p001.annotation.v000001.json
        doc_001_p001.annotation.v000002.json
        doc_001_p001.annotation.latest.json

  exports/
    pp_doclayout_v3/
      export_20260521_000001/
        images/
        images_mask/
        annotations/
          instance_train.json
          instance_val.json
        export_config.json
        export_report.md
    k12_question_json/
      export_20260521_000002/
        questions.jsonl
        export_config.json
        export_report.md

  visualizations/
    overlay/
    hard_cases/
    cross_page/
    option_image/

  backups/
    snapshots/
    checksums/
```

文件写入规则：

```text
1. raw/ 只追加，不覆盖。
2. paddleocr_vl_runs/ 只追加，不覆盖。
3. annotations 历史 revision 不删除。
4. latest.json 可以是指针文件或冗余副本。
5. exports 可以重建，但每次导出必须生成独立 export_id。
```

---

## 7. 核心数据库表

### 7.1 projects

```text
id
name
description
schema_version
created_at
updated_at
```

### 7.2 assets

保存文件级资产。

```text
id
asset_type              raw_pdf / page_image / authorization / output_json / export_file
storage_path
original_filename
mime_type
size_bytes
sha256
width
height
created_by
created_at
readonly
deleted_at
```

约束：

```text
sha256 建唯一索引或局部唯一索引。
readonly=true 的资产禁止覆盖。
```

### 7.3 documents

```text
id
project_id
document_code
document_type
source_type
authorization_id
domain_metadata_json
split                 train / val / eval / external_auxiliary
lock_status           unlocked / locked
created_at
updated_at
```

说明：

```text
document_type 可取 exam_paper / contract / report / invoice / book_page 等。
domain_metadata_json 保存场景字段，例如 K12 的 subject、grade、exam_type、year_or_term、province_or_region。
平台核心不把 subject / grade / exam_type 作为固定字段。
```

### 7.4 pages

```text
id
document_id
page_id
page_index
image_asset_id
width
height
capture_method
visual_difficulty
status                imported / preannotated / annotated / reviewed / locked
created_at
updated_at
```

索引：

```text
(document_id, page_index)
(status)
(visual_difficulty)
```

### 7.5 paddleocr_vl_runs

```text
id
project_id
run_id
pipeline_version
model_name
run_config_json
input_scope_json
status                queued / running / succeeded / failed / canceled
started_at
finished_at
created_by
created_at
error_message
```

`run_config_json` 必须记录：

```text
layout_detection_model_name
layout_detection_model_dir
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
vl_rec_backend
vl_rec_server_url
restructure_pages parameters
```

### 7.6 paddleocr_vl_run_outputs

```text
id
run_id
page_id
raw_res_json_asset_id
markdown_asset_id
visualization_asset_id
layout_candidate_asset_id
restructured_asset_id
checksum_json
created_at
```

### 7.7 annotation_revisions

```text
id
project_id
document_id
page_id
revision_no
parent_revision_id
annotation_json_asset_id
status                draft / submitted / reviewed / locked / superseded
qc_status             pending / passed / failed / warning
created_by
created_at
change_summary
change_reason
```

约束：

```text
(page_id, revision_no) 唯一。
locked revision 不允许修改。
回滚创建新 revision，不覆盖旧 revision。
```

### 7.8 annotation_objects

从 annotation revision JSON 抽取的索引表。

```text
id
revision_id
ann_id
label_namespace        paddle.layout / k12
label_name
bbox_xyxy              jsonb
quad                   jsonb
polygon                jsonb
read_order
attributes_json
source_refs_json
status
created_at
```

索引：

```text
(revision_id)
(label_namespace, label_name)
(read_order)
GIST / SP-GiST 空间索引可后续增加
```

### 7.9 relation_objects

```text
id
revision_id
rel_id
relation_type
from_ann_id
to_ann_id
attributes_json
status
created_at
```

### 7.10 label_registry

```text
id
project_id
namespace
name
display_name
geometry_types_json
attributes_schema_json
exportable_to_pp_doclayout_v3
default_color
is_builtin
is_active
created_at
updated_at
```

内置两类标签：

```text
paddle.layout.* 官方 PP-DocLayoutV3 25 类
scenario.* 或具体场景命名空间，例如 k12.*、medical.*、invoice.*
```

### 7.11 relation_registry

```text
id
project_id
name
display_name
from_label_constraints_json
to_label_constraints_json
attributes_schema_json
is_active
created_at
updated_at
```

### 7.12 qc_results

```text
id
project_id
document_id
page_id
revision_id
qc_type               schema / geometry / k12_structure / dataset / export
status                passed / warning / failed
summary
details_json
created_at
created_by_job_id
```

### 7.13 review_records

```text
id
revision_id
reviewer_id
review_status          approved / rejected / needs_fix
comment
created_at
```

### 7.14 export_jobs

```text
id
project_id
export_id
export_type            pp_doclayout_v3 / k12_question_json / element_table / statistics_report
export_profile_json
input_scope_json
source_revisions_json
status                 queued / running / succeeded / failed / canceled
output_dir
report_asset_id
created_by
created_at
started_at
finished_at
error_message
```

### 7.15 background_jobs

```text
id
job_type
status
payload_json
result_json
progress
created_by
created_at
started_at
finished_at
error_message
```

---

## 8. 标注主 JSON

后端保存每页一个 revision JSON，结构与功能设计文档一致。

关键字段：

```text
schema_version
project_id
document_id
page_id
image
source
paddleocr_vl_runs
active_paddleocr_vl_run_id
k12_annotations
relations
qc
history
```

标注对象必须支持：

```text
id
type
label_namespace
geometry.bbox_xyxy
geometry.quad
geometry.polygon
geometry.mask_ref
read_order
attributes
content
source_refs
provenance
status
```

后端写入流程：

```text
1. API 接收前端提交的 annotation draft。
2. Pydantic 校验基础结构。
3. JSON Schema 校验标签属性。
4. 创建新 annotation revision JSON。
5. 写入对象存储。
6. 登记 annotation_revisions。
7. 重建 annotation_objects / relation_objects 索引。
8. 触发自动 QC job。
```

---

## 9. API 设计

### 9.1 认证与用户

```text
POST /api/auth/login
POST /api/auth/logout
GET  /api/me
```

角色：

```text
admin
data_manager
annotator
reviewer
exporter
viewer
```

### 9.2 项目与配置

```text
GET  /api/projects
POST /api/projects
GET  /api/projects/{project_id}

GET  /api/projects/{project_id}/labels
POST /api/projects/{project_id}/labels
PUT  /api/projects/{project_id}/labels/{label_id}

GET  /api/projects/{project_id}/relations
POST /api/projects/{project_id}/relations
PUT  /api/projects/{project_id}/relations/{relation_id}

GET  /api/projects/{project_id}/export-profiles
POST /api/projects/{project_id}/export-profiles
```

### 9.3 数据导入

```text
POST /api/projects/{project_id}/assets/upload
POST /api/projects/{project_id}/documents
POST /api/projects/{project_id}/documents/{document_id}/pages/import
GET  /api/projects/{project_id}/documents
GET  /api/documents/{document_id}
GET  /api/pages/{page_id}
GET  /api/pages/{page_id}/image
```

导入规则：

```text
1. 上传文件后计算 sha256。
2. raw asset 只追加。
3. PDF 渲染为 page images 时保留原始 PDF 与页面图片映射。
4. 写入 source manifest。
```

### 9.4 PaddleOCR-VL 预标注

```text
POST /api/projects/{project_id}/paddleocr-vl-runs
GET  /api/projects/{project_id}/paddleocr-vl-runs
GET  /api/paddleocr-vl-runs/{run_id}
GET  /api/pages/{page_id}/paddleocr-vl-runs
GET  /api/pages/{page_id}/paddleocr-vl-output/{run_id}
```

创建 run 时传入：

```json
{
  "input_scope": {
    "document_ids": ["doc_001"],
    "page_ids": []
  },
  "run_config": {
    "pipeline_version": "v1.5",
    "layout_shape_mode": "rect",
    "layout_nms": true,
    "layout_unclip_ratio": 1.0,
    "merge_layout_blocks": true
  }
}
```

### 9.5 标注 revision

```text
GET  /api/pages/{page_id}/annotation/latest
GET  /api/pages/{page_id}/annotation/revisions
GET  /api/annotation-revisions/{revision_id}
POST /api/pages/{page_id}/annotation/revisions
POST /api/annotation-revisions/{revision_id}/submit
POST /api/annotation-revisions/{revision_id}/lock
POST /api/annotation-revisions/{revision_id}/rollback
```

保存 revision 时，后端不覆盖旧 revision。

### 9.6 标注对象与关系

为了减少前端保存冲突，MVP 可以整页保存 JSON。后续可增加对象级 patch API：

```text
PATCH /api/annotation-revisions/{revision_id}/objects/{ann_id}
POST  /api/annotation-revisions/{revision_id}/objects
DELETE /api/annotation-revisions/{revision_id}/objects/{ann_id}

POST  /api/annotation-revisions/{revision_id}/relations
PATCH /api/annotation-revisions/{revision_id}/relations/{rel_id}
DELETE /api/annotation-revisions/{revision_id}/relations/{rel_id}
```

MVP 建议：

```text
前端本地编辑一页 annotation。
点击保存时提交整页 JSON。
后端创建新 revision。
```

### 9.7 质检

```text
POST /api/annotation-revisions/{revision_id}/qc/run
GET  /api/annotation-revisions/{revision_id}/qc-results

POST /api/projects/{project_id}/qc/dataset/run
GET  /api/projects/{project_id}/qc-results
```

### 9.8 复核

```text
POST /api/annotation-revisions/{revision_id}/reviews
GET  /api/annotation-revisions/{revision_id}/reviews
GET  /api/projects/{project_id}/review-queue
```

### 9.9 导出

```text
POST /api/projects/{project_id}/exports
GET  /api/projects/{project_id}/exports
GET  /api/exports/{export_id}
GET  /api/exports/{export_id}/download
```

创建导出：

```json
{
  "export_type": "pp_doclayout_v3",
  "input_scope": {
    "split": "train",
    "document_ids": [],
    "page_ids": []
  },
  "export_profile": {
    "target_format": "COCOInstSegDataset_with_read_order",
    "include_labels": [
      "k12.question_block",
      "k12.option_block",
      "k12.option_image"
    ]
  }
}
```

### 9.10 后台任务

```text
GET /api/jobs/{job_id}
GET /api/jobs/{job_id}/logs
POST /api/jobs/{job_id}/cancel
```

---

## 10. 核心业务流程

### 10.1 数据导入流程

```text
1. 用户上传 PDF / 图片。
2. 后端计算 sha256。
3. 写入 assets。
4. 如果是 PDF，worker 渲染页面图像。
5. 创建 document / pages。
6. 生成 source_record.json。
7. 页面状态变为 imported。
```

### 10.2 PaddleOCR-VL 预标注流程

```text
1. 用户创建 paddleocr_vl_run。
2. API Server 写入 run record，创建 background job。
3. Worker 读取 run_config 和页面图片。
4. 调用 PaddleOCR-VL 官方 pipeline。
5. 保存 res.json / markdown / visualization。
6. 可选保存 PP-DocLayoutV3 boxes / polygon_points / order。
7. 计算 checksum。
8. 写入 paddleocr_vl_run_outputs。
9. 页面状态变为 preannotated。
```

约束：

```text
1. 每次运行生成新 run_id。
2. 不覆盖旧 run 输出。
3. run_config 必须完整保存。
4. 模型失败不影响已有标注。
```

### 10.3 标注保存流程

```text
1. 前端加载 latest revision 或初始化空 annotation。
2. 用户编辑 bbox / quad / polygon / relations。
3. 前端提交整页 annotation JSON。
4. 后端校验 schema。
5. 后端创建新 revision。
6. 保存 annotation revision JSON。
7. 重建 annotation_objects / relation_objects 索引。
8. 触发 QC。
9. 返回 revision_id。
```

### 10.4 复核流程

```text
1. 标注员提交 revision。
2. revision 状态变为 submitted。
3. reviewer 在 review queue 中领取。
4. reviewer 批准、拒绝或要求修正。
5. 批准后 revision 状态变为 reviewed。
6. eval 数据可由 admin 锁定。
```

### 10.5 回滚流程

```text
1. 用户选择历史 revision。
2. 后端不覆盖当前 revision。
3. 后端复制历史 revision 内容，创建新 revision。
4. history 记录 rollback_from_revision_id 和原因。
```

---

## 11. 质检设计

### 11.1 Schema QC

检查：

```text
JSON 是否合法
schema_version 是否支持
annotation id 是否唯一
relation from_id / to_id 是否存在
label 是否存在于 label_registry
attributes 是否符合 attributes_schema
```

### 11.2 Geometry QC

检查：

```text
bbox_xyxy 是否越界
bbox 面积是否为正
quad 是否四点
quad 面积是否为正
polygon 是否至少三点
polygon 是否越界
bbox / quad / polygon 是否明显不一致
```

### 11.3 Scenario Structure QC

场景结构 QC 不属于平台核心硬编码规则，应由 `scenario_profile.qc_rule_set` 配置和加载。

通用平台只负责执行规则、记录结果和阻断不合格导出。具体检查项由场景定义。

K12 场景示例：

```text
question_block 是否有 question_number 或 review_flag
option_image 是否有 owner 关系
option_block 是否属于 question
选择题是否有 option_label
跨页题是否有 page_spans
section_title 是否能关联题目
```

其他场景可以定义完全不同的规则，例如：

```text
合同场景：seal 是否关联签署页，signature 是否关联签署主体。
医疗场景：finding_region 是否关联检查项目，table 是否关联报告段落。
票据场景：key 是否关联 value，金额字段是否通过格式校验。
```

### 11.4 Dataset QC

检查：

```text
train / eval 是否同源泄漏
eval 是否含增强样本
eval 是否含合成样本
split 是否按 document_id 或场景定义的 group_id 隔离；K12 场景可按 paper_id / exam_id 隔离
来源授权字段是否缺失
easy / medium / hard 分布是否异常
```

### 11.5 Export QC

PP-DocLayoutV3 导出前检查：

```text
每个导出对象有合法 bbox / polygon
category_id 稳定且唯一
COCO bbox 为 [x, y, width, height]
segmentation 非空
area > 0
read_order 为非负整数
同一 image 的 read_order 连续
categories 与 export_profile 一致
```

---

## 12. 导出器设计

### 12.1 Exporter 接口

后端内部定义统一 exporter 接口：

```python
class Exporter:
    export_type: str

    def validate_scope(self, scope): ...
    def collect_inputs(self, scope): ...
    def validate_inputs(self, inputs): ...
    def export(self, inputs, output_dir): ...
    def write_report(self, output_dir): ...
```

### 12.2 PP-DocLayoutV3 Exporter

输入：

```text
annotation latest reviewed revision
label_registry
export_profile
page image assets
split manifest
```

输出：

```text
images/
images_mask/
annotations/instance_train.json
annotations/instance_val.json
export_config.json
export_report.md
```

转换规则：

```text
bbox_xyxy -> COCO bbox [x, y, width, height]
polygon -> segmentation
quad -> segmentation fallback
bbox -> rectangular segmentation fallback
read_order -> annotation.read_order
label -> category_id
```

导出后可选触发：

```text
PaddleX check_dataset
```

### 12.3 场景导出器示例：K12 Question JSON Exporter

该导出器不是平台核心要求，而是 K12 场景扩展包中的一个 exporter 示例。其他场景可以注册自己的导出器。

输入：

```text
question_block
section_title
option_block
option_label
option_image
relations
PaddleOCR-VL block_content
page_spans
```

输出：

```text
questions.jsonl
export_report.md
```

原则：

```text
K12 Question JSON 由标注对象和关系装配生成。
不直接把 PaddleOCR-VL res.json 当 gold truth。
```

### 12.4 Statistics Report Exporter

统计报告导出器应支持通用字段 + 场景字段。

通用统计：

```text
页数
文档数
split 分布
标签分布
标注对象数量
关系对象数量
采集方式分布
难度分布
QC 通过率
复核状态分布
```

K12 场景可额外统计：

```text
页数
试卷数
题目数
学科分布
年级分布
题型分布
采集方式分布
难度分布
question_block 数量
option_block 数量
option_image 数量
formula 数量
table 数量
cross_page question 数量
QC 通过率
```

---

## 13. 权限设计

### 13.1 角色权限

```text
viewer
  查看项目、页面、标注和报告。

annotator
  创建 draft revision，编辑未锁定页面。

reviewer
  审核 submitted revision，写 review_records。

data_manager
  导入数据，修改 manifest/source 字段。

exporter
  创建导出任务，下载导出包。

admin
  管理标签、关系、用户、锁定数据、回滚 revision。
```

### 13.2 锁定规则

```text
locked document/page/revision 不允许直接修改。
修正 locked 数据必须创建新 revision。
eval locked 数据默认不能进入训练导出。
admin 才能解除锁定或批准特殊导出。
```

---

## 14. 并发与冲突处理

MVP 采用 revision 级并发控制。

```text
1. 前端加载 revision_id。
2. 保存时提交 base_revision_id。
3. 如果 base_revision_id 不是当前 latest，后端返回 conflict。
4. 用户选择覆盖为新 revision 或手动合并。
```

数据库不做对象级实时协同。后续如需要多人同时编辑同页，再设计对象级 patch 和锁。

---

## 15. 备份与恢复

### 15.1 备份内容

```text
PostgreSQL dump
raw assets checksums
annotation revision json
paddleocr_vl run outputs
export configs and reports
label / relation registry
```

### 15.2 备份频率

```text
数据库：每日全量，关键阶段手动快照。
annotation JSON：每日快照。
raw assets：按 checksum 定期校验。
exports：可重建，保留 export_config 和 report。
```

### 15.3 恢复要求

恢复后必须能：

```text
1. 找回任意 page 的 latest revision。
2. 找回任意 historical revision。
3. 找回任意 paddleocr_vl run 输出。
4. 根据 export_config 重建导出包。
5. 校验 raw asset checksum。
```

---

## 16. 错误处理与审计

### 16.1 错误处理

```text
API 错误返回 request_id。
后台任务失败记录 error_message 和 traceback 摘要。
导出失败保留部分输出目录用于排查。
PaddleOCR-VL 失败不删除 run 目录，状态标记 failed。
```

### 16.2 审计日志

需要记录：

```text
登录
数据导入
标注保存
revision 提交
review 操作
锁定 / 解锁
回滚
导出
标签配置修改
关系配置修改
```

审计字段：

```text
actor_id
action
resource_type
resource_id
before_json
after_json
created_at
request_id
```

---

## 17. MVP 开发拆分

### 17.1 第一阶段

```text
1. FastAPI 项目骨架。
2. PostgreSQL 表：assets / documents / pages / annotation_revisions。
3. 文件上传、sha256、raw asset 归档。
4. 页面列表和图片访问 API。
5. annotation revision 整页保存和读取。
6. label_registry 内置 PP-DocLayoutV3 25 类，并支持按 scenario_profile 加载场景扩展类。
7. 基础 schema / geometry QC。
```

### 17.2 第二阶段

```text
1. PaddleOCR-VL run job。
2. 保存 res.json / markdown / visualization / layout candidates。
3. 从 PaddleOCR-VL 输出生成 suggested annotations。
4. review workflow。
5. revision conflict 检测。
```

### 17.3 第三阶段

```text
1. PP-DocLayoutV3 exporter。
2. 场景导出器示例：K12 Question JSON exporter。
3. statistics report exporter。
4. export job 管理和下载。
5. PaddleX check_dataset 集成。
```

### 17.4 第四阶段

```text
1. 多人任务分配。
2. 审计日志。
3. 备份任务。
4. overlay 批量可视化。
5. 数据集级 QC。
```

---

## 18. 验收标准

后端 MVP 验收：

```text
1. 能导入图片并生成 asset / document / page 记录。
2. raw asset 不会被覆盖，sha256 可查。
3. 能保存和读取页面 annotation revision。
4. 每次保存都生成新 revision，不覆盖旧 revision。
5. 能从 revision JSON 重建 annotation_objects 和 relation_objects 索引。
6. 能执行基础 QC，并返回错误列表。
7. 能保存 PaddleOCR-VL run_config 和 run 输出路径。
8. 能导出 PP-DocLayoutV3 COCOInstSegDataset + read_order。
9. 能通过场景导出器导出业务目标格式；K12 场景下可导出 K12 Question JSON。
10. locked eval 数据不能被普通用户修改或导出到训练集。
```

---

## 19. 关键结论

后端不应试图改造 PaddleOCR-VL 或 PPOCRLabel 的内部数据流。正确边界是：

```text
PaddleOCR-VL 输出只读归档。
平台维护通用标注对象、场景扩展标注和关系。
数据库负责状态、索引、权限和任务。
文件系统负责大文件、原始输出、revision 和导出包。
导出器负责把平台主数据转换为 PP-DocLayoutV3 / 场景业务 JSON 等目标格式。
```

这样既能保持官方模型输入输出稳定，也能满足不同场景的标注、质检、版本、备份和训练数据导出的扩展需求。K12 试卷只是当前第一个场景 profile，不应成为平台核心的硬编码前提。
