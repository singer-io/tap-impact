import unittest
from unittest.mock import MagicMock, patch

from tap_impact.client import ImpactForbiddenError
from tap_impact.discover import (
    _apply_access_checks,
    _check_stream_access,
    _get_child_to_parent_map,
    _prune_inaccessible_children,
    discover,
)
from tap_impact.streams import STREAMS


class TestGetChildToParentMap(unittest.TestCase):
    """Tests for _get_child_to_parent_map helper."""

    def test_all_children_are_mapped(self):
        mapping = _get_child_to_parent_map()
        for parent_name, parent_config in STREAMS.items():
            for child_name in parent_config.get('children', {}):
                self.assertIn(child_name, mapping)
                self.assertEqual(mapping[child_name], parent_name)

    def test_parent_streams_not_in_map(self):
        mapping = _get_child_to_parent_map()
        for parent_name in STREAMS:
            self.assertNotIn(parent_name, mapping)


class TestCheckStreamAccess(unittest.TestCase):
    """Tests for _check_stream_access helper."""

    def setUp(self):
        self.client = MagicMock()

    def test_returns_true_when_accessible(self):
        self.client.request.return_value = {'data': []}
        result = _check_stream_access(self.client, 'ads', 'Ads')
        self.assertTrue(result)
        self.client.request.assert_called_once_with(
            'GET', path='Ads', params={'PageSize': 1}, endpoint='ads'
        )

    def test_returns_false_on_forbidden(self):
        self.client.request.side_effect = ImpactForbiddenError('403 Forbidden')
        result = _check_stream_access(self.client, 'ads', 'Ads')
        self.assertFalse(result)

    def test_non_forbidden_exception_propagates(self):
        self.client.request.side_effect = Exception('Server Error')
        with self.assertRaises(Exception):
            _check_stream_access(self.client, 'ads', 'Ads')


class TestPruneInaccessibleChildren(unittest.TestCase):
    """Tests for _prune_inaccessible_children."""

    def test_child_removed_when_parent_absent(self):
        schemas = {'actions': {}, 'contacts': {}}
        field_metadata = {'actions': [], 'contacts': []}
        # 'campaigns' (parent of actions and contacts) is not in schemas
        child_to_parent = {'actions': 'campaigns', 'contacts': 'campaigns'}

        _prune_inaccessible_children(schemas, field_metadata, child_to_parent)

        self.assertNotIn('actions', schemas)
        self.assertNotIn('contacts', schemas)
        self.assertNotIn('actions', field_metadata)
        self.assertNotIn('contacts', field_metadata)

    def test_child_kept_when_parent_present(self):
        schemas = {'campaigns': {}, 'actions': {}}
        field_metadata = {'campaigns': [], 'actions': []}
        child_to_parent = {'actions': 'campaigns'}

        _prune_inaccessible_children(schemas, field_metadata, child_to_parent)

        self.assertIn('campaigns', schemas)
        self.assertIn('actions', schemas)

    def test_unrelated_streams_not_affected(self):
        schemas = {'ads': {}, 'invoices': {}}
        field_metadata = {'ads': [], 'invoices': []}
        child_to_parent = {'actions': 'campaigns'}

        _prune_inaccessible_children(schemas, field_metadata, child_to_parent)

        self.assertIn('ads', schemas)
        self.assertIn('invoices', schemas)


class TestApplyAccessChecks(unittest.TestCase):
    """Tests for _apply_access_checks."""

    def _make_schemas(self, stream_names):
        return {name: {} for name in stream_names}

    def _make_metadata(self, stream_names):
        return {name: [] for name in stream_names}

    def test_all_accessible_no_change(self):
        client = MagicMock()
        client.request.return_value = {}

        parent_names = list(STREAMS.keys())
        schemas = self._make_schemas(parent_names)
        field_metadata = self._make_metadata(parent_names)
        original_count = len(schemas)

        _apply_access_checks(client, schemas, field_metadata)

        self.assertEqual(len(schemas), original_count)

    def test_one_parent_inaccessible_removed(self):
        client = MagicMock()

        def mock_request(method, path, params, endpoint):
            if endpoint == 'ads':
                raise ImpactForbiddenError('403')
            return {}

        client.request.side_effect = mock_request

        schemas = {'ads': {}, 'campaigns': {}, 'invoices': {}}
        field_metadata = {'ads': [], 'campaigns': [], 'invoices': []}

        _apply_access_checks(client, schemas, field_metadata)

        self.assertNotIn('ads', schemas)
        self.assertIn('campaigns', schemas)
        self.assertIn('invoices', schemas)

    def test_parent_inaccessible_cascades_to_children(self):
        client = MagicMock()

        def mock_request(method, path, params, endpoint):
            if endpoint == 'campaigns':
                raise ImpactForbiddenError('403')
            return {}

        client.request.side_effect = mock_request

        # Include campaigns and a few of its children plus an unrelated stream
        schemas = {'campaigns': {}, 'actions': {}, 'contacts': {}, 'ads': {}}
        field_metadata = {'campaigns': [], 'actions': [], 'contacts': [], 'ads': []}

        _apply_access_checks(client, schemas, field_metadata)

        self.assertNotIn('campaigns', schemas)
        self.assertNotIn('actions', schemas)
        self.assertNotIn('contacts', schemas)
        self.assertIn('ads', schemas)

    def test_all_parents_inaccessible_raises(self):
        client = MagicMock()
        client.request.side_effect = ImpactForbiddenError('403')

        parent_names = list(STREAMS.keys())
        schemas = self._make_schemas(parent_names)
        field_metadata = self._make_metadata(parent_names)

        with self.assertRaises(ImpactForbiddenError):
            _apply_access_checks(client, schemas, field_metadata)

    def test_no_inaccessible_streams_no_warning(self):
        client = MagicMock()
        client.request.return_value = {}

        schemas = {'ads': {}}
        field_metadata = {'ads': []}

        # Should not raise and not log warning - just verify it runs cleanly
        _apply_access_checks(client, schemas, field_metadata)
        self.assertIn('ads', schemas)


class TestDiscover(unittest.TestCase):
    """Integration-style tests for the discover() function."""

    @patch('tap_impact.discover._apply_access_checks')
    @patch('tap_impact.discover.get_schemas')
    def test_discover_builds_catalog_for_accessible_streams(
        self, mock_get_schemas, mock_access_checks
    ):
        mock_get_schemas.return_value = (
            {
                'ads': {
                    'type': 'object',
                    'properties': {'id': {'type': ['null', 'string']}},
                }
            },
            {'ads': []},
        )
        mock_access_checks.return_value = None  # no-op

        client = MagicMock()
        config = {'start_date': '2024-01-01T00:00:00Z'}

        catalog = discover(client, config)

        stream_ids = [s.tap_stream_id for s in catalog.streams]
        self.assertIn('ads', stream_ids)

    @patch('tap_impact.discover._apply_access_checks')
    @patch('tap_impact.discover.get_schemas')
    def test_discover_excludes_conversion_paths_without_model_id(
        self, mock_get_schemas, mock_access_checks
    ):
        mock_get_schemas.return_value = (
            {
                'campaigns': {
                    'type': 'object',
                    'properties': {'id': {'type': ['null', 'string']}},
                },
                'conversion_paths': {
                    'type': 'object',
                    'properties': {'uri': {'type': ['null', 'string']}},
                },
            },
            {'campaigns': [], 'conversion_paths': []},
        )
        mock_access_checks.return_value = None

        client = MagicMock()
        config = {}  # no model_id

        catalog = discover(client, config)

        stream_ids = [s.tap_stream_id for s in catalog.streams]
        self.assertIn('campaigns', stream_ids)
        self.assertNotIn('conversion_paths', stream_ids)

    @patch('tap_impact.discover._apply_access_checks')
    @patch('tap_impact.discover.get_schemas')
    def test_discover_includes_conversion_paths_with_model_id(
        self, mock_get_schemas, mock_access_checks
    ):
        mock_get_schemas.return_value = (
            {
                'campaigns': {
                    'type': 'object',
                    'properties': {'id': {'type': ['null', 'string']}},
                },
                'conversion_paths': {
                    'type': 'object',
                    'properties': {'uri': {'type': ['null', 'string']}},
                },
            },
            {'campaigns': [], 'conversion_paths': []},
        )
        mock_access_checks.return_value = None

        client = MagicMock()
        config = {'model_id': 'model_123'}

        catalog = discover(client, config)

        stream_ids = [s.tap_stream_id for s in catalog.streams]
        self.assertIn('campaigns', stream_ids)
        self.assertIn('conversion_paths', stream_ids)

    @patch('tap_impact.discover._apply_access_checks', side_effect=ImpactForbiddenError('403'))
    @patch('tap_impact.discover.get_schemas')
    def test_discover_raises_when_all_streams_inaccessible(
        self, mock_get_schemas, mock_access_checks
    ):
        mock_get_schemas.return_value = ({'ads': {}}, {'ads': []})

        client = MagicMock()
        config = {}

        with self.assertRaises(ImpactForbiddenError):
            discover(client, config)

    @patch('tap_impact.discover._apply_access_checks')
    @patch('tap_impact.discover.get_schemas')
    def test_discover_passes_client_and_config_to_access_checks(
        self, mock_get_schemas, mock_access_checks
    ):
        mock_get_schemas.return_value = ({'ads': {}}, {'ads': []})
        mock_access_checks.return_value = None

        client = MagicMock()
        config = {'start_date': '2024-01-01T00:00:00Z'}

        discover(client, config)

        mock_access_checks.assert_called_once()
        call_args = mock_access_checks.call_args[0]
        self.assertEqual(call_args[0], client)


if __name__ == '__main__':
    unittest.main()
