# GitBook access — docs.cakewallet.com (docs backend)

The docs live in GitBook, not in a git repo. Everything needed to read/edit them
programmatically is below, so no session has to rediscover it.
## Hard rules

**Agents NEVER merge GitBook change requests.** Every CR is created, verified
inside the CR, and then left open for Seth to review and merge manually. This
overrides any "it's verified, merge it" reasoning.

## Auth

- GitBook API token (starts `gb_api_`) is stored in the login keychain:
  ```bash
  security find-generic-password -s cake-docs-gitbook -w
  ```
  (account `cake-docs`). If the item is missing, regenerate a token in GitBook
  → Settings → API tokens and re-add it with `-U`. Never paste the token into
  files, chats, or shell history.

- GitBook MCP (works over plain HTTP with the same token):
  `https://mcp.gitbook.com/mcp` — JSON-RPC, `Authorization: Bearer <token>`,
  `Accept: application/json, text/event-stream`. Initialize → notifications/initialized,
  then `tools/call`; keep the `Mcp-Session-Id` response header for follow-ups.
  Tool surface: `create_change_request`, `submit_or_merge_change_request`,
  `get_page`, `get_site_structure`, `list_sites`, `list_site_topics`, `search`
  (this one searches the **API operation catalog**), `describe_operation`,
  `invoke_operation`, `get_usage_guide`.

## REST API

- Base URL is **`https://api.gitbook.com/v1`** (v3 returns a redirect hint only).
- Fetch page markdown:
  `GET /v1/spaces/:spaceId/content/path/:pagePath?format=markdown`
  — multi-segment paths must be URL-encoded (`setup%2Frestore-existing-wallet`).
- Page tree: `GET /v1/spaces/:spaceId/content` (nested `pages[]`).
- Apply CR content:
  `POST /v1/spaces/:spaceId/change-requests/:crId/content?compat=false` with
  `{"changes":[{"operation":"update_page","page":"<pageId>","document":{"markdown":"..."}}]}`
- Verify inside a CR before merging:
  `GET /v1/spaces/:spaceId/change-requests/:crId/content/path/:pagePath?format=markdown`

## Ids that matter

| Thing | Id |
|---|---|
| Organization | `Ksgcu2spQyb8ZrFM3st6` |
| Site docs.cakewallet.com | `site_VMiJI` |
| Home space (release notes) | `JjcHspJyXLzqlhmsKM3N` |
| Get Started 6.x space | `XUxrs2r29bTlRr2etoiy` |
| Features 6.x space | `42pJTvTiQMiULx18h5vy` |
| Cryptos space | `tSLIJ3VE2UcCjtTcoMgl` |
| `release-notes` page | `go9jnC4xCX3zaJNWsRGp` |
| `decred` page | `70d068b0e935eedea7e638644c81af5abe3f5e90` |
| `zano` page | `30f09803ecd562791865d2093e31628326e40c5b` |

`get_site_structure` lists section→space mapping for the rest (Cake Pay, Cupcake,
FAQ, Tutorials, Support, 5.x variants).

## Editing rules (hard-won — from the Notion "Docs screenshots" runbook)

1. **Submit the fetched markdown VERBATIM**, keeping its leading `# Title` line;
   otherwise GitBook consumes the first heading as the page title and silently
   moves the slug (broke `install/android` once).
2. **Relative internal links degrade to plain text on import** even though
   working links export as `[X](parent/child)`. Re-submit same-space links as
   `[X](/pages/<parent-slug>/<child-slug>)`, cross-space as full
   `https://docs.cakewallet.com/...` URLs. The "Previous versions" list on
   `release-notes` bit twice.
3. **Re-fetch inside the CR and diff before merging** — confirm title, slug and
   path are unchanged, not just the body. GitBook also normalizes markdown on
   apply, so expect cosmetic export drift.
4. One `update_page` change per call is the safe habit; up to 50 changes are
   allowed per batch but a single invalid change rejects the whole batch.
5. `submit_or_merge_change_request` exists but is **off-limits for agents** — see
   Hard rules above. File the CR, verify it, report the link, and stop.

## Release-notes page shape (Seth-approved)

- Parent `/release-notes` always holds the **latest release** under
  `## Latest: X.Y.Z — <Month Year>` with a `Covers …` line listing every covered
  tag with dates; per-patch `#### vX.Y.Z — <date>` subsections under
  `### Improvements & fixes`; `### Highlights` for series-level features.
- Older series are subpages `release-notes/cake-wallet-6.N`; promote the current
  Latest content into a new series page when a new minor ships.
- Screenshot hosting for all docs pages is this repo (raw.githubusercontent URLs,
  one folder per release), per the Notion runbook.
