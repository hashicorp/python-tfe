# AGENTS.md — guide for AI agents working in this repository

If you are an AI coding agent (Claude Code, Codex, Cursor, GitHub Copilot Workspace, etc.) about to make changes to this repository, read this file first. It will save you from generating code that diverges from the codebase's conventions.

If you are a human contributor, the same conventions apply to you — but the more comprehensive [`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md) and the deep-dive references linked below are written for you specifically.

## What this repo is

`pytfe` is the official Python SDK for the HCP Terraform and Terraform Enterprise V2 API. It wraps roughly 50 resource services (workspaces, runs, policies, teams, agents, …) and is consumed by downstream projects. Source layout:

```
src/pytfe/
  client.py            # TFEClient — composition root, wires every resource
  config.py            # TFEConfig — auth, timeout, retry, proxy settings
  _http.py             # HTTPTransport — request, retry, redirects, auth
  _jsonapi.py          # JSON:API envelope helpers
  _logging.py.         # Logging primitives for the pytfe SDK
  errors.py            # Typed exception hierarchy (TFEError + ~80 subclasses)
  utils.py             # Validation + small helpers
  models/              # Pydantic v2 models, one file per resource
  resources/           # Service classes, one file per resource

tests/units/           # Pytest unit tests with mocked transport, one file per resource
examples/              # Runnable CLI demos, one file per resource (or extended)
docs/                  # Internal reference (see below)
```

## Required reading before generating code

These three documents define the patterns this codebase already uses. Generating code without consulting them will produce inconsistent output:

| Topic | Doc |
|---|---|
| `list_*` methods, pagination, iterator vs list, the `_list` helper | [`docs/ITERATORS.md`](docs/ITERATORS.md) |
| Pydantic model conventions: `ConfigDict`, aliases, validators, relationships, exporting | [`docs/MODELS.md`](docs/MODELS.md) |
| Resource service patterns: method shape, JSON:API envelopes, client wiring, examples | [`docs/RESOURCE.md`](docs/RESOURCE.md) |
| Logging: namespace, redaction, env-var setup, debug round-trip traces | [`docs/LOGGING.md`](docs/LOGGING.md) |

Each doc ends with a checklist. Use those checklists; they encode the rules a reviewer will look for.

## Source verification for API shape

Before adding a new resource, endpoint, enum, or non-obvious response parser, verify the wire contract against primary sources:

- Official HCP Terraform API docs: https://developer.hashicorp.com/terraform/cloud-docs/api-docs
- go-tfe implementation: https://github.com/hashicorp/go-tfe
- OpenAPI specs or live probes when the public docs/go-tfe are missing, beta, or ambiguous

Use the official docs and go-tfe as the first sources of truth. OpenAPI and live probes are supporting evidence, especially for endpoints that are newly released or not fully documented yet. When behavior is surprising, note the source you checked in the PR description, test name, example header, or a short code comment.

## The cardinal rules

A handful of conventions are pervasive enough that you'll regret breaking them. In rough order of "how loudly it breaks at review time":

1. **`list_*` methods return `Iterator[X]`.** Not `list[X]`, not `Iterable[X]`, not a custom `Pager`. Use `for item in self._list(path): yield ...` inside the method body. ([ITERATORS.md](docs/ITERATORS.md))

2. **JSON:API attribute names go through `Field(alias="...")`.** The API sends `created-at`, Python uses `created_at`. Pair with `model_config = ConfigDict(populate_by_name=True, validate_by_name=True)` on the model. ([MODELS.md](docs/MODELS.md))

3. **`model_dump(by_alias=True, exclude_none=True)` for write payloads.** Without `by_alias=True` you'll send snake_case to the API and it will silently drop the fields. Add `mode="json"` if the options contain enums.

4. **For new public APIs, prefer typed `TFEError` subclasses.** The error hierarchy in `errors.py` is part of the public API, and downstream consumers often `except TFEError:` once. Existing methods still expose many `ValueError` paths; do not change those established exceptions unless the breaking-change impact is explicitly accepted.

5. **Validate IDs at the top of every method.** Use `valid_string_id` from `utils.py`. New methods should prefer typed `Invalid<Thing>IDError` errors; existing resources may already use `ValueError` and should keep that public behavior unless a breaking change is intentional.

6. **Wire every new resource into `client.py`.** A resource not added to `TFEClient.__init__` is unreachable. Same for new models in `models/__init__.py`.

7. **Use the standard verb names: `list`, `read`, `create`, `update`, `delete`.** Plus `add_*` / `remove_*` for relationship modifications. Argument order is always *identifiers first, options last*.

## Things that look reasonable but are actually wrong here

These are mistakes a competent Python developer would make if they hadn't read the conventions. Avoid them:

- **Don't catch `httpx` errors directly.** The transport already translates them into `TFEError` subclasses. Catching `httpx.HTTPError` in a resource means the typed error never propagates.
- **Always send the bearer token, even to absolute URLs returned by the API.** Endpoints like `hosted_state_download_url`, `hosted_state_upload_url`, plan `json-output`, and apply `errored-state` redirect to `archivist.terraform.io` — which is HashiCorp infrastructure that *requires* the bearer. go-tfe does the same (see `state_version.go::Download` + `tfe.go::NewRequest`). Stripping the bearer breaks downstream consumers (notably the Ansible collection's statefile + dynamic-inventory flows). `HTTPTransport.request` accepts `include_auth=False` only as an opt-out for the hypothetical case of calling a genuinely non-HashiCorp host; do not use it for Archivist URLs.
- **Don't write a custom page loop.** `self._list(path, params=...)` handles pagination + non-paginated endpoints transparently. Rolling your own loop will diverge from the rest of the codebase.
- **Don't reuse generators.** Iterators returned by `list_*` are single-use. If you need to traverse twice, `materialized = list(client.foo.list_bars(...))` first.
- **Don't add features beyond what was asked.** This codebase is approaching v1.0.0. Adding "while I'm here" refactors or speculative abstractions slows reviews and risks breaking the Ansible collection.
- **Don't assume every successful response is `{"data": ...}`.** Check the docs/go-tfe/spec for each endpoint: some return a JSON:API envelope, some return a bare resource object, `204 No Content`, `null`, raw bytes, or a redirect to a blob URL. Add tests for non-standard shapes.
- **Don't use bare `list[...]` annotations inside a resource class after defining `def list(...)`.** In class scope, mypy can resolve `list` to the method instead of the builtin. Use `builtins.list[...]`, `Sequence[...]`, or another unshadowed type.
- **Don't `print()` or use ad-hoc `logging.getLogger(__name__)` calls in library code.** The SDK has a structured logging framework — use `pytfe._logging.transport_logger` for HTTP traffic, or `pytfe._logging.logger` (the `pytfe` root) for higher-level events. Everything from that namespace is silent by default (NullHandler) and respects the user's `setup_logging()` or stdlib configuration. See [LOGGING.md](docs/LOGGING.md) for redaction rules — bearer tokens and `token`/`secret`/`password` keys are auto-redacted by `RoundTrip`, but only inside that formatter. Never `log.info(token)` directly.

## Known cross-dependencies you should not break

| Consumer | What they depend on |
|---|---|
| `hashicorp/terraform-ansible-collection` | The pytfe public API — resource methods, model fields, exception classes. Any signature change here is a breaking change. In particular, `client.projects.list_tag_bindings` is consumed with an `isinstance(response, list)` check; it intentionally still returns `list[TagBinding]` (see [ITERATORS.md](docs/ITERATORS.md) — Known exceptions). |
| Downstream user code generally | Method signatures, return types, model fields, and exception types. New errors should subclass an existing parent so `except TFEError:` continues to work, but existing `ValueError` behavior should not be changed casually. |

When in doubt about whether a change is breaking: check `gh search code '<symbol>' --owner hashicorp` to see if the Ansible repo uses it.

## How to make a change

This is the workflow that produces low-friction reviews. Follow it.

1. **Understand the scope first.** If the task is "add resource X", read `docs/RESOURCE.md` end-to-end. If it's "fix bug in Y", read `Y`'s current implementation and tests before touching anything.
2. **Check official API docs and go-tfe for the canonical API shape.** `pytfe` mirrors the HCP Terraform API and often follows go-tfe's surface. URL paths, method names, payload shapes, response shapes, enum values, and redirect behavior should be verified against https://developer.hashicorp.com/terraform/cloud-docs/api-docs and https://github.com/hashicorp/go-tfe before designing anything.
3. **Add models first** (`src/pytfe/models/<resource>.py`), then the resource (`src/pytfe/resources/<resource>.py`), then wire both into the respective `__init__.py` / `client.py`.
4. **Write tests.** Mock `HTTPTransport`. One test per method, plus an invalid-id case for every public method. See `tests/units/test_comment.py` as a small reference.
5. **Run `make test` and `make lint`.** Both must pass. `pytest tests/units/` runs the suite directly; it should be < 2 seconds.
6. **Add or extend an example.** Real engineers will copy-paste it; make it work end-to-end. Use env vars (`TFE_TOKEN`, `TFE_ORG`) for auth, never hard-code credentials.
7. **If the change is non-trivial, verify live.** The repo doesn't run integration tests in CI, so the only way to catch a wrong URL or a typo in an attribute alias is to run the example against a real organization.

## Things to never do

- **Never put a token, password, or other credential in any file.** Use environment variables. The user will rotate them after; you don't need to know them.
- **Never use `git push --force` or `git reset --hard` without explicit instruction.** Same for `--no-verify`, force-push to `main`, or rebasing public commits.
- **Never commit `.env`, `credentials.json`, `*.tfstate`, or anything with secrets.** Match against the existing `.gitignore` if unsure.
- **Never bypass pre-commit hooks.** If a hook fails, fix the underlying issue.
- **Never run an example that creates real resources against production without explicit user confirmation.** Sandbox orgs are safe; user's actual workspace is not.

## Style

The codebase uses [ruff](https://docs.astral.sh/ruff/) for both formatting and linting and [mypy](https://mypy.readthedocs.io/) for type checking. Type hints are required on every public method's signature. Docstrings are required on every public method — keep them to one or two lines unless the behavior is genuinely non-obvious.

Comments are minimal by design. A comment should explain *why* something non-obvious is true, not *what* the code does. The names and types should be enough to convey "what".

```python
# ❌ Don't
# Increment the counter by 1
counter += 1

# ✅ Do (only when the why is non-obvious)
# Run task stages are wire values, not Python names. If the API/go-tfe says
# "pre-plan", keep the hyphen; do not "normalize" it to snake_case.
stage_value = raw_value
```

## When you're done

A reasonable PR includes:

- Code (resource + models)
- Tests covering every public method
- An updated or new example
- A short `CHANGELOG.md` entry under `# v<next-minor>.0 (Unreleased)` describing the user-visible change

Open the PR with a description that explains *why* the change is needed, links to any HCP Terraform API docs or go-tfe code referenced, and notes any behavior changes a downstream consumer might see.

The reviewer's checklist will be the union of the checklists in [`docs/ITERATORS.md`](docs/ITERATORS.md), [`docs/MODELS.md`](docs/MODELS.md), and [`docs/RESOURCE.md`](docs/RESOURCE.md). Pre-running them yourself is the fastest way to a merge.
