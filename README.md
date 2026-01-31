# Team Coach

A coordination agent for distributed teams. Synthesizes Telegram channels, meeting transcripts, and documents into daily digests — running as a cron job on GitHub Actions.

This repository contains two versions of the same system — an exploration of how to build with LLMs.

## The Story

I started with 1000+ lines of carefully engineered code: Pydantic models, map/reduce pipelines, structured extraction, defensive programming. Everything I knew about building reliable software.

Then I deleted most of it.

The current system is ~60 lines of prompt. It works better.

**[Read the full story →](https://tj-zhang.com/blog/how-i-learned-to-stop-engineering-and-trust-the-model/)**

## What's Here

```
.
├── v1-overengineered/     # The first attempt: map/reduce, structured data, 1000+ LOC
│   ├── src/               # Pydantic models, extraction pipelines, reduce logic
│   ├── SPEC.md            # The elaborate specification
│   └── ...
│
└── [everything else]      # The evolved system: trust the model
    ├── config/            # The prompt that replaced most of the code
    ├── src/               # Telegram/GDrive integration
    └── .github/workflows/ # Cron job that runs the whole thing
```

## Comparing the Two

**v1 (over-engineered):**
- Text → structured data → processing → text
- Explicit schemas for people, projects, decisions
- Map phase extracts, reduce phase merges
- I tell the model exactly what to look for

**v2 (current):**
- Text → model → text
- "You're a team coach. Here's the context. Help the team."
- Model decides what matters
- Runs daily on GitHub Actions cron

The v1 code is preserved in `v1-overengineered/` if you want to see what I unlearned.

## The Interesting Part: GitHub Actions as AI Agent Infrastructure

The system runs entirely on GitHub Actions — no servers, no infrastructure:

1. **Daily cron trigger** — GitHub wakes up the workflow
2. **Data collection** — Pulls from Telegram API and Google Drive
3. **LLM generation** — Claude Code Action runs with file system access
4. **Persistent memory** — Agent memory stored in GDrive, downloaded/uploaded each run
5. **Distribution** — Uploads digest to GDrive, notifies via Telegram

Free compute, free orchestration. Just need API keys.

## Running It

```bash
# Install
uv sync

# Export from Telegram
synapse-pipeline export-telegram --start 2025-06-01 --end 2025-06-07

# The actual work happens in config/team_coach_prompt.md
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for system design.

---

*Built while learning that engineering instincts from deterministic systems don't always apply to LLMs.*
