# RecallGate 项目计划书

> 项目定位：**面向多模型 AI Coding Agent 的低 token、可控、可回收、可纠偏的本地记忆调度器。**

---

## 0. 项目一句话定位

**RecallGate** 不是普通的 AI Agent 长期记忆库。

它的核心目标是：

> 本地广泛读取记忆，模型只读取最短、最相关、最需要的记忆。

英文定位：

> **RecallGate is a token-efficient, controllable memory firewall and orchestration layer for multi-agent coding workflows.**

中文定位：

> **RecallGate 是一个面向多模型 AI 编程流程的低 token、可控记忆防火墙与记忆调度层。**

核心宣传语：

> **Give every agent only the memory it needs — and nothing else.**

中文：

> **只给每个 Agent 它真正需要的记忆，其他一律不注入。**

---

## 1. 为什么要做这个项目

### 1.1 当前 AI Agent 的共同问题

现在的 AI Coding Agent 普遍存在几个问题：

1. **模型记忆不可靠**
   - 模型可能记错用户背景。
   - 模型可能把 A 项目的记忆带到 B 项目。
   - 模型可能引用过期规则。
   - 模型记忆通常不够透明，用户很难精细控制。

2. **上下文注入成本高**
   - 很多 Agent 会重复读取项目说明。
   - 很多 Agent 会反复解释同一个错误。
   - 很多 Agent 会把大量无关历史塞进上下文。
   - token 成本越来越高。

3. **记忆没有生命周期**
   - 有些记忆只是临时任务，不应该长期影响项目。
   - 有些记忆已经过期，但仍可能被 Agent 使用。
   - 有些记忆用户不想删除，只想暂时不让 Agent 读取。
   - 很多系统缺少 archive / trash / restore 这种安全机制。

4. **多模型协同时记忆边界混乱**
   - Coder 模型不需要知道文案细节。
   - Writer 模型不需要知道测试实现细节。
   - Reviewer 模型只需要知道风险规则和质量标准。
   - 所有模型共享完整上下文会浪费 token，也容易互相污染。

5. **项目记忆和单个对话记忆混在一起**
   - 项目长期规则应该长期保留。
   - 单次对话的临时进度不应该永久污染项目记忆。
   - 需要明确区分 Project Memory 和 Conversation Memory。

---

## 2. 项目核心原则

RecallGate 必须从第一版开始就围绕“极致性价比”设计。

### 2.1 五条基本原则

```text
1. 默认不调用大模型
2. 本地读取不消耗 token，可以多读
3. 模型注入必须极少，默认控制在 100–500 tokens
4. 先用本地规则、索引、标签筛选，再考虑可选 AI 总结
5. 所有记忆文件都应该可人工编辑、可 Git 管理、可恢复
```

### 2.2 最核心的工程原则

```text
Read broadly locally. Inject minimally into models.
```

中文：

```text
本地广泛读取，模型极简注入。
```

### 2.3 成本原则

```text
Local reads are free. Model context is expensive.
```

中文：

```text
本地读取免费，模型上下文昂贵。
```

### 2.4 记忆原则

```text
Don't give agents more memory. Give them better memory.
```

中文：

```text
不要给 Agent 更多记忆，要给它更好的记忆。
```

---

## 3. 项目和现有项目的区别

### 3.1 已有相近方向

当前已经存在一些相近项目或官方能力：

1. **agentmemory**
   - 方向：AI coding agents 的持久记忆。
   - 支持 Claude Code、Codex、Cursor 等。
   - 更像 searchable memory server。
   - 差异：它重点是统一持久记忆，不是“低 token 极简注入 + 可回收 + 分角色调度 + 模型记忆纠偏”。

2. **TencentDB-Agent-Memory**
   - 方向：fully local long-term memory for AI Agents。
   - 特点：本地长期记忆、分层 pipeline、零外部 API 依赖。
   - 差异：它更偏大而全长期记忆引擎，不是面向 coding workflow 的轻量 memory firewall。

3. **memsearch**
   - 方向：persistent unified memory layer for AI agents。
   - 特点：Markdown + Milvus，支持 Claude Code、Codex 等。
   - 差异：它偏统一记忆搜索层，而 RecallGate 偏记忆权限控制、压缩、分配和纠偏。

4. **GitHub Copilot Memory**
   - 方向：Copilot 记住 repository facts 和 personal coding preferences。
   - 差异：它绑定 Copilot 生态；RecallGate 要做本地、跨 Agent、用户可控、可编辑、可回收的中立层。

### 3.2 RecallGate 避开的方向

不要正面做：

```text
通用 AI Agent Memory
通用 Long-term Memory Server
大型向量数据库记忆系统
大而全 MCP Memory Server
大而全 AI Agent 平台
```

这些方向已经有人做，而且大公司和资本也会进入。

### 3.3 RecallGate 要打的差异化

RecallGate 的差异点是：

```text
1. 本地程序可以大量读取记忆，但模型只收到极简 brief
2. active / archive / trash / restore 记忆生命周期
3. 项目记忆和单个对话记忆严格分离
4. 本地记忆优先于模型记忆，用于纠正模型错误记忆
5. 多模型协同时按角色分配记忆
6. 每条记忆都有 short 版本，模型默认只读 short
7. 默认零 API、零模型调用、低依赖、可离线
8. 注入前预估 token 成本
```

---

## 4. 核心概念定义

## 4.1 模型记忆 Model Memory

模型记忆指 ChatGPT、Claude、Copilot、Cursor、Codex 等平台内部可能保存的用户偏好、历史上下文或项目印象。

特点：

```text
不完全透明
不一定可控
可能过期
可能跨项目混淆
可能和当前项目冲突
```

例子：

```text
模型记得用户做 WordPress 项目，但当前仓库其实是 Python CLI 项目。
模型记得用户喜欢某种业务规则，但当前项目不适用。
```

## 4.2 Agent 记忆 Agent Memory

Agent 记忆是 RecallGate 在本地管理的记忆。

特点：

```text
本地保存
用户可查看
用户可编辑
用户可归档
用户可放入回收站
用户可恢复
可 Git 管理
可按项目隔离
可按角色分配
```

## 4.3 本地记忆优先规则

优先级必须明确：

```text
Priority 1: 当前用户明确指令
Priority 2: 本地 active memory
Priority 3: 当前项目文件事实
Priority 4: 当前对话上下文
Priority 5: 模型长期记忆
```

核心规则：

```text
Local active memory overrides model memory when conflicts occur.
```

中文：

```text
当模型记忆与本地 active 记忆冲突时，以本地 active 记忆为准。
```

---

## 5. 记忆类型设计

RecallGate 至少需要区分以下记忆类型。

### 5.1 Project Memory 项目记忆

长期有效，绑定当前 Git 仓库或项目。

保存内容：

```text
项目是什么
技术栈是什么
核心规则是什么
不能改什么
历史重要决策
踩过的坑
测试规则
发布规则
架构规则
兼容性要求
```

例子：

```text
This is a Python CLI project.
Keep zero core dependencies.
Do not change public CLI behavior.
Tests must use temp fixtures, not fragile example files.
CHANGELOG must include every released version.
```

### 5.2 Conversation Memory 单个对话记忆

只对当前对话或当前任务有效。

保存内容：

```text
本轮任务目标
本轮尝试过什么
本轮失败过什么
用户本次临时要求
当前还没完成的事项
```

例子：

```text
Current task focuses only on CI/test reliability.
User does not want mobile layout changes in this round.
Tried solution A and it failed.
```

### 5.3 Role Memory 角色记忆

按模型角色分配。

建议角色：

```text
coder
tester
writer
reviewer
planner
security
```

每个角色只读取自己需要的记忆。

### 5.4 Correction Memory 纠偏记忆

专门用于纠正模型错误记忆。

例子：

```text
This is a Python CLI repo, not a WordPress project.
Use local project memory over model memory.
Ignore archived and trashed memories.
```

### 5.5 Global User Preference 全局用户偏好

长期有效，但应该谨慎注入。

例子：

```text
User prefers short, step-by-step technical instructions.
Do not provide too many steps at once.
```

这类记忆不能无脑注入所有项目，要根据任务相关性决定。

---

## 6. 记忆生命周期

每条记忆必须有状态。

### 6.1 状态定义

```text
active      当前可被读取和注入
archived    暂时隐藏，不参与默认上下文
trash       回收站，不参与上下文，但可恢复
deleted     永久删除，不可恢复
```

### 6.2 状态规则

```text
1. 默认 brief 只读取 active
2. archive 不进入模型上下文
3. trash 不进入模型上下文
4. delete 才是真正删除
5. restore 可以从 trash 恢复到 active 或 archived
6. 用户必须能看到 archive 和 trash 里的内容
```

### 6.3 为什么需要回收站

不能简单删除记忆，因为：

```text
用户可能只是暂时不需要
未来任务可能需要恢复
删除太激进，不安全
回收站让用户有控制感
```

---

## 7. 目录结构设计

第一版建议使用 Markdown + JSON index，不用数据库。

```text
.recallgate/
├── project/
│   ├── rules.md
│   ├── decisions.md
│   ├── pitfalls.md
│   ├── files.md
│   └── summary.md
│
├── conversations/
│   ├── current.md
│   └── history/
│       ├── 2026-06-07-ci-fix.md
│       └── 2026-06-08-release-check.md
│
├── roles/
│   ├── coder.md
│   ├── tester.md
│   ├── writer.md
│   ├── reviewer.md
│   └── planner.md
│
├── corrections/
│   └── model-conflicts.md
│
├── archive/
│   ├── project/
│   ├── conversations/
│   └── roles/
│
├── trash/
│   ├── project/
│   ├── conversations/
│   └── roles/
│
├── reports/
│   └── token-savings.md
│
├── index.json
└── config.toml
```

---

## 8. 单条记忆的数据结构

每条记忆需要同时有完整内容和极简内容。

### 8.1 YAML/JSON 字段建议

```yaml
id: mem_0001
scope: repo
type: rule
status: active
audience:
  - coder
  - tester
priority: high
importance: 10
confidence: 1.0
created_at: 2026-06-07
updated_at: 2026-06-07
last_used: null
use_count: 0
keywords:
  - tests
  - fixtures
  - examples
content: "Previous tests depended on files from examples/, which made test_cli.py fragile across environments. Future tests should use temporary directories or fixtures instead of real example files."
short: "Tests must use temp fixtures, not fragile example files."
source: user
```

### 8.2 content 和 short 的区别

`content` 给人看，保存完整背景。

`short` 给模型读，必须极短。

例子：

完整记忆：

```text
之前 test_cli.py 依赖 examples 目录里的真实文件，导致测试在不同环境下不稳定。以后测试应该使用临时目录或 fixture，不要依赖 examples 的真实文件。
```

极简记忆：

```text
Tests must use temp fixtures, not fragile example files.
```

模型默认只读 `short`。

---

## 9. 低 token 设计

### 9.1 核心原则

```text
完整记忆库可以很大。
注入模型的内容必须很小。
```

### 9.2 三种记忆读取级别

#### Level 1: One-line Correction

用于快速纠偏。

```text
Use local repo memory over model memory; this is a zero-dependency Python CLI project.
```

#### Level 2: Task Brief

用于普通任务。

```text
RecallGate Brief:
- This is a Python CLI project.
- Keep zero core dependencies.
- Tests must use temp fixtures, not fragile example files.
- For this task, focus only on CI/test reliability.
```

#### Level 3: Deep Memory

只在必要时启用。

```text
Read detailed decisions.md and pitfalls.md for release workflow history.
```

默认使用 Level 1 或 Level 2。

### 9.3 默认 brief 限制

第一版建议默认 brief 不超过：

```text
100–500 tokens
```

可以配置：

```bash
recallgate brief "fix tests" --budget 300
```

---

## 10. Token 预估功能

### 10.1 能不能做

能做，而且不消耗模型 token。

因为本地 token 预估只是本地计算，不调用大模型。

### 10.2 预估方式

第一版用低成本估算：

```text
英文：1 token ≈ 4 个英文字符
中文：1 个中文字符 ≈ 1–2 tokens
```

第一版可以用通用估算：

```text
estimated_tokens = ceil(character_count / 4)
```

后续可选支持本地 tokenizer。

### 10.3 输出指标

每次 brief 输出：

```text
Injected tokens: 实际注入模型的估算 token
Skipped tokens: 本地读取但没有注入的估算 token
Saved rate: 节省比例
```

计算方式：

```text
saving_rate = 1 - injected_tokens / full_memory_tokens
```

### 10.4 示例输出

```text
Token Estimate:
- Full active memory: ~12,400 tokens
- Injected brief: ~180 tokens
- Skipped: ~12,220 tokens
- Estimated saving: ~98.5%
```

### 10.5 为什么这是核心卖点

用户可以在把记忆发给模型前知道成本。

宣传语：

```text
Before sending memory to your agent, know the cost.
```

中文：

```text
在把记忆发给 Agent 之前，先知道大概要消耗多少 token。
```

---

## 11. 多模型记忆调度

### 11.1 核心原则

```text
Shared outline, private depth.
```

中文：

```text
共享大纲，分工深记。
```

### 11.2 多模型职责

```text
Local Memory Agent = 总管
Coder Model = 只深记代码相关
Tester Model = 只深记测试相关
Writer Model = 只深记文档相关
Reviewer Model = 只深记风险和质量标准
Security Model = 只深记安全规则和危险操作
```

### 11.3 每个模型都知道什么

所有模型都可以知道：

```text
当前项目是什么
当前任务目标是什么
必须遵守的最高优先级规则
本地记忆优先于模型记忆
archive/trash 记忆不能使用
```

### 11.4 每个模型只深度读取什么

Coder 读取：

```text
代码结构
技术栈
兼容性要求
不能改的 API
相关踩坑记录
```

Tester 读取：

```text
测试规则
历史测试坑
CI 要求
fixture 规则
```

Writer 读取：

```text
README 风格
CHANGELOG 规则
文档语气
发布说明格式
```

Reviewer 读取：

```text
风险清单
发布前检查项
兼容性要求
安全规则
```

---

## 12. Memory Firewall 记忆防火墙

RecallGate 应该有一个核心概念：

```text
Memory Firewall
```

中文：

```text
记忆防火墙
```

### 12.1 作用

```text
阻止错误模型记忆影响当前项目
阻止 archive 记忆被默认读取
阻止 trash 记忆被读取
阻止过期记忆进入上下文
阻止其他项目记忆串入当前任务
阻止低置信度记忆影响关键任务
```

### 12.2 注入模型的权限声明

每次 brief 顶部可以加极短规则：

```text
Memory Authority:
- Current user instruction has highest priority.
- Local active memory overrides model memory.
- Ignore archived or trashed memories.
```

### 12.3 纠偏示例

当模型把项目记错时：

```text
Correction:
- This is a Python CLI repo, not a WordPress project.
- Use local project memory as source of truth.
```

---

## 13. 记忆评分系统

### 13.1 为什么需要评分

不能让所有记忆永久 active。

需要判断：

```text
哪些记忆有用
哪些记忆过期
哪些记忆冲突
哪些记忆应该归档
哪些记忆应该进入回收站
```

### 13.2 Memory Score 建议

```text
Memory Score =
重要性 × 35%
最近使用 × 20%
重复命中 × 20%
用户确认 × 15%
任务相关性 × 10%
```

### 13.3 高价值记忆

应该长期 active：

```text
用户明确说“以后都这样”
项目硬规则
多次重复强调
每次任务都相关
历史大坑
发布规则
安全规则
```

### 13.4 低价值记忆

建议 archive 或 trash：

```text
一次性任务
临时路径
过期版本号
已完成进度
截图临时状态
已经失效的规则
和新规则冲突的旧规则
```

### 13.5 注意

RecallGate 第一版不应该自动删除记忆。

正确流程：

```text
系统建议
用户确认
进入 archive 或 trash
```

---

## 14. 项目记忆和对话记忆的升级机制

### 14.1 Conversation Memory 不能自动变 Project Memory

因为单次对话常常包含临时要求。

必须通过 review 或用户确认升级。

### 14.2 升级条件

Conversation Memory 可以升级为 Project Memory 的情况：

```text
用户明确说以后都这样
同一规则多次出现
影响未来任务
属于项目硬规则
属于历史踩坑
属于发布或测试规则
```

### 14.3 命令示例

```bash
recallgate promote conv_2026_0607_003 --to project.rules
```

### 14.4 review 示例

```text
Suggested to promote:

1. "Tests must not depend on example files."
Reason: repeated in 3 conversations and affects future test design.

Action:
- promote
- keep as conversation memory
- archive
- trash
```

---

## 15. CLI 命令设计

### 15.1 MVP 必须有的命令

```bash
recallgate init
recallgate add
recallgate list
recallgate trash
recallgate restore
recallgate brief
recallgate review
```

### 15.2 建议命令完整列表

#### 初始化

```bash
recallgate init
```

创建 `.recallgate/` 目录结构。

#### 添加记忆

```bash
recallgate add "Keep zero core dependencies." --scope repo --type rule --role coder
```

#### 查看记忆

```bash
recallgate list
recallgate list --status active
recallgate list --scope repo
recallgate list --role tester
```

#### 放入回收站

```bash
recallgate trash mem_0001
```

#### 恢复

```bash
recallgate restore mem_0001
```

#### 归档

```bash
recallgate archive mem_0001
```

#### 生成 brief

```bash
recallgate brief "fix GitHub Actions test failure"
```

#### 指定角色 brief

```bash
recallgate brief "fix tests" --role tester
recallgate brief "update README" --role writer
recallgate brief "review release readiness" --role reviewer
```

#### token 预算

```bash
recallgate brief "fix tests" --budget 300
```

#### 纠偏

```bash
recallgate correct "model thinks this is a WordPress project"
```

#### 审查记忆

```bash
recallgate review
```

#### 升级对话记忆

```bash
recallgate promote conv_001 --to project.rules
```

#### token 预估

```bash
recallgate estimate
recallgate estimate --brief "fix tests"
```

---

## 16. brief 输出格式

### 16.1 普通 brief

```text
RecallGate Brief

Memory Authority:
- Current user instruction has highest priority.
- Local active memory overrides model memory.
- Ignore archived or trashed memories.

Correction:
- This is a Python CLI project, not WordPress.

Project Rules:
- Keep zero core dependencies.
- Do not change public CLI behavior.
- Tests must use temp fixtures, not fragile example files.

Current Task:
- Focus only on CI/test reliability.

Token Estimate:
- Full active memory: ~12,400 tokens
- Injected brief: ~180 tokens
- Estimated saving: ~98.5%
```

### 16.2 Coder brief

```text
Coder Memory Brief

Authority:
- Use local active memory over model memory.

Project:
- Python CLI project.
- Keep zero core dependencies.
- Preserve public CLI behavior.

Relevant Pitfalls:
- Tests must use temp fixtures, not fragile example files.

Task:
- Fix CI/test reliability only.

Estimated tokens: ~95
```

### 16.3 Writer brief

```text
Writer Memory Brief

Authority:
- Use local active memory over model memory.

Docs Rules:
- README must stay in sync with CLI behavior.
- CHANGELOG must include every released version.
- Keep documentation concise and developer-friendly.

Task:
- Update docs only if behavior changed.

Estimated tokens: ~78
```

---

## 17. MVP 第一版范围

### 17.1 第一版必须做

```text
1. Markdown + JSON index 本地记忆库
2. active / archive / trash / restore
3. project memory / conversation memory 分离
4. short memory 字段
5. role-based brief
6. correction brief
7. token estimate
8. budget limit
9. review 建议归档/回收
10. 默认不调用大模型
```

### 17.2 第一版不做

```text
不做 Web UI
不做向量数据库
不做 embedding
不做复杂 MCP
不做自动删除
不做云同步
不做多用户权限系统
不做完整 Agent 平台
```

### 17.3 第一版语言建议

建议 Python。

原因：

```text
CLI 容易做
跨平台
用户容易安装
适合快速发布 PyPI
可以保持零核心依赖
```

也可以用 TypeScript，但第一版 Python 更适合快速做 CLI。

---

## 18. MVP 开发路线

## Phase 0: 项目骨架

目标：可以安装、可以运行。

任务：

```text
创建 pyproject.toml
创建 src/recallgate/
创建 CLI 入口
创建 README.md
创建 LICENSE
创建 tests/
创建 GitHub Actions
```

验收：

```bash
recallgate --help
```

可以正常输出帮助。

---

## Phase 1: init + 目录结构

目标：初始化 `.recallgate/`。

命令：

```bash
recallgate init
```

生成：

```text
.recallgate/
├── project/
├── conversations/
├── roles/
├── corrections/
├── archive/
├── trash/
├── reports/
├── index.json
└── config.toml
```

验收：

```text
重复 init 不破坏已有记忆
缺失目录可自动补齐
```

---

## Phase 2: add + list

目标：可以添加和查看记忆。

命令：

```bash
recallgate add "Keep zero core dependencies." --scope repo --type rule --role coder
recallgate list
```

必须支持字段：

```text
id
scope
type
status
audience
priority
content
short
keywords
created_at
updated_at
```

验收：

```text
index.json 正确更新
Markdown 文件正确生成
list 能按状态、scope、role 过滤
```

---

## Phase 3: archive / trash / restore

目标：实现可控生命周期。

命令：

```bash
recallgate archive mem_0001
recallgate trash mem_0001
recallgate restore mem_0001
```

规则：

```text
active 才能进入默认 brief
archive 不进入默认 brief
trash 不进入默认 brief
restore 默认恢复为 active，也可以恢复为 archived
```

验收：

```text
trash 后 brief 不再读取该记忆
restore 后 brief 可重新读取
delete 需要二次确认或明确参数
```

---

## Phase 4: brief

目标：生成低 token brief。

命令：

```bash
recallgate brief "fix tests"
recallgate brief "fix tests" --role tester
recallgate brief "fix tests" --budget 300
```

筛选规则第一版使用本地规则：

```text
status = active
role 匹配
scope 匹配
keywords 命中
priority 排序
importance 排序
```

输出内容：

```text
Memory Authority
Correction
Project Rules
Role Memory
Current Task
Token Estimate
```

验收：

```text
不会读取 archive/trash
会优先输出 short
超过 budget 时压缩条数
```

---

## Phase 5: correction

目标：纠正模型错误记忆。

命令：

```bash
recallgate correct "model thinks this is a WordPress project"
```

输出：

```text
Correction:
- This is a Python CLI repo, not a WordPress project.
- Use local active memory as source of truth.
```

验收：

```text
输出极短
优先引用 project summary 和 active rules
不会输出无关内容
```

---

## Phase 6: token estimate

目标：本地预估 token 成本。

命令：

```bash
recallgate estimate
recallgate brief "fix tests" --estimate-tokens
```

指标：

```text
full_active_memory_tokens
injected_brief_tokens
skipped_tokens
saving_rate
```

验收：

```text
不调用模型 API
输出估算结果
预算模式可用
```

---

## Phase 7: review

目标：建议哪些记忆应该归档、回收、升级。

命令：

```bash
recallgate review
```

第一版规则：

```text
长期未使用 -> 建议 archive
低 importance + 低 use_count -> 建议 archive
和新记忆冲突 -> 建议 trash 旧记忆
conversation 多次出现 -> 建议 promote
```

验收：

```text
只建议，不自动删除
用户可以选择 keep/archive/trash/promote
```

---

## 19. 评分和筛选算法第一版

### 19.1 不使用 AI 的原因

为了极致性价比：

```text
默认不调用模型
默认不使用 embedding
默认不依赖向量数据库
```

### 19.2 本地评分公式

```text
score =
importance_score * 0.35 +
recency_score * 0.20 +
use_count_score * 0.20 +
user_confirmed_score * 0.15 +
keyword_match_score * 0.10
```

### 19.3 简单规则

```text
priority high > medium > low
scope repo > conversation，除非当前任务强相关
role 匹配 > role 不匹配
short 优先输出
content 默认不输出
```

---

## 20. 关键安全规则

### 20.1 永远不默认读取 trash

```text
trash memory must never be injected by default
```

### 20.2 archive 不默认读取

```text
archive memory is hidden unless explicitly restored or included
```

### 20.3 delete 必须谨慎

```text
delete should require explicit confirmation
```

CLI 可以设计为：

```bash
recallgate delete mem_0001 --yes
```

### 20.4 模型记忆必须可被本地记忆覆盖

brief 里必须有 authority 声明。

### 20.5 不自动升级临时记忆

conversation memory 不能自动进入 project memory。

---

## 21. README 核心内容建议

### 21.1 开头

```markdown
# RecallGate

Token-efficient controllable memory for multi-agent coding workflows.

RecallGate reads your local project and conversation memory broadly, filters it locally, and injects only the shortest role-specific memory into AI coding agents.
```

### 21.2 核心卖点

```markdown
- Local-first memory
- No model calls by default
- Active / archive / trash / restore lifecycle
- Project memory and conversation memory separation
- Role-based memory briefs
- Model memory correction
- Token estimation before injection
- Git-friendly Markdown storage
```

### 21.3 核心理念

```markdown
Local reads are free. Model context is expensive.
```

### 21.4 示例

```bash
recallgate init
recallgate add "Keep zero core dependencies." --scope repo --type rule --role coder
recallgate brief "fix GitHub Actions" --role coder --budget 300
```

---

## 22. 商业化和扩展方向

### 22.1 GitHub 开源核心

第一阶段开源：

```text
CLI
Markdown storage
JSON index
Token estimate
brief generation
archive/trash/restore
```

### 22.2 后续可扩展

```text
VS Code extension
Cursor integration
Claude Code hook
Codex CLI wrapper
MCP server
Web dashboard
Team memory review
Optional local embedding
Optional AI compression
```

### 22.3 付费方向

如果后期商业化，可以做：

```text
团队版 memory review
多仓库 memory sync
企业安全审计
Agent token saving report
VS Code Pro 插件
```

---

## 23. 项目命名

### 23.1 推荐名称

```text
recallgate
```

原因：

```text
比 repo-memory 更有差异
突出 gate / firewall / control
适合表达“哪些记忆允许进入模型上下文”
```

### 23.2 备选名称

```text
repo-memory
context-gate
agent-memory-vault
memory-firewall
context-vault
```

### 23.3 最终推荐

```text
recallgate
```

副标题：

```text
Token-efficient controllable memory for AI coding agents.
```

---

## 24. 最终项目定义

RecallGate 的最终定义：

```text
RecallGate 是一个本地优先、低 token、可控、可回收、可纠偏的 AI Coding Agent 记忆调度器。
它在本地广泛读取项目记忆和对话记忆，通过规则、角色、状态、优先级和 token 预算进行筛选，
然后只向模型注入最短、最相关、最必要的记忆 brief。
```

英文定义：

```text
RecallGate is a local-first, token-efficient memory firewall and orchestration layer for AI coding agents. It reads broad project and conversation memory locally, filters and compresses it without model calls by default, and injects only short, role-specific, high-confidence memory briefs into agents.
```

---

## 25. 最重要的边界

这个项目不是：

```text
不是通用大模型记忆库
不是向量数据库项目
不是大而全 Agent 平台
不是替代 Claude / Codex / Cursor
不是让 Agent 记住一切
```

这个项目是：

```text
本地记忆管理器
记忆防火墙
记忆调度器
低 token brief 生成器
模型错误记忆纠偏层
多模型记忆分配器
```

---

## 26. 最终核心卖点

```text
1. 本地多读，模型少读
2. 记忆可控，可归档，可回收，可恢复
3. 项目记忆和对话记忆分离
4. 模型记忆出错时，本地记忆纠偏
5. 多模型只读取各自需要的记忆
6. 每次注入前预估 token 成本
7. 默认零 API、零模型调用、低依赖
8. Markdown + Git-friendly
```

一句话总结：

```text
RecallGate 不追求让 Agent 记住更多，而是让 Agent 只读取正确、必要、最低成本的记忆。
```

---

## 27. 第一版成功标准

MVP 成功不看功能多，而看这几个指标：

```text
1. 用户能初始化本地记忆库
2. 用户能添加、查看、归档、回收、恢复记忆
3. 用户能区分 project memory 和 conversation memory
4. 用户能给 coder/tester/writer/reviewer 生成不同 brief
5. brief 默认很短
6. archive/trash 绝不进入默认 brief
7. 能输出 token 预估和节省率
8. 不调用任何模型 API 也能工作
```

---

## 28. 建议第一条 GitHub 项目描述

短描述：

```text
Token-efficient controllable memory for AI coding agents.
```

长描述：

```text
RecallGate is a local-first memory firewall for AI coding agents. It keeps project and conversation memory in Git-friendly Markdown files, supports active/archive/trash/restore lifecycle, corrects stale model memory, and injects only short role-specific briefs to minimize token cost.
```

---

## 29. 项目开发优先级

### 必须优先

```text
1. init
2. add/list
3. status lifecycle
4. brief
5. role-based brief
6. token estimate
```

### 第二优先

```text
1. review
2. promote
3. correction
4. conflict detection
```

### 第三优先

```text
1. MCP
2. VS Code extension
3. Claude/Codex/Cursor integration
4. optional AI summarization
5. optional tokenizer
```

---

## 30. 结论

这个项目可以做，而且不要做成普通 Agent Memory。

真正的方向是：

```text
低 token + 可控生命周期 + 本地纠偏 + 多模型记忆调度
```

最终定位：

```text
RecallGate: Token-efficient controllable memory firewall for multi-agent coding workflows.
```

中文：

```text
RecallGate：面向多模型 AI 编程流程的低 token、可控记忆防火墙。
```
