# Magpie TTS Studio v0.2.4

## Crash fix: NeMo / Magpie embedding mismatch

Fixed a first-generation crash seen with recent NeMo builds:

```text
RuntimeError: Error(s) in loading state_dict for Embedding:
size mismatch for weight: copying a param with shape torch.Size([2362, 768])
from checkpoint, the shape in current model is torch.Size([2364, 768]).
```

The app now applies a narrow runtime compatibility patch while loading the Magpie checkpoint:

- if a PyTorch `Embedding` differs only by a small number of vocabulary rows,
- and the embedding width is unchanged,
- the overlapping checkpoint rows are copied,
- extra runtime rows keep their initialized values,
- the GUI does not abort during model loading.

This is intended for small tokenizer/checkpoint drift between NeMo nightly/current builds and the public Magpie checkpoint. It does not silently ignore broad architecture mismatches.

## Model loading improvement

- Local Magpie `.nemo` files are now loaded directly with `restore_from(...)` instead of first trying `from_pretrained(...)` on the local snapshot folder.
- Hugging Face/Transformers/NeMo cache environment variables are now set explicitly to the selected project cache directory before loading.

## Progressbar improvement

- First-time model loading now uses an indeterminate/pulsing progressbar instead of appearing stuck at roughly 5%.
- Once the model is ready, normal percentage progress resumes.

## Error dialog improvement

- Full tracebacks are still written to the GUI log.
- The popup is shortened to the useful tail of the traceback so the window is less overwhelming.
