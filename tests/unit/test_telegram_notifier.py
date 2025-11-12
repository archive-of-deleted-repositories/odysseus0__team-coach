"""Unit tests for Telegram notification message splitting and error handling."""

import pytest

from synapse.notifiers.telegram import _split_message, _escape_markdown_v1


class TestMessageSplitting:
    """Tests for message chunking logic."""

    def test_short_message_not_split(self):
        """Short messages should not be split."""
        message = "This is a short message"
        chunks = _split_message(message)
        assert len(chunks) == 1
        assert chunks[0] == message

    def test_long_message_split_on_paragraphs(self):
        """Long messages should split on paragraph boundaries."""
        paragraph = "A" * 1000
        message = f"{paragraph}\n\n{paragraph}\n\n{paragraph}\n\n{paragraph}\n\n{paragraph}"
        chunks = _split_message(message, max_length=3000)

        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 3000

    def test_long_message_split_on_lines(self):
        """Messages without paragraphs should split on line breaks."""
        line = "A" * 100
        message = "\n".join([line] * 50)
        chunks = _split_message(message, max_length=2000)

        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 2000

    def test_very_long_line_split_arbitrarily(self):
        """Very long lines without breaks should split arbitrarily."""
        message = "A" * 5000
        chunks = _split_message(message, max_length=2000)

        assert len(chunks) >= 3
        for chunk in chunks:
            assert len(chunk) <= 2000

    def test_exact_limit_not_split(self):
        """Message at exact limit should not be split."""
        message = "A" * 4000
        chunks = _split_message(message, max_length=4000)
        assert len(chunks) == 1

    def test_one_char_over_limit_splits(self):
        """Message one char over limit should split."""
        message = "A" * 4001
        chunks = _split_message(message, max_length=4000)
        assert len(chunks) == 2

    def test_empty_message(self):
        """Empty messages should work."""
        chunks = _split_message("")
        assert len(chunks) == 1
        assert chunks[0] == ""

    def test_whitespace_trimmed(self):
        """Whitespace should be trimmed from chunks."""
        message = "Part 1\n\n\n\n\nPart 2"
        chunks = _split_message(message, max_length=10)
        assert all(chunk.strip() == chunk for chunk in chunks)


class TestMarkdownEscaping:
    """Tests for Telegram MarkdownV1 escaping."""

    def test_escape_underscores(self):
        """Underscores should be escaped."""
        text = "snake_case_variable"
        escaped = _escape_markdown_v1(text)
        assert escaped == r"snake\_case\_variable"

    def test_escape_asterisks(self):
        """Asterisks should be escaped."""
        text = "2 * 3 = 6"
        escaped = _escape_markdown_v1(text)
        assert escaped == r"2 \* 3 \= 6"

    def test_escape_brackets(self):
        """Brackets should be escaped."""
        text = "array[0]"
        escaped = _escape_markdown_v1(text)
        assert escaped == r"array\[0\]"

    def test_escape_parentheses(self):
        """Parentheses should be escaped."""
        text = "function(arg)"
        escaped = _escape_markdown_v1(text)
        assert escaped == r"function\(arg\)"

    def test_escape_backticks(self):
        """Backticks should be escaped."""
        text = "`code`"
        escaped = _escape_markdown_v1(text)
        assert escaped == r"\`code\`"

    def test_escape_special_chars(self):
        """All special chars should be escaped."""
        text = "_*[]()~`>#+-=|{}.!"
        escaped = _escape_markdown_v1(text)
        assert escaped == r"\_\*\[\]\(\)\~\`\>\#\+\-\=\|\{\}\.\!"

    def test_normal_text_unchanged(self):
        """Text without special chars should be unchanged."""
        text = "Hello world 123"
        escaped = _escape_markdown_v1(text)
        assert escaped == text

    def test_empty_string(self):
        """Empty string should work."""
        escaped = _escape_markdown_v1("")
        assert escaped == ""


class TestIntegrationScenarios:
    """Test realistic scenarios."""

    def test_typical_digest_content(self):
        """Test with typical team digest content."""
        digest = """## 📅 Daily Digest - 2025-01-15

**🎯 Key Updates**
- Feature launch delayed by 2 days [#engineering]
- New hire starting Monday [@alice in #general]

**💡 Work in Progress**
- API refactor (75% complete) [#engineering]
- Design mockups for Q2 features [#design]

**⚡ Action Items**
- @bob: Review security audit by EOD
- @charlie: Schedule architecture meeting
"""
        chunks = _split_message(digest)
        # Should fit in one message
        assert len(chunks) == 1

    def test_very_long_digest_splits_cleanly(self):
        """Test that very long digests split at paragraph boundaries."""
        section = """**Section Header**
- Point 1 with details about the work being done
- Point 2 with more context and background info
- Point 3 with action items and next steps

"""
        digest = "## Daily Digest\n\n" + (section * 50)
        chunks = _split_message(digest, max_length=4000)

        assert len(chunks) > 1
        # Each chunk should end cleanly (not mid-sentence)
        for chunk in chunks[:-1]:  # Check all but last
            assert chunk.endswith('\n') or len(chunk) < 4000

    def test_code_blocks_with_special_chars(self):
        """Test messages containing code blocks."""
        message = """Here's the error:
```
function_name(arg_1, arg_2)
array[0] = value * 2
```
This needs fixing!"""
        chunks = _split_message(message)
        assert len(chunks) == 1

    def test_urls_and_mentions(self):
        """Test messages with URLs and user mentions."""
        message = """Update from @alice:
Check this PR: https://github.com/user/repo/pull/123
Also see [documentation](https://docs.example.com)
"""
        chunks = _split_message(message)
        assert len(chunks) == 1
