# RecallGate Architecture

RecallGate follows one rule:

```text
Read broadly locally. Inject minimally into models.
```

## Data flow

```text
.recallgate local memory files
        ↓
local filtering and scoring
        ↓
role-aware short memory selection
        ↓
token budget trimming
        ↓
brief pasted into AI coding agent
```

## What consumes tokens?

Local file reading and token estimation do not consume model tokens.

Tokens are only consumed when the final brief is sent to a model.

## Memory authority

```text
1. Current user instruction
2. Local active memory
3. Current repo files
4. Current conversation
5. Model memory
```

Archived and trashed memories are never injected by default.
