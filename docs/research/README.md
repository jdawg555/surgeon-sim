# research/

Decision documents for non-trivial integrations. Each doc lays out the
question, the realistic options, the rough effort, and a recommendation,
so we can commit a focused session to the right path instead of
discovering scope mid-implementation.

| doc | question | decision |
|---|---|---|
| [TOTALSEGMENTATOR.md](TOTALSEGMENTATOR.md) | TotalSegmentator as a second volume source for `python/case_pipeline`, and how to handle the disc-segmentation gap? | **Option 1** (CT + geometric disc synthesis). Decided 2026-05-08. ~2.5 days of focused work to land a PR. |
| [SOFA.md](SOFA.md) | SOFA for tissue + bone physics on Quest 3? | **Defer** — Unity-native physics polish wins for now. Decided 2026-05-08. |
| [UNITY_PHYSICS_POLISH.md](UNITY_PHYSICS_POLISH.md) | What we're doing instead of SOFA. | Active plan. Voxel bone drilling → Obi softbody retraction → particle blood. |

These are not commitments — they are records of decisions. Each doc
ends with a "decision" section quoting the choice and the rationale,
so future-us (or a teammate, or a stream viewer) can see *why* we
picked a path.

When a decision changes, open a new PR that updates the doc; do not
rewrite history.
