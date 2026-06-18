"""Test tap respects start date for incremental streams."""
from base import ImpactBaseTest
from tap_tester.base_suite_tests.start_date_test import StartDateTest


class ImpactStartDateTest(StartDateTest, ImpactBaseTest):
    """Instantiate start date according to the desired data set and run the test."""

    @staticmethod
    def name():
        return "tap_tester_impact_start_date_test"

    def streams_to_test(self):
        # Exclude conversion_paths (requires model_id).
        streams_to_exclude = {
            "conversion_paths",
        }
        return self.expected_stream_names().difference(streams_to_exclude)

    @property
    def start_date_1(self):
        """Start date before all test data."""
        return "2020-01-01T00:00:00Z"

    @property
    def start_date_2(self):
        """Start date in the middle of test data range."""
        return "2021-01-01T00:00:00Z"
