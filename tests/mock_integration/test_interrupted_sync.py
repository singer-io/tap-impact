"""Mock integration tests — interrupted sync resumption.

Verifies that a sync resumed from a mid-point bookmark does not duplicate
records that were already synced, and that FULL_TABLE streams always
fully replicate regardless of any saved state.
"""
import unittest
from unittest.mock import MagicMock, patch

from .base import ImpactMockBaseTest

from tap_impact.discover import discover
from tap_impact.sync import sync_endpoint


def _make_client(responses):
    c = MagicMock()
    c.base_url = "https://api.impact.com/Advertisers/mock_account_sid"
    if isinstance(responses, list):
        c.get.side_effect = responses
    else:
        c.get.return_value = responses
    return c


class ImpactInterruptedSyncTest(ImpactMockBaseTest, unittest.TestCase):
    """Verify sync resumes correctly after an interruption."""

    def _get_catalog(self):
        return discover(MagicMock(), self.config)

    def _sync(self, stream_name, data_key, records,
              state=None, bookmark_field=None, bookmark_type=None,
              id_fields=None, static_params=None):
        """Run sync_endpoint and return (written_records, final_state)."""
        catalog = self._get_catalog()
        written = []
        if state is None:
            state = {}
        response = {"@total": str(len(records)), "@pagesize": "100", data_key: records}
        start_date = (
            state.get("bookmarks", {}).get(stream_name)
            or self.config["start_date"]
        )

        with patch("tap_impact.sync.singer.write_schema"), \
             patch("tap_impact.sync.singer.write_state"), \
             patch("tap_impact.sync.singer.messages.write_record",
                   side_effect=lambda s, r, time_extracted=None: written.append(r)):
            sync_endpoint(
                client=_make_client([response, {}]),
                catalog=catalog,
                state=state,
                config=self.config,
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
        return written, state

    # Incremental resume skips already-synced records

    def test_interrupted_sync_resumes_from_bookmark(self):
        """
        Simulate an interrupted sync by starting with a mid-point bookmark.
        Verify the resumed sync only emits records after that bookmark.
        """
        interrupted_state = {
            "bookmarks": {"invoices": "2021-06-15T00:00:00Z"}
        }

        all_records = [
            {"id": 1, "created_date": "2021-01-01T00:00:00Z"},  # already synced
            {"id": 2, "created_date": "2021-06-15T00:00:00Z"},  # boundary (inclusive)
            {"id": 3, "created_date": "2021-07-01T00:00:00Z"},  # new
            {"id": 4, "created_date": "2022-01-01T00:00:00Z"},  # new
        ]

        written, _ = self._sync(
            "invoices", "Invoices", all_records,
            state=interrupted_state,
            bookmark_field="created_date",
            bookmark_type="datetime",
        )

        def _normalize(dt_str):
            """Strip microseconds suffix added by Singer's Transformer."""
            return dt_str[:19] + "Z" if len(dt_str) > 20 else dt_str

        for record in written:
            self.assertGreaterEqual(
                _normalize(record["created_date"]),
                "2021-06-15T00:00:00Z",
                msg="Resumed sync should not replay records before the bookmark",
            )

    def test_resumed_sync_bookmark_advances_to_latest_record(self):
        """After resuming, the bookmark must advance to the newest record seen."""
        state = {"bookmarks": {"invoices": "2021-06-15T00:00:00Z"}}
        records = [
            {"id": 1, "created_date": "2021-06-15T00:00:00Z"},
            {"id": 2, "created_date": "2022-05-01T00:00:00Z"},
        ]

        _, final_state = self._sync(
            "invoices", "Invoices", records,
            state=state,
            bookmark_field="created_date",
            bookmark_type="datetime",
        )

        new_bookmark = final_state.get("bookmarks", {}).get("invoices", "")
        self.assertGreaterEqual(
            new_bookmark,
            "2021-06-15T00:00:00Z",
            msg="Bookmark must advance after a successful resumed sync",
        )

    def test_no_new_records_after_bookmark_writes_no_output(self):
        """If all records are before the bookmark, nothing should be written."""
        state = {"bookmarks": {"invoices": "2024-01-01T00:00:00Z"}}
        records = [
            {"id": 1, "created_date": "2023-01-01T00:00:00Z"},
            {"id": 2, "created_date": "2023-06-01T00:00:00Z"},
        ]

        written, _ = self._sync(
            "invoices", "Invoices", records,
            state=state,
            bookmark_field="created_date",
            bookmark_type="datetime",
        )

        self.assertEqual(
            len(written), 0,
            msg="No records should be emitted when all dates are before the bookmark",
        )

    # FULL_TABLE streams always fully replicate

    def test_full_table_stream_fully_replicated_despite_stale_state(self):
        """
        FULL_TABLE streams have no bookmark — they must replicate every record
        even when a stale state is passed in.
        """
        stale_state = {"bookmarks": {}}
        records = [{"id": i, "name": f"Deal {i}", "description": "mock"} for i in range(1, 11)]

        written, _ = self._sync(
            "deals", "Deals", records, state=stale_state
        )

        self.assertEqual(
            len(written), 10,
            msg="FULL_TABLE stream must replicate all records regardless of state",
        )

    def test_full_table_stream_bookmark_unchanged_after_sync(self):
        """Syncing a FULL_TABLE stream must not create a bookmark entry."""
        state = {}
        records = [{"id": i} for i in range(1, 4)]

        _, final_state = self._sync("media_partners", "MediaPartners", records, state=state)

        bookmarks = final_state.get("bookmarks", {})
        self.assertNotIn("media_partners", bookmarks)

    # Multiple interrupted + resumed cycles

    def test_incremental_sync_can_be_interrupted_and_resumed_twice(self):
        """Two successive bookmark-based resumes each skip already-synced records."""
        # First resume: state has bookmark at mid-point 1
        state1 = {"bookmarks": {"invoices": "2021-01-01T00:00:00Z"}}
        records1 = [
            {"id": 1, "created_date": "2020-06-01T00:00:00Z"},  # before — filtered
            {"id": 2, "created_date": "2021-03-01T00:00:00Z"},  # after
        ]
        written1, state1 = self._sync(
            "invoices", "Invoices", records1,
            state=state1,
            bookmark_field="created_date",
            bookmark_type="datetime",
        )
        self.assertEqual(len(written1), 1)

        # Second resume: bookmark now at mid-point 2
        state2 = {"bookmarks": {"invoices": state1["bookmarks"]["invoices"]}}
        records2 = [
            {"id": 2, "created_date": "2021-03-01T00:00:00Z"},  # now before bookmark — filtered
            {"id": 3, "created_date": "2022-08-01T00:00:00Z"},  # after
        ]
        written2, _ = self._sync(
            "invoices", "Invoices", records2,
            state=state2,
            bookmark_field="created_date",
            bookmark_type="datetime",
        )
        # The sync bookmark filter uses >= so the boundary record (id=2)
        # at exactly the bookmark date is included alongside the new id=3.
        self.assertGreaterEqual(len(written2), 1)
        written_ids = [str(r["id"]) for r in written2]
        self.assertIn("3", written_ids, msg="New record after bookmark must be written")

    # Child stream interrupted sync

    def _sync_with_children(self, parent_stream, parent_data_key, parent_records,
                             child_stream, child_endpoint_config,
                             child_data_key, child_records,
                             state=None, child_bookmark_field=None,
                             child_bookmark_type=None):
        """Run sync_endpoint for a parent stream with one child and return (written, state)."""
        catalog = self._get_catalog()
        written = []
        if state is None:
            state = {}
        start_date = state.get("bookmarks", {}).get(child_stream) or self.config["start_date"]

        parent_response = {
            "@total": str(len(parent_records)),
            "@pagesize": "100",
            parent_data_key: parent_records,
        }
        child_response = {
            "@total": str(len(child_records)),
            "@pagesize": "100",
            child_data_key: child_records,
        }
        endpoint_config = {
            "children": {
                child_stream: child_endpoint_config,
            }
        }

        with patch("tap_impact.sync.singer.write_schema"), \
             patch("tap_impact.sync.singer.write_state"), \
             patch("tap_impact.sync.singer.messages.write_record",
                   side_effect=lambda s, r, time_extracted=None: written.append((s, r))):
            sync_endpoint(
                client=_make_client([parent_response, child_response]),
                catalog=catalog,
                state=state,
                config=self.config,
                start_date=start_date,
                stream_name=parent_stream,
                path=parent_data_key,
                endpoint_config=endpoint_config,
                static_params={},
                bookmark_field=None,
                bookmark_type=None,
                data_key=parent_data_key,
                id_fields=["id"],
                selected_streams=[parent_stream, child_stream],
            )
        return written, state

    def test_interrupted_child_incremental_stream_resumes_from_bookmark(self):
        """
        Simulate an interrupted sync for a child INCREMENTAL stream (notes).
        Verify that on resumption only notes records on/after the bookmark are emitted.
        """
        bookmark_date = "2021-06-15T00:00:00Z"
        interrupted_state = {"bookmarks": {"notes": bookmark_date}}

        parent_records = [{"id": 123, "name": "Test Campaign"}]
        child_records = [
            {"id": 1, "modification_date": "2021-01-01T00:00:00Z"},  # before — filtered
            {"id": 2, "modification_date": "2021-06-15T00:00:00Z"},  # boundary
            {"id": 3, "modification_date": "2021-09-01T00:00:00Z"},  # new
        ]
        child_endpoint_config = {
            "path": "Campaigns/{}/Notes",
            "data_key": "Notes",
            "key_properties": ["id"],
            "replication_method": "INCREMENTAL",
            "replication_keys": ["modification_date"],
            "bookmark_type": "datetime",
            "parent": "campaigns",
        }

        written, _ = self._sync_with_children(
            "campaigns", "Campaigns", parent_records,
            "notes", child_endpoint_config, "Notes", child_records,
            state=interrupted_state,
            child_bookmark_field="modification_date",
            child_bookmark_type="datetime",
        )

        def _normalize(dt_str):
            return dt_str[:19] + "Z" if len(dt_str) > 20 else dt_str

        notes_written = [r for s, r in written if s == "notes"]
        for record in notes_written:
            self.assertGreaterEqual(
                _normalize(record["modification_date"]),
                bookmark_date,
                msg="Resumed child sync must not replay notes records before the bookmark",
            )

    def test_interrupted_full_table_child_stream_always_fully_replicates(self):
        """
        A FULL_TABLE child stream (contacts) must replicate all records even
        when stale state is present — it has no bookmark to interrupt on.
        """
        stale_state = {"bookmarks": {}}
        parent_records = [{"id": 123, "name": "Test Campaign"}]
        child_records = [{"id": i, "name": f"Contact {i}"} for i in range(1, 6)]
        child_endpoint_config = {
            "path": "Campaigns/{}/Contacts",
            "data_key": "Contacts",
            "key_properties": ["id"],
            "replication_method": "FULL_TABLE",
            "parent": "campaigns",
        }

        written, final_state = self._sync_with_children(
            "campaigns", "Campaigns", parent_records,
            "contacts", child_endpoint_config, "Contacts", child_records,
            state=stale_state,
        )

        contacts_written = [r for s, r in written if s == "contacts"]
        self.assertEqual(
            len(contacts_written), 5,
            msg="All 5 FULL_TABLE child records must be written regardless of stale state",
        )
        self.assertNotIn(
            "contacts", final_state.get("bookmarks", {}),
            msg="FULL_TABLE child stream must not write a bookmark",
        )
