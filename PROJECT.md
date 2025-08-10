# Synapse Pipeline - Project Context

## Purpose

Synapse Pipeline solves the **context fragmentation problem** in remote teams. When team members work across time zones using different communication channels (Telegram, meetings, docs), important information gets lost or siloed. This tool automatically collects, synthesizes, and distributes team updates to keep everyone aligned.

## ⚠️ Manual Requirement

**Meeting notes must be manually moved to the coordination folder!**
- Meeting organizers must copy notes to: `Flashbots_X/Coordination Agent/context_data/`
- Without this step, the pipeline won't see meeting data
- This is a known limitation that requires human coordination

## Current Status

### ✅ MVP Complete
All core functionality is implemented and working:
- Telegram API export via telethon
- Google Drive sync via rclone  
- Claude-based digest generation
- Telegram bot notifications
- GitHub Actions automation

### 🚀 Ready for Production
The pipeline can be deployed immediately. See README.md for setup instructions.

## Current Limitations

### Stateless Operation
- No memory between runs - can't detect what's new vs. already processed
- May reprocess same content if still within time window

### No Source Attribution
- Digest doesn't indicate where information originated
- Users can't trace back to original discussions

### Limited Observability
- Minimal logging of what was processed
- Hard to debug when issues occur

## Roadmap

### ✅ Phase 1: Observability (Complete)
- Added detailed logging of processed files
- Show specific Telegram channels with message counts
- Show Google Drive files downloaded with sizes
- Enhanced workflow summary for debugging

### ✅ Phase 2: Source Citation (Complete)
- Updated prompt to include inline source references
- Added citation format for channels and documents
- Improved accountability through attribution

### Phase 3: State Management
- Implement memory between runs
- Detect and highlight changes since last digest
- Avoid reprocessing unchanged content

## Technical Documentation

- **Architecture**: See [ARCHITECTURE.md](./ARCHITECTURE.md) for system design and data flow
- **Setup**: See [README.md](./README.md) for installation and configuration
- **Development**: See [CLAUDE.md](./CLAUDE.md) for development guidance
