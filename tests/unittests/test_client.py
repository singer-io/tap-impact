import unittest
from unittest.mock import MagicMock
import requests

from tap_impact.client import (
    get_exception_for_error_code,
    raise_for_error,
    ImpactBadRequestError,
    ImpactUnauthorizedError,
    ImpactForbiddenError,
    ImpactNotFoundError,
    ImpactMethodNotAllowedError,
    ImpactConflictError,
    ImpactUnprocessableEntityError,
    ImpactInternalServiceError,
    ImpactUnknownError,
    ImpactError,
    ImpactClient,
    ERROR_CODE_EXCEPTION_MAPPING,
)


class TestGetExceptionForErrorCode(unittest.TestCase):
    """Tests for get_exception_for_error_code()."""

    def test_400_returns_bad_request(self):
        self.assertIs(get_exception_for_error_code(400), ImpactBadRequestError)

    def test_401_returns_unauthorized(self):
        self.assertIs(get_exception_for_error_code(401), ImpactUnauthorizedError)

    def test_402_returns_request_failed(self):
        from tap_impact.client import ImpactRequestFailedError
        self.assertIs(get_exception_for_error_code(402), ImpactRequestFailedError)

    def test_403_returns_forbidden(self):
        self.assertIs(get_exception_for_error_code(403), ImpactForbiddenError)

    def test_404_returns_not_found(self):
        self.assertIs(get_exception_for_error_code(404), ImpactNotFoundError)

    def test_405_returns_method_not_allowed(self):
        self.assertIs(get_exception_for_error_code(405), ImpactMethodNotAllowedError)

    def test_409_returns_conflict(self):
        self.assertIs(get_exception_for_error_code(409), ImpactConflictError)

    def test_422_returns_unprocessable(self):
        self.assertIs(get_exception_for_error_code(422), ImpactUnprocessableEntityError)

    def test_500_returns_internal(self):
        self.assertIs(get_exception_for_error_code(500), ImpactInternalServiceError)

    def test_520_returns_unknown(self):
        self.assertIs(get_exception_for_error_code(520), ImpactUnknownError)

    def test_unmapped_code_returns_base_error(self):
        self.assertIs(get_exception_for_error_code(999), ImpactError)

    def test_all_mapped_codes_present(self):
        """Ensure the ERROR_CODE_EXCEPTION_MAPPING covers the expected set of codes."""
        expected_codes = {400, 401, 402, 403, 404, 405, 409, 422, 500, 520}
        self.assertEqual(set(ERROR_CODE_EXCEPTION_MAPPING.keys()), expected_codes)


class TestRaiseForError(unittest.TestCase):
    """Tests for raise_for_error()."""

    def _make_response(self, status_code, json_body=None, content=b"error", reason="Error"):
        resp = MagicMock()
        resp.status_code = status_code
        resp.reason = reason
        resp.text = str(json_body)
        resp.content = content
        if json_body is not None:
            resp.json.return_value = json_body
            resp.raise_for_status.side_effect = requests.HTTPError(
                response=resp
            )
        else:
            resp.raise_for_status.side_effect = requests.HTTPError(
                response=resp
            )
        return resp

    def test_empty_content_returns_none(self):
        resp = self._make_response(500, content=b"")
        # Should not raise — empty body is a no-op
        result = raise_for_error(resp)
        self.assertIsNone(result)

    def test_json_error_field_raises_mapped_exception(self):
        body = {"error": "Unauthorized", "message": "Invalid credentials", "status": 401}
        resp = self._make_response(401, json_body=body)
        with self.assertRaises(ImpactUnauthorizedError):
            raise_for_error(resp)

    def test_json_errorCode_field_raises_mapped_exception(self):
        body = {"errorCode": "NOT_FOUND", "message": "Resource not found", "status": 404}
        resp = self._make_response(404, json_body=body)
        with self.assertRaises(ImpactNotFoundError):
            raise_for_error(resp)

    def test_json_without_error_key_raises_base_impact_error(self):
        body = {"someOtherKey": "value"}
        resp = self._make_response(500, json_body=body)
        with self.assertRaises(ImpactError):
            raise_for_error(resp)

    def test_non_json_body_raises_impact_error(self):
        resp = self._make_response(503, content=b"<html>Service Unavailable</html>")
        resp.json.side_effect = ValueError("No JSON")
        with self.assertRaises(ImpactError):
            raise_for_error(resp)


class TestImpactClientInit(unittest.TestCase):
    """Tests for ImpactClient construction — no network calls."""

    def test_base_url_construction(self):
        client = ImpactClient(
            account_sid="ACCT123",
            auth_token="TOKEN456",
            api_catalog="Advertisers",
        )
        self.assertIn("ACCT123", client.base_url)
        self.assertIn("Advertisers", client.base_url)

    def test_base_url_contains_api_host(self):
        client = ImpactClient(
            account_sid="ACCT",
            auth_token="TOK",
            api_catalog="Partners",
        )
        self.assertTrue(client.base_url.startswith("https://api.impact.com"))

    def test_different_api_catalog(self):
        client1 = ImpactClient("A", "T", "Advertisers")
        client2 = ImpactClient("A", "T", "Partners")
        self.assertNotEqual(client1.base_url, client2.base_url)
