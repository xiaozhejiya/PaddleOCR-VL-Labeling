# Git 提交信息规范

版本：v0.1
日期：2026-06-03

## 目录

- 1. 标题格式
- 2. 正文格式
- 3. 提交前检查
- 4. 标准示例
- 5. 禁止写法

---

本项目提交信息使用 Conventional Commits 的类型和可选 scope，但标题和正文说明必须使用中文。提交信息应说明“改了什么、为什么改、如何验证”，不能只写笼统的 update、fix bug 或调整代码。

## 1. 标题格式

```text
<type>(<scope>): <中文摘要>
```

要求：

```text
1. type 使用英文小写，必须从 feat / fix / docs / test / refactor / chore / style / perf / build / ci / revert 中选择。
2. scope 使用英文小写，表示影响范围，例如 backend / frontend / sql / docs / auth / workspace / export。
3. 中文摘要必须具体说明用户可感知行为、工程边界或修复对象。
4. 中文摘要不要以句号结尾，不写“更新代码”“修复问题”“优化逻辑”这类空泛描述。
5. 同一个提交不要混入无关领域变更；前后端、文档、数据库、配置变更应按功能边界拆分。
```

示例：

```text
chore(frontend): 隐藏数据面板导航并记录提交规则
fix(backend): 修复项目角色绑定缺少审计日志的问题
docs(sql): 补充数据库初始化账号和权限说明
refactor(backend): 将 ORM 模型迁移到 app/db/models
```

## 2. 正文格式

正文使用无序列表，每条以 `- ` 开头。除非常小的纯文档修正外，正文至少包含两类信息：变更内容和验证结果。

推荐结构：

```text
<type>(<scope>): <中文摘要>

- 说明主要行为变化或代码结构变化，写清影响范围
- 说明为什么需要这个改动，或原先存在什么风险
- 说明保留了哪些兼容路径、未改动哪些边界，避免误解
- 说明执行过的验证命令和结果；如果未验证，必须说明原因
```

正文要求：

```text
1. 使用中文完整短句，不写只对作者本人有意义的缩写。
2. 每条 bullet 只描述一类事实，避免把多个无关改动塞进一行。
3. 涉及用户界面、API、数据库、权限、审计、导出、配置时，必须写清对使用者或调用方的影响。
4. 涉及测试、构建、迁移、脚本时，必须写明执行的命令，例如 npm run build、pytest backend/tests、alembic upgrade head。
5. 如果存在未完成项、兼容风险或未执行验证，必须在正文中明确说明，不能省略。
```

## 3. 提交前检查

提交前按变更范围运行检查，并在 commit 正文中写明结果。

后端变更至少运行：

```powershell
ruff check backend/app backend/tests
pytest backend/tests
```

前端变更至少运行：

```powershell
npm run build
npm run test
```

数据库 migration 变更还应验证：

```powershell
alembic upgrade head
```

要求：

```text
1. 只改文档时可以不运行构建或测试，但提交正文必须说明“仅文档变更，未运行构建或测试”。
2. 如果某项检查因环境、依赖或数据库不可用无法执行，必须在提交正文说明原因。
3. 涉及前后端联动时，分别运行前端和后端检查，不能只验证其中一端。
```

## 4. 标准示例

```text
chore(frontend): 隐藏数据面板导航并记录提交规则

- 从工作台侧边栏导航配置中移除数据面板入口，保留原有 dashboard 路由和页面逻辑
- 新增 doc/开发文档/COMMIT_RULES.md，记录中文 commit 标题和无序列表正文规范
- 验证 npm run build 通过
```

```text
fix(backend): 补齐项目角色绑定审计日志

- 在项目角色绑定写入后同步创建 audit_logs 记录，避免绕过角色授予审计链
- 要求调用方传入 granted_by，并在审计 after_json 中记录成员、角色和授权人
- 补充 repository 单元测试，覆盖系统角色拒绝绑定和项目角色授予审计
- 验证 ruff check backend 和 pytest backend/tests 通过
```

## 5. 禁止写法

```text
update
fix bug
docs: update
feat: add page
chore: misc changes
```

原因：

```text
1. 看不出影响范围。
2. 看不出具体行为变化。
3. 看不出是否包含验证。
4. 后续排查问题时无法快速定位提交意图。
```
