"""Tests for slugify helper."""
from omi_sync.slugify import slugify


class TestSlugify:
    def test_basic_slugify(self):
        assert slugify("Hello World") == "hello-world"

    def test_special_characters_removed(self):
        assert slugify("Meeting: Q1 Planning!") == "meeting-q1-planning"

    def test_multiple_spaces_collapsed(self):
        assert slugify("Too   Many   Spaces") == "too-many-spaces"

    def test_unicode_handled(self):
        assert slugify("Café Meeting") == "cafe-meeting"

    def test_empty_string(self):
        assert slugify("") == "untitled"

    def test_max_length(self):
        result = slugify("A" * 100, max_length=50)
        assert len(result) <= 50

    def test_only_special_chars(self):
        assert slugify("!!!@@@###") == "untitled"
