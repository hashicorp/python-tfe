#!/usr/bin/env python3
# Copyright IBM Corp. 2025, 2026
# SPDX-License-Identifier: MPL-2.0

"""
================================================================================
  Terraform Explorer API — walkthrough (TFEClient.explorer)
================================================================================

  https://developer.hashicorp.com/terraform/cloud-docs/api-docs/explorer

  PUBLIC FUNCTIONS
  ───────────────────────────────────────────────────
    ┌────────────────────────┬────────────────────────────────────┬──────────────────────────────────────────────────────────────────────────────┬──────────────────────────────┐
    │ Function               │ Purpose                            │ Input parameters                                                             │ Returns                      │
    ├────────────────────────┼────────────────────────────────────┼──────────────────────────────────────────────────────────────────────────────┼──────────────────────────────┤
    │ query                  │ Execute any Explorer query         │ organization: str; options: ExplorerQueryOptions                             │ Iterator[ExplorerRow]        │
    │ export_csv             │ Export query results as CSV        │ organization: str; options: ExplorerQueryOptions                             │ str (CSV document)           │
    │ list_saved_views       │ List saved Explorer views          │ organization: str                                                            │ Iterator[ExplorerSavedView]  │
    │ create_saved_view      │ Create saved Explorer view         │ organization: str; options: ExplorerSavedViewCreateOptions                   │ ExplorerSavedView            │
    │ read_saved_view        │ Fetch one saved view by id         │ organization: str; view_id: str                                              │ ExplorerSavedView            │
    │ update_saved_view      │ Update saved view definition       │ organization: str; view_id: str; options: ExplorerSavedViewUpdateOptions     │ ExplorerSavedView            │
    │ delete_saved_view      │ Remove saved view by id            │ organization: str; view_id: str                                              │ ExplorerSavedView            │
    │ saved_view_results     │ Execute saved view, stream rows    │ organization: str; view_id: str                                              │ Iterator[ExplorerRow]        │
    │ saved_view_results_csv │ Saved view results as CSV          │ organization: str; view_id: str                                              │ str (CSV; fallbacks)         │
    └────────────────────────┴────────────────────────────────────┴──────────────────────────────────────────────────────────────────────────────┴──────────────────────────────┘
    delete_saved_view: if the DELETE response has no JSON body, the client returns a
      minimal ExplorerSavedView with the same id.
    saved_view_results_csv: tries the saved-view CSV endpoint first; on failure it may
      call export_csv after read_saved_view, or build CSV from saved_view_results.

  INPUT AND OUTPUT MODELS (how to pass; allowed values)
  ───────────────────────────────────────────────────────
    Full column tables and operator semantics:
      https://developer.hashicorp.com/terraform/cloud-docs/api-docs/explorer

  Plain string parameters (no model)
    - organization — First argument on every method: org name as str (non-empty; invalid
      values raise InvalidOrgError).
    - view_id — str for saved-view routes (non-empty; invalid values raise
      InvalidExplorerSavedViewIDError). Use the id returned by list_saved_views or
      create_saved_view.

  ExplorerQueryOptions — second argument to query(org, options) and export_csv(org, options)
    How to pass: build one instance and pass it by name, for example
      ExplorerQueryOptions(view_type=ExplorerViewType.WORKSPACES, sort="-workspace_name",
      filters=[ExplorerUrlFilter(...)]).
    Required:
      - view_type — ExplorerViewType (serialized to HTTP query key type). Allowed strings
        per product docs: workspaces, tf_versions, providers, modules. This SDK also
        defines resources for APIs that support that view.
    Optional:
      - sort — Comma-separated snake_case field names for the active view; prefix "-" for
        descending order.
      - fields — Comma-separated snake_case columns to return (must be valid for the view).
      - page_number, page_size — Integers; page_number ≥ 1; page_size between 1 and 100.
      - filters — List of ExplorerUrlFilter; combined with logical AND.

  ExplorerUrlFilter — each element of ExplorerQueryOptions.filters
    How to pass: ExplorerUrlFilter(index=0, field="workspace_name", operator="contains",
      value="prod", value_index=0).
    Allowed:
      - index — int ≥ 0 (first filter is 0, then 1, 2, …).
      - field — snake_case column name for the current view_type (see Explorer doc View Types).
      - operator — one of: is, is_not, contains, does not contain, is_empty, is_not_empty,
        gt, lt, gteq, lteq, is_before, is_after (use the exact token your API version documents;
        each operator only applies to compatible field types).
      - value — str; use ISO 8601 timestamps for is_before / is_after when filtering datetimes.
      - value_index — must be 0.

  ExplorerSavedViewCreateOptions — second argument to create_saved_view(org, options)
    How to pass: ExplorerSavedViewCreateOptions(name="...", query_type=ExplorerViewType....,
      query=ExplorerSavedQuery(...)).
    Allowed:
      - name — non-empty str.
      - query_type — same ExplorerViewType set as view_type (JSON body key query-type).
      - query — ExplorerSavedQuery (see below).

  ExplorerSavedViewUpdateOptions — third argument to update_saved_view(org, view_id, options)
    How to pass: ExplorerSavedViewUpdateOptions(name="...", query=ExplorerSavedQuery(...)).
    PATCH replaces the stored query entirely—send a full ExplorerSavedQuery each time.

  ExplorerSavedQuery — nested only inside create/update options
    How to pass: ExplorerSavedQuery(query_type=ExplorerViewType.WORKSPACES, filter=[...],
      fields=[...], sort=[...]).
    Allowed:
      - query_type — required; same values as ExplorerQueryOptions.view_type (JSON key type).
      - filter — optional list of ExplorerSavedQueryFilter(field=..., operator=..., value=[...]).
      - fields — optional list of snake_case column names.
      - sort — optional list of field names; leading "-" on an entry means descending.

  ExplorerSavedQueryFilter — one dict-like row inside ExplorerSavedQuery.filter
    How to pass: ExplorerSavedQueryFilter(field="workspace_name", operator="contains",
      value=["prod"]).
    Allowed: field and operator follow the same rules as URL filters; value is always a
      list of strings (even for a single operand).

  Output models (return values only; you do not instantiate these for requests)
    ExplorerRow — from query(), saved_view_results(): read .id, .row_type, .attributes.
      .attributes is a dict of column values; keys may be hyphenated or snake_case depending
      on the API field name.
    ExplorerSavedView — from create_saved_view, read_saved_view, update_saved_view,
      delete_saved_view, list_saved_views: .id, .name, .created_at, .query_type, .query.
    str — from export_csv, saved_view_results_csv: raw CSV document body.
    Iterator[...] — lazy streams; consume with for-loops or list(...) if you need a list.

  SCRIPT SECTIONS
  ───────────────
    Sections 1 through 3 always run (read-only): query, export_csv, list_saved_views.
    Sections 4 through 6 run when TFE_EXPLORER_VIEW_ID is set: read_saved_view,
    saved_view_results, saved_view_results_csv.
    Section 7 runs when TFE_EXPLORER_DEMO_MUTATIONS=1: create_saved_view,
    update_saved_view, delete_saved_view.

  HOW TO RUN
  ──────────
    From the repository root, install in editable mode, then execute this file:
      pip install -e .
      python examples/explorer.py


  ENVIRONMENT VARIABLES
  ─────────────────────
    TFE_TOKEN                     Required. API token with Explorer access.
    TFE_ADDRESS                   Optional. API base URL; defaults to https://app.terraform.io
    TFE_ORGANIZATION              Optional. Organization name (the script substitutes a placeholder if unset).
    TFE_EXPLORER_VIEW_ID          Optional. When set, exercises saved-view read and export paths (sections 4–6).
    TFE_EXPLORER_DEMO_MUTATIONS   Optional. Allowed value to enable writes: 1 only.
      Any other value skips section 7 (create, update, delete).
"""

from __future__ import annotations

import os
import sys
import textwrap
import uuid

from pytfe import TFEClient, TFEConfig
from pytfe.errors import TFEError
from pytfe.models import (
    ExplorerQueryOptions,
    ExplorerSavedQuery,
    ExplorerSavedQueryFilter,
    ExplorerSavedViewCreateOptions,
    ExplorerSavedViewUpdateOptions,
    ExplorerUrlFilter,
    ExplorerViewType,
)

_LINE = "-" * 72


def _banner(title: str, subtitle: str = "") -> None:
    """Print a plain section divider and title for stdout readability."""
    print(f"\n{_LINE}\n{title}")
    if subtitle:
        print(subtitle)
    print(_LINE)


def _print_csv_lines(label: str, csv_text: str, max_chars: int, max_lines: int) -> None:
    """Print a readable, line-oriented slice of a CSV string without decorative framing."""
    snippet = csv_text[:max_chars]
    truncated = len(csv_text) > max_chars
    lines = snippet.splitlines() or ([snippet] if snippet else ["(empty)"])
    print(label)
    for raw in lines[:max_lines]:
        display = raw if len(raw) <= 68 else raw[:67] + "..."
        print(f"  {display}")
    if len(lines) > max_lines:
        print(
            f"  ... ({len(lines) - max_lines} more line(s) not shown in this preview)"
        )
    if truncated:
        print(
            f"  (Preview truncated by character limit; full length {len(csv_text):,} chars.)"
        )


def main() -> None:
    """Execute the Explorer walkthrough; refer to the module docstring for API details."""
    token = os.getenv("TFE_TOKEN")
    if not token:
        print(
            "Error: TFE_TOKEN is not set. Export a valid API token before running this example."
        )
        sys.exit(1)

    address = os.getenv("TFE_ADDRESS", "https://app.terraform.io")
    org = os.getenv("TFE_ORGANIZATION", "your-org-name")
    view_id = os.getenv("TFE_EXPLORER_VIEW_ID")
    demo_mutations = os.getenv("TFE_EXPLORER_DEMO_MUTATIONS") == "1"

    # TFEClient is the entry point for all Terraform Enterprise / HCP Terraform API
    # access in this SDK. TFEConfig carries the base URL and bearer token; every
    # resource (including explorer) uses the same underlying HTTP session.
    client = TFEClient(TFEConfig(address=address, token=token))

    _banner(
        "Terraform Explorer API example",
        f"Organization: {org!r}\nAPI base URL: {address}",
    )

    # -------------------------------------------------------------------------
    # Step 1: client.explorer.query(organization, options)
    # -------------------------------------------------------------------------
    # Runs GET .../organizations/{org}/explorer with query-string parameters derived
    # from ExplorerQueryOptions. Here we request the workspaces view, sort by
    # workspace_name descending (leading hyphen in sort), and add a single URL-style
    # filter (workspace_name contains "42"). The iterator yields ExplorerRow objects
    # (id, row_type, attributes dict); we only print the first five rows.
    _banner(
        "Step 1 of 7: query()",
        "Workspaces view, sorted by -workspace_name, filter workspace_name contains '42'.",
    )
    query_opts = ExplorerQueryOptions(
        view_type=ExplorerViewType.WORKSPACES,
        sort="-workspace_name",
        filters=[
            ExplorerUrlFilter(
                index=0,
                field="workspace_name",
                operator="contains",
                value="42",
            ),
        ],
    )
    try:
        count = 0
        for i, row in enumerate(client.explorer.query(org, query_opts)):
            if i >= 5:
                break
            count += 1
            name = row.attributes.get("workspace-name") or row.attributes.get(
                "workspace_name"
            )
            print(f"  Row {count}:")
            print(f"    id:               {row.id}")
            print(f"    row_type:         {row.row_type!r}")
            print(f"    workspace_name:  {name!r}")
            print("    ---")
        print(f"Summary: printed {count} row(s) (limit 5).")
    except TFEError as e:
        print(f"  API error: {e}")
    except Exception as e:
        print(f"  Error: {e}")

    # -------------------------------------------------------------------------
    # Step 2: client.explorer.export_csv(organization, options)
    # -------------------------------------------------------------------------
    # Same query parameters as query(), but the response is a single CSV document
    # (full unpaged export per API semantics). We only print an opening slice so the
    # terminal stays readable.
    _banner(
        "Step 2 of 7: export_csv()",
        "Workspaces view, no filters; preview first 400 characters / up to 8 lines.",
    )
    try:
        csv_text = client.explorer.export_csv(
            org, ExplorerQueryOptions(view_type=ExplorerViewType.WORKSPACES)
        )
        _print_csv_lines(
            "CSV preview (document may be large):",
            csv_text,
            max_chars=400,
            max_lines=8,
        )
        print("Summary: export_csv completed.")
    except TFEError as e:
        print(f"  API error: {e}")
    except Exception as e:
        print(f"  Error: {e}")

    # -------------------------------------------------------------------------
    # Step 3: client.explorer.list_saved_views(organization)
    # -------------------------------------------------------------------------
    # GET .../organizations/{org}/explorer/views returns every saved Explorer view
    # (saved query) in the organization. Each item is an ExplorerSavedView with id,
    # name, query, and query_type.
    _banner(
        "Step 3 of 7: list_saved_views()",
        "Iterate all saved views; print id, name, and query_type for each.",
    )
    try:
        n = 0
        for sv in client.explorer.list_saved_views(org):
            n += 1
            print(f"  Saved view {n}:")
            print(f"    id:          {sv.id}")
            print(f"    name:        {sv.name!r}")
            print(f"    query_type:  {sv.query_type!r}")
            print("    ---")
        print(f"Summary: listed {n} saved view(s).")
    except TFEError as e:
        print(f"  API error: {e}")
    except Exception as e:
        print(f"  Error: {e}")

    if view_id:
        # ---------------------------------------------------------------------
        # Step 4: client.explorer.read_saved_view(organization, view_id)
        # ---------------------------------------------------------------------
        # GET .../explorer/views/{view_id} fetches one saved view definition (not the
        # materialized result rows). view_id must be an id returned by list or create.
        _banner(
            "Step 4 of 7: read_saved_view()",
            f"view_id from TFE_EXPLORER_VIEW_ID: {view_id!r}",
        )
        try:
            sv = client.explorer.read_saved_view(org, view_id)
            print("  Saved view record:")
            print(f"    id:          {sv.id}")
            print(f"    name:        {sv.name!r}")
            q_preview = textwrap.shorten(repr(sv.query), width=68, placeholder=" ...")
            print(f"    query:       {q_preview}")
            print(f"    query_type:  {sv.query_type!r}")
            print("Summary: read_saved_view completed.")
        except TFEError as e:
            print(f"  API error: {e}")

        # ---------------------------------------------------------------------
        # Step 5: client.explorer.saved_view_results(organization, view_id)
        # ---------------------------------------------------------------------
        # GET .../explorer/views/{view_id}/results re-executes the saved query and
        # streams ExplorerRow results (same shape as query()). We print the first three.
        _banner(
            "Step 5 of 7: saved_view_results()",
            "First 3 rows from re-running the saved view query.",
        )
        try:
            for i, row in enumerate(client.explorer.saved_view_results(org, view_id)):
                if i >= 3:
                    break
                print(f"  Result row {i + 1}:")
                print(f"    id:        {row.id}")
                print(f"    row_type:  {row.row_type!r}")
                print("    ---")
            print("Summary: saved_view_results completed (limit 3 rows printed).")
        except TFEError as e:
            print(f"  API error: {e}")

        # ---------------------------------------------------------------------
        # Step 6: client.explorer.saved_view_results_csv(organization, view_id)
        # ---------------------------------------------------------------------
        # Intended to match GET .../explorer/views/{view_id}/csv. This SDK may fall
        # back to export_csv after read_saved_view, or synthesize CSV from results,
        # when the dedicated CSV route is unavailable.
        _banner(
            "Step 6 of 7: saved_view_results_csv()",
            "Preview first 300 characters / up to 6 lines; fallbacks may apply.",
        )
        try:
            csv_sv = client.explorer.saved_view_results_csv(org, view_id)
            _print_csv_lines(
                "CSV preview:",
                csv_sv,
                max_chars=300,
                max_lines=6,
            )
            print("Summary: saved_view_results_csv completed.")
        except TFEError as e:
            print(f"  API error: {e}")
            note = textwrap.fill(
                "Note: A 404 often means the saved view was removed, the id belongs to "
                "another organization, or this deployment has no dedicated CSV route. "
                "The client retries via export_csv after read_saved_view, then builds "
                "CSV from saved_view_results. If step 5 worked, confirm an editable "
                "install (pip install -e .).",
                width=70,
                subsequent_indent="    ",
            )
            for line in note.splitlines():
                print(f"  {line}")
    else:
        _banner(
            "Steps 4 through 6 skipped",
            "Set environment variable TFE_EXPLORER_VIEW_ID to the saved view id to run "
            "read_saved_view, saved_view_results, and saved_view_results_csv.",
        )

    if demo_mutations:
        suffix = uuid.uuid4().hex[:8]
        base_name = f"python-tfe-explorer-example-{suffix}"
        _banner(
            "Step 7 of 7: create_saved_view, update_saved_view, delete_saved_view",
            f"Uses a unique temporary name so reruns do not collide: {base_name!r}",
        )
        try:
            # ExplorerSavedViewCreateOptions maps to POST .../explorer/views: a display
            # name, the primary query_type for the saved definition, and an embedded
            # ExplorerSavedQuery (view type, optional filters with list-valued operands).
            create_opts = ExplorerSavedViewCreateOptions(
                name=base_name,
                query_type=ExplorerViewType.WORKSPACES,
                query=ExplorerSavedQuery(
                    query_type=ExplorerViewType.WORKSPACES,
                    filter=[
                        ExplorerSavedQueryFilter(
                            field="workspace_name",
                            operator="contains",
                            value=["test"],
                        )
                    ],
                ),
            )
            # client.explorer.create_saved_view persists a new saved view; the response
            # includes the server-assigned id required for subsequent update/delete.
            created = client.explorer.create_saved_view(org, create_opts)
            print(f"  create_saved_view: new id {created.id}")

            # ExplorerSavedViewUpdateOptions maps to PATCH: at minimum a new name and
            # a full replacement ExplorerSavedQuery payload for the stored definition.
            update_opts = ExplorerSavedViewUpdateOptions(
                name=f"{base_name}-updated",
                query=ExplorerSavedQuery(
                    query_type=ExplorerViewType.WORKSPACES,
                    filter=[
                        ExplorerSavedQueryFilter(
                            field="workspace_name",
                            operator="contains",
                            value=["demo"],
                        )
                    ],
                ),
            )
            # client.explorer.update_saved_view applies the patch to the id returned
            # from create_saved_view in this demonstration sequence.
            updated = client.explorer.update_saved_view(org, created.id, update_opts)
            print(f"  update_saved_view: name is now {updated.name!r}")

            # client.explorer.delete_saved_view removes the saved view; some API
            # responses omit JSON, in which case the client still returns a minimal
            # ExplorerSavedView carrying the deleted id.
            deleted = client.explorer.delete_saved_view(org, created.id)
            print(f"  delete_saved_view: completed for id {deleted.id}")
            print("Summary: mutation sequence finished.")
        except TFEError as e:
            print(f"  API error: {e}")
            sys.exit(1)
    else:
        _banner(
            "Step 7 skipped",
            "Set TFE_EXPLORER_DEMO_MUTATIONS=1 to run create_saved_view, "
            "update_saved_view, and delete_saved_view (writes to your organization).",
        )

    print(f"\n{_LINE}\nExample completed.\n{_LINE}")


if __name__ == "__main__":
    main()
