# Magpie TTS Studio v0.2.5

## Future-proof NeMo / Magpie embedding compatibility

Version 0.2.4 handled the observed `2362 -> 2364` embedding row-count mismatch. Version 0.2.5 generalizes that fix so newer NeMo/tokenizer builds can tolerate larger vocabulary row-count drift without requiring another hardcoded patch.

The compatibility layer now:

- accepts compatible row-count-only differences instead of one specific shape pair,
- still requires both tensors to be 2D PyTorch `Embedding` weights,
- still requires the embedding width to match exactly,
- copies all overlapping checkpoint rows,
- keeps newly created runtime rows initialized when the runtime vocabulary is larger,
- ignores extra checkpoint rows with a clear warning when the runtime vocabulary is smaller,
- refuses broad mismatches beyond safety limits,
- keeps true architecture changes fatal instead of hiding them.

## Safety knobs for future NeMo releases

The default limits are intentionally generous but not unlimited:

- `MAGPIE_EMBEDDING_COMPAT_MAX_ROWS=4096`
- `MAGPIE_EMBEDDING_COMPAT_MAX_RATIO=0.50`

Advanced users can override them in the environment before starting the GUI. The patch can also be disabled completely with:

```bat
set MAGPIE_DISABLE_EMBEDDING_COMPAT_PATCH=1
```

This is useful for diagnosing whether a future NeMo release has a real model architecture break rather than a tokenizer/vocabulary drift.
