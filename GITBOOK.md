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
6. **Renaming a page is deterministic — set `title` and `slug` explicitly.**
   `update_page` accepts `title` and `slug` alongside `document`, so a rename
   never has to rely on GitBook inferring a title from the first heading:
   ```json
   {"operation":"update_page","page":"<pageId>","title":"Recovery phrase or keys",
    "slug":"recovery-phrase-or-keys","document":{"markdown":"..."}}
   ```
   Slugs are frequently **custom and not derived from the title** (`find-seed-phrase`
   vs "How to find my seed phrase"), so never assume changing the title moves the
   slug — set both, then re-read inside the CR to confirm `title`/`slug`/`path`.
7. **Link forms on import** (probed 2026-09-21, one CR, all four in one page):
   | form | result |
   |---|---|
   | `[X](/pages/<pageId>)` | real internal link — **use this**, survives renames |
   | `[X](/pages/<parent>/<child>)` | real internal link |
   | `[X](https://docs.cakewallet.com/...)` | real link — use across spaces |
   | `[X](parent/child)` (bare relative) | **degrades to plain text** |
   Any page you re-submit loses *every* bare relative link it contains, not just
   the ones you touched — convert them all before applying (the Features index
   had 28).

## Release-notes page shape (Seth-approved)

- Parent `/release-notes` always holds the **latest release** under
  `## Latest: X.Y.Z — <Month Year>` with a `Covers …` line listing every covered
  tag with dates; per-patch `#### vX.Y.Z — <date>` subsections under
  `### Improvements & fixes`; `### Highlights` for series-level features.
- Older series are subpages `release-notes/cake-wallet-6.N`; promote the current
  Latest content into a new series page when a new minor ships.
- Screenshot hosting for all docs pages is this repo (raw.githubusercontent URLs,
  one folder per release), per the Notion runbook.

## Redirects (site level)

Renames need a redirect from the old published path. Two things to know:

- **Redirects are a fallback, not an override.** Creating one whose `source` is a
  path that still has a live page does **not** shadow that page (verified
  2026-09-21: the old URL kept returning 200). So it is safe to pre-create the
  redirect while the rename CR is still open — it starts working the moment the
  CR merges.
- GitBook's own auto-created redirects are **307 temporary** (`permanent: false`).
  Create them explicitly with `permanent: true` for a rename so they are 301s.

```bash
# list
GET  /v1/orgs/Ksgcu2spQyb8ZrFM3st6/sites/site_VMiJI/redirects
# create
POST /v1/orgs/Ksgcu2spQyb8ZrFM3st6/sites/site_VMiJI/redirects
{"source":"/features/managing-your-wallet/seed-keys",
 "destination":{"kind":"site-page","siteSpaceId":"sitesp_ugha9","pageId":"<pageId>"},
 "permanent":true,"captureWildcard":false}
```

`pageId` is stable across a rename, so use the page's existing id. siteSpace ids:

| Section | siteSpaceId |
|---|---|
| Home | `sitesp_5uY53` |
| Get Started 6.x | `sitesp_Yi4ZE` |
| Cryptocurrencies | `sitesp_4yrGG` |
| Features 6.x | `sitesp_ugha9` |
| Cake Pay | `sitesp_8AyvA` |
| Cupcake | `sitesp_YiJCt` |
| FAQ | `sitesp_rh19L` |
| Tutorials | `sitesp_0kesN` |
| Support | `sitesp_pICzk` |

## Variant spaces are separate content

`Get Started` and `Features` each have a **5.x** space as well as 6.x
(`8LA6pa3iUU0P3UwSsckD`, `fAEZgu32eMDqLiRpwhSd`). The 5.x spaces have their own
copies of pages like `setup/restore-existing-wallet/seed-or-keys`, and their
relative links resolve inside 5.x. Do **not** rewrite 5.x links when renaming a
6.x page — 5.x documents the older app, where the old labels are correct.

