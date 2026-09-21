# DaVinci Resolve — footage ideas on the timeline

`footage_ideas.py` writes footage / b-roll ideas onto the timeline that is
currently open in Resolve, as timeline markers (and optionally as Text+ titles).

## Run it

1. Resolve > Workspace > Console
2. Switch the console to the **Py3** tab
3. Paste the whole file in, press Enter

`resolve` is already defined in that console, so nothing else is needed.

To run it from a terminal instead, Resolve's scripting module has to be
importable (`RESOLVE_SCRIPT_API` / `RESOLVE_SCRIPT_LIB`), and
Preferences > System > General > *External scripting using* must be set to
**Local**.

## Settings

Everything is at the top of the file.

| Setting | What it does |
| --- | --- |
| `IDEAS` | Your list of `(label, note)` pairs. The label shows on the ruler, the note is inside the marker. |
| `MODE` | `markers` (default), `titles` for Text+ cards, or `both`. |
| `PLACEMENT` | `clip` puts one idea at the head of each clip; `even` spreads them across the timeline. |
| `SOURCE_TRACK` | Which video track `clip` placement reads from. |
| `TITLE_TRACK` | Track for Text+ cards. `None` adds a new track on top. |
| `MARKER_COLOR` | Any Resolve marker colour name, e.g. `Yellow`, `Sky`, `Fuchsia`. |
| `CYCLE_IDEAS` | Reuse the list from the top when there are more clips than ideas. |

## Notes

- Markers are placed relative to the timeline start frame, which is what
  Resolve's `AddMarker` expects.
- Only one marker can live on a given frame, so a collision steps forward up to
  24 frames before giving up on that idea.
- Text+ mode is best-effort: it inserts the generator and then tries to write
  into its `StyledText` input. If Resolve won't let it, the card is still placed
  and you type the text in yourself.
- Nothing here deletes or moves existing clips or markers.
