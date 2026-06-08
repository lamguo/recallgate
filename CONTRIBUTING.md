# Contributing

RecallGate is designed to stay small, local-first, and token-efficient.

Before adding a feature, ask:

1. Does it work without model/API calls by default?
2. Does it reduce injected context instead of increasing it?
3. Does it keep memory controllable and recoverable?
4. Can users inspect the memory files directly?

Run tests:

```bash
python -m unittest discover -s tests
```
