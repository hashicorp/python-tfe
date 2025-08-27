import pytest
import requests

from tfe import config


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    """Reset environment variables before each test."""
    monkeypatch.delenv("TFE_ADDRESS", raising=False)
    monkeypatch.delenv("TFE_TOKEN", raising=False)
    monkeypatch.delenv("TFE_HOST", raising=False)
    monkeypatch.setenv("TFE_TOKEN", "abc123")
    yield


@pytest.fixture
def cfg():
    """Provide a fresh Config instance with clean environment."""
    return config.Config()


@pytest.fixture
def test_session():
    """Provide a clean requests session without default headers."""
    session = requests.Session()
    session.headers["User-Agent"] = "test"
    session.headers["Authorization"] = "Bearer test"
    return session


class TestConfig:
    def test_default_config(self, cfg):
        """Test that default configuration values are set correctly."""
        assert cfg.address == config.DEFAULT_ADDRESS
        assert cfg.base_path == config.DEFAULT_BASE_PATH
        assert cfg.registry_base_path == config.DEFAULT_REGISTRY_PATH
        assert isinstance(cfg.http_client, requests.Session)
        assert "User-Agent" in cfg.http_client.headers
        assert cfg.retry_log_hook is None
        assert cfg.retry_server_errors is False

    def test_env_address_and_token(self, monkeypatch):
        """Test that environment variables TFE_ADDRESS and TFE_TOKEN are read correctly."""
        monkeypatch.setenv("TFE_ADDRESS", "https://custom.tfe")
        cfg = config.Config()
        assert cfg.address == "https://custom.tfe"
        assert cfg.token == "abc123"

    def test_env_host_fallback(self, monkeypatch):
        """Test that TFE_HOST is used as fallback when TFE_ADDRESS is not set."""
        monkeypatch.setenv("TFE_HOST", "host.tfe")
        cfg = config.Config()
        assert cfg.address == "https://host.tfe"

    def test_explicit_address_override(self):
        """Test that explicitly passed address overrides environment variables."""
        cfg = config.Config(address="https://explicit.tfe")
        assert cfg.address == "https://explicit.tfe"

    def test_headers_update(self):
        """Test that custom headers are properly merged with default headers."""
        custom_headers = {"Authorization": "Bearer testtoken", "X-Test": "yes"}
        cfg = config.Config(headers=custom_headers)
        assert "Authorization" in cfg.http_client.headers
        assert cfg.http_client.headers["Authorization"] == "Bearer testtoken"
        assert "X-Test" in cfg.http_client.headers
        assert cfg.http_client.headers["X-Test"] == "yes"
        assert "User-Agent" in cfg.http_client.headers

    def test_retry_log_hook_and_server_errors(self):
        """Test that retry configuration is properly set."""

        def dummy_hook(retries, response):
            pass

        cfg = config.Config(retry_log_hook=dummy_hook, retry_server_errors=True)
        assert cfg.retry_log_hook == dummy_hook
        assert cfg.retry_server_errors is True

    def test_custom_session(self, test_session):
        """Test that User-Agent is set when session has no default User-Agent."""
        cfg = config.Config(http_client=test_session)
        assert "User-Agent" in cfg.http_client.headers
        assert cfg.http_client.headers["User-Agent"] == "test"
        assert cfg.http_client.headers["Authorization"] == "Bearer test"

    def test_validate_config(self, monkeypatch):
        """Test that configuration validation works as expected."""
        with pytest.raises(ValueError, match="API token is required") as _:
            monkeypatch.setenv("TFE_TOKEN", "")
            _ = config.Config(token="")

        with pytest.raises(ValueError, match="Address must include protocol") as _:
            monkeypatch.setenv("TFE_TOKEN", "test-token")
            monkeypatch.setenv("TFE_ADDRESS", "test.foo.bar")
            _ = config.Config()
