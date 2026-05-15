"""Mock integration tests for tap-impact pagination.

Verifies the tap keeps requesting pages until the API signals end-of-data.
"""
import unittest
from unittest.mock import MagicMock, patch

try:
    from base import ImpactBaseTest
except ImportError:
    from tests.base import ImpactBaseTest

from tap_impact.discover import discover
from tap_impact.sync import sync_endpoint


def _make_client(responses):
    c = MagicMock()
    c.base_url = "https://api.impact.com/Advertisers/mock_account_sid"
    c.get.side_effect = responses
    return c


class ImpactPaginationTest(ImpactBaseTest, unittest.TestCase):
    """Verify page-based pagination for streams that paginate."""

    def _get_catalog(self):
        return discover(self.config)

    # Multi-page sync fetches all pages

    @patch("tap_impact.sync.singer.write_schema")
    @patch("tap_impact.sync.singer.write_state")
    @patch("tap_impact.sync.singer.messages.write_record")
    def test_deals_fetches_multiple_pages(self, mock_write_record, mock_write_state, mock_write_schema):
        """Tap should keep fetching pages until @nextpageuri is absent."""
        page1_records = [{"id": i, "name": f"Deal {i}"} for i in range(1, 101)]
        page2_records = [{"id": i, "name": f"Deal {i}"} for i in range(101, 151)]

        responses = [
            # Page 1: has a next-page URI
            {
                "@total": "150",
                "@pagesize": "100",
                "@nextpageuri": "/Advertisers/mock_account_sid/Deals.json?Page=2",
                "Deals": page1_records,
            },
            # Page 2: no next-page URI → end of data
            {
                "@total": "150",
                "@pagesize": "100",
                "Deals": page2_records,
            },
        ]

        catalog = self._get_catalog()
        records_written = []
        mock_write_record.side_effect = lambda s, r, time_extracted=None: records_written.append(r)

        sync_endpoint(
            client=_make_client(responses),
            catalog=catalog,
            state={},
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

        # All 150 records across 2 pages should be written
        self.assertEqual(len(records_written), 150)

    @patch("tap_impact.sync.singer.write_schema")
    @patch("tap_impact.sync.singer.write_state")
    @patch("tap_impact.sync.singer.messages.write_record")
    def test_single_page_stops_after_one_request(self, mock_write_record, mock_write_state, mock_write_schema):
        """Single-page response: tap must stop after one request."""
        records = [{"id": i} for i in range(1, 26)]
        responses = [
            {
                "@total": "25",
                "@pagesize": "100",
                "MediaPartners": records,
            },
        ]

        catalog = self._get_catalog()
        client = _make_client(responses)
        records_written = []
        mock_write_record.side_effect = lambda s, r, time_extracted=None: records_written.append(r)

        sync_endpoint(
            client=client,
            catalog=catalog,
            state={},
            config=self.config,
            start_date="2020-01-01T00:00:00Z",
            stream_name="media_partners",
            path="MediaPartners",
            endpoint_config={},
            static_params={},
            bookmark_field=None,
            bookmark_type=None,
            data_key="MediaPartners",
            id_fields=["id"],
            selected_streams=["media_partners"],
        )

        self.assertEqual(len(records_written), 25)

    @patch("tap_impact.sync.singer.write_schema")
    @patch("tap_impact.sync.singer.write_state")
    @patch("tap_impact.sync.singer.messages.write_record")
    def test_empty_response_writes_zero_records(self, mock_write_record, mock_write_state, mock_write_schema):
        """An empty response must result in zero records written."""
        responses = [{"@total": "0", "@pagesize": "100", "PhoneNumbers": []}]
        catalog = self._get_catalog()
        records_written = []
        mock_write_record.side_effect = lambda s, r, time_extracted=None: records_written.append(r)

        result = sync_endpoint(
            client=_make_client(responses),
            catalog=catalog,
            state={},
            config=self.config,
            start_date="2020-01-01T00:00:00Z",
            stream_name="phone_numbers",
            path="PhoneNumbers",
            endpoint_config={},
            static_params={},
            bookmark_field=None,
            bookmark_type=None,
            data_key="PhoneNumbers",
            id_fields=["id"],
            selected_streams=["phone_numbers"],
        )

        self.assertEqual(len(records_written), 0)

    @patch("tap_impact.sync.singer.write_schema")
    @patch("tap_impact.sync.singer.write_state")
    @patch("tap_impact.sync.singer.messages.write_record")
    def test_three_page_incremental_stream(self, mock_write_record, mock_write_state, mock_write_schema):
        """Verify multi-page pagination works correctly for INCREMENTAL streams."""
        def _invoice_batch(start_id, count, date):
            return [{"id": start_id + i, "created_date": date} for i in range(count)]

        responses = [
            {
                "@total": "250",
                "@pagesize": "100",
                "@nextpageuri": "/Advertisers/x/Invoices.json?Page=2",
                "Invoices": _invoice_batch(1, 100, "2024-01-15T00:00:00Z"),
            },
            {
                "@total": "250",
                "@pagesize": "100",
                "@nextpageuri": "/Advertisers/x/Invoices.json?Page=3",
                "Invoices": _invoice_batch(101, 100, "2024-02-15T00:00:00Z"),
            },
            {
                "@total": "250",
                "@pagesize": "100",
                "Invoices": _invoice_batch(201, 50, "2024-03-15T00:00:00Z"),
            },
        ]

        catalog = self._get_catalog()
        records_written = []
        mock_write_record.side_effect = lambda s, r, time_extracted=None: records_written.append(r)
        state = {}

        sync_endpoint(
            client=_make_client(responses),
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

        self.assertEqual(len(records_written), 250)
        # Bookmark should be updated to the latest date seen
        self.assertIn("invoices", state.get("bookmarks", {}))
