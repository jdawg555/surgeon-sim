# research/

Decision documents for non-trivial integrations. Each doc lays out the
question, the realistic options, the rough effort, and a recommendation,
so we can commit a focused session to the right path instead of
discovering scope mid-implementation.

| doc | question |
|---|---|
| [TOTALSEGMENTATOR.md](TOTALSEGMENTATOR.md) | Should TotalSegmentator be the second volume source for `python/case_pipeline`, and how do we handle the disc-segmentation gap? |
| [SOFA.md](SOFA.md) | Is SOFA the right physics layer for surgeon-sim, and how do we bridge it to Quest 3? |

These are not commitments. Each doc ends with a "decision needed"
section — once those are answered, the doc stays as a record, and the
implementation goes in its own PR.
