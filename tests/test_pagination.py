"""Test tap can replicate multiple pages of data for streams that use pagination."""
from base import ImpactBaseTest
from tap_tester.base_suite_tests.pagination_test import PaginationTest


class ImpactPaginationTest(PaginationTest, ImpactBaseTest):
    """Ensure tap can replicate multiple pages of data for streams that use pagination."""

    @staticmethod
    def name():
        return "tap_tester_impact_pagination_test"

    def streams_to_test(self):
        # Exclude streams that are unlikely to have enough data for pagination,
        # and conversion_paths which requires a model_id.
        streams_to_exclude = {
            "company_information",
            "conversion_paths",
        }
        return self.expected_stream_names().difference(streams_to_exclude)
