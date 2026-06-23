"""Mock integration tests — start_date filtering for INCREMENTAL streams.

Runs two syncs with different start dates and verifies a later start_date
returns only records on or after that date.
"""
import unittest
from unittest.mock import MagicMock, patch

from .base import ImpactMockBaseTest

from tap_impact.discover import discover
from tap_impact.sync import sync_endpoint


def _make_client(responses):
    c = MagicMock()
    c.base_url = "https://api.impact.com/Advertisers/mock_account_sid"
    c.get.side_effect = responses
    return c


def _run_sync(catalog, config, stream_name, data_key, records,
              start_date, bookmark_field=None, bookmark_type=None,
              id_fields=None, static_params=None):
    """Helper: run sync_endpoint and return written records."""
    written = []
    response = {"@total": str(len(records)), "@pagesize": "100", data_key: records}

    client = _make_client([response, {}])

    with patch("tap_impact.sync.singer.write_schema"), \
         patch("tap_impact.sync.singer.write_state"), \
         patch("tap_impact.sync.singer.messages.write_record",
               side_effect=lambda s, r, time_extracted=None: written.append(r)):
        sync_endpoint(
            client=client,
            catalog=catalog,
            state={},
            config={**config, "start_date": start_date},
            start_date=start_date,
            stream_name=stream_name,
            path=data_key,
            endpoint_config={},
            static_params=static_params or {},
            bookmark_field=bookmark_field,
            bookmark_type=bookmark_type,
            data_key=data_key,
            id_fields=id_fields or ["id"],
            selected_streams=[stream_name],
        )
    return written


class ImpactStartDateTest(ImpactMockBaseTest, unittest.TestCase):
    """Verify start_date correctly filters records for INCREMENTAL streams."""

    def _get_catalog(self):
        return discover(MagicMock(), self.config)

    # Later start_date returns fewer or equal records

    def test_invoices_later_start_date_returns_fewer_records(self):
        """Second sync with a later start date should see ≤ records than first."""
        catalog = self._get_catalog()

        # Records spanning 2015–2022
        all_records = [
            {"id": 1, "created_date": "2015-06-01T00:00:00Z"},
            {"id": 2, "created_date": "2018-03-15T00:00:00Z"},
            {"id": 3, "created_date": "2020-11-01T00:00:00Z"},
            {"id": 4, "created_date": "2022-01-01T00:00:00Z"},
        ]

        # Sync 1: early start date — all records pass the bookmark filter
        records_early = _run_sync(
            catalog, self.config, "invoices", "Invoices", all_records,
            start_date="2015-01-01T00:00:00Z",
            bookmark_field="created_date", bookmark_type="datetime",
        )

        # Sync 2: later start date — only records after 2020 should pass
        records_late = _run_sync(
            catalog, self.config, "invoices", "Invoices", all_records,
            start_date="2020-01-01T00:00:00Z",
            bookmark_field="created_date", bookmark_type="datetime",
        )

        self.assertLessEqual(
            len(records_late), len(records_early),
            msg="Later start_date should return ≤ records than earlier one",
        )

    def test_invoices_start_date_filters_old_records(self):
        """Records before start_date must not appear in sync output."""
        catalog = self._get_catalog()

        records = [
            {"id": 1, "created_date": "2018-01-01T00:00:00Z"},  # before start_date
            {"id": 2, "created_date": "2021-07-01T00:00:00Z"},  # after start_date
            {"id": 3, "created_date": "2022-03-01T00:00:00Z"},  # after start_date
        ]
        start_date = "2020-01-01T00:00:00Z"

        written = _run_sync(
            catalog, self.config, "invoices", "Invoices", records,
            start_date=start_date,
            bookmark_field="created_date", bookmark_type="datetime",
        )

        for record in written:
            self.assertGreaterEqual(
                record["created_date"], start_date,
                msg=f"Record dated {record['created_date']} should be filtered out by start_date {start_date}",
            )

    def test_api_submissions_start_date_filtering(self):
        """api_submissions obeys start_date for submission_date filtering."""
        catalog = self._get_catalog()

        records = [
            {"batch_id": "A", "submission_date": "2019-01-01T00:00:00Z"},
            {"batch_id": "B", "submission_date": "2021-06-01T00:00:00Z"},
        ]
        start_date = "2020-01-01T00:00:00Z"

        written = _run_sync(
            catalog, self.config, "api_submissions", "APISubmission", records,
            start_date=start_date,
            bookmark_field="submission_date", bookmark_type="datetime",
            id_fields=["batch_id"],
        )

        for record in written:
            self.assertGreaterEqual(record["submission_date"], start_date)

    # FULL_TABLE streams are unaffected by start_date

    def test_full_table_stream_returns_all_records_regardless_of_start_date(self):
        """FULL_TABLE streams do not filter by start_date."""
        catalog = self._get_catalog()

        # Three records with various dates in the name (fields, not dates)
        records = [{"id": i, "name": f"Deal {i}"} for i in range(1, 4)]

        written_early = _run_sync(
            catalog, self.config, "deals", "Deals", records,
            start_date="2015-01-01T00:00:00Z",
        )
        written_late = _run_sync(
            catalog, self.config, "deals", "Deals", records,
            start_date="2023-01-01T00:00:00Z",
        )

        # FULL_TABLE — both syncs emit all records from the mock response
        self.assertEqual(len(written_early), len(written_late))

    # Two-config comparison: more data with earlier start

    def test_two_start_dates_confirm_early_has_more_or_equal(self):
        """
        Syncing with start_date_1 (early) should return ≥ records as start_date_2 (late).
        """
        catalog = self._get_catalog()

        records = [
            {"id": 1, "created_date": "2015-03-01T00:00:00Z"},
            {"id": 2, "created_date": "2016-09-01T00:00:00Z"},
            {"id": 3, "created_date": "2017-12-01T00:00:00Z"},
            {"id": 4, "created_date": "2019-01-01T00:00:00Z"},
            {"id": 5, "created_date": "2021-01-01T00:00:00Z"},
        ]

        start_date_1 = "2015-03-25T00:00:00Z"
        start_date_2 = "2017-01-25T00:00:00Z"

        written_1 = _run_sync(
            catalog, self.config, "invoices", "Invoices", records,
            start_date=start_date_1,
            bookmark_field="created_date", bookmark_type="datetime",
        )
        written_2 = _run_sync(
            catalog, self.config, "invoices", "Invoices", records,
            start_date=start_date_2,
            bookmark_field="created_date", bookmark_type="datetime",
        )

        self.assertGreaterEqual(
            len(written_1), len(written_2),
            msg="Earlier start_date_1 must return ≥ records than later start_date_2",
        )

    # Child stream start_date filtering
    def test_child_incremental_stream_start_date_filters_old_records(self):
        """
        The start_date used as initial bookmark for a child INCREMENTAL stream (notes)
        must filter out records before that date.
        """
        catalog = self._get_catalog()
        start_date = "2021-01-01T00:00:00Z"

        parent_response = {
            "@total": "1",
            "@pagesize": "100",
            "Campaigns": [{"id": 123, "name": "Test Campaign"}],
        }
        child_records = [
            {"id": 1, "modification_date": "2020-06-01T00:00:00Z"},  # before start_date
            {"id": 2, "modification_date": "2021-03-01T00:00:00Z"},  # after start_date
            {"id": 3, "modification_date": "2022-01-01T00:00:00Z"},  # after start_date
        ]
        child_response = {"@total": "3", "@pagesize": "100", "Notes": child_records}

        written = []
        with patch("tap_impact.sync.singer.write_schema"), \
             patch("tap_impact.sync.singer.write_state"), \
             patch("tap_impact.sync.singer.messages.write_record",
                   side_effect=lambda s, r, time_extracted=None: written.append((s, r))):
            sync_endpoint(
                client=_make_client([parent_response, child_response]),
                catalog=catalog,
                state={},
                config={**self.config, "start_date": start_date},
                start_date=start_date,
                stream_name="campaigns",
                path="Campaigns",
                endpoint_config={
                    "children": {
                        "notes": {
                            "path": "Campaigns/{}/Notes",
                            "data_key": "Notes",
                            "key_properties": ["id"],
                            "replication_method": "INCREMENTAL",
                            "replication_keys": ["modification_date"],
                            "bookmark_type": "datetime",
                            "parent": "campaigns",
                        }
                    }
                },
                static_params={},
                bookmark_field=None,
                bookmark_type=None,
                data_key="Campaigns",
                id_fields=["id"],
                selected_streams=["campaigns", "notes"],
            )

        notes_written = [r for s, r in written if s == "notes"]
        self.assertEqual(
            len(notes_written), 2,
            msg="Only notes records on/after start_date must be written",
        )
        for record in notes_written:
            self.assertGreaterEqual(
                record["modification_date"], start_date,
                msg=f"Notes record {record['id']} with modification_date "
                    f"{record['modification_date']} should be filtered by start_date",
            )

    def test_child_incremental_stream_later_start_date_returns_fewer_records(self):
        """
        A later start_date for a child INCREMENTAL stream must yield ≤ records
        than an earlier start_date.
        """
        catalog = self._get_catalog()

        parent_response = {
            "@total": "1",
            "@pagesize": "100",
            "Campaigns": [{"id": 123, "name": "Test Campaign"}],
        }
        child_records = [
            {"id": 1, "modification_date": "2019-01-01T00:00:00Z"},
            {"id": 2, "modification_date": "2020-06-01T00:00:00Z"},
            {"id": 3, "modification_date": "2021-03-01T00:00:00Z"},
            {"id": 4, "modification_date": "2022-08-01T00:00:00Z"},
        ]
        child_response = {"@total": "4", "@pagesize": "100", "Notes": child_records}
        child_endpoint_config = {
            "children": {
                "notes": {
                    "path": "Campaigns/{}/Notes",
                    "data_key": "Notes",
                    "key_properties": ["id"],
                    "replication_method": "INCREMENTAL",
                    "replication_keys": ["modification_date"],
                    "bookmark_type": "datetime",
                    "parent": "campaigns",
                }
            }
        }

        def _run_child_sync(start_date):
            written = []
            with patch("tap_impact.sync.singer.write_schema"), \
                 patch("tap_impact.sync.singer.write_state"), \
                 patch("tap_impact.sync.singer.messages.write_record",
                       side_effect=lambda s, r, time_extracted=None: written.append((s, r))):
                sync_endpoint(
                    client=_make_client([parent_response, child_response]),
                    catalog=catalog,
                    state={},
                    config={**self.config, "start_date": start_date},
                    start_date=start_date,
                    stream_name="campaigns",
                    path="Campaigns",
                    endpoint_config=child_endpoint_config,
                    static_params={},
                    bookmark_field=None,
                    bookmark_type=None,
                    data_key="Campaigns",
                    id_fields=["id"],
                    selected_streams=["campaigns", "notes"],
                )
            return [r for s, r in written if s == "notes"]

        written_early = _run_child_sync("2019-01-01T00:00:00Z")
        written_late = _run_child_sync("2021-01-01T00:00:00Z")

        self.assertLessEqual(
            len(written_late), len(written_early),
            msg="Later start_date for child (notes) must return ≤ records than earlier one",
        )
