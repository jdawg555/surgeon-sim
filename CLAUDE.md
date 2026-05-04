# CLAUDE.md

Project memory for Claude Code working on **surgeon-sim**. Loaded on every
session; keep it short.

## What this project is

An open-source spine-surgery simulator for Meta Quest 3. Passion project,
**not** a clinical product, **not** a company, **not** affiliated with any
medical organization. Built in public with Claude Code, demoed live on
Twitch.

Mannequin and phantom demos only. No PHI. No clinical-decision use.

## Stream-safety rules (read every session)

Sessions on this project are **streamed live on Twitch**. The stream
captures the terminal, the editor, and the browser. Treat that surface
the same as posting screenshots to a public forum.

**Never read, paste, or echo any of the following in a tool call whose
output will be visible in the assistant transcript:**

- Files matching `.env*`, `secrets*`, `*.pem`, `*.key`, `id_rsa*`,
  `*.cred*`, `*.token*`, `service-account*.json`, `firebase*adminsdk*.json`
- Any string that looks like an API key, OAuth token, JWT, or Personal
  Access Token (long opaque strings starting with `sk-`, `gh[ps]_`,
  `ghu_`, `ghs_`, `xox[bp]-`, `wit_`, etc.)
- Wit.ai server access tokens, Meta Quest organization IDs, Meta XR
  registry credentials
- Personal email addresses, phone numbers, physical addresses, real
  patient names, MRNs, dates of birth, DICOM headers from real cases
- Stripe keys, AWS keys, GCP service-account JSON, Cloudflare API tokens
- Anything from `~/.ssh/`, `~/.aws/`, `~/.config/gcloud/`,
  `~/.cloudflared/`, `~/AppData/Roaming/...credentials*`
- Output of `gh auth token`, `npm whoami --token`, `git credential fill`

**If a tool call would surface any of the above, stop and tell the user
out loud ("I was about to open something sensitive, holding off") rather
than running it.** Do not attempt to "preview" sensitive files.

**Do not commit or paste:**

- Real Wit.ai tokens — use the placeholder `WIT_AI_TOKEN_PLACEHOLDER`
  in any example or doc; the surgeon configures their own locally.
- Real DICOM cases or any patient-identifiable medical data. The
  literature-default measurements in `python/spineoptimizer/core/models.py`
  (`DiscSpaceMeasurement.from_literature`) are anatomy averages and are
  fine to use on stream.
- Author identities other than the GitHub noreply set in this repo's
  local `.git/config`. Do not pass `-c user.email=...` overrides.

## Voice / tone for any docs or copy I write here

- Plain, direct, no marketing hype.
- "AI assists; humans confirm." Carry that thesis through.
- No clinical claims. The README and docs already say "mannequin demo
  only, no PHI" — keep that disclaimer visible on anything new.
- Avoid em-dashes; prefer periods, commas, or colons. Avoid implant
  manufacturer names in narrative copy. The catalog data file lists
  real SKUs (sourced from FDA filings) and that's fine — but don't
  drop "Stryker" / "Medtronic" into prose.

## Architecture in one paragraph

Three layers. **Domain + data** (`unity/Assets/Scripts/Domain/`,
`unity/Assets/Resources/implant_catalog.json`, `python/spineoptimizer/core/`).
**Deterministic core** (`unity/Assets/Scripts/Fitting/FitEngine.cs`,
`python/spineoptimizer/fitting/fit_engine.py`, `python/core/`). **XR
layer** (`unity/Assets/Scripts/Anchoring/`, `Voice/`, `Step/`, `Stream/`,
`DragonflySession.cs`). The lower layers have zero Unity dependencies and
are unit-testable headset-free; the XR layer is the only thing that
touches Meta XR SDK.

When in doubt about where new code goes: if it could compile in a console
app, it belongs in the lower layers.

## Workflow on this repo

- `main` is protected; push to a branch and open a PR.
- Squash-merge with `gh pr merge --squash --admin --delete-branch` once
  the user has approved.
- After merging: `git checkout main && git pull --ff-only`.
- The Unity project lives in `unity/`. Local Unity-generated folders
  (`Library/`, `Temp/`, `Logs/`, `UserSettings/`) are gitignored — never
  add them.
