#!/bin/bash

# Generate newsletter using Claude Code as an agent with tools

echo "Launching Claude Code agent to generate newsletter..."
echo ""

# Pipe the agent prompt/instructions to claude with allowed tools
cat newsletter_agent_prompt.md | claude -p "Execute the provided instructions" \
  --allowedTools "LS" "Read" "Write" \
  --verbose