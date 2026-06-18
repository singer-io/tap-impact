"""Mock integration tests for tap-impact stream discovery.

Calls tap_impact.discover.discover() directly — no HTTP calls needed
since discovery only reads local schema JSON files.
"""
import unittest
from unittest.mock import MagicMock
from singer import metadata

from .base import ImpactBaseTest

from tap_impact.discover import discover


class ImpactDiscoveryTest(ImpactBaseTest, unittest.TestCase):
    """Verify discover() returns the correct catalog without any API calls."""

    def _get_catalog(self):
        """Run discover with mock config (no model_id → conversion_paths excluded)."""
        return discover(MagicMock(), self.config)

    def _get_catalog_with_model(self):
        """Run discover with a model_id to include conversion_paths."""
        return discover(MagicMock(), {**self.config, "model_id": "mock_model_123"})

    def test_discovery_returns_expected_streams(self):
        """Verify all expected streams (minus conversion_paths) are discovered."""
        catalog = self._get_catalog()
        discovered = {s.tap_stream_id for s in catalog.streams}
        # conversion_paths requires model_id; without it, it is excluded
        expected = self.expected_stream_names() - {"conversion_paths"}
        self.assertEqual(discovered, expected)

    def test_discovery_includes_conversion_paths_when_model_id_set(self):
        """Verify conversion_paths appears when model_id is in config."""
        catalog = self._get_catalog_with_model()
        discovered = {s.tap_stream_id for s in catalog.streams}
        self.assertIn("conversion_paths", discovered)

    def test_discovery_stream_count_without_model_id(self):
        """24 of 25 streams are returned when no model_id is provided."""
        catalog = self._get_catalog()
        self.assertEqual(len(catalog.streams), len(self.expected_stream_names()) - 1)

    def test_discovery_primary_keys(self):
        """Verify key_properties match expected for every discovered stream."""
        catalog = self._get_catalog_with_model()
        expected = self.expected_metadata()
        for stream in catalog.streams:
            with self.subTest(stream=stream.tap_stream_id):
                self.assertEqual(
                    set(stream.key_properties or []),
                    expected[stream.tap_stream_id][self.PRIMARY_KEYS],
                )

    def test_discovery_schema_has_properties(self):
        """Every stream schema must have at least one property."""
        catalog = self._get_catalog()
        for stream in catalog.streams:
            with self.subTest(stream=stream.tap_stream_id):
                schema_dict = stream.schema.to_dict()
                self.assertIn("properties", schema_dict)
                self.assertGreater(len(schema_dict["properties"]), 0)

    def test_discovery_replication_method(self):
        """Verify forced-replication-method matches expected for every stream."""
        catalog = self._get_catalog_with_model()
        expected = self.expected_metadata()
        for stream in catalog.streams:
            with self.subTest(stream=stream.tap_stream_id):
                mdata = metadata.to_map(stream.metadata)
                actual = (
                    metadata.get(mdata, (), "forced-replication-method")
                    or metadata.get(mdata, (), "replication-method")
                )
                self.assertEqual(
                    actual,
                    expected[stream.tap_stream_id][self.REPLICATION_METHOD],
                )

    def test_discovery_replication_keys_for_incremental_streams(self):
        """INCREMENTAL streams must expose valid-replication-keys metadata."""
        catalog = self._get_catalog_with_model()
        expected = self.expected_metadata()
        for stream in catalog.streams:
            stream_meta = expected.get(stream.tap_stream_id, {})
            if stream_meta.get(self.REPLICATION_METHOD) != "INCREMENTAL":
                continue
            with self.subTest(stream=stream.tap_stream_id):
                mdata = metadata.to_map(stream.metadata)
                rep_keys = metadata.get(mdata, (), "valid-replication-keys") or []
                self.assertGreater(
                    len(rep_keys), 0,
                    msg=f"{stream.tap_stream_id} should have valid-replication-keys",
                )

    def test_full_table_streams_have_no_replication_keys(self):
        """FULL_TABLE streams must NOT have valid-replication-keys metadata."""
        catalog = self._get_catalog_with_model()
        expected = self.expected_metadata()
        for stream in catalog.streams:
            stream_meta = expected.get(stream.tap_stream_id, {})
            if stream_meta.get(self.REPLICATION_METHOD) != "FULL_TABLE":
                continue
            with self.subTest(stream=stream.tap_stream_id):
                mdata = metadata.to_map(stream.metadata)
                rep_keys = metadata.get(mdata, (), "valid-replication-keys") or []
                self.assertEqual(
                    set(rep_keys),
                    set(),
                    msg=f"{stream.tap_stream_id} should not have replication keys",
                )

    def test_discovery_child_streams_have_parent_metadata(self):
        """Child streams must carry parent-tap-stream-id metadata."""
        catalog = self._get_catalog_with_model()
        expected = self.expected_metadata()
        for stream in catalog.streams:
            sname = stream.tap_stream_id
            if self.PARENT not in expected.get(sname, {}):
                continue
            with self.subTest(stream=sname):
                mdata = metadata.to_map(stream.metadata)
                parent_val = metadata.get(mdata, (), "parent-tap-stream-id")
                expected_parent = expected[sname][self.PARENT]
                self.assertEqual(
                    parent_val,
                    expected_parent,
                    msg=f"{sname}: expected parent '{expected_parent}', got '{parent_val}'",
                )

    def test_discovery_parent_streams_have_no_parent_metadata(self):
        """Top-level streams must NOT have parent-tap-stream-id metadata."""
        catalog = self._get_catalog_with_model()
        expected = self.expected_metadata()
        for stream in catalog.streams:
            sname = stream.tap_stream_id
            if self.PARENT in expected.get(sname, {}):
                continue  # skip child streams
            with self.subTest(stream=sname):
                mdata = metadata.to_map(stream.metadata)
                parent_val = metadata.get(mdata, (), "parent-tap-stream-id")
                self.assertIsNone(
                    parent_val,
                    msg=f"Top-level stream {sname} should not have parent metadata",
                )

    def test_tap_stream_id_matches_stream_name(self):
        """tap_stream_id and stream name should be identical."""
        catalog = self._get_catalog()
        for entry in catalog.streams:
            self.assertEqual(entry.tap_stream_id, entry.stream)
