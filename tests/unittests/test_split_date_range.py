import unittest
from datetime import datetime, timedelta
from parameterized import parameterized

from tap_impact.sync import split_date_range

# Define DEFAULT_WINDOW_SIZE to be 45 days
DEFAULT_WINDOW_SIZE = 45


class TestSplitDateRange(unittest.TestCase):

    @parameterized.expand([
        # Test case 1: Date range with only one range (start_date and end_date within the same window)
        ("single_range",
         datetime(2024, 1, 1),
         datetime(2024, 1, 30),  # Only one 45-day window
         [(datetime(2024, 1, 1), datetime(2024, 1, 30))]),

        # Test case 2: Date range with exactly two windows
        ("two_ranges",
         datetime(2024, 1, 1),
         datetime(2024, 3, 15),  # 45 days + 45 days window
         [
             (datetime(2024, 1, 1), datetime(2024, 2, 15)),
             (datetime(2024, 2, 15), datetime(2024, 3, 15))  # Updated start date to 16th
         ]),

        # Test case 3: Date range with exactly three windows
        ("three_ranges",
         datetime(2024, 1, 1),
         datetime(2024, 4, 10),  # 45 days + 45 days + 45 days
         [
             (datetime(2024, 1, 1), datetime(2024, 2, 15)),
             (datetime(2024, 2, 15), datetime(2024, 3, 31)),
             (datetime(2024, 3, 31), datetime(2024, 4, 10))  # Updated start date to 3rd
         ]),

        # Test case 4: Date range where end_date is before start_date (empty range)
        ("no_range",
         datetime(2024, 3, 15),
         datetime(2024, 1, 1),  # end_date is before start_date
         []),

        # Test case 5: Date range with start_date and end_date being the same (single range)
        ("same_date",
         datetime(2024, 1, 1),
         datetime(2024, 1, 1),  # start_date == end_date
         []),  # Expecting an empty range

        # Test case 6: Date range spanning multiple months (more than two windows)
        ("multiple_ranges",
         datetime(2024, 1, 1),
         datetime(2024, 6, 10),  # 45 days + 45 days + 45 days + 45 days
         [
             (datetime(2024, 1, 1), datetime(2024, 2, 15)),
             (datetime(2024, 2, 15), datetime(2024, 3, 31)),
             (datetime(2024, 3, 31), datetime(2024, 5, 15)),
             (datetime(2024, 5, 15), datetime(2024, 6, 10))  # Updated start date to 16th
         ]),
    ])
    def test_split_date_range(self, name, start_date, end_date, expected_ranges):
        """Test splitting a date range into smaller ranges."""
        actual_ranges = split_date_range(start_date, end_date)

        # Compare the actual result with the expected result
        self.assertEqual(actual_ranges, expected_ranges)

        # Compare the length of actual_ranges and expected_ranges
        self.assertEqual(len(actual_ranges), len(expected_ranges), f"Length mismatch for {name}. "
                                                                   f"Expected {len(expected_ranges)} but got {len(actual_ranges)}.")
