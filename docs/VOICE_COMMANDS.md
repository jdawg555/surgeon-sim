# Voice commands

Surgeon-facing grammar. Narrow on purpose: any phrase outside this list is
ignored, which is how you keep voice control safe in a sterile field.

| Phrase | Action |
|---|---|
| `show C three C four` … `show C six C seven` | Highlight cervical level |
| `show L one L two` … `show L four L five` | Highlight lumbar level |
| `show L five S one` | Highlight L5-S1 |
| `show implant` | Render best-fit implant overlay |
| `hide implant` | Clear implant overlay |
| `next step` | Advance procedure step |
| `back` | Previous procedure step |
| `anchor reset` | Drop current anchor; ready to re-anchor |

## Why phrases, not numbers

`KeywordRecognizer` (Windows editor) and Wit.ai (on-device Quest) both
match against fixed phrase tables. Spelling out "L four L five" instead
of "L4 L5" is more robust to mishearing in noisy rooms.

## Adding a phrase

1. Add a `case` in `VoiceCommandRouter.Dispatch`.
2. Add the phrase to the `keywords` array in `Start`.
3. Document it here.

## Failure modes to budget for

- **Mishears under mask + suction noise.** The narrow grammar helps; a
  push-to-talk button on the controller is the next step.
- **Bilingual surgeons.** Today: English only. Wit.ai supports per-locale
  intent models when we need it.
