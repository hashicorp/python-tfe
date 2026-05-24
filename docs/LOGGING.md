# Logging in pyTFE

Internal reference for the SDK's logging framework. Companion to [`ITERATORS.md`](ITERATORS.md), [`MODELS.md`](MODELS.md), [`RESOURCE.md`](RESOURCE.md).

The framework is designed to be **silent by default** (library best practice — no logs unless the caller opts in), **integrated with stdlib `logging`** (so it composes with the user's existing setup), and **safe** (bearer tokens and other credentials are redacted before they ever reach a handler).

## The one-line quickstart for users

```bash
PYTFE_LOG=debug python my_script.py
```

`setup_logging()` is invoked automatically when the `pytfe` package is imported, so the env var is the entire user surface — no code change required. Programmatic equivalent (handy in tests or in REPLs where the env var was set after import):

```python
import pytfe
pytfe.setup_logging()
```

`setup_logging()` is idempotent — calling it more than once is safe.

That's it. Anything between `DEBUG`-level HTTP request/response traces and `INFO`-level retry decisions will show up on stderr with a per-line format like:

```
[2026-05-25 14:12:26 pytfe.transport DEBUG]
> GET /api/v2/organizations/acme/workspaces?page[number]=1&page[size]=100
< 200 OK
< {
<   "data": [
<     { "id": "ws-...", "type": "workspaces", ... }
<   ]
< }
```

## Logger namespace

| Logger | What it logs |
|---|---|
| `pytfe`           | Root namespace; rarely emits directly. Use it to dial **everything** pytfe says up or down at once. |
| `pytfe.transport` | HTTP request/response (DEBUG), retry decisions (INFO), transport exceptions (DEBUG). The noisy one. |

There is no `pytfe.resource.*` per-service logger. Resource methods do not log; if a caller needs visibility into "the SDK is calling `client.workspaces.read('ws-abc')'" they get it via the transport log right below it.

Standard stdlib selectors apply:

```python
import logging
logging.getLogger("pytfe").setLevel(logging.INFO)            # everything
logging.getLogger("pytfe.transport").setLevel(logging.DEBUG) # just HTTP
```

## Configuration knobs

The framework has three environment variables. All are optional.

| Variable | Default | Effect |
|---|---|---|
| `PYTFE_LOG` | unset | `debug` or `info` (case-insensitive) configures stdlib `logging` for you. Anything else is ignored. |
| `PYTFE_LOG_HEADERS` | `false` | When truthy, include request/response headers in `RoundTrip` output. Sensitive ones are still redacted; this just turns on the `> * Header: value` lines at all. |
| `PYTFE_LOG_TRUNCATE_BYTES` | `1024` | Truncation budget for any single string in a logged body. Values below 96 are clamped up. |

All three are read at call time, not at import — switching `PYTFE_LOG_HEADERS=true` in the middle of a long-running process takes effect on the next request.

## Redaction guarantees

The `RoundTrip` formatter (in [`src/pytfe/_logging.py`](../src/pytfe/_logging.py)) redacts before formatting, so the redacted value never reaches the logger:

**Headers** — replaced with `**REDACTED**` when matched. Names matched case-insensitively:

```
authorization
cookie
set-cookie
proxy-authorization
x-tfc-task-signature
```

Plus any header whose name contains the substring `token`, `secret`, `password`, `api-key`, or `apikey`.

**JSON bodies** — when the response body is JSON, these top-level *and nested* keys have their values replaced (case-insensitive key match):

```
token, access_token, refresh_token,
secret, password,
private_key, client_secret
```

This is structural: a value can be redacted even if it's deep inside an array of nested objects. **String values themselves are not scanned for tokens** — only the keys are matched. If you stuff a bearer token into a field named `"description"`, it will appear in the log.

The `**REDACTED**` constant is exported from `pytfe._logging` if you ever need to assert on it in a test.

## Truncation behavior

Bodies are formatted, not echoed:

- JSON arrays beyond the budget are clipped with `"... (N additional elements)"`.
- JSON string values longer than the per-string budget are clipped with `"... (N more bytes)"`.
- Non-JSON bodies are shown verbatim (after the same per-string truncation).
- Binary bodies (state-version downloads, CV tarballs, anything with a non-text/non-JSON `Content-Type`) are rendered as `[raw stream]` — the body is not decoded or formatted.

This keeps a `--list` over a 10,000-workspace organization to one screen of log output instead of 10MB.

## How the transport uses it

[`src/pytfe/_http.py`](../src/pytfe/_http.py) emits:

| Event | Logger | Level | Cost when disabled |
|---|---|---|---|
| Every HTTP request/response round-trip | `pytfe.transport` | DEBUG | Zero — guarded by `isEnabledFor(DEBUG)`. The `RoundTrip` object is only constructed when the level is enabled. |
| Retry decisions (`429`, `5xx`, `Retry-After`) | `pytfe.transport` | INFO | One conditional + format-string evaluation. |
| Transport exceptions during retry loop | `pytfe.transport` | DEBUG | Zero (same guard pattern). |

There is no DEBUG cost when logging is off, even on 10k-request workloads.

## How to use it in new SDK code

If you're adding code under `src/pytfe/`, prefer the framework over `print` or ad-hoc `logging.getLogger(__name__)`:

```python
# resources/something.py
from .._logging import logger

def some_operation(self, foo):
    if logger.isEnabledFor(logging.INFO):
        logger.info("performing some_operation on %s", foo)
    ...
```

Two rules:

1. **Always guard non-trivial log argument construction** with `isEnabledFor`. Don't pay format/serialize cost when the level is off.
2. **Never log a token, password, or other secret yourself.** Only `RoundTrip` knows how to redact, and it only redacts what it knows about. If you're tempted to write `logger.info("got token %s", token)` — don't.

For low-level transport additions, use `transport_logger` (also exported from `pytfe._logging`).

## What this isn't

- **Not a metrics framework.** No counters, gauges, timing histograms. If you want metrics, wrap the client.
- **Not an audit log.** Logs are for debugging, not for compliance trails.
- **Not a tracing framework.** No correlation IDs, no OpenTelemetry spans. Standard stdlib `logging` only.
- **Not Ansible-aware.** When the Ansible collection imports pytfe, the `pytfe` logger inherits from Ansible's root logger like any other library — which means it stays silent unless the Ansible user explicitly raises the level. No special integration is needed or provided.

## Checklist when reviewing log-touching code

- [ ] New library log calls use `pytfe._logging.logger` or `pytfe._logging.transport_logger`, not `logging.getLogger(__name__)` ad hoc
- [ ] Anything more expensive than a literal format string is guarded with `isEnabledFor(...)`
- [ ] No raw tokens, passwords, or other credentials in any log call
- [ ] If logging a header dict, it goes through `redact_headers(...)`
- [ ] If logging a request/response, it uses `RoundTrip(resp).generate()` so the standard redaction + truncation applies
- [ ] Logger default level is unchanged (i.e. NullHandler still active for callers who don't opt in)
