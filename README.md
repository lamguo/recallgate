<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://img.shields.io/badge/dependencies-0-%234ADE80?style=flat-square">
    <img alt="RecallGate" src="https://img.shields.io/badge/dependencies-0-%234ADE80?style=flat-square">
  </picture>
  <img src="https://img.shields.io/badge/API%20calls-0-%2394a3b8?style=flat-square" alt="0 API calls">
  <img src="https://img.shields.io/badge/license-MIT-%2394a3b8?style=flat-square" alt="MIT">
  <img src="https://img.shields.io/badge/tests-31%20passing-%234ADE80?style=flat-square" alt="Tests">
</p>

# RecallGate

> **Give every AI agent only the memory it needs — and nothing else.**

RecallGate is a **token-efficient, controllable memory gate for AI coding agents**.

It helps Claude Code, Codex CLI, Cursor, Gemini CLI, Copilot-style agents, and multi-agent coding workflows stop wasting context on irrelevant history.

```text
Without RecallGate:  1,240 tokens → $0.02 per ask → model reads everything
With RecallGate:        95 tokens → $0.001 per ask → model reads only what matters
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

---

## Why you'll use this

### "My AI keeps forgetting the project rules"

```bash
recall-gate correct "model keeps suggesting requests library — we use stdlib only"
```

Outputs a <100-token correction brief. Paste it into any AI agent. Problem solved.

### "I'm burning tokens on irrelevant context"

```bash
recall-gate estimate --task "fix tests" --role tester --json
```

Returns structured data: `{"full_active_memory_tokens": 1240, "injected_brief_tokens": 95, "estimated_saving_percent": 92.3}`. Know your savings before you inject.

### "Coder, tester, and writer agents need different context"

```bash
recall-gate brief "fix deployment" --role coder     # sees deployment rules
recall-gate brief "update docs"   --role writer     # sees README guidelines
recall-gate brief "review PR"     --role reviewer    # sees audit checklist
```

Each agent role sees only its relevant memories. Shared rules go to `--role all`.

### "I have 50 memories and don't know what's stale"

```bash
recall-gate review --apply          # auto-archive low-value memories
recall-gate list --sort use_count   # see what's never been used
recall-gate search "fixtures"       # find without opening index.json
```

---

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

### Memory lifecycle

```text
active   → readable by default
archive  → hidden but recoverable
trash    → blocked from agents, still recoverable
deleted  → permanently removed from index and disk
```

### Role-based routing

Every memory targets one or more roles. `--role all` means everyone sees it.

```bash
recall-gate brief "fix tests"    --role tester     # only tester memories
recall-gate brief "update README" --role writer    # only writer memories
recall-gate brief "review"       --role reviewer   # only reviewer memories
```

The goal: **Shared outline, private depth.**

---

## Command reference

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

---

## About injection

`brief` prints plain text by design in v0.1.0. You copy the output into Claude Code, Codex CLI, Cursor, Gemini CLI, Copilot Chat, or any other coding agent.

Automatic injection is intentionally not included in the first version because the core tool should stay local, predictable, and provider-agnostic. Future integrations can add MCP, editor plugins, or agent hooks on top of the same brief engine.

---

## Design philosophy

```text
Default model calls:       0
Default API keys:          0
Default runtime deps:      0
Default storage:           local Markdown + JSON
Default tokenizer:         built-in estimator
Default test discovery:    python -m unittest discover
```

RecallGate is built to be **cheap, local, and predictable**. No vector database. No LLM calls. No network. No vendor lock-in. You commit your `.recallgate` folder to Git, and every teammate gets the same memory.

### What RecallGate is

- A local memory gate
- A memory firewall
- A token-saving brief generator
- A role-based memory router
- A stale model memory correction layer

### What RecallGate is not

- Not a hosted memory service
- Not a vector database
- Not a full AI agent framework
- Not a replacement for Claude Code, Codex, Cursor, or Copilot
- Not a tool that blindly remembers everything

---

## Support

If RecallGate saves you tokens and time, consider buying me a coffee:

[![PayPal](https://img.shields.io/badge/Donate-PayPal-%2300457C?style=flat-square)](https://paypal.me/lamguo)
[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-%23EA4AAA?style=flat-square)](https://github.com/sponsors/lamguo)

Every bit of support helps keep the project actively maintained. Thank you! ❤️

---

## Status

`v0.1.0` — alpha MVP with **31 unit tests, 0 dependencies, and 17 CLI commands**.

**Coming next:** MCP server, editor plugins, auto-conflict detection, and optional AI compression.

## License

MIT
