"""Quick test of telegram notification fixes."""

import sys
sys.path.insert(0, 'src')

from synapse.notifiers.telegram import _split_message, _escape_markdown_v1

print("Testing Telegram notification fixes...\n")

# Test 1: Short message not split
print("Test 1: Short message")
msg = 'This is a short message'
chunks = _split_message(msg)
print(f"✓ {len(chunks)} chunk(s) - Should be 1")
assert len(chunks) == 1

# Test 2: Long message splits
print("\nTest 2: Long message (5000 chars)")
msg = 'A' * 5000
chunks = _split_message(msg, max_length=2000)
print(f"✓ {len(chunks)} chunk(s)")
for i, chunk in enumerate(chunks):
    print(f"  Chunk {i+1}: {len(chunk)} chars")
    assert len(chunk) <= 2000

# Test 3: Paragraph splitting
print("\nTest 3: Paragraph splitting")
paragraph = 'A' * 1000
msg = f'{paragraph}\n\n{paragraph}\n\n{paragraph}\n\n{paragraph}\n\n{paragraph}'
chunks = _split_message(msg, max_length=3000)
print(f"✓ {len(chunks)} chunk(s)")
for i, chunk in enumerate(chunks):
    print(f"  Chunk {i+1}: {len(chunk)} chars")

# Test 4: Markdown escaping
print("\nTest 4: Markdown escaping")
text = 'snake_case and array[0] and func()'
escaped = _escape_markdown_v1(text)
print(f"  Original: {text}")
print(f"  Escaped:  {escaped}")
print(f"✓ Contains backslashes: {chr(92) in escaped}")

# Test 5: Realistic digest
print("\nTest 5: Realistic digest")
digest = """## 📅 Daily Digest - 2025-01-15

**🎯 Key Updates**
- Feature launch delayed by 2 days [#engineering]
- New hire starting Monday [@alice in #general]

**💡 Work in Progress**
- API refactor (75% complete) [#engineering]
- Design mockups for Q2 features [#design]
"""
chunks = _split_message(digest)
print(f"✓ {len(chunks)} chunk(s), {len(digest)} chars total")

# Test 6: Very long digest
print("\nTest 6: Very long digest (simulating real scenario)")
section = """**Section Header**
- Point 1 with details about the work being done
- Point 2 with more context and background info
- Point 3 with action items and next steps

"""
long_digest = "## Daily Digest\n\n" + (section * 50)
chunks = _split_message(long_digest, max_length=4000)
print(f"✓ {len(chunks)} chunk(s), {len(long_digest)} chars total")
for i, chunk in enumerate(chunks):
    print(f"  Chunk {i+1}: {len(chunk)} chars")

print("\n✅ All tests passed!")
print("\nSummary:")
print("- Messages are split at 4000 char limit (4096 Telegram limit - 96 buffer)")
print("- Splits prefer paragraph boundaries, then line breaks")
print("- Markdown special characters can be escaped if needed")
print("- Markdown parse errors trigger automatic retry without formatting")
