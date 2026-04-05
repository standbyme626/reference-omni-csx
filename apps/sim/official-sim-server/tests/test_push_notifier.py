"""Tests for PushNotifier.

Mocks httpx to verify dispatch logic without real HTTP calls.
"""

import time
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.domain.push_notifier import DispatchResult, PushNotifier
from app.models.models import PushEvent


@pytest.fixture
def mock_push_event():
    event = MagicMock(spec=PushEvent)
    event.event_type = "trade.OrderStatusChanged"
    event.run_id = "test-run-uuid-1234"
    event.step_no = 1
    event.platform = "taobao"
    event.body_json = {"order_id": "123", "status": "paid"}
    event.headers_json = {"Content-Type": "application/json"}
    return event


class TestPushNotifierNoSubscribers:
    def test_dispatch_no_subscribers_returns_ok(self, mock_push_event):
        notifier = PushNotifier(subscriber_urls=[])
        result = notifier.dispatch(mock_push_event)
        assert result.ok is True

    def test_dispatch_none_subscribers_returns_ok(self, mock_push_event):
        notifier = PushNotifier(subscriber_urls=None)
        result = notifier.dispatch(mock_push_event)
        assert result.ok is True


class TestPushNotifierHappyPath:
    def test_dispatch_success_on_first_attempt(self, mock_push_event):
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("httpx.Client") as MockClient:
            mock_client = MagicMock()
            mock_client.post.return_value = mock_response
            MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            notifier = PushNotifier(
                subscriber_urls=["http://localhost:8000/api/push-events"],
                timeout_s=3.0,
                max_retries=2,
            )
            result = notifier.dispatch(mock_push_event)

        assert result.ok is True
        assert result.status_code == 200


class TestPushNotifierRetry:
    def test_dispatch_500_then_200_retry_succeeds(self, mock_push_event):
        fail_response = MagicMock()
        fail_response.status_code = 500
        fail_response.text = "Internal Server Error"

        success_response = MagicMock()
        success_response.status_code = 200

        with patch("httpx.Client") as MockClient:
            mock_client = MagicMock()
            mock_client.post.side_effect = [fail_response, success_response]
            MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            notifier = PushNotifier(
                subscriber_urls=["http://localhost:8000/api/push-events"],
                timeout_s=3.0,
                max_retries=2,
            )
            result = notifier.dispatch(mock_push_event)

        assert result.ok is True
        assert result.status_code == 200

    def test_dispatch_all_failures_returns_failed(self, mock_push_event):
        fail_response = MagicMock()
        fail_response.status_code = 500
        fail_response.text = "error"

        with patch("httpx.Client") as MockClient:
            mock_client = MagicMock()
            mock_client.post.return_value = fail_response
            MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            notifier = PushNotifier(
                subscriber_urls=["http://localhost:8000/api/push-events"],
                timeout_s=3.0,
                max_retries=2,
            )
            result = notifier.dispatch(mock_push_event)

        assert result.ok is False
        assert "HTTP 500" in result.error

    def test_dispatch_timeout_eventually_fails(self, mock_push_event):
        with patch("httpx.Client") as MockClient:
            mock_client = MagicMock()
            mock_client.post.side_effect = httpx.TimeoutException("timeout")
            MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            notifier = PushNotifier(
                subscriber_urls=["http://localhost:8000/api/push-events"],
                timeout_s=3.0,
                max_retries=1,
            )
            result = notifier.dispatch(mock_push_event)

        assert result.ok is False
        assert "timeout" in result.error


class TestPushNotifierDispatchPayload:
    def test_dispatch_sends_correct_payload(self, mock_push_event):
        captured_body = None

        def capture_post(*args, **kwargs):
            nonlocal captured_body
            captured_body = kwargs.get("json")
            resp = MagicMock()
            resp.status_code = 200
            return resp

        with patch("httpx.Client") as MockClient:
            mock_client = MagicMock()
            mock_client.post = capture_post
            MockClient.return_value.__enter__ = MagicMock(return_value=mock_client)
            MockClient.return_value.__exit__ = MagicMock(return_value=False)

            notifier = PushNotifier(
                subscriber_urls=["http://localhost:8000/api/push-events"],
                timeout_s=3.0,
                max_retries=0,
            )
            notifier.dispatch(mock_push_event)

        assert captured_body is not None
        assert captured_body["event_type"] == "trade.OrderStatusChanged"
        assert captured_body["run_id"] == "test-run-uuid-1234"
        assert captured_body["step_no"] == 1
        assert captured_body["platform"] == "taobao"
