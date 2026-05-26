# annotation_workspace_interaction_spec.md 三次 Review

日期：2026-05-26  
被 review 文档：`doc/开发文档/前端/annotation_workspace_interaction_spec.md`  
Review 目标：重新判断标注工作台交互规范是否符合当前平台目标、后端 revision 模型、前端开发规范、角色 / capabilities 设计和 MVP 实施计划。

## 目录

- 1. 总体结论
- 2. 已解决的问题
- 3. 主要问题
- 4. 次要问题
- 5. 符合项目目标的部分
- 6. 建议修改顺序

---

## 1. 总体结论

该文档整体方向仍然符合项目目标：MVP 聚焦 bbox 标注闭环，明确 image coordinate 与 viewport coordinate 的边界，尊重后端 revision 模型，不允许 409 冲突自动覆盖 latest revision，也没有照搬 PPOCRLabel 的桌面端文件状态。

但在进入前端编码前，仍建议修正以下问题：

```text
1. 自动保存被放入 MVP，但缺少 revision 成本控制和状态拆分策略。
2. read_order 应进入 MVP，但需要明确专用人工排序模式、保存语义和 QC 边界。
3. 仍引用本机 PPOCRLabel 绝对路径。
4. Ctrl+C 被定义为“复制并粘贴偏移框”，容易产生误操作。
5. 工作台交互没有对接最新的 roles / capabilities 设计。
```

---

## 2. 已解决的问题

### 2.1 文档版本号已一致

当前文档头部为：

```text
版本：v0.3
```

版本记录也包含 `v0.3`。之前“头部版本 v0.2、版本记录已有 v0.3”的问题已经解决。

---

## 3. 主要问题

### 3.1 自动保存进入 MVP，但缺少 revision 成本控制

位置：

```text
doc/开发文档/前端/annotation_workspace_interaction_spec.md:465
doc/开发文档/前端/annotation_workspace_interaction_spec.md:466
doc/开发文档/前端/annotation_workspace_interaction_spec.md:467
doc/开发文档/前端/annotation_workspace_interaction_spec.md:480
doc/开发文档/后端/k12_annotation_platform_backend_design.md:1488
doc/开发文档/后端/k12_annotation_platform_backend_design.md:1489
```

问题：

```text
文档要求 MVP 自动保存有效 draft，并且自动保存和手动保存使用同一套 revision 并发控制。
后端设计中每次保存都会创建新的 annotation revision。
如果用户持续拖拽、调整、改标签，自动保存可能产生大量不可变 revision、manifest、审计记录和索引重建任务。
文档虽然要求“节流或合并”，但没有给出最低策略，例如 debounce 时间、最小间隔、最大 pending 队列、是否触发 QC、是否在 revision 列表中折叠 autosave revision。
```

影响：

```text
1. 大体量数据标注时 revision 数量可能快速膨胀。
2. 自动保存失败和 409 conflict 会变得频繁。
3. 后端 annotation_objects 重建和 QC 触发成本上升。
4. 审计日志会混入大量低价值 autosave 记录。
5. 如果 autosave 与手动保存共用 saving 状态，可能频繁阻断继续标注。
```

建议：

```text
保留自动保存，但必须补充硬性策略：
1. 自动保存 debounce 不低于 3-5 秒。
2. 同一 page 至少间隔 30-60 秒才创建一次正式 revision。
3. 拖拽、控制点调整、中文输入组合期间不保存。
4. pending autosave 同时只能有一个。
5. autosave 不触发完整 QC，除非用户手动保存或显式运行 QC。
6. autosave revision 使用 trigger=autosave 标记，并在 revision 列表中默认折叠。
7. 区分 manual_saving 与 autosaving，避免后台自动保存阻断继续标注。
```

严重级别：高

### 3.2 read_order 应进入 MVP，但原文交互定义还不够明确

位置：

```text
doc/开发文档/前端/annotation_workspace_interaction_spec.md:191
doc/开发文档/前端/annotation_workspace_interaction_spec.md:417
doc/开发文档/前端/annotation_workspace_interaction_spec.md:420
doc/开发文档/前端/annotation_workspace_interaction_spec.md:612
doc/开发文档/前端/frontend_development_spec.md:1208
doc/开发文档/mvp_implementation_plan.md:429
```

问题：

```text
PP-DocLayoutV3 训练数据需要可靠的阅读顺序。对 K12 试卷、多栏排版、图文混排和题块跨区域场景来说，完全依赖自动规则生成 read_order 容易产生错误。
交互规范第 5 节仍把 read_order 标为后续预留，但第 10 节又定义 Ctrl+B 触发 bbox/read_order 排序建议，快捷键表也把 Ctrl+B 放进 MVP 快捷键。
这说明文档已经意识到 read_order 的价值，但没有把它明确成 MVP 的人工标注能力。
考虑到已有 PaddleOCR-VL 预标注和 bbox 基础，轻量人工 read_order 模式的实现复杂度可控，不应推迟到复杂工作台阶段。
```

建议：

```text
建议将 read_order 轻量人工标注纳入 MVP：
1. 将 read_order 从“后续预留”移入 MVP 工具模式。
2. 增加专用 read_order 模式，用户按阅读顺序点击 bbox，系统依次写入 read_order=1..N。
3. 在 bbox 中心或上方显示序号 badge，缩放时保持可读但不遮挡主要内容。
4. 支持在序号 badge 或属性面板中直接修改数字。
5. 支持撤销、清空当前页排序、重新从 1 开始排序。
6. Ctrl+B 只作为自动排序建议入口，必须经用户确认后才写入 draft，不能直接作为 gold truth。
7. read_order 修改随整页 annotation revision 一起保存，MVP 不需要单独对象级排序 API。
8. 导出前 QC 必须检查缺失、重复、非连续和非导出对象混入排序的问题。
```

严重级别：高


### 3.3 缺少 roles / capabilities 到工作台状态的映射

位置：

```text
doc/开发文档/前端/annotation_workspace_interaction_spec.md:486
doc/开发文档/前端/annotation_workspace_interaction_spec.md:573
doc/开发文档/前端/frontend_development_spec.md:883
doc/开发文档/后端/k12_annotation_platform_backend_design.md:1422
```

问题：

```text
当前交互规范只写了 permission denied、readonly 和用户无编辑权限，但没有说明工作台应该如何消费后端 capabilities。
后端设计已经明确由后端返回 capabilities，前端不应直接根据 role_key 推断权限。
如果交互规范不补这个映射，标注工具栏、保存按钮、自动保存、快捷键、锁定提示可能各自实现一套权限判断。
```

建议：

```text
在“只读和锁定状态”或单独小节中补充：
1. 工作台加载 page 时同时加载 project capabilities。
2. bbox 工具、拖拽、删除、复制、保存依赖 can_create_annotation_revision 或等价 capability。
3. 复核入口依赖 can_review_revision。
4. 锁定 / 解锁入口依赖 can_lock_revision / can_unlock_revision。
5. 导出入口不在工作台直接判断 role_key，而使用 can_create_export_job。
6. 403 后刷新 capabilities，并展示只读原因。
7. 快捷键触发写操作前必须重新检查当前 capabilities、locked、conflict 和 saving 状态。
```

严重级别：中

---

## 4. 次要问题

### 4.1 Ctrl+C 同时复制并粘贴偏移框，语义偏激进

位置：

```text
doc/开发文档/前端/annotation_workspace_interaction_spec.md:407
doc/开发文档/前端/annotation_workspace_interaction_spec.md:611
```

问题：

```text
Ctrl+C 被定义为“复制并粘贴一个偏移后的 bbox”。
这符合部分标注工具习惯，但不符合通用 Web 应用中 Ctrl+C 只复制、不产生新对象的直觉。
虽然文档限制了画布焦点和文本选区，但误触仍可能直接制造新对象。
```

建议：

```text
MVP 可以改为：
1. Ctrl+C 只复制到内部 clipboard，不改变 draft。
2. Ctrl+D 作为“复制并偏移新对象”的快捷键。
3. 如果坚持 Ctrl+C 直接生成新对象，需要在 UI 中明确说明，并保证动作可撤销。
```

严重级别：低到中

### 4.2 自动保存失败状态与 dirty 状态关系需要更明确

位置：

```text
doc/开发文档/前端/annotation_workspace_interaction_spec.md:496
doc/开发文档/前端/annotation_workspace_interaction_spec.md:497
```

问题：

```text
文档允许失败后显示 autosave_failed 或 dirty。
这两个状态对用户含义不同：dirty 表示未保存，autosave_failed 表示尝试保存失败且需要用户注意。
如果实现时混用，状态栏和离页提示容易不一致。
```

建议：

```text
定义状态层级：
saved -> dirty -> autosave_pending -> autosaving -> saved
manual_saving 独立于 autosaving。
autosave_failed 是 dirty 的带错误子状态。
manual save 成功才能清除 autosave_failed。
```

严重级别：低

---

## 5. 符合项目目标的部分

以下内容与当前项目目标匹配，应保留：

```text
1. 明确 Web 前端不能照搬 PPOCRLabel 桌面端文件状态。
2. MVP 聚焦 bbox 闭环，暂不做 polygon、quad 人工精修和多人实时协作。
3. 坐标保存使用 image coordinate，缩放和平移只影响显示。
4. 坐标转换集中到 geometry.ts，并要求单元测试。
5. 保存必须携带 base_revision_id。
6. 409 conflict 不允许自动覆盖 latest revision。
7. readonly / locked / permission denied 状态不能通过快捷键绕过。
8. QC issue 可以定位到对象或区域。
9. localStorage 不保存完整 annotation JSON、原始试卷内容或敏感数据。
10. 输入框聚焦时不触发画布快捷键。
```

这些设计与后端 revision 模型、私有数据保护、标注复杂度和 MVP 优先级是一致的。

---

## 6. 建议修改顺序

建议先改：

```text
1. 去掉或替换本地 PPOCRLabel 绝对路径。
2. 决定自动保存是否进入 MVP；如果保留，补硬性节流、折叠、QC 和状态拆分策略。
3. 将 read_order 专用人工排序模式写入 MVP 交互范围，并明确 Ctrl+B 只是排序建议。
4. 补充 capabilities 到工作台工具、保存、快捷键和 readonly 的映射。
5. 重新评估 Ctrl+C 直接复制并生成新对象的交互语义。
```

如果只想尽快进入前端开发，最低限度也应先完成前 4 项。
