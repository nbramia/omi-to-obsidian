"""Tests for frontmatter writing."""
from omi_sync.frontmatter_writer import write_frontmatter


class TestFrontmatterWriter:
    def test_stable_key_ordering(self):
        """Keys are written in deterministic order."""
        data = {"z_key": "last", "a_key": "first", "date": "2026-01-10"}
        result1 = write_frontmatter(data)
        result2 = write_frontmatter(data)
        assert result1 == result2
        # Keys should be sorted alphabetically
        assert result1.index("a_key") < result1.index("date") < result1.index("z_key")

    def test_yaml_format(self):
        """Output is valid YAML frontmatter."""
        data = {"date": "2026-01-10", "source": "omi"}
        result = write_frontmatter(data)
        assert result.startswith("---\n")
        assert result.endswith("---\n")

    def test_list_values(self):
        """List values are properly formatted."""
        data = {"people": ["Alice", "Bob"]}
        result = write_frontmatter(data)
        assert "people:" in result
        assert "Alice" in result
        assert "Bob" in result

    def test_boolean_values(self):
        """Boolean values are properly formatted."""
        data = {"omi_sync": True}
        result = write_frontmatter(data)
        assert "omi_sync: true" in result
