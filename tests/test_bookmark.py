"""Mock integration tests for tap-impact bookmark (state) behaviour.

Patches ImpactClient.request so no live API is needed.
Uses sync_endpoint directly with a MagicMock client.
"""
import unittest
from unittest.mock import MagicMock, patch

try:
    from base import ImpactBaseTest
except ImportError:
    from tests.base import ImpactBaseTest

from tap_impact.discover import discover
from tap_impact.sync import sync_endpoint


def _make_mock_client(side_effects):
    """Return a MagicMock client whose get() iterates through side_effects."""
    mock_client = MagicMock()
    mock_client.base_url = "https://api.impact.com/Advertisers/mock_account_sid"
    if isinstance(side_effects, list):
        mock_client.get.side_effect = side_effects
    else:
        mock_client.get.return_value = side_effects
    return mock_client


class ImpactBookmarkTest(ImpactBaseTest, unittest.TestCase):
    """Verify bookmark behaviour for INCREMENTAL streams."""

    def _get_catalog(self):
        return discover(MagicMock(), {**self.config, "model_id": "mock_model"})

    def _invoice_records(self, created_date="2024-03-01T00:00:00Z"):
        """Minimal valid invoice record."""
        return [{
            "id": 1001,
            "created_date": created_date,
            "invoice_status": "paid",
        }]

    def _invoice_api_response(self, created_date="2024-03-01T00:00:00Z"):
        return {
            "@total": "1",
            "@pagesize": "100",
            "Invoices": self._invoice_records(created_date),
        }

    @patch("tap_impact.sync.singer.write_schema")
    @patch("tap_impact.sync.singer.write_state")
    @patch("tap_impact.sync.singer.messages.write_record")
    def test_bookmark_written_after_incremental_sync(self,
                                                     mock_write_record,
                                                     mock_write_state,
                                                     mock_write_schema):
        """Syncing an INCREMENTAL stream must write a bookmark to state."""
        catalog = self._get_catalog()
        state = {}
        mock_client = _make_mock_client([
            self._invoice_api_response("2024-03-01T00:00:00Z"),
            {},  # empty response to end pagination
        ])

        sync_endpoint(
            client=mock_client,
            catalog=catalog,
            state=state,
            config=self.config,
            start_date="2020-01-01T00:00:00Z",
            stream_name="invoices",
            path="Invoices",
            endpoint_config={"replication_method": "INCREMENTAL", "replication_keys": ["created_date"]},
            static_params={"StartDate": "<last_datetime>"},
            bookmark_field="created_date",
            bookmark_type="datetime",
            data_key="Invoices",
            id_fields=["id"],
            selected_streams=["invoices"],
        )

        self.assertIn("bookmarks", state)
        self.assertIn("invoices", state["bookmarks"])
        bookmark = state["bookmarks"]["invoices"]
        self.assertIsNotNone(bookmark)

    # Bookmark value matches the max replication key in the batch

    @patch("tap_impact.sync.singer.write_schema")
    @patch("tap_impact.sync.singer.write_state")
    @patch("tap_impact.sync.singer.messages.write_record")
    def test_bookmark_value_is_max_replication_key(self,
                                                   mock_write_record,
                                                   mock_write_state,
                                                   mock_write_schema):
        """The bookmark written must equal the maximum replication key seen."""
        catalog = self._get_catalog()
        state = {}
        # Two records: the later date should become the bookmark
        mock_client = _make_mock_client([
            {
                "@total": "2",
                "@pagesize": "100",
                "Invoices": [
                    {"id": 1, "created_date": "2024-01-01T00:00:00Z"},
                    {"id": 2, "created_date": "2024-06-01T00:00:00Z"},
                ],
            },
            {},
        ])

        sync_endpoint(
            client=mock_client,
            catalog=catalog,
            state=state,
            config=self.config,
            start_date="2020-01-01T00:00:00Z",
            stream_name="invoices",
            path="Invoices",
            endpoint_config={},
            static_params={},
            bookmark_field="created_date",
            bookmark_type="datetime",
            data_key="Invoices",
            id_fields=["id"],
            selected_streams=["invoices"],
        )

        bookmark = state["bookmarks"]["invoices"]
        # Bookmark should reflect the later record
        self.assertIn("2024-06-01", bookmark)

    # Second sync uses bookmark to filter older records

    @patch("tap_impact.sync.singer.write_schema")
    @patch("tap_impact.sync.singer.write_state")
    @patch("tap_impact.sync.singer.messages.write_record")
    def test_second_sync_only_emits_newer_records(self,
                                                  mock_write_record,
                                                  mock_write_state,
                                                  mock_write_schema):
        """A sync started from a bookmark should skip records before the bookmark."""
        catalog = self._get_catalog()
        mid_date = "2024-04-01T00:00:00Z"
        state = {"bookmarks": {"invoices": mid_date}}

        mock_client = _make_mock_client([
            {
                "@total": "2",
                "@pagesize": "100",
                "Invoices": [
                    {"id": 1, "created_date": "2024-01-01T00:00:00Z"},  # before bookmark
                    {"id": 2, "created_date": "2024-06-01T00:00:00Z"},  # after bookmark
                ],
            },
            {},
        ])

        records_written = []
        mock_write_record.side_effect = lambda s, r, time_extracted=None: records_written.append((s, r))

        sync_endpoint(
            client=mock_client,
            catalog=catalog,
            state=state,
            config=self.config,
            start_date="2020-01-01T00:00:00Z",
            stream_name="invoices",
            path="Invoices",
            endpoint_config={},
            static_params={},
            bookmark_field="created_date",
            bookmark_type="datetime",
            data_key="Invoices",
            id_fields=["id"],
            selected_streams=["invoices"],
        )

        for stream_name, record in records_written:
            if stream_name == "invoices":
                self.assertGreaterEqual(
                    record["created_date"], mid_date,
                    msg="Records before the bookmark should be filtered out",
                )

    # FULL_TABLE streams never write a bookmark

    @patch("tap_impact.sync.singer.write_schema")
    @patch("tap_impact.sync.singer.write_state")
    @patch("tap_impact.sync.singer.messages.write_record")
    def test_full_table_stream_writes_no_bookmark(self,
                                                  mock_write_record,
                                                  mock_write_state,
                                                  mock_write_schema):
        """FULL_TABLE streams have no bookmark_field and must NOT write to bookmarks."""
        catalog = self._get_catalog()
        state = {}
        mock_client = _make_mock_client([
            {
                "@total": "1",
                "@pagesize": "100",
                "Deals": [{"id": 1, "name": "Test Deal"}],
            },
            {},
        ])

        sync_endpoint(
            client=mock_client,
            catalog=catalog,
            state=state,
            config=self.config,
            start_date="2020-01-01T00:00:00Z",
            stream_name="deals",
            path="Deals",
            endpoint_config={},
            static_params={},
            bookmark_field=None,
            bookmark_type=None,
            data_key="Deals",
            id_fields=["id"],
            selected_streams=["deals"],
        )

        bookmarks = state.get("bookmarks", {})
        self.assertNotIn("deals", bookmarks)

    # State bookmarks do not interfere between streams

    @patch("tap_impact.sync.singer.write_schema")
    @patch("tap_impact.sync.singer.write_state")
    @patch("tap_impact.sync.singer.messages.write_record")
    def test_bookmark_only_updates_synced_stream(self,
                                                 mock_write_record,
                                                 mock_write_state,
                                                 mock_write_schema):
        """Writing a bookmark for invoices must not alter api_submissions bookmarks."""
        catalog = self._get_catalog()
        state = {
            "bookmarks": {
                "api_submissions": "2023-01-01T00:00:00Z",
            }
        }
        mock_client = _make_mock_client([
            self._invoice_api_response("2024-03-01T00:00:00Z"),
            {},
        ])

        sync_endpoint(
            client=mock_client,
            catalog=catalog,
            state=state,
            config=self.config,
            start_date="2020-01-01T00:00:00Z",
            stream_name="invoices",
            path="Invoices",
            endpoint_config={},
            static_params={},
            bookmark_field="created_date",
            bookmark_type="datetime",
            data_key="Invoices",
            id_fields=["id"],
            selected_streams=["invoices"],
        )

        # api_submissions bookmark must be unchanged
        self.assertEqual(
            state["bookmarks"].get("api_submissions"),
            "2023-01-01T00:00:00Z",
        )
