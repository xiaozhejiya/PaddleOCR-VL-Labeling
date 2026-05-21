# K12 试卷数据要求说明

版本：v1.0  
用途：用于 PaddleOCR 全球衍生模型挑战赛中，指导 K12 试卷识别与解析任务的数据采集、评估集构建、训练集组织与标注验收。  
核心原则：**评估集质量优先于训练集规模。评估集一旦被认定为合成数据占比过高，将直接失去排名资格；训练集即使部分来自公开/网络数据，也应保证来源说明、授权风险、标注规范和统计分析。**

---

## 1. 总体判断

本次 K12 试卷任务的数据要求应按以下优先级处理：

```text
第一优先级：评估集真实、独立、可客观评价模型能力
第二优先级：评估集标注准确、可复核、可视化质量高
第三优先级：评估集覆盖 K12 试卷的真实复杂场景
第四优先级：训练集规模、训练集来源和训练增强策略
```

评分表中，“评估集质量”单项 20 分，而且合成评估集占比过高会触发一票否决。相比之下，训练数据集构建科学性虽然也是 20 分，但其中“数据来源是否清晰”对应 5 分；如果训练集部分来自公开或网络数据，只要来源、许可、用途、标注和质检交代清楚，风险相对可控。

因此，数据工作建议采用：

```text
评估集：100% 真实采集 / 授权真实数据，不使用增强图，不使用合成图。
训练集：真实采集为主，可以混合公开辅助数据和增强数据，但必须单独标注来源。
验证集：尽量真实采集，少量增强仅用于内部分析，不建议用于最终报告核心指标。
```

---

## 2. 评估集是本项目的第一关键

### 2.1 评估集的红线

评估集不能出现以下情况：

```text
1. 以合成模板、PDF 自动渲染、AI 生成图像作为评估集主体。
2. 使用训练集中同一套试卷的不同页或不同拍摄版本作为评估集。
3. 使用公开网络试卷作为评估集主体，但没有授权或来源说明。
4. 评估集中大量页面来自同一版式、同一题型、同一学科，分布过窄。
5. 标注错误明显、question_block 重叠严重、题号/选项归属错误未复核。
6. 评估集标签参与训练、调参或 prompt 优化。
7. 只用清晰 PDF 图像，缺乏真实拍摄、扫描、擦除、阴影、倾斜等复杂场景。
```

必须明确写入项目文档：

```text
评估集仅用于最终评价，不用于训练、不用于调参、不用于规则开发。
评估集不含增强样本。
评估集不含合成样本，或合成/模板样本比例为 0。
评估集按 paper_id / exam_id 分组独立切分，避免同源泄漏。
```

---

## 3. 评估集规模建议

评分表推荐评估集达到 500 页以上。为了更稳地支撑比赛评价，建议目标设为：

```text
基础达标：≥ 500 页真实试卷图像
推荐目标：1000 页真实试卷图像
冲高目标：1200–1500 页真实试卷图像
```

如果做 1000 页评估集，建议大致达到：

```text
试卷页数：1000 页
完整试卷套数：不少于 80–150 套，避免少量试卷重复页过多
题目数量：约 5000–8000 道
question_block 实例：约 5000–8000 个
option_block 实例：约 12000–25000 个，取决于选择题比例
option_image 实例：至少 300–800 个，越多越能体现 K12 场景复杂性
formula 实例：至少 1500–3000 个
table 实例：至少 200–500 个
stem_figure 实例：至少 500–1500 个
cross_page question：建议至少 30–100 道
```

如果暂时无法达到 1000 页，至少保证：

```text
评估集 ≥ 500 页
题目数 ≥ 3000 道
图文混合题、图片选项题、跨页题、表格题、公式题均有覆盖
```

---

## 4. 评估集来源要求

### 4.1 推荐来源

优先使用以下来源：

```text
1. 教师授权提供的校内单元测、月考、期中、期末、模拟卷。
2. 学校或教研组授权的自编练习卷。
3. 自主整理、重排并拥有使用权的 K12 试卷。
4. 真实纸质试卷扫描件。
5. 真实纸质试卷手机拍摄件。
6. 已作答试卷经手写/批注擦除后的题面图像。
```

### 4.2 不建议作为评估集主体的来源

```text
1. 商业教辅书扫描页，除非有明确授权。
2. 题库网站或培训机构平台下载的试卷，除非许可明确。
3. 公开数据集中的题目图像，除非许可证允许且只作为少量补充。
4. AI 生成题目或模板自动生成试卷。
5. 只由 PDF 转图片生成的清晰页面。
```

### 4.3 来源台账必须保留

每份评估集试卷都应记录：

```text
paper_id
source_type：teacher_authorized / school_authorized / self_created / public_auxiliary
authorization_id
subject
grade
exam_type：unit_test / monthly_test / midterm / final / mock_exam / worksheet
year_or_term
province_or_region
capture_method：scanner / phone_photo / erased_answer_sheet
capture_device
resolution_or_dpi
lighting_condition
perspective_level
blur_level
fold_or_damage
handwriting_erased
split：eval
```

建议文件名：

```text
dataset_manifest_eval.csv
```

---

## 5. 评估集视觉场景要求

评分表强调真实视觉复杂度。评估集至少应包含 4 类以上真实场景，不能全部是清晰 PDF。

### 5.1 推荐场景类别

```text
1. 清晰扫描件
2. 手机正常拍摄件
3. 手机轻微倾斜 / 透视变形
4. 阴影 / 弱光 / 局部反光
5. 轻微模糊 / 手持抖动
6. 折痕 / 卷曲 / 纸张边缘不平
7. 作答后擦除样本
8. 双栏或多栏版式
9. 跨页题
10. 图文混排、图片选项、公式选项、表格题
```

### 5.2 推荐比例

对于 1000 页评估集，建议：

```text
清晰扫描 / 清晰拍照：35%–45%
手机正常拍摄：15%–20%
手机倾斜 / 透视：10%–15%
光照复杂 / 阴影 / 反光：10%–15%
轻微模糊 / 折痕 / 卷曲：5%–10%
作答后擦除样本：10% 左右
跨页题 / 双栏 / 图文混排 hard case：单独确保数量，不仅按页比例计算
```

注意：

```text
评估集中的复杂场景必须是真实采集，不要用程序化增强生成。
训练集可以增强，评估集不建议增强。
```

---

## 6. 评估集内容结构要求

K12 试卷解析要体现结构复杂度和语义复杂度，不能只采选择题或纯文本题。

### 6.1 学科建议

优先采集理科与综合题型较多的学科：

```text
数学：公式、几何图、函数图、证明题、计算题
物理：电路图、实验装置图、表格、计算题
化学：实验装置图、反应式、表格、推断题
生物：图示题、表格题、材料题
英语 / 语文：阅读理解、材料题、作文题，可作为补充
```

### 6.2 题型覆盖

评估集至少覆盖：

```text
single_choice        单选题
multiple_choice      多选题
true_false           判断题
fill_blank           填空题
calculation          计算题
proof                证明题
short_answer         简答题
experiment           实验探究题
reading              阅读理解题
matching             连线 / 匹配题
diagram_labeling     看图填空 / 图示标注题
composite            综合题 / 材料题 / 题组
essay                作文 / 写作题，视学科决定是否纳入
```

### 6.3 结构复杂样本必须保留

这些样本对得分有价值：

```text
1. 图片选项：A/B/C/D 是几何图、函数图、实验图等。
2. 图文混合选项：选项中同时有文字、公式、图片。
3. 公式选项：选项为公式或公式+文字。
4. 题干配图：题干中的几何图、电路图、实验图。
5. 表格题：实验记录表、数据表、统计表。
6. 跨页题：题目跨越两页或子题分布在下一页。
7. 材料题：一个材料下面多个小题。
8. 双栏试卷：左右分栏、阅读顺序复杂。
9. 擦除后试卷：学生答案擦除后保留真实残留噪声。
```

---

## 7. 评估集难度分层

评估集应包含 easy / medium / hard，并且分布合理。

建议定义：

```text
Easy：
清晰扫描或清晰拍照；单栏；纯文本为主；无复杂配图；题目边界清晰。

Medium：
含公式、表格、配图、图片选项；轻微倾斜、阴影或擦除残留；题目结构较复杂。

Hard：
跨页题、双栏/多栏、图文混合选项、低光照/强阴影、折痕/卷曲、擦除造成局部破坏、材料题或综合题组。
```

推荐比例：

```text
Easy：30%–40%
Medium：40%–50%
Hard：15%–25%
```

不能出现：

```text
全部 easy：无法体现任务挑战。
全部 hard：不符合真实分布，也会导致评估不稳定。
```

---

## 8. 评估集标注要求

评估集标注必须比训练集更严格。建议所有评估集样本至少双人复核或高风险样本 100% 复核。

### 8.1 必标字段

每页必须标注：

```text
page_id
paper_id
page_index
subject
grade
capture_method
visual_difficulty：easy / medium / hard
```

每道题必须标注：

```text
question_id
section_id
section_title
question_number
question_type
is_cross_page
page_spans
question_block bbox / polygon
source_element_ids
stem text
options，非选择题为 []
figures
formulas
tables
answer，若可获得
analysis，若可获得
knowledge_points，若已建设知识点体系
review_flags
```

### 8.2 检测类标注

建议评估集保留这些版面标签：

```text
section_title        大题标题
question_block       整题区域
subquestion_block    小题区域
question_number      题号
stem_block           题干区域
option_label         选项标签
option_block         选项区域
stem_figure          题干共享图片
option_image         选项图片
formula              公式
table                表格
answer_area          答题区
analysis_block       解析区
page_header          页眉
page_footer          页脚
noise_or_erasure     擦除残留、遮挡、污渍等干扰区域
```

最低不可少的是：

```text
question_block
section_title
question_number
option_label
option_block
stem_figure
option_image
formula
table
cross_page page_spans
```

---

## 9. 评估集 JSON 结构要求

推荐每道题采用以下结构：

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
      "polygon": [[120, 326], [2260, 326], [2260, 1040], [120, 1040]],
      "source_element_ids": ["p001_e0002", "p001_e0003"]
    }
  ],
  "content": {
    "stem": {
      "text": "下列图形中，既是轴对称图形又是中心对称图形的是（ ）",
      "source_element_ids": ["p001_e0003"]
    },
    "options": [
      {
        "label": "A",
        "option_type": "image_only",
        "text": "",
        "source_element_ids": ["p001_e0005", "p001_e0006"],
        "content_spans": [
          {
            "type": "image",
            "source_element_id": "p001_e0006",
            "crop_ref": "crops/p001_e0006.png"
          }
        ]
      }
    ],
    "figures": [],
    "formulas": [],
    "tables": []
  },
  "answer": {
    "available": true,
    "value": "A"
  },
  "knowledge_points": [],
  "review_flags": []
}
```

关键原则：

```text
1. 非选择题 options = []，不要强行补选项。
2. 图片选项必须挂到 option.content_spans，不要只放在全局 figures。
3. 跨页题用 page_spans，不用单一 bbox。
4. 题目 bbox 应由 source_element_ids 或 question_block 坐标确定。
5. 标注文件应保留可追溯的 source_element_ids。
```

---

## 10. 跨页题评估集要求

跨页题是 K12 试卷解析的重要复杂场景，应在评估集中保留。

### 10.1 标注方式

```json
{
  "question_id": "paper_001_q021",
  "question_number": "21",
  "is_cross_page": true,
  "page_spans": [
    {
      "page_id": "paper_001_p003",
      "role": "question_head",
      "bbox_xyxy": [120, 2450, 2320, 3480],
      "source_element_ids": ["p003_e102", "p003_e103"]
    },
    {
      "page_id": "paper_001_p004",
      "role": "question_tail",
      "bbox_xyxy": [120, 120, 2320, 980],
      "source_element_ids": ["p004_e001", "p004_e002"]
    }
  ],
  "merged_image": {
    "path": "merged_questions/paper_001_q021.png",
    "merge_policy": "vertical_stitch_by_page_order"
  }
}
```

### 10.2 质检要求

```text
所有跨页题 100% 人工复核。
所有跨页题必须检查 page_spans 是否完整。
如果跨页题包含选项 B/C/D 延续到下一页，必须检查 option owner 是否正确。
如果跨页题是材料题或综合题，必须检查 parent_question_id / sub_question_id。
```

---

## 11. 图片选项与图文混合选项要求

评估集中必须保留一定数量的图片选项和图文混合选项。它们能体现 K12 试卷区别于普通 OCR 的核心价值。

### 11.1 选项类型

```text
text_only          纯文本选项
image_only         纯图片选项
text_image         文本 + 图片选项
formula_only       公式选项
text_formula       文本 + 公式选项
mixed              文本 + 图片 + 公式等混合选项
```

### 11.2 标注要求

```text
1. 每个 option_block 必须有 label：A/B/C/D 或 ①②③④。
2. 图片选项必须有 option_image，并明确 owner。
3. 图文混合选项中，text 和 image 都要作为 content_spans。
4. 题干共享图不要误挂到某个 option。
5. 如果一个大图内部包含 A/B/C/D 子图，尽量切成多个 option_image；无法切分时标 review_flag。
```

---

## 12. 评估集质检要求

评估集应建立独立质检流程。

### 12.1 自动质检

```text
JSON schema 是否合法
question_id 是否唯一
page_id / paper_id 是否存在
bbox / polygon 是否越界
question_block 是否严重重叠
option_block 是否落在 question_block 内
option_image 是否有 owner
选择题是否存在 option_label
非选择题 options 是否为空数组
cross_page question 是否有多个 page_spans
知识点 id 是否存在于 taxonomy
评估集是否与训练集同源泄漏
```

### 12.2 人工质检

```text
普通题目抽检 20%
图片选项题 100% 复核
跨页题 100% 复核
材料题 / 综合题 100% 复核
知识点标注抽检 20%
所有 hard 样本 100% 可视化检查
```

### 12.3 可视化质检

每页生成 overlay 图，至少显示：

```text
question_block
section_title
question_number
option_block
option_image
stem_figure
formula
table
cross_page 标记
```

建议输出：

```text
visualizations/eval_overlay/
visualizations/eval_hard_cases/
visualizations/eval_cross_page/
visualizations/eval_option_image/
```

---

## 13. 评估集统计报告要求

必须生成评估集统计报告。建议文件名：

```text
eval_dataset_statistics_report.md
```

至少包含：

```text
总页数
总试卷数
总题目数
学科分布
年级分布
题型分布
采集方式分布
视觉场景分布
难度分布：easy / medium / hard
question_block 数量
option_block 数量
option_image 数量
formula 数量
table 数量
stem_figure 数量
cross_page question 数量
擦除样本数量
图片选项题数量
图文混合选项题数量
每页平均题目数
每题平均元素数
知识点分布，若已有知识点标注
```

建议提供图表：

```text
题型分布柱状图
学科/年级分布图
采集方式分布图
视觉场景分布图
难度分布图
layout 标签数量柱状图
跨页题样例可视化
图片选项样例可视化
标注错误修复前后对比图
```

---

## 14. 训练集要求：相对可放宽，但不能完全失控

训练集可以比评估集更灵活。

### 14.1 训练集可以使用的来源

```text
1. 自采真实试卷
2. 教师/学校授权试卷
3. 公开数据集中的相关 K12 题目或试卷图片
4. 网络公开试卷，但必须记录来源和版权风险
5. 基于真实训练集生成的数据增强样本
6. 用于知识点标注的公开语义数据集，如 K12Vista、MDK12-Bench、Math23K 等
```

### 14.2 训练集使用公开/网络数据的风险

训练集即使来自网络，最直接影响的是“训练数据来源是否清晰”这一项。但注意：如果训练集没有标注规范、没有质检、没有统计分析，仍然会继续影响训练数据集构建科学性的其他子项。

因此即使训练集来自公开数据，也要保留：

```text
source_url 或 dataset_name
license / terms of use
是否允许二次标注
是否允许再发布
是否只用于训练，不进入评估
对应 paper_id / sample_id
```

### 14.3 训练集与评估集必须隔离

```text
1. 公开数据不要混入核心评估集。
2. 同一套试卷不能同时出现在 train 和 eval。
3. 同一道题的清晰版、拍照版、增强版不能跨 train/eval。
4. 增强样本只能来自训练集，不能来自评估集。
5. 评估集锁定后，不能再被用于开发规则或调参。
```

---

## 15. 训练集推荐规模

如果评估集为 1000 页：

```text
最低训练集：3000 页真实/公开混合训练页
推荐训练集：5000 页真实/公开混合训练页
增强训练集：基于真实训练页生成 1–2 倍增强样本
验证集：300–500 页真实样本
```

建议：

```text
真实训练页：3000–5000 页
增强页：3000–10000 页
公开辅助语义数据：单独作为 external_auxiliary，不计入真实训练页
```

训练集可以增强，但必须单独统计：

```text
real_train_pages
aug_train_pages
public_auxiliary_pages_or_questions
```

---

## 16. 推荐交付材料

围绕评估集，应至少准备：

```text
eval_dataset_card.md
exam_paper_requirements_eval_focused.md
collection_protocol_eval.md
annotation_guideline_eval.md
eval_label_schema.json
eval_dataset_manifest.csv
eval_quality_control_report.md
eval_dataset_statistics_report.md
eval_split_policy.md
visualizations/eval_overlay/
visualizations/eval_hard_cases/
visualizations/eval_cross_page/
visualizations/eval_option_image/
```

围绕训练集，可准备：

```text
train_dataset_manifest.csv
train_source_license_report.md
augmentation_config.yaml
train_dataset_statistics_report.md
```

---

## 17. 最终执行建议

建议按以下顺序推进：

```text
1. 先确定评估集来源与授权。
2. 先采 100 页 pilot eval-like 数据，验证标注规范。
3. 固化评估集 label schema。
4. 扩展到 1000 页真实评估集。
5. 对评估集做 100% 自动质检和高风险人工复核。
6. 评估集锁定，不再参与训练和规则开发。
7. 训练集再根据需要从自采、公开数据、增强数据中补充。
8. 输出评估集统计报告和可视化报告。
```

最核心的一句话：

```text
评估集必须真实、独立、多样、难度合理、标注可靠；训练集可以更灵活，但必须说明来源、隔离评估集，并保留标注与统计文档。
```

