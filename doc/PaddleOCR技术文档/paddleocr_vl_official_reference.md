# PaddleOCR-VL / PP-DocLayoutV3 官方输入输出与格式参考

版本：v0.1  
日期：2026-05-20  
用途：记录 PaddleOCR-VL-1.5、PP-DocLayoutV3、后处理 pipeline、训练数据格式和平台设计约束，避免后续开发时混淆 PaddleOCR-VL 输出、PP-DocLayoutV3 训练数据和 K12 自定义标注数据。

---

## 1. 信息来源

本文只整理当前已核验的官方或准官方资料：

```text
1. PaddleOCR-VL 官方使用教程
   https://www.paddleocr.ai/latest/en/version3.x/pipeline_usage/PaddleOCR-VL.html

2. PaddleX Layout Analysis / PP-DocLayoutV3 模块教程
   https://paddlepaddle.github.io/PaddleX/3.5/en/module_usage/tutorials/ocr_modules/layout_analysis.html

3. PaddleOCR Layout Analysis 模块文档
   https://www.paddleocr.ai/latest/en/version3.x/module_usage/layout_analysis.html

4. PaddleOCR-VL-1.5 Hugging Face 模型卡
   https://huggingface.co/PaddlePaddle/PaddleOCR-VL-1.5
```

注意：PaddleOCR / PaddleX 文档版本更新较快，且同一功能在 PaddleOCR 文档和 PaddleX 文档中的命名可能略有差异。涉及训练格式时，以 PaddleX 的 PP-DocLayoutV3 模块教程为主要依据；涉及完整文档解析 pipeline 时，以 PaddleOCR-VL 官方使用教程为主要依据。

---

## 2. PaddleOCR-VL-1.5 的工程边界

### 2.1 不应把 0.9B VLM 当成完整 PaddleOCR-VL pipeline

官方文档明确区分：

```text
PaddleOCR-VL pipeline
  = layout analysis
  + VLM-based recognition
  + pipeline result merging / restructuring / serialization

PaddleOCR-VL-1.5-0.9B
  = 完整 pipeline 内部的 VLM 识别组件
```

工程上不要直接把 `PaddleOCR-VL-1.5-0.9B` 等同于完整页面级文档解析系统。

Hugging Face 上的 transformers 示例只适合：

```text
1. element-level recognition
2. text spotting
3. formula / table / chart / seal 等局部任务
```

不等同于完整页面级 document parsing。

### 2.2 推荐三段式理解

官方教程把 PaddleOCR-VL 简化为两个核心阶段：

```text
1. layout analysis
2. VLM-based recognition
```

但从工程接入和平台设计角度，建议按三段理解：

```text
1. Layout Analysis
   整页输入，检测版面元素，确定位置和阅读顺序，并生成元素级 crop。

2. VLM Recognition
   将每个局部区域独立送入 VLM，得到文本、公式、表格、图表、印章等识别结果。

3. Pipeline Post-processing
   按阅读顺序合并各元素结果，生成 page-level parsing result，并支持 Markdown、JSON、Word、HTML、XLSX、多页重构等输出。
```

平台设计必须保留第 3 段的结果，因为最终 `res.json`、Markdown 和服务化返回结果都不是 VLM 原始输出，而是 pipeline 后处理后的结构化结果。

---

## 3. PaddleOCR-VL pipeline 输入

### 3.1 CLI 输入

典型命令：

```bash
paddleocr doc_parser -i ./paddleocr_vl_demo.png --save_path ./output
```

输入可以是：

```text
1. 图片路径
2. PDF 路径
3. URL
4. 本地图片目录
5. 文件路径列表，Python API 中使用
```

目录预测目前不建议混入 PDF；PDF 应指定具体文件路径。

### 3.2 Python API 输入

```python
from paddleocr import PaddleOCRVL

pipeline = PaddleOCRVL(pipeline_version="v1.5")
output = pipeline.predict("path/to/document_image.png")
for res in output:
    res.print()
    res.save_to_json(save_path="output")
    res.save_to_markdown(save_path="output")
```

PDF 会按页处理，通常每页生成独立结果。多页重构应显式调用 `restructure_pages()`。

### 3.3 关键 pipeline 参数

和平台相关的参数包括：

```text
pipeline_version
layout_detection_model_name
layout_detection_model_dir
layout_threshold
layout_nms
layout_unclip_ratio
layout_merge_bboxes_mode
layout_shape_mode
vl_rec_model_name
vl_rec_model_dir
vl_rec_backend
vl_rec_server_url
use_doc_orientation_classify
use_doc_unwarping
use_layout_detection
use_chart_recognition
use_ocr_for_image_block
merge_layout_blocks
markdown_ignore_labels
format_block_content
vlm_extra_args
```

这些参数应完整记录到平台的 `model_run_config` 中。重跑模型时生成新的 `run_id`，不能覆盖旧结果。

---

## 4. Layout Analysis 阶段

### 4.1 PP-DocLayoutV3 定位

PaddleX 文档说明：

```text
PP-DocLayoutV3 属于 layout analysis module。
它基于 DETR 架构，backbone 为 PPHGNetV2-L。
它在实例分割任务上增加 reading order prediction branch。
```

它输出的信息包括：

```text
1. layout element 类别
2. bbox，推理结果中常见字段为 coordinate: [xmin, ymin, xmax, ymax]
3. instance segmentation contour / polygon_points
4. reading order index
```

这比传统 layout detection 只输出矩形框更丰富。

### 4.2 PP-DocLayoutV3 官方 25 类

PaddleX PP-DocLayoutV3 文档列出的 25 个类别如下。导出训练数据时应优先采用这些官方英文类别名作为参考。

| 序号 | 类别名 | 说明 |
|---:|---|---|
| 1 | `abstract` | 摘要 |
| 2 | `algorithm` | 算法 |
| 3 | `aside_text` | 侧边栏文本 |
| 4 | `chart` | 图表 |
| 5 | `content` | 目录 |
| 6 | `display_formula` | 行间公式 |
| 7 | `doc_title` | 文档标题 |
| 8 | `figure_title` | 图/表/图表标题 |
| 9 | `footer` | 页脚 |
| 10 | `footer_image` | 页脚图片 |
| 11 | `footnote` | 脚注 |
| 12 | `formula_number` | 公式编号 |
| 13 | `header` | 页眉 |
| 14 | `header_image` | 页眉图片 |
| 15 | `image` | 图片 |
| 16 | `inline_formula` | 行内公式 |
| 17 | `number` | 页码 |
| 18 | `paragraph_title` | 段落标题 |
| 19 | `reference` | 参考文献 |
| 20 | `reference_content` | 参考文献内容 |
| 21 | `seal` | 印章 |
| 22 | `table` | 表格 |
| 23 | `text` | 文本 |
| 24 | `vertical_text` | 竖排文本 |
| 25 | `vision_footnote` | 图注 |

设计影响：

```text
1. 平台内置标签注册表必须包含官方 25 类。
2. K12 自定义标签必须与官方 25 类分命名空间，例如 `k12.question_block`。
3. 导出 PP-DocLayoutV3 训练数据时，需要明确 category mapping。
4. 如果训练 K12-enhanced PP-DocLayoutV3，需要在导出 profile 中决定：
   A. 只训练官方 25 类；
   B. 官方 25 类 + K12 扩展类；
   C. 只训练 K12 扩展类。
```

### 4.3 PP-DocLayoutV3 推理输出

PaddleX 示例中，`create_model("PP-DocLayoutV3")` 的结果结构大致为：

```json
{
  "res": {
    "input_path": "layout.jpg",
    "page_index": null,
    "boxes": [
      {
        "cls_id": 22,
        "label": "text",
        "score": 0.98,
        "coordinate": [34.1, 349.8, 358.5, 611.0],
        "polygon_points": [
          [34.1, 349.8],
          [358.5, 349.8],
          [358.5, 611.0],
          [34.1, 611.0]
        ],
        "order": 3
      }
    ]
  }
}
```

字段含义：

```text
input_path       输入图片路径
page_index       PDF 页码；非 PDF 时通常为 None
boxes            按阅读顺序排列的检测对象列表
cls_id           类别 ID
label            类别名
score            置信度
coordinate       bbox，格式为 [xmin, ymin, xmax, ymax]
polygon_points   实例分割轮廓点，格式为 [[x1,y1], [x2,y2], ...]
order            阅读顺序，通常从 0 开始
```

### 4.4 关于四点、多边形和 bbox

需要区分三个概念：

```text
coordinate
  轴对齐 bbox，格式 [xmin, ymin, xmax, ymax]。
  这不是四点标注，而是两个对角点压平成四个数：
  左上点 (xmin, ymin) + 右下点 (xmax, ymax)。

polygon_points
  实例分割轮廓点。
  官方示例常见为四点矩形轮廓，但字段本身是点列表，可以表达四点或多点 polygon。

layout_shape_mode
  PaddleOCR-VL pipeline 中控制 layout 几何表达的参数，支持 rect / quad / poly / auto。
```

`layout_shape_mode` 含义：

```text
rect  输出轴对齐矩形框。
quad  输出四点任意四边形，适合倾斜或透视区域。
poly  输出多点闭合轮廓，适合不规则或弯曲区域。
auto  自动选择合适表达方式。
```

设计影响：

```text
1. 平台可以让标注员先画普通矩形 bbox，但内部不能只保留 bbox。
2. 对普通矩形，平台应能从 bbox 自动生成四点 quad / polygon。
3. 对倾斜、透视、异形区域，平台应预留人工 quad / polygon 标注能力。
4. 推荐平台内部统一存 bbox_xyxy + quad + polygon；polygon 可以由 bbox 或 quad 派生。
5. PP-DocLayoutV3 导出时，从 polygon 或 quad 生成 COCO segmentation；若只有 bbox，则生成矩形四点 segmentation 并在导出报告中标记 fallback。
```

---

## 5. VLM Recognition 阶段

### 5.1 完整 pipeline 中的 VLM 输入

完整 PaddleOCR-VL pipeline 中，VLM 不是直接处理整页后直接输出整页 JSON。官方描述是：

```text
layout analysis 先检测并裁剪元素级子图；
每个子图独立送入 VLM；
VLM 输出局部识别结果；
pipeline 再按阅读顺序合并。
```

因此，平台不要尝试修改 0.9B VLM 的 region-level 输入输出。

### 5.2 0.9B standalone / transformers 任务

Hugging Face 模型卡给出的 standalone 任务包括：

```text
ocr
table
chart
formula
spotting
seal
```

对应 prompt：

```text
OCR:
Table Recognition:
Chart Recognition:
Formula Recognition:
Spotting:
Seal Recognition:
```

模型卡也说明：transformers 示例仅支持 element-level recognition 和 text spotting；推荐使用官方 PaddleOCR pipeline，因为官方方法更快且支持 page-level document parsing。

---

## 6. Pipeline Post-processing 阶段

### 6.1 为什么后处理必须单独考虑

PaddleOCR-VL 的 page-level 输出不是单个模型一次性吐出的原始结果，而是经过 pipeline 合并后的结构化结果。

后处理至少涉及：

```text
1. layout box 后处理，例如 NMS、unclip、overlap merge。
2. region-level VLM 结果回填到 layout block。
3. 根据 reading order 合并元素级结果。
4. 生成 parsing_res_list。
5. 生成 Markdown / JSON / Word / HTML / XLSX 等输出。
6. PDF 多页场景下执行 restructure_pages。
```

平台保存数据时，必须把以下三类结果分开：

```text
1. layout analysis 原始或近原始结果
2. VLM region recognition 结果
3. pipeline post-processing 后的 res.json / markdown / visualization
```

如果当前只能拿到第 3 类，也应把它作为只读官方 pipeline 输出保存。

### 6.2 layout 相关后处理参数

和 layout 后处理强相关的参数：

```text
layout_threshold
  layout 置信度阈值。

layout_nms
  是否执行 NMS 过滤重叠框。

layout_unclip_ratio
  对 layout 检测框做扩张。

layout_merge_bboxes_mode
  对重叠或包含框进行过滤或保留。
  可选模式包括 large / small / union，也支持按类别配置。

merge_layout_blocks
  控制是否合并跨列或上下错位列的 layout boxes。
```

这些参数会影响最终 `parsing_res_list`，因此必须进入 `run_config`。

### 6.3 多页后处理 restructure_pages

官方 Python API 支持：

```python
pages_res = list(pipeline.predict(input_file))
output = pipeline.restructure_pages(
    pages_res,
    merge_tables=True,
    relevel_titles=True,
    concatenate_pages=False
)
```

参数含义：

```text
merge_tables       是否合并跨页表格，默认 True
relevel_titles     是否重建多级标题，默认 True
concatenate_pages  是否把多页结果合并成单页，默认 False
```

设计影响：

```text
1. 每页原始 predict 结果要保存。
2. restructure_pages 的输出也要保存为独立 run artifact。
3. K12 跨页题不应直接依赖 restructure_pages；应在 K12 标注层独立维护 page_spans。
4. 但可参考 page_continuation_flags、阅读顺序和跨页表格合并结果做辅助判断。
```

---

## 7. PaddleOCR-VL pipeline 输出

### 7.1 Result 对象方法

官方 Result 对象支持：

```text
print()
save_to_json()
save_to_img()
save_to_markdown()
save_to_html()
save_to_xlsx()
save_to_word()
```

平台至少需要保存：

```text
1. save_to_json 输出
2. save_to_markdown 输出
3. save_to_img 输出
4. 调用参数 run_config
5. 输入图片/PDF hash
```

### 7.2 JSON 输出字段

`save_to_json()` 保存的结果和 `res.json` 属性内容一致。关键字段包括：

```text
input_path
page_index
page_count
width
height
model_settings
doc_preprocessor_res
parsing_res_list
```

`model_settings` 中包含：

```text
use_doc_preprocessor
use_layout_detection
use_chart_recognition
format_block_content
markdown_ignore_labels
```

`doc_preprocessor_res` 只在启用文档预处理时存在，可能包含：

```text
use_doc_orientation_classify
use_doc_unwarping
angle
```

`parsing_res_list` 是最重要的 page-level 元素列表。每个元素常见字段：

```text
block_bbox
block_label
block_content
block_id
block_order
```

字段含义：

```text
block_bbox      layout 区域 bbox
block_label     layout 区域标签，例如 text / table
block_content   区域内容
block_id        区域编号，用于展示 layout 排序结果
block_order     区域阅读顺序；非排序部分可能为 None
```

注意：

```text
1. parsing_res_list 的顺序代表解析后的阅读顺序。
2. JSON 文件不能保存 numpy.array，因此保存时会转换成 list。
3. res.json 是 pipeline 后处理结果，不等于 PP-DocLayoutV3 训练标注。
```

### 7.3 img 属性输出

`res.img` 是可视化图像字典，可能包含：

```text
layout_det_res
overall_ocr_res
text_paragraphs_ocr_res
formula_res_region1
table_cell_img
seal_res_region1
```

如果未使用相关可选模块，可能只包含 `layout_det_res`。

这些图像主要用于调试和质检，不应作为训练标注的唯一来源。

### 7.4 markdown 属性输出

`res.markdown` 是 Markdown 结果字典，可能包含：

```text
markdown_texts
markdown_images
page_continuation_flags
```

Markdown 适合展示和 RAG 输入，但不适合作为 K12 切题、元素归属和 PP-DocLayoutV3 训练的主数据格式。

### 7.5 服务化接口输出

服务化接口返回结构中，核心字段是：

```text
result
  layoutParsingResults[]
    prunedResult
    markdown
    outputImages
    inputImage
  dataInfo
```

其中：

```text
prunedResult   简化后的结构化结果
markdown       Markdown 文本和图片
outputImages   可视化图片，通常为 base64
inputImage     输入图像
```

平台对服务化结果的处理原则与本地 `save_to_json()` 一致：只读归档，不反向覆盖人工标注。

---

## 8. PP-DocLayoutV3 训练数据格式

### 8.1 官方格式

PaddleX 文档说明，PP-DocLayoutV3 使用：

```text
COCOInstSegDataset format
+ read_order field
```

推荐目录结构：

```text
doclayoutv3_examples/
  images/
    train_0001.jpg
    val_0001.jpg
  images_mask/
    ...
  annotations/
    instance_train.json
    instance_val.json
```

说明：

```text
images       原始图像目录
images_mask  训练用图像目录，官方示例说明内容与 images 相同
annotations  COCO instance segmentation annotation
```

### 8.2 annotation 示例

官方示例的核心字段：

```json
{
  "id": 1,
  "image_id": 1,
  "category_id": 22,
  "bbox": [34.1, 349.8, 324.4, 261.2],
  "segmentation": [[34.1, 349.8, 358.5, 349.8, 358.5, 611.0, 34.1, 611.0]],
  "area": 84740.0,
  "iscrowd": 0,
  "read_order": 0
}
```

字段说明：

```text
bbox          COCO bbox，格式 [x, y, width, height]
segmentation  COCO polygon segmentation
area          区域面积
iscrowd       COCO 字段，通常为 0
read_order    阅读顺序，非负整数，从 0 开始
```

标准 COCO 文件还应包含：

```text
images
annotations
categories
```

平台导出器必须稳定生成 `categories`，并且不要让 category_id 随导出批次漂移。

### 8.3 read_order 要求

官方要求：

```text
1. read_order 是非负整数。
2. 同一张图内的所有 read_order 应形成连续序列。
3. 通常从 0 开始。
```

设计影响：

```text
1. 平台标注层必须支持人工维护 read_order。
2. 自动生成 read_order 可以作为草稿，但导出前必须 QC。
3. 每张图导出前要重新检查 read_order 是否连续。
```

### 8.4 check_dataset

PaddleX 支持数据集检查：

```bash
python main.py -c paddlex/configs/modules/layout_analysis/PP-DocLayoutV3.yaml \
  -o Global.mode=check_dataset \
  -o Global.dataset_dir=./dataset/doclayoutv3_examples
```

通过后会输出：

```text
check_dataset_result.json
可视化样例
样本分布直方图
```

平台导出 PP-DocLayoutV3 数据后，应提供一键执行或提示执行 `check_dataset`。

### 8.5 训练、评估和集成

PaddleX 支持：

```text
1. check_dataset
2. train
3. evaluate
4. predict
5. weight conversion
```

官方文档还说明，训练得到的 PP-DocLayoutV3 权重可以集成到 PaddleX pipeline 或 PaddleOCR-VL / document parsing pipeline 中，只需替换 layout analysis module 的模型路径。

设计影响：

```text
1. 平台导出的 PP-DocLayoutV3 数据要保留 export_config。
2. export_config 记录 category mapping、split、source revision。
3. 训练得到的新模型路径应能作为 PaddleOCR-VL 的 layout_detection_model_dir 使用。
```

---

## 9. 对 K12 标注平台的修正规则

### 9.1 主数据格式不能只围绕 PaddleOCR-VL res.json

`res.json` 是完整 pipeline 后处理结果，不是训练 PP-DocLayoutV3 的原生标注格式。因此平台主 JSON 应分层保存：

```text
raw_asset
paddleocr_vl_run
paddleocr_vl_res_json
layout_candidates
k12_annotations
k12_relations
qc_records
export_records
```

### 9.2 原始输出只读保存

以下文件或对象不允许被人工修改：

```text
1. 原始 PDF / 图片
2. PaddleOCR-VL 原始 res.json
3. PaddleOCR-VL 原始 Markdown
4. PaddleOCR-VL 原始 visualization
5. PP-DocLayoutV3 原始 boxes 输出
```

人工标注和修正只能新增到：

```text
k12_annotations
k12_relations
review_records
revision files
```

### 9.3 K12 自定义标签不要污染官方 25 类

建议命名空间：

```text
paddle.layout.text
paddle.layout.table
paddle.layout.inline_formula

k12.question_block
k12.option_block
k12.option_image
k12.stem_figure
k12.answer_area
```

导出时再映射到目标格式。

### 9.4 几何字段必须升级

平台内部建议统一字段：

```json
{
  "geometry": {
    "bbox_xyxy": [120, 326, 2260, 1040],
    "quad": [[120, 326], [2260, 326], [2260, 1040], [120, 1040]],
    "polygon": [[120, 326], [2260, 326], [2260, 1040], [120, 1040]],
    "mask_ref": null
  }
}
```

说明：

```text
bbox_xyxy  便于页面显示和快速空间计算，对应 coordinate 的 [xmin, ymin, xmax, ymax]。
quad       由四点表示倾斜/透视区域；普通矩形可由 bbox 自动生成 quad。
polygon    便于兼容 COCO segmentation 和 poly 模式；普通矩形可由 bbox 自动生成四点 polygon。
mask_ref   为未来精细 mask 预留。
```

### 9.5 PP-DocLayoutV3 导出器的最低要求

导出器必须完成：

```text
1. 筛选要导出的标签。
2. 生成稳定 category_id。
3. 将 bbox_xyxy 转成 COCO bbox [x,y,w,h]。
4. 将 quad / polygon 转成 segmentation。
5. 计算 area。
6. 生成 read_order。
7. 检查 read_order 连续。
8. 生成 images / annotations / categories。
9. 复制或链接 images 和 images_mask。
10. 写入 export_config 和 export_report。
```

### 9.6 PaddleOCR-VL 后处理输出的用途

PaddleOCR-VL `res.json` 适合：

```text
1. 作为预标注来源。
2. 生成 Element Table。
3. 给 K12 Question Assembler 提供 block_content。
4. 对比模型版本。
5. 做错误分析。
```

不适合直接作为：

```text
1. PP-DocLayoutV3 训练标注。
2. K12 最终 gold annotation。
3. 跨页题唯一真相。
4. option_image owner 唯一真相。
```

---

## 10. 后续需要继续核验的问题

以下点在实际开发前还需要结合本地安装的 PaddleOCR / PaddleX 版本进一步确认：

```text
1. PaddleOCR-VL-1.5 默认 layout_detection_model_name 在当前安装版本中具体是什么。
2. 当前版本 `save_to_json()` 是否会保留 polygon / quad，还是只保留 block_bbox。
3. 是否能通过公开 API 直接拿到 PP-DocLayoutV3 的 polygon_points 和 order。
4. `layout_shape_mode=quad/poly` 在 res.json 中的具体字段表现。
5. 自定义 PP-DocLayoutV3 类别训练时，配置文件中 category list 和 num_classes 的实际修改位置。
6. 使用自训练 PP-DocLayoutV3 权重接入 PaddleOCR-VL pipeline 时，类别名映射如何传递到后处理。
7. PaddleOCR-VL 后处理是否会过滤未知 layout label。
8. X-AnyLabeling 的 PaddleOCR 面板能否保留 quad/poly 结果，或只保存可视化框。
```

这些问题应通过一个最小实验集验证：

```text
1. 选 3 页真实试卷。
2. 跑 PaddleOCR-VL-1.5。
3. 保存 res.json / img / markdown。
4. 单独跑 PP-DocLayoutV3。
5. 对比 parsing_res_list、boxes、polygon_points、order。
6. 测试 layout_shape_mode=rect/quad/poly/auto。
7. 测试导出一份 PP-DocLayoutV3 demo 训练集并运行 check_dataset。
```

---

## 11. 当前结论

```text
1. PP-DocLayoutV3 官方原生 layout 类别是 25 类。
2. PP-DocLayoutV3 训练格式是 COCO instance segmentation + read_order。
3. 官方推理结果中的 coordinate 是两点对角 bbox 表达，不是四点。
4. polygon_points 才是轮廓点列表；官方示例常见为四点矩形，也可能扩展为多点 polygon。
5. 官方训练样例使用 polygon segmentation；矩形框可以转成四点 segmentation，但平台应预留多点 polygon。
6. PaddleOCR-VL-1.5 完整能力来自 layout analysis + VLM recognition + pipeline post-processing。
7. 0.9B VLM standalone 只适合局部识别和 spotting，不等于完整文档解析。
8. PaddleOCR-VL res.json 是后处理后的页面级结果，不是 PP-DocLayoutV3 训练格式。
9. 平台应只读保存 PaddleOCR-VL 原始输出，在旁边维护 K12 标注和关系。
10. PP-DocLayoutV3 导出器需要从 K12 主 JSON 转成 COCOInstSegDataset + read_order。
11. 后续平台设计必须记录 run_config，尤其是 layout_nms、layout_unclip_ratio、layout_merge_bboxes_mode、layout_shape_mode、merge_layout_blocks 和 restructure_pages 参数。
```
