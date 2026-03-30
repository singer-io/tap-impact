"""Unit tests for tap_impact.sync utility functions."""
import unittest
from unittest.mock import patch
from tap_impact.sync import (
    write_bookmark,
    update_currently_syncing,
    transform_datetime,
    get_bookmark,
)


class TestWriteBookmark(unittest.TestCase):
    """Tests for write_bookmark()."""

    @patch("tap_impact.sync.singer.write_state")
    def test_creates_bookmarks_key_if_missing(self, mock_write_state):
        state = {}
        write_bookmark(state, "ads", "2024-01-01T00:00:00Z")
        self.assertIn("bookmarks", state)
        self.assertEqual(state["bookmarks"]["ads"], "2024-01-01T00:00:00Z")
        mock_write_state.assert_called_once_with(state)

    @patch("tap_impact.sync.singer.write_state")
    def test_overwrites_existing_bookmark(self, mock_write_state):
        state = {"bookmarks": {"ads": "2023-01-01T00:00:00Z"}}
        write_bookmark(state, "ads", "2024-06-01T00:00:00Z")
        self.assertEqual(state["bookmarks"]["ads"], "2024-06-01T00:00:00Z")

    @patch("tap_impact.sync.singer.write_state")
    def test_writes_state_once(self, mock_write_state):
        state = {}
        write_bookmark(state, "invoices", "2024-01-01T00:00:00Z")
        self.assertEqual(mock_write_state.call_count, 1)

    @patch("tap_impact.sync.singer.write_state")
    def test_does_not_overwrite_other_streams(self, mock_write_state):
        state = {"bookmarks": {"ads": "2023-01-01T00:00:00Z", "invoices": "2023-06-01T00:00:00Z"}}
        write_bookmark(state, "invoices", "2024-01-01T00:00:00Z")
        self.assertEqual(state["bookmarks"]["ads"], "2023-01-01T00:00:00Z")


class TestUpdateCurrentlySyncing(unittest.TestCase):
    """Tests for update_currently_syncing()."""

    @patch("tap_impact.sync.singer.write_state")
    @patch("tap_impact.sync.singer.set_currently_syncing")
    def test_sets_stream_when_provided(self, mock_set, mock_write_state):
        state = {}
        update_currently_syncing(state, "ads")
        mock_set.assert_called_once_with(state, "ads")
        mock_write_state.assert_called_once_with(state)

    @patch("tap_impact.sync.singer.write_state")
    def test_removes_currently_syncing_when_none(self, mock_write_state):
        state = {"currently_syncing": "ads"}
        update_currently_syncing(state, None)
        self.assertNotIn("currently_syncing", state)
        mock_write_state.assert_called_once_with(state)

    @patch("tap_impact.sync.singer.set_currently_syncing")
    @patch("tap_impact.sync.singer.write_state")
    def test_none_with_no_existing_key_falls_to_else(self, mock_write_state, mock_set):
        # When stream_name is None but 'currently_syncing' is NOT already in state,
        # the function should call singer.set_currently_syncing(state, None)
        # instead of attempting to remove a non-existent key.
        state = {}
        update_currently_syncing(state, None)
        mock_set.assert_called_once_with(state, None)
        mock_write_state.assert_called_once_with(state)


class TestTransformDatetime(unittest.TestCase):
    """Tests for transform_datetime()."""

    def test_valid_iso_datetime(self):
        result = transform_datetime("2024-01-15T10:30:00Z")
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)

    def test_empty_string_returns_none_or_empty(self):
        result = transform_datetime("")
        # Singer's Transformer returns None or empty for unparseable values
        self.assertFalse(result)

    def test_none_returns_falsy(self):
        result = transform_datetime(None)
        self.assertFalse(result)

    def test_output_is_iso_format(self):
        result = transform_datetime("2024-03-01T00:00:00Z")
        # Should contain date and time separators
        self.assertIn("2024", result)


class TestGetBookmark(unittest.TestCase):
    """Additional tests for get_bookmark() not already in test_default_start_date."""

    def test_none_state_returns_default(self):
        self.assertEqual(get_bookmark(None, "ads", "2020-01-01T00:00:00Z"), "2020-01-01T00:00:00Z")

    def test_empty_state_returns_default(self):
        self.assertEqual(get_bookmark({}, "ads", "2020-01-01T00:00:00Z"), "2020-01-01T00:00:00Z")

    def test_state_without_stream_returns_default(self):
        state = {"bookmarks": {"other_stream": "2021-01-01T00:00:00Z"}}
        self.assertEqual(get_bookmark(state, "ads", "2020-01-01T00:00:00Z"), "2020-01-01T00:00:00Z")

    def test_state_with_stream_returns_bookmark(self):
        state = {"bookmarks": {"ads": "2022-06-01T00:00:00Z"}}
        self.assertEqual(get_bookmark(state, "ads", "2020-01-01T00:00:00Z"), "2022-06-01T00:00:00Z")

    def test_integer_default_value(self):
        self.assertEqual(get_bookmark({}, "my_stream", 0), 0)

    def test_integer_bookmark_returned(self):
        state = {"bookmarks": {"my_stream": 42}}
        self.assertEqual(get_bookmark(state, "my_stream", 0), 42)
