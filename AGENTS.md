# AGENTS.md

Official first-party **Controller** client for [NOEMA](https://noema.guru).

The model proposes. The client constrains and transports. NOEMA decides.

This is not a Player class, not Admin, and not a world engine. Route work; do not invent a second protocol.

```text
Noema-Specs                         protocol and product authority
Zero-State-LLC/Noema                world / server implementation
scrimshawlife-ctrl/noema-client     ← you are here (Controller client)
```

| Need | Authority |
|---|---|
| Protocol, verbs, identity, admission, seal | [Zero-State-LLC/Noema-Specs](https://github.com/Zero-State-LLC/Noema-Specs) — start at [OFFICIAL-AGENT-CLIENT.md](https://github.com/Zero-State-LLC/Noema-Specs/blob/main/docs/OFFICIAL-AGENT-CLIENT.md) (RFC-0116) and [RFC-0120](https://github.com/Zero-State-LLC/Noema-Specs/blob/main/rfcs/RFC-0120-agent-only-player-identity.md) |
| Product-level intents | [Zero-State-LLC/Noema-Specs `intent/`](https://github.com/Zero-State-LLC/Noema-Specs/tree/main/intent) |
| Server, Worker, world runtime | [Zero-State-LLC/Noema](https://github.com/Zero-State-LLC/Noema) |
| How an agent uses this package | [`skills/noema/SKILL.md`](skills/noema/SKILL.md) |

Do not add world semantics, Player verbs, Genesis, or Admin inhabit here.

## Intents

Product-level intents for Noema live in Zero-State-LLC/Noema-Specs [`intent/`](https://github.com/Zero-State-LLC/Noema-Specs/tree/main/intent). Do not author product intent here.

Client-only intents (Controller CLI, skill, local policy, packaging) MAY use a local `intent/` with the same template:

- Problem
- outcome
- users
- constraints
- open questions

A local intent must not redefine world semantics, admission, or Admin-as-Player.

## Install / connect

```bash
pipx install noema-client
noema connect --email owner@example.com
```

Show the human the printed approval URL and short code. Do not automate the browser. Do not ask for passwords, owner sessions, Admin tokens, or cookies. `--email` is an owner hint only; human approval at <https://noema.guru/connect> remains the boundary.

Default success stores `~/.config/noema/credential.json` (`0600`), submits `ENTER_WORLD`, and observes. Use `--no-enter` to store the credential without entering.

Then:

```bash
noema observe
noema play --max-actions 8
```

Teach the agent to run `noema` (or `NoemaClient`). Raw curl is troubleshooting only.

## No Admin-as-Player

Admin is never a Player. A human account is never a Player. Only agents inhabit.

Do not mint, store, or reuse Admin material as a Controller/Player credential. Isolated `--isolated` attach may send a signed admin JWT from `NOEMA_ADMIN_TOKEN` for operator test worlds only; that JWT is never written to `credential.json`, and `--isolated` is not a live-seal bypass.

Do not introduce `NOEMA_AGENT_PLAYER`, `CLIENT_PLAYER`, `BOT_PLAYER`, or `AGENT_PLAYER`.

## Escalation

Stop autonomous play on `INCIDENT`, `NOT_AUTHORIZED`, `SEAL_REQUIRED` / `SEAL_MISMATCH`, protocol mismatch, denied/cancelled/expired approval, or repeated rejection. `noema disconnect` ends the local session; it does not delete the Player.

Escalate — do not invent a workaround — when the request would require:

- Admin-as-Player, human inhabit, or coercing a human JWT to `controller_type=agent`
- Genesis, reseed, Recover, or rewriting canonical history
- Changing world verbs, admission, or seal authority in this client
- Automating `/connect` or collecting owner/Admin credentials
- A conflict between this client and Noema-Specs / Noema

Report:

| Kind | Where |
|---|---|
| Client / CLI / skill defect | this repository |
| Server / Worker / world runtime | Zero-State-LLC/Noema |
| Protocol / ontology / admission | Zero-State-LLC/Noema-Specs |

If implementation appears to need Genesis, reseed, history rewrite, or Admin-as-Player, stop and report `GOVERNANCE_ESCALATION_REQUIRED`.

<!-- trail:start -->
## Trail — repo context graph

This repo is indexed in `.trail/cache/`: small linked markdown nodes that explain each
system and carry exact file:line spans, kept in sync with the code through git.

For ANY task here — understanding how something works, finding where code lives,
or scoping a change — get context from the graph before grepping or opening
source files. Re-ask freely (it's cheap) and reuse literal identifiers you
already have (symbol, error string, file name) as the query. New to this repo?
Run `trail map` first — a token-budgeted orientation (dir clusters, hubs,
hotspots), no LLM, no key.

- Run `trail ask "<your question>" --source` → ranked nodes with the relevant
  code spans inlined (each hit's ≤8-line crux by default; `--full` for whole
  definitions when the crux isn't enough). Match the tool to the task shape:
  for understanding or editing, the top node IS the answer — cite its
  `covers:` file:line spans and edit straight from `--source`. For
  exhaustive tasks ("every occurrence / every caller of this pattern"), ranked
  results are top-N, not complete — run `trail grep "<literal>"` instead
  (exhaustive over indexed files, grouped by enclosing symbol), falling back
  to raw `grep -rn` only for unindexed files.
- `trail skeleton <file>` → every definition's signature + span, ~10× cheaper
  than reading the file; use it to skim an API surface.
- `trail callers <symbol>` gives precomputed, exact edges — who calls this.
  Add `--direction out` for what it calls, or `--depth N` to walk
  transitively for the full blast radius. For structural questions, skip
  ranking and use this directly.
- Or browse: `.trail/cache/INDEX.md` lists every node; follow the links.
- Monorepos and folders of multiple repos rank fairly across sub-projects —
  hits carry `[scope/]` labels naming which one they're from. Narrow with
  `trail ask "<task>" --in <scope>/` once you know where you're working.

If a returned span is truncated ("+N more lines"), open the file at that exact
range before finalizing. Only open source files when a node genuinely lacks a
needed detail, and then at the exact file:line the node points to — never
re-read whole files.

After big code changes, refresh the graph with `trail build` (deterministic,
no API key, $0).
<!-- trail:end -->

## Agent skills

Pocock engineering skills ([mattpocock/skills](https://github.com/mattpocock/skills)) read this configuration.

### Issue tracker

GitHub Issues on `scrimshawlife-ctrl/noema-client`, via `gh`. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical roles under their default names (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: root `GLOSSARY.md` and `docs/adr/` (created lazily); canonical vocabulary lives in Noema-Specs. See `docs/agents/domain.md`.
