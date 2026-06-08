<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fimg.shields.io%2Fbadge&label=token%20saving&message=up%20to%2092%25&color=%234ADE80&style=flat-square">
    <img alt="RecallGate: Token-efficient memory for AI coding agents" src="https://img.shields.io/badge/token%20saving-up%20to%2092%25-%234ADE80?style=flat-square">
  </picture>
</p>

<h1 align="center">RecallGate</h1>
<p align="center">
  <b>Give every AI agent only the memory it needs — and nothing else.</b>
</p>

<p align="center">
  <a href="#install"><img src="https://img.shields.io/badge/install-pip%20install%20-e.svg?style=flat-square" alt="Install"></a>
  <img src="https://img.shields.io/badge/dependencies-0-%234ADE80?style=flat-square" alt="0 deps">
  <img src="https://img.shields.io/badge/API%20calls-0-%2394a3b8?style=flat-square" alt="0 API calls">
  <img src="https://img.shields.io/badge/license-MIT-%2394a3b8?style=flat-square" alt="MIT">
  <a href="https://github.com/lamguo/recallgate"><img src="https://img.shields.io/badge/github-lamguo%2Frecallgate-%23181717?style=flat-square" alt="GitHub"></a>
</p>

---

Every time you ask Claude Code, Cursor, Copilot, or Codex to fix something, **it re-reads your entire project memory**. That costs tokens, costs time, and still doesn't stop it from making the same mistakes.

RecallGate is a 1-second CLI command that turns 1,240 tokens of project memory into a **95-token brief** — filtered by role, ranked by relevance, and capped by budget.

```text
Without RecallGate:  1,240 tokens  →  $0.02 per ask  →  model reads everything
With RecallGate:        95 tokens  →  $0.001 per ask  →  model reads only what matters
                                                                  ▲ 92.3% cheaper
```

**Zero dependencies. Zero API calls. Offline. One `.recallgate` folder.**

---

## Install

```bash
pip install recallgate
# or from source
git clone https://github.com/lamguo/recallgate.git
cd recallgate && pip install -e .
```

## Quick start — 10 seconds to value

```bash
# 1. Init a workspace in your project
cd my-project && recall-gate init

# 2. Add project rules (they stay in Git-friendly .md files)
recall-gate add "Keep zero core dependencies." --role coder --priority high
recall-gate add "Tests use temp fixtures, not example files." --role tester
recall-gate add "README must match CLI behavior exactly." --role writer

# 3. Generate a 100-token brief for your coding agent
recall-gate brief "fix CI pipeline test failure" --role tester --budget 100
```

Paste the output into your AI agent. That's it.

## Why you'll use this

### "My AI keeps forgetting the project rules"

```bash
recall-gate correct "model keeps suggesting requests library — we use stdlib only"
```

Outputs a <100-token correction brief. Paste it. Problem solved.

### "I'm burning tokens on irrelevant context"

```bash
recall-gate estimate --task "fix tests" --role tester --json
```

Returns structured data like `{"full_active_memory_tokens": 1240, "injected_brief_tokens": 95, "estimated_saving_percent": 92.3}`. Know your savings before you inject.

### "Coder, tester, and writer agents need different context"

```bash
recall-gate brief "fix deployment" --role coder     # sees deployment rules
recall-gate brief "update docs"   --role writer     # sees README guidelines
recall-gate brief "review PR"     --role reviewer    # sees audit checklist
```

Each role sees only its relevant memories. Shared rules go to `--role all`.

### "I have 50 memories and don't know what's stale"

```bash
recall-gate review --apply          # auto-archive low-value memories
recall-gate list --sort use_count   # see what's never been used
recall-gate search "fixtures"       # find without opening index.json
```

## Features

| | What | Why it matters |
|---|---|---|
| 🎯 | **Role-filtered briefs** | Coder gets coding rules, writer gets docs rules, tester gets test rules |
| ✂️ | **Token budget control** | Set `default_budget = 100` in config — briefs are hard-capped |
| 🔄 | **Memory lifecycle** | `active` → `archive` → `trash` → `delete`. Nothing lost by accident |
| 🔧 | **Edit in place** | `recall-gate edit mem_0001 --priority critical` — no delete+re-create |
| 🔍 | **Full-text search** | Searches content, short text, keywords, scope, type, priority |
| 📦 | **JSON output** | `--json` on every command — pipe into scripts, editors, MCP |
| 📂 | **Git-friendly storage** | Each memory is a `.md` file with YAML frontmatter. Diff, commit, review |
| 🌐 | **CJK support** | Chinese memory gets readable slugs and meaningful keywords |
| 🧼 | **Auto-review** | `recall-gate review --apply` archives unused memories automatically |

## The full command reference

```
recall-gate
  init                           Create workspace
  add <content>                  Add a memory
  edit/update <id>               Edit memory fields
  info <id>                      Full memory details
  list [--sort] [--reverse]      List memories
  search <query>                 Full-text search
  brief <task>                   Token-efficient memory brief
  correct <issue>                Correction brief (model forgets)
  estimate                       Token cost estimate
  review [--apply]               Suggest/apply cleanup
  archive / trash / restore      Lifecycle commands
  promote <id>                   Move conversation to project
  delete <id> --yes              Permanent removal

Global flags:
  --json      Machine-readable output on all commands
  --root      Target a specific workspace (for automation)
```

## Design philosophy

```text
Default model calls:       0
Default API keys:          0
Default runtime deps:      0
Default storage:           local Markdown + JSON
Default tokenizer:         built-in estimator
```

RecallGate is built to be **cheap, local, and predictable**. No vector database. No LLM calls. No network. No vendor lock-in. You commit your `.recallgate` folder to Git, and every teammate gets the same memory.

## Status

`v0.1.0` — fully functional MVP with 28 unit tests, 0 dependencies, and 17 CLI commands.

**Coming next:** MCP server, editor plugins, auto-conflict detection, and optional AI compression.

## License

MIT
