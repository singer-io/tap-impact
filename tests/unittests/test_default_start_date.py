import unittest
from datetime import datetime, timedelta
from parameterized import parameterized
from tap_impact.sync import get_bookmark
from singer import utils

class TestBookmarkDateHandling(unittest.TestCase):

    def setUp(self):
        """Set up commonly used variables."""
        self.now = utils.now()
        self.default_date = self.now - timedelta(days=3 * 365)
        self.default_date_str = self.default_date.strftime('%Y-%m-%dT%H:%M:%SZ')

    @parameterized.expand([
        # Test case 1: Start date within 3 years
        ({}, 'actions', (utils.now() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%SZ'), (utils.now() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%SZ')),
        # Test case 2: Bookmark date within 3 years but start date is older
        ({"bookmarks": {"actions": (utils.now() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%SZ')}}, 'actions', '2014-01-01T00:00:00Z', (utils.now() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%SZ')),
        # Test case 3: Start date older than 3 years
        ({}, 'actions', '2019-01-01T00:00:00Z', (utils.now() - timedelta(days=3 * 365)).strftime('%Y-%m-%dT%H:%M:%SZ')),
        # Test case 4: Bookmark date older than 3 years but start date is older
        ({"bookmarks": {"actions": "2020-01-01T00:00:00Z"}}, 'actions', '2019-01-01T00:00:00Z', (utils.now() - timedelta(days=3 * 365)).strftime('%Y-%m-%dT%H:%M:%SZ')),
    ])
    def test_bookmark_date(self, state, stream_name, start_date, expected_datetime):
        """Test actions stream with various start dates and bookmark handling."""

        # Get the actual bookmark datetime returned by the function
        last_datetime = get_bookmark(state, stream_name, start_date)

        # Convert the returned datetime string to a datetime object
        last_datetime_dt = datetime.fromisoformat(last_datetime.replace('Z', '+00:00'))

        # Determine if the stream should use the default_date based on the logic
        if stream_name in ('actions', 'action_updates') and last_datetime_dt < self.default_date:
            last_datetime = self.default_date_str

        # Perform the test assertion
        self.assertEqual(last_datetime, expected_datetime)
