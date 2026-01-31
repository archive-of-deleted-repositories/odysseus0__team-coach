# Team Coach

A coordination agent for distributed teams. Synthesizes Telegram channels, meeting transcripts, and documents into daily digests.

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
    ├── src/               # Telegram/GDrive integration, feedback loops
    └── ...
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
- Feedback loop: team corrects the bot, corrections accumulate

The v1 code is preserved in `v1-overengineered/` if you want to see what I unlearned.

## Running It

The current system integrates with Telegram and Google Drive. See the setup docs:

- [Architecture overview](ARCHITECTURE.md)
- [Feedback system design](FEEDBACK_CORRECTION_DESIGN.md)

```bash
# Install
uv sync

# Export from Telegram
synapse-pipeline export-telegram --start 2025-06-01 --end 2025-06-07

# Generate digest (the actual work happens in config/team_coach_prompt.md)
synapse-pipeline generate-digest
```

## The Prompt

The core of the system is in `config/team_coach_prompt.md`. It's short. That's the point.

---

*Built while learning that engineering instincts from deterministic systems don't always apply to LLMs.*
