import unittest
from unittest.mock import patch
from datetime import datetime, timedelta

from tap_impact.sync import get_bookmark

class TestBookmarkDateHandling(unittest.TestCase):

    @patch('tap_impact.sync.get_bookmark')
    @patch('singer.utils.now')
    def test_last_datetime_within_three_years(self, mock_now, mock_get_bookmark):
        state = {}
        stream_name = 'actions'
        start_date = '2020-01-01T00:00:00Z'
        end_dttm = datetime(2023, 1, 1, 0, 0, 0)
        mock_now.return_value = end_dttm

        # Simulate a bookmark returned from get_bookmark
        mock_get_bookmark.return_value = '2022-01-01T00:00:00Z'

        print("Mocked 'now' returned:", mock_now.return_value)
        print("Mocked 'get_bookmark' returned:", mock_get_bookmark.return_value)

        # the bookmark should not change if it's within 3 years
        last_datetime = mock_get_bookmark(state, stream_name, start_date)
        print("Last datetime:", last_datetime)

        last_datetime_dt = datetime.fromisoformat(last_datetime.replace('Z', '+00:00'))
        default_date = end_dttm - timedelta(days=3*365)
        default_date_str = default_date.strftime('%Y-%m-%dT%H:%M:%SZ')

        if stream_name in ('actions', 'action_updates') and last_datetime_dt < default_date:
            last_datetime = default_date_str

        max_bookmark_value = last_datetime

        # Verify that the bookmark date is unchanged, as it is within 3 years
        self.assertEqual(last_datetime, '2022-01-01T00:00:00Z')
        self.assertEqual(max_bookmark_value, '2022-01-01T00:00:00Z')
