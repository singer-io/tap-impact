"""Test tap sets a bookmark and respects it for the next sync of a stream."""
from base import ImpactBaseTest
from tap_tester.base_suite_tests.bookmark_test import BookmarkTest


class ImpactBookmarkTest(BookmarkTest, ImpactBaseTest):
    """Test tap sets a bookmark and respects it for the next sync of a stream."""

    start_date = "2020-01-01T00:00:00Z"

    @staticmethod
    def name():
        return "tap_tester_impact_bookmark_test"

    def streams_to_test(self):
        # Restrict to INCREMENTAL streams that have reliable test data
        streams_to_exclude = {
            "conversion_paths",
        }
        return self.incremental_streams().difference(streams_to_exclude)

    def incremental_streams(self):
        return {
            stream for stream, meta in self.expected_metadata().items()
            if meta[self.REPLICATION_METHOD] == self.INCREMENTAL
        }

    def calculate_new_bookmarks(self):
        """Return bookmarks that result in some records being synced in sync 2."""
        return {
            "invoices": "2020-06-01T00:00:00Z",
            "api_submissions": "2020-06-01T00:00:00Z",
            "ftp_file_submissions": "2020-06-01T00:00:00Z",
            "actions": "2020-06-01T00:00:00Z",
            "action_inquiries": "2020-06-01T00:00:00Z",
            "action_updates": "2020-06-01T00:00:00Z",
            "notes": "2020-06-01T00:00:00Z",
        }
