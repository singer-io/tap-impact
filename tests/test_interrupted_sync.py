"""Test tap can resume from an interrupted sync."""
from base import ImpactBaseTest
from tap_tester.base_suite_tests.interrupted_sync_test import InterruptedSyncTest


class ImpactInterruptedSyncTest(InterruptedSyncTest, ImpactBaseTest):
    """Test tap sets a bookmark and respects it for the next sync of a stream."""

    @staticmethod
    def name():
        return "tap_tester_impact_interrupted_sync_test"

    def streams_to_test(self):
        # Restrict to INCREMENTAL streams; exclude conversion_paths (requires model_id)
        streams_to_exclude = {
            "conversion_paths",
        }
        return self.expected_stream_names().difference(streams_to_exclude)

    def manipulate_state(self):
        """Manipulate state to simulate an interrupted sync.

        Sets the currently_syncing stream and partial bookmarks to test
        that the tap can resume from where it left off.
        """
        return {
            "currently_syncing": "invoices",
            "bookmarks": {
                "api_submissions": "2020-06-01T00:00:00Z",
                "invoices": "2020-06-01T00:00:00Z",
            },
        }
