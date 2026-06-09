# 标注工作台交互规范

版本：v0.4  
日期：2026-05-26  
参考：

```text
doc/开发文档/前端/frontend_development_spec.md
doc/开发文档/k12_annotation_platform_design.md
doc/开发文档/后端/k12_annotation_platform_backend_design.md
E:\code\python\PPOCRLabel/README.md
E:\code\python\PPOCRLabel/libs/canvas.py
```

## 目录

- 版本记录
- 1. 目标与边界
- 2. PPOCRLabel 参考边界
- 3. MVP 交互范围
- 4. 工作台布局
- 5. 工具模式
- 6. 坐标系统
- 7. 画布浏览
- 8. bbox 标注
- 9. 对象选择与编辑
- 10. 撤销、重做、复制和 read_order
- 11. 标签与属性
- 12. 保存、revision 与冲突
- 13. QC 展示与定位
- 14. 只读、锁定与 capabilities 状态
- 15. 快捷键
- 16. 验收标准
- 17. 关键结论

---

## 版本记录

| 版本 | 日期 | 说明 |
|---|---|---|
| v0.1 | 2026-05-26 | 初版标注工作台交互规范，定义 MVP bbox 创建、选择、拖拽、缩放、保存、冲突处理和 QC 定位规则。 |
| v0.2 | 2026-05-26 | 参考 PPOCRLabel 补充快捷键、工具模式、撤销重做、复制、排序和浏览器快捷键冲突规则。 |
| v0.3 | 2026-05-26 | 补充自动保存交互策略，明确自动保存与 revision、冲突、只读、离页提示和浏览器本地存储的边界。 |
| v0.4 | 2026-05-26 | 根据三次 review 修正：补自动保存 revision 成本控制，read_order 纳入 MVP，接入 capabilities，调整 Ctrl+C 语义，移除 PPOCRLabel 本机绝对路径。 |
| v0.5 | 2026-06-09 | 更新画布渲染架构为固定视口 Canvas 矩阵渲染，补充页面缩略图导航列和翻页快捷键规范。 |

---

## 1. 目标与边界

本文定义前端标注工作台的交互规则，重点约束页面图片上的 bbox 标注、对象选择、对象编辑、read_order、坐标换算、快捷键、手动保存、自动保存、capabilities 映射、revision 冲突处理和 QC 错误定位。

快捷键属于本文职责范围，因为它直接影响标注效率、用户动作含义、readonly 限制和冲突处理。本文只定义“用户按什么键应触发什么交互”和“什么状态下不能触发”，不定义具体 keydown 监听代码、组件拆分、事件总线或 Vue 实现细节；这些属于 `frontend_development_spec.md` 和后续组件规范。

自动保存属于本文职责范围，因为它直接影响 dirty、autosave_pending、autosaving、manual_saving、conflict、readonly、离开页面提示和 revision 链路。本文只定义自动保存何时允许、何时禁止、用户应看到什么状态，不定义具体定时器、请求封装、状态管理库或重试算法。

本文不维护完整产品流程、完整 API 清单、完整视觉设计系统、完整权限模型、多人实时协作、复杂 polygon 编辑或具体前端代码实现。权限事实来源以后端 capabilities 为准，本文只定义工作台如何消费 capabilities 并进入 readonly / disabled / conflict 等交互状态。

---

## 2. PPOCRLabel 参考边界

PPOCRLabel 是本项目标注工作台的重要交互参考，但不能直接照搬。它是 Qt 桌面应用，本项目是 Web 前端，并且后端采用 revision、权限、锁定和 QC 工作流。

可参考：

```text
1. 快捷键驱动高频操作。
2. W 创建矩形框。
3. Q / Home 创建多点框。
4. A / D 切换上一张和下一张。
5. Delete / Backspace 删除选中框。
6. Ctrl + Z 撤销。
7. Ctrl + C 复制选中框到内部 clipboard，不直接创建新对象。
8. Ctrl + G 聚焦缩放到选中框。
9. Ctrl + B 对框按空间位置生成排序建议。
10. Ctrl + 鼠标左键多选。
11. 方向键微调选中框。
12. Z / X / C / V / B 选择四点框顶点并用方向键移动。
13. Ctrl + 鼠标滚轮缩放。
```

不直接照搬：

```text
1. Ctrl + V 在 PPOCRLabel 中用于确认图片；Web 中 Ctrl + V 是粘贴，本文不占用。
2. Ctrl + R / Ctrl + Shift + R 在浏览器中接近刷新语义，本文不用于 OCR 重识别。
3. Ctrl + A 在浏览器中是全选，本文不用于显示全部框。
4. 删除图片、重识别全部框、模型调用等不属于 MVP 标注画布交互。
5. PPOCRLabel 的文件状态、Label.txt、Cache.cach 和本地自动导出机制不适用于本项目 revision 架构。
```

适配原则：

```text
1. 优先保留标注员熟悉的高频键：W、A、D、Delete、Ctrl+Z、Ctrl+C、Ctrl+G、方向键。
2. 避免覆盖浏览器和文本编辑器的关键默认行为。
3. 快捷键只在工作台或画布焦点范围内生效。
4. 输入框、文本域、下拉框、富文本区域聚焦时不触发画布快捷键。
5. 任何快捷键都不能绕过 readonly、locked、capabilities 和 revision conflict 限制。
6. Ctrl + C 只表示复制到内部 clipboard；创建偏移副本使用 Ctrl + D 或工具栏按钮。
```

---

## 3. MVP 交互范围

MVP 必须支持：

```text
1. 加载 page image 和 latest annotation revision。
2. 显示 raw candidate、manual annotation、selected object、QC issue 四类 overlay。
3. 画布缩放和平移。
4. 创建 bbox。
5. 选择 bbox。
6. 拖拽移动 bbox。
7. 拖拽控制点调整 bbox 尺寸。
8. 方向键微调 bbox。
9. 撤销和重做本地草稿编辑。
10. 复制选中 bbox 到内部 clipboard，并支持显式创建偏移副本。
11. 轻量人工 read_order 编辑。
12. 给对象设置 label 和基础 attributes。
13. 手动保存整页 annotation revision。
14. 自动保存有效草稿，防止长时间编辑丢失。
15. 处理 409 revision 冲突。
16. 从 QC issue 定位到对应对象或区域。
```

MVP 暂不实现：

```text
1. 人工绘制任意 polygon。
2. 人工调整倾斜 quad。
3. 多对象批量几何变换。
4. 多人实时协同编辑。
5. revision 可视化 diff。
6. 复杂关系连线编辑器。
7. 跨页题专用工作台。
8. OCR 重识别快捷键。
```

---

## 4. 工作台布局

推荐五区布局：

```text
最左侧：页面缩略图列表（PPT 风格，点击切换，当前页高亮）
左侧：标签选择面板
中间：试卷页面画布（固定视口 Canvas + SVG overlay）
右侧：对象属性 / QC 问题
底部：工具栏 / revision 状态 / 保存状态
```

页面导航：

```text
1. 最左侧面板显示同项目所有页面缩略图，点击切换当前页面。
2. 工具栏显示上一张/下一张按钮和页码指示器（如 "3 / 20"）。
3. 快捷键 A 切换到上一张，D 切换到下一张。
4. 首张时禁用上一张，末张时禁用下一张。
5. 页面切换时保留旧页面内容直到新页面加载完成，避免全屏闪烁。
6. 页面列表和缩略图在后台异步加载，不阻塞主工作台渲染。
```

约束：

```text
1. 中间画布始终是主操作区域。
2. 左侧和右侧面板可以折叠，但不能遮挡当前选中对象。
3. 保存状态必须常驻可见，至少区分 saved、dirty、autosave_pending、autosaving、autosave_failed、manual_saving、conflict、readonly。
4. 当前 page_id、revision_no、base_revision_id 应能在调试信息或状态区查看。
5. 工具栏必须显示当前工具模式、缩放比例和只读原因。
```

---

## 5. 工具模式

工作台至少包含以下工具模式：

```text
select
  选择、移动、调整已有对象。

bbox
  创建矩形 bbox。

read_order
  按阅读顺序点击 bbox，写入或修正当前页 read_order。

pan
  平移画布。通常为临时模式，由 Space + drag 或中键拖拽触发。
```

后续预留：

```text
quad
  四点框编辑。

polygon
  多点轮廓编辑。

relation
  关系连线编辑。
```

模式切换规则：

```text
1. W 切换到 bbox 模式。
2. V 切换到 select 模式。
3. R 切换到 read_order 模式。
4. Space 按下时临时进入 pan，松开后回到原模式。
5. Esc 取消当前绘制或回到 select。
6. readonly 状态下只能使用 select 和 pan。
7. read_order 模式必须依赖 can_create_annotation_revision 或等价写入 capability。
```

---

## 6. 坐标系统

前端必须同时维护三套坐标：

```text
image coordinate
  原始页面图像坐标，单位为像素。annotation JSON 中的 bbox_xyxy、quad、polygon 均使用该坐标。

viewport coordinate
  Canvas 逻辑坐标系，固定尺寸（如 800×600），与 CSS 像素 1:1 映射。SVG overlay 的 viewBox 与此一致。

screen coordinate
  鼠标事件相对于 Canvas 元素左上角的 CSS 像素偏移。
```

坐标转换（由 `useCanvasRenderer` 管理）：

```text
screenToImage(sx, sy)    screen → image：imgX = (sx - offsetX) / scale
imageToViewport(ix, iy)  image → viewport：vpX = ix * scale + offsetX
```

其中 scale 和 offsetX/Y 由图片适配到固定视口时计算，随缩放/平移变化。

要求：

```text
1. 保存到后端的所有几何字段必须是 image coordinate。
2. 鼠标事件得到的 screen coordinate 必须先转换为 image coordinate 后再存储。
3. 缩放和平移只影响显示，不改变 annotation JSON 中的原始坐标。
4. SVG overlay 中的标注坐标使用 imageToViewport() 从 image coordinate 转换而来。
5. 所有坐标写入前必须 clamp 到图像边界内。
6. 坐标转换必须有单元测试覆盖缩放、平移、边界和反向转换。
```

bbox 规则：

```text
bbox_xyxy = [xmin, ymin, xmax, ymax]
xmin < xmax
ymin < ymax
坐标为 number，保存前可按后端要求四舍五入为整数像素。
```

quad / polygon 规则：

```text
1. MVP 中 quad 和 polygon 可由 bbox 自动生成。
2. 自动生成的 quad / polygon 必须标记来源为 auto_generated。
3. 后续人工编辑 quad / polygon 时，不得再静默覆盖为 bbox 派生结果。
```

---

## 7. 画布浏览

画布采用固定视口架构（`useCanvasRenderer`），Canvas 物理/CSS 尺寸锁定为 800×600，不因图片分辨率改变。图片通过矩阵变换等比缩放并居中显示在固定视口内。

缩放：

```text
1. Ctrl + 鼠标滚轮缩放。
2. 支持工具栏按钮缩放：放大、缩小、适配宽度、适配整页、100%。
3. 缩放中心优先使用鼠标位置；工具栏缩放以画布中心为中心。
4. 缩放比例必须有上下限（MIN_SCALE=0.05, MAX_SCALE=20），避免图片消失或过度放大。
5. 缩放比例必须显示给用户。
6. 缩放使用锚点缩放算法：保持鼠标下图片点不变，公式为 offsetX = cx - imgX * newScale。
```

平移：

```text
1. Space + drag 进入临时平移。
2. 中键拖拽可以平移。
3. 非绘制模式下拖拽空白区域可以平移。
4. 平移不得改变 annotation 坐标。
```

聚焦：

```text
1. Ctrl + G 聚焦并缩放到当前选中对象。
2. 从 QC issue 定位时复用同一套聚焦行为。
3. 聚焦不得修改对象选区之外的草稿内容。
```

加载状态：

```text
1. 图片未加载完成时禁用标注操作。
2. 图片加载失败时显示错误、request_id 和重试入口。
3. 画布不允许无提示空白。
```

---

## 8. bbox 标注

创建流程：

```text
1. 用户按 W 或点击 bbox 工具。
2. 在画布按下鼠标左键，记录起点 image coordinate。
3. 拖拽时显示 preview bbox。
4. 松开鼠标后生成 bbox_xyxy。
5. bbox 面积低于最小阈值时丢弃，并提示用户。
6. 自动生成矩形 quad 和 polygon。
7. 新对象进入 selected 状态，并打开右侧属性面板。
8. 新对象创建后 draft 状态变为 dirty。
```

默认对象字段：

```text
id
  前端生成临时 id，保存后以后端返回或 revision 内容为准。

label
  默认使用当前选中的标签；无标签时要求用户选择后才能保存。

geometry.bbox_xyxy
  用户绘制结果。

geometry.quad
  由 bbox 自动生成四点。

geometry.polygon
  由 bbox 自动生成四点 polygon。

geometry_source
  bbox 标记为 bbox_manual，quad / polygon 标记为 auto_generated。
```

创建限制：

```text
1. readonly、locked、conflict、manual_saving 状态禁止新建对象。
2. 图片未加载完成禁止新建对象。
3. 当前没有可用 label_registry 时允许绘制草稿，但保存前必须补齐 label。
4. 当前用户缺少 can_create_annotation_revision 或等价 capability 时禁止新建对象。
```

---

## 9. 对象选择与编辑

选择：

```text
1. 单击对象边框或填充区域选中对象。
2. 点击空白区域取消选择。
3. 对象重叠时优先选择视觉层级最高或面积最小的对象。
4. 右侧对象列表点击也应同步选中画布对象。
5. Ctrl + 鼠标左键多选作为增强能力；MVP 可先只支持单选。
```

移动：

```text
1. 选中对象后拖拽主体可移动 bbox。
2. 移动时保持 bbox 宽高不变。
3. 移动结果必须 clamp 到图像边界内。
4. 移动完成后标记 draft dirty。
```

微调：

```text
1. 方向键每次移动选中 bbox 1px。
2. Shift + 方向键每次移动 10px。
3. 微调单位使用 image coordinate。
4. 微调不能让对象越界。
```

调整尺寸：

```text
1. 选中对象显示 8 个控制点。
2. 拖拽控制点调整 bbox。
3. 反向拖拽越过对边时，仍需保证 xmin < xmax、ymin < ymax。
4. 调整完成后重新生成矩形 quad 和 polygon，并标记 auto_generated。
```

删除：

```text
1. Delete 或 Backspace 删除当前选中对象。
2. 删除前如果对象有关联关系，应提示会同步删除或要求先解除关系。
3. 删除只是更新当前 draft，直到保存 revision 后才成为后端事实。
```

四点精修预留：

```text
1. PPOCRLabel 使用 Z / X / C / V 选择四个顶点，B 回到整体移动。
2. 本项目 MVP 不开放人工 quad 顶点编辑。
3. 后续开放 quad 工具时，可复用 Z / X / C / V / B 作为顶点精修快捷键。
```

---

## 10. 撤销、重做、复制和 read_order

撤销 / 重做：

```text
1. Ctrl + Z 撤销上一次本地草稿编辑。
2. Ctrl + Y 或 Ctrl + Shift + Z 重做。
3. 撤销栈只记录当前 page_id 和 base_revision_id 下的本地草稿编辑。
4. 保存成功后可以保留撤销栈，但不得撤回到另一个 base_revision_id。
5. 重新加载 latest、切换页面或处理冲突时，应明确清理或隔离撤销栈。
```

复制：

```text
1. Ctrl + C 在画布焦点且有选中对象时，只复制到工作台内部 clipboard，不修改 draft。
2. 如果页面中存在文本选区或输入控件聚焦，不拦截 Ctrl + C。
3. Ctrl + C 不生成新 id，不改变选中对象，不标记 dirty。
4. Ctrl + D 或工具栏“复制并偏移”按钮才创建偏移后的新 bbox。
5. 创建偏移副本时必须生成新 id。
6. 偏移副本保留 label 和 attributes，但 history/source 标记为 copied_from。
7. 偏移副本创建后进入 selected 状态，并标记 draft dirty。
8. Ctrl + D 只在画布焦点、无文本选区、非 readonly 且具备写入 capability 时拦截浏览器默认行为。
```

read_order 人工排序：

```text
1. read_order 模式纳入 MVP。
2. 用户按阅读顺序点击 bbox，系统依次写入 read_order=1..N。
3. read_order badge 显示在 bbox 中心或上方，缩放时保持可读，但不得遮挡主要试卷文字。
4. 用户可以在 read_order badge 或右侧属性面板中直接修改序号。
5. 支持撤销、清空当前页排序、重新从 1 开始排序。
6. read_order 修改只更新当前 draft，并随整页 annotation revision 一起保存。
7. MVP 不需要单独 read_order API。
8. readonly、locked、conflict 或缺少 can_create_annotation_revision 时禁止 read_order 编辑。
```

自动排序建议：

```text
1. Ctrl + B 只触发 bbox/read_order 自动排序建议入口。
2. 自动排序按从上到下、从左到右生成建议顺序。
3. 自动排序建议必须经用户确认后才写入 draft，不能直接作为 gold truth。
4. 如果 read_order 已有人工作业，覆盖前必须二次确认。
5. 排序建议写入 draft 后必须可撤销。
6. 建议写入后应标记 read_order_source=auto_suggested 或等价来源；人工点击排序标记为 manual。
7. 导出前 QC 必须检查缺失、重复、非连续和非导出对象混入排序的问题。
```

---

## 11. 标签与属性

标签：

```text
1. 标签来自后端 label_registry，不在前端写死。
2. 新建对象必须有 label 才能保存。
3. 标签颜色用于画布识别，但不能作为唯一状态表达。
4. 未知标签显示为 unknown，并阻止保存或提示重新选择。
5. Ctrl + E 聚焦右侧标签/属性编辑区域。
```

属性：

```text
1. 属性表单由 label 的 attributes_schema 决定。
2. 前端可以做基础必填和格式校验。
3. 最终 schema 校验以后端为准。
4. 属性错误应定位到右侧表单字段和对应画布对象。
```

---

## 12. 保存、revision 与冲突

保存：

```text
1. Ctrl + S 或保存按钮保存当前 draft。
2. 保存按钮只在 dirty、具备 can_create_annotation_revision、非 readonly、非 manual_saving 状态可用。
3. 保存整页 annotation JSON 时必须携带 base_revision_id。
4. 手动保存过程中状态为 manual_saving，禁用重复手动保存。
5. 保存成功后状态为 saved，并更新 revision_id、revision_no、base_revision_id。
6. 保存失败不得清空本地 draft。
```

保存状态：

```text
saved
  当前 draft 与已确认 revision 一致。

dirty
  当前 draft 有本地修改，尚未保存。

autosave_pending
  已安排自动保存，但尚未发送请求。

autosaving
  自动保存请求进行中。

autosave_failed
  自动保存失败，是 dirty 的带错误子状态，必须保留手动保存入口。

manual_saving
  用户触发的手动保存进行中。

conflict
  后端返回 revision conflict，必须由用户显式处理。

readonly
  由于锁定、权限、历史 revision 或 conflict 等原因不可写。
```

状态流转约束：

```text
1. 常规自动保存流转为 saved -> dirty -> autosave_pending -> autosaving -> saved。
2. manual_saving 独立于 autosaving，不能用一个 saving 状态混淆。
3. autosaving 不应阻断用户继续选择、缩放、查看和编辑当前 draft；新增编辑应合并为下一次 autosave_pending。
4. 同一 page 同时最多允许一个 pending autosave 和一个 in-flight autosave。
5. 手动保存优先级高于自动保存；用户触发 Ctrl + S 后必须清理或合并已排队的 autosave。
6. autosave_failed 不能简化显示为普通 dirty；手动保存成功必须清除 autosave_failed。
```

自动保存：

```text
1. MVP 应支持自动保存有效 draft，防止长时间标注后因页面关闭、网络波动或误操作导致丢失。
2. 自动保存与手动保存使用同一套 revision 并发控制，必须携带 base_revision_id。
3. 自动保存成功后同样更新 revision_id、revision_no、base_revision_id，并将状态置为 saved。
4. 自动保存请求应能在审计信息中区分 trigger=autosave 或等价来源，具体字段由 API 文档定义。
5. 自动保存不等于提交复核、确认图片或锁定 revision，不改变 submitted、reviewed、locked 等流程状态。
6. 自动保存不得静默覆盖 latest revision。
7. 自动保存 revision 在 revision 列表中默认折叠，只在用户展开历史或调试信息时显示。
8. 自动保存不触发完整 QC；完整 QC 只由手动保存后的流程或用户显式运行 QC 触发。
```

触发策略：

```text
1. draft 从 saved 变为 dirty 后，应在用户停止绘制、拖拽、缩放控制点、标签编辑等写操作后再触发自动保存。
2. 正在绘制新框、拖拽对象、调整控制点、输入中文组合字符或编辑表单字段时，不应立即触发自动保存。
3. 手动 Ctrl + S 或保存按钮应立即保存，并清理已排队的自动保存。
4. 切换页面、离开工作台或关闭浏览器标签页时，如存在 dirty draft，应优先提示用户；是否尝试自动保存取决于当前网络和后端能力，不能依赖异步请求必然完成。
5. 自动保存 debounce 默认 5 秒，最低不得低于 3 秒。
6. 同一 page 自动保存创建正式 revision 的最小间隔默认 60 秒，最低不得低于 30 秒。
7. 间隔内产生的多次修改必须合并，不得为每次拖拽、控制点调整或属性输入创建 revision。
8. autosave in-flight 期间产生的新修改只设置下一次 autosave_pending，不追加多个队列项。
```

禁止自动保存：

```text
1. readonly、locked、conflict、manual_saving、capabilities 加载失败或缺少写入 capability 状态。
2. 当前 draft 未通过最小保存校验，例如新建对象缺少必填 label。
3. 当前 base_revision_id 已知不是 latest。
4. 后端返回 409 conflict 后，直到用户完成冲突处理。
5. 网络离线或鉴权失效时，禁止继续排队无限重试。
6. 当前用户缺少 can_create_annotation_revision 或等价写入 capability。
```

自动保存失败：

```text
1. 自动保存失败不得清空本地 draft，也不得把状态显示为 saved。
2. 失败后状态必须显示为 autosave_failed，并保留手动保存入口。
3. 如果失败原因是 409 conflict，按本文 409 冲突规则处理。
4. 如果失败原因是校验错误，应定位到对象或属性字段，并暂停自动保存直到用户修正。
5. 自动保存失败提示应克制，避免每次重试都弹出阻断式对话框。
6. 自动保存失败后不得无限重试；应等待用户继续编辑、手动保存或网络状态恢复后再进入 autosave_pending。
```

本地持久化边界：

```text
1. MVP 自动保存以服务端 revision 为准，不使用 localStorage 保存完整 annotation JSON、原始试卷内容或敏感数据。
2. 如后续需要离线草稿或浏览器本地恢复，必须单独设计安全边界、过期策略、加密策略和清理机制。
3. sessionStorage 仅可保存低敏 UI 状态，例如面板折叠、当前 tab、缩放比例，不作为标注事实来源。
```

提交 / 确认：

```text
1. PPOCRLabel 使用 Ctrl + V / End 确认图片；Web 中不占用 Ctrl + V。
2. 如果后续需要“提交复核”或“标记完成”，建议使用 Ctrl + Enter，并要求二次确认。
3. 提交流程属于复核工作流，具体规则以后端设计和产品流程为准。
```

409 冲突：

```text
1. 后端返回 revision conflict 时，前端状态进入 conflict。
2. 不允许自动覆盖 latest revision。
3. 用户至少可以选择：重新加载 latest、保留本地草稿另存为新 revision、取消处理。
4. 如果后端不支持自动合并，前端不得伪造合并成功。
5. conflict 状态下禁止继续编辑几何对象，直到用户作出选择。
```

离开页面：

```text
1. dirty 状态离开页面必须二次确认。
2. manual_saving 或 autosaving 状态离开页面必须提示保存未完成或仍在后台保存。
3. conflict 状态离开页面必须提示本地修改可能丢失。
4. saved 或 readonly 状态可以直接离开。
```

---

## 13. QC 展示与定位

QC 问题来源以后端 QC 结果为准。

展示要求：

```text
1. 右侧 QC 面板按 severity 分组。
2. 每条 QC issue 显示类型、说明、关联对象、可修复建议。
3. 点击 QC issue 时定位到对象或区域。
4. 画布中 QC error 使用独立视觉层，不覆盖原标签颜色。
5. 无 QC 问题时显示明确空态。
```

定位规则：

```text
1. issue 有 ann_id 时选中对应对象。
2. issue 有 bbox 或 polygon 时缩放到问题区域。
3. issue 是页面级错误时显示页面级提示，不强行选中对象。
4. 已删除对象关联的历史 issue 应显示为 stale 或等待重新 QC。
5. Ctrl + G 可对当前 QC 定位对象执行同样的聚焦缩放。
```

---

## 14. 只读、锁定与 capabilities 状态

capabilities 来源：

```text
1. 工作台加载 page 时必须同时加载当前 project 的 capabilities。
2. capabilities 的 API 以后端 OpenAPI 为准，推荐来源为 `/api/v1/projects/{project_id}/me/capabilities`。
3. 前端不根据 role_key 自行推断安全权限，role_key 只用于展示。
4. 同一用户在不同 project 中 capabilities 可能不同，切换 project 或收到 403 后必须重新加载。
5. capabilities 缺失、加载失败或过期时，工作台默认进入 readonly，并显示原因。
```

capability 映射：

```text
can_create_annotation_revision
  允许创建 bbox、移动、调整、删除、Ctrl+D 偏移复制、read_order 编辑、手动保存和自动保存。

can_review_revision
  允许进入复核入口、提交 review decision 或查看 reviewer 操作面板。

can_lock_revision
  允许显示锁定入口并发起锁定操作。

can_unlock_revision
  允许显示解锁入口并发起解锁操作。

can_create_export_job
  允许从工作台进入导出任务创建入口。工作台不能通过 role_key 自行判断导出权限。
```

capabilities 交互规则：

```text
1. 工具栏按钮、上下文菜单、批量操作、保存按钮和快捷键写操作必须统一读取 capabilities。
2. 缺少 capability 的入口优先 disabled 并显示原因；如果入口涉及敏感资源，可以隐藏。
3. 收到 403 后必须刷新 capabilities，并把当前写操作失败原因展示到状态栏或 inline alert。
4. 快捷键触发写操作前必须重新检查当前 capabilities、locked、conflict、manual_saving 和 autosaving 状态。
5. capabilities 只能优化前端体验，最终权限以后端写接口校验为准。
```

只读来源：

```text
1. locked page。
2. locked revision。
3. 用户缺少 can_create_annotation_revision 或等价写入 capability。
4. 当前 revision 不是 latest 且不允许基于历史直接编辑。
5. revision conflict 尚未处理。
6. capabilities 加载失败或收到 403 后尚未重新确认权限。
```

只读行为：

```text
1. 允许缩放、平移、选择对象、查看属性、查看 QC。
2. 禁止创建、移动、调整、删除、Ctrl+D 生成副本、read_order 编辑和自动排序写入。
3. 禁止手动保存和自动保存 revision。
4. 需要显示只读原因。
5. 快捷键仍可用于浏览和聚焦，但不能触发写操作。
6. Ctrl + C 只复制到内部 clipboard 或复制可见文本，不得生成新对象。
```

---

## 15. 快捷键

### 15.1 MVP 快捷键表

| 快捷键 | 行为 | 状态限制 |
|---|---|---|
| `V` | 选择工具 | 画布或工作台焦点 |
| `W` | bbox 工具 | 具备 can_create_annotation_revision，非 readonly、非 locked、非 conflict |
| `R` | read_order 工具 | 具备 can_create_annotation_revision，非 readonly、非 locked、非 conflict |
| `Space + drag` | 临时平移 | 图片已加载 |
| `Ctrl + Wheel` | 缩放 | 图片已加载 |
| `Ctrl + +` | 放大 | 图片已加载 |
| `Ctrl + -` | 缩小 | 图片已加载 |
| `Ctrl + 0` | 100% | 图片已加载 |
| `F` | 适配整页 | 图片已加载 |
| `Shift + F` | 适配宽度 | 图片已加载 |
| `Ctrl + G` | 聚焦缩放到选中对象或 QC 定位对象 | 有目标对象或目标区域 |
| `Arrow` | 选中 bbox 微调 1px | 非 readonly 且有选中对象 |
| `Shift + Arrow` | 选中 bbox 微调 10px | 非 readonly 且有选中对象 |
| `Delete / Backspace` | 删除选中对象 | 非 readonly 且有选中对象 |
| `Ctrl + Z` | 撤销 | 有本地撤销记录 |
| `Ctrl + Y` / `Ctrl + Shift + Z` | 重做 | 有本地重做记录 |
| `Ctrl + C` | 复制选中对象到内部 clipboard | 画布焦点、无文本选区、有选中对象 |
| `Ctrl + D` | 复制并偏移生成新对象 | 画布焦点、无文本选区、具备 can_create_annotation_revision、非 readonly |
| `Ctrl + B` | 生成 bbox/read_order 排序建议 | 具备 can_create_annotation_revision、非 readonly、有多个对象；写入前需确认 |
| `Ctrl + E` | 聚焦标签/属性编辑 | 有选中对象 |
| `Ctrl + S` | 手动保存当前 draft | dirty、具备 can_create_annotation_revision、非 readonly、非 manual_saving |
| `Esc` | 取消绘制、取消选择或关闭轻量浮层 | 按当前上下文处理 |
| `A` | 上一张图片 | 非输入焦点；dirty、manual_saving、autosaving 或 autosave_failed 时先确认 |
| `D` | 下一张图片 | 非输入焦点；dirty、manual_saving、autosaving 或 autosave_failed 时先确认 |

### 15.2 预留快捷键

| 快捷键 | 预留行为 | 启用条件 |
|---|---|---|
| `Q` / `Home` | quad / polygon 工具 | 后续开放多点框时启用 |
| `Z` / `X` / `C` / `V` | 选择第 1/2/3/4 个顶点 | 后续开放 quad 顶点编辑时启用 |
| `B` | 回到整体移动 | 后续开放顶点编辑时启用；注意与 bbox 工具键 W 区分 |
| `Ctrl + Left Click` | 多选对象 | 后续开放批量操作时启用 |
| `Ctrl + Enter` | 提交复核或标记完成 | 后续复核工作流确定后启用 |

### 15.3 快捷键冲突规则

```text
1. 输入框、文本域、下拉框、富文本、contenteditable 聚焦时，不触发画布快捷键。
2. 存在浏览器文本选区时，不拦截 Ctrl + C。
3. 不使用 Ctrl + V 作为确认、保存或提交快捷键。
4. 不使用 Ctrl + R 或 Ctrl + Shift + R 作为重识别快捷键。
5. 不使用 Ctrl + A 控制画布显示。
6. Ctrl + S 只在工作台焦点内拦截浏览器保存网页行为。
7. Ctrl + D 只在画布焦点内拦截浏览器添加书签行为，并必须有可点击 UI 入口。
8. 所有写操作快捷键必须经过 capabilities、锁定、conflict、manual_saving、autosaving 状态检查。
9. 每个快捷键必须有可点击 UI 入口，不能只依赖键盘。
```

---

## 16. 验收标准

MVP 标注工作台可按以下标准验收：

```text
1. 能加载一张 page image 和 latest annotation。
2. 能缩放、平移并保持坐标稳定。
3. 能创建 bbox，并保存为 image coordinate。
4. 创建 bbox 后能自动生成矩形 quad 和 polygon。
5. 能选择、移动、调整、微调、复制到内部 clipboard、Ctrl+D 生成偏移副本和删除 bbox。
6. Ctrl + Z / Ctrl + Y 能在当前页本地草稿内撤销和重做。
7. saved、dirty、autosave_pending、autosaving、autosave_failed、manual_saving、conflict、readonly 状态可见。
8. 手动保存和自动保存都携带 base_revision_id。
9. 自动保存 debounce、同页最小 revision 间隔、单 pending 队列和 autosave revision 折叠策略明确生效。
10. 自动保存不会在绘制、拖拽、readonly、manual_saving、conflict、缺少 capability 或校验失败状态下触发。
11. autosave 不触发完整 QC，手动保存或显式 QC 才进入完整 QC 流程。
12. read_order 模式能按点击顺序写入 1..N，显示序号 badge，支持撤销、清空和重新排序。
13. Ctrl + B 只生成排序建议，经确认后才写入 draft。
14. 409 冲突不会自动覆盖 latest revision。
15. locked 或无权限状态下无法通过鼠标或快捷键编辑。
16. 工作台按钮、菜单、保存、自动保存和快捷键写操作均基于后端 capabilities 判断。
17. QC issue 能在右侧列表显示，并能定位到对象或区域。
18. 导出前 QC 能检查 read_order 缺失、重复、非连续和非导出对象混入。
19. 输入框聚焦时，不触发画布快捷键。
20. 浏览器 localStorage 不保存完整 annotation JSON、原始试卷内容或敏感数据。
```

---

## 17. 关键结论

MVP 标注工作台以稳定的 bbox 标注闭环和轻量 read_order 人工排序为核心，可以吸收 PPOCRLabel 的高频快捷键经验，但不能照搬其桌面端文件状态、自动导出和浏览器冲突快捷键。

所有保存到后端的几何数据必须使用 image coordinate。缩放和平移只是显示变换，不能污染 annotation JSON。

revision 冲突必须显式处理，不允许前端自动覆盖后端 latest revision。

read_order 是 MVP 标注事实的一部分，随整页 annotation revision 保存。自动排序只能作为建议，人工确认后才写入 draft，导出前必须经过缺失、重复和连续性 QC。

自动保存是防丢失机制，不是提交复核机制。它必须服从 revision、capabilities、锁定、校验和冲突规则，必须控制 revision 成本，并且不能依赖浏览器本地存储作为标注事实来源。

快捷键是交互规范的一部分，但实现细节不是本文职责。实现时必须保证快捷键不会绕过 capabilities、锁定、只读、manual_saving、autosaving 和冲突状态。
