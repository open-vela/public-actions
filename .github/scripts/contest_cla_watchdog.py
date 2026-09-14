#!/usr/bin/env python3
"""Watchdog for contest PRs whose required CLA status never got reported.

Contest repositories gate merges on a required status check (``cla/signature``)
that is produced by the ``cla`` workflow. Occasionally GitHub drops the event
that should start that workflow, so the status is never posted and the PR stays
blocked forever with nothing to click on:

  * the whole repository stops dispatching Actions events (no workflow run
    record is created at all), or
  * a single run is created but stays ``queued`` and is never scheduled.

Both look identical from the PR page: the required check sits pending forever.

Detection deliberately does NOT look at ``actions/runs`` counts -- GitHub ages
old run records out, so a repository with zero runs may simply have been idle.
The only reliable signal is: an open PR whose head commit carries no
``cla/signature`` status at all.

Remedy is staged:

  1. First sighting of a given head commit -> post ``/check-cla``, which is the
     documented way to re-trigger the check. This fixes the "single run was
     swallowed" case on its own.
  2. Still missing on a later pass, even though we already retried this exact
     head commit -> the repository is dropping events entirely. That needs a
     human to reset Actions on the repository, so the run fails loudly with the
     exact commands in the job summary.

The retry marker is stored in the comment we post, so no external state is
needed: seeing our own marker for the current head commit is what tells a later
run that the cheap remedy has already been tried.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

API = "https://api.github.com"
GRAPHQL = f"{API}/graphql"
MARKER_PREFIX = "<!-- contest-cla-watchdog retry oid="

SEARCH_QUERY = """
query($q: String!, $after: String) {
  search(query: $q, type: ISSUE, first: 50, after: $after) {
    issueCount
    pageInfo { hasNextPage endCursor }
    nodes {
      ... on PullRequest {
        number
        url
        createdAt
        isDraft
        repository { name }
        commits(last: 1) {
          nodes {
            commit {
              oid
              committedDate
              statusCheckRollup {
                contexts(first: 100) {
                  nodes {
                    ... on StatusContext { context }
                    ... on CheckRun { name }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""


def env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def env_flag(name: str) -> bool:
    return env(name).lower() in ("1", "true", "yes")


def request(url: str, token: str, method: str = "GET", payload: dict | None = None) -> dict | list:
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read() or b"null")


def graphql(token: str, variables: dict) -> dict:
    data = request(GRAPHQL, token, "POST", {"query": SEARCH_QUERY, "variables": variables})
    if data.get("errors"):
        raise RuntimeError(f"GraphQL errors: {json.dumps(data['errors'])}")
    return data["data"]


def parse_ts(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def collect_open_prs(token: str, org: str, prefix: str) -> list[dict]:
    """Return every open PR in `org` whose repository name starts with `prefix`.

    One GraphQL search page carries the PR, its head commit and that commit's
    status contexts, so the whole scan costs a handful of calls instead of two
    REST calls per PR.
    """
    out: list[dict] = []
    cursor = None
    while True:
        page = graphql(token, {"q": f"org:{org} is:pr is:open", "after": cursor})["search"]
        for node in page["nodes"]:
            if not node:
                continue
            name = node["repository"]["name"]
            if not name.startswith(prefix):
                continue
            commits = node["commits"]["nodes"]
            if not commits:
                continue
            commit = commits[0]["commit"]
            rollup = commit.get("statusCheckRollup") or {}
            contexts = {
                c.get("context") or c.get("name")
                for c in (rollup.get("contexts", {}).get("nodes") or [])
                if c
            }
            out.append(
                {
                    "repo": name,
                    "number": node["number"],
                    "url": node["url"],
                    "created_at": parse_ts(node["createdAt"]),
                    "draft": node["isDraft"],
                    "oid": commit["oid"],
                    "committed_at": parse_ts(commit["committedDate"]),
                    "contexts": contexts,
                }
            )
        if not page["pageInfo"]["hasNextPage"]:
            return out
        cursor = page["pageInfo"]["endCursor"]


def already_retried(token: str, org: str, pr: dict) -> bool:
    """True if a previous pass already posted /check-cla for this head commit."""
    marker = f"{MARKER_PREFIX}{pr['oid']} -->"
    url = f"{API}/repos/{org}/{pr['repo']}/issues/{pr['number']}/comments?per_page=100"
    for comment in request(url, token):
        if marker in (comment.get("body") or ""):
            return True
    return False


def post_retry(token: str, org: str, pr: dict, context: str) -> None:
    body = (
        "/check-cla\n\n"
        f"The required `{context}` status was missing on this pull request's head "
        "commit, which means the CLA workflow never reported back. Re-running the "
        "check automatically.\n\n"
        "No action is needed from you unless the check reports an actual CLA "
        "problem after this run.\n\n"
        f"{MARKER_PREFIX}{pr['oid']} -->"
    )
    request(
        f"{API}/repos/{org}/{pr['repo']}/issues/{pr['number']}/comments",
        token,
        "POST",
        {"body": body},
    )


def write_summary(lines: list[str]) -> None:
    path = env("GITHUB_STEP_SUMMARY")
    text = "\n".join(lines) + "\n"
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(text)
    print(text)


def main() -> int:
    read_token = env("GH_TOKEN")
    if not read_token:
        print("::error::GH_TOKEN is required")
        return 2
    write_token = env("GH_WRITE_TOKEN")
    org = env("ORG", "open-vela")
    prefix = env("REPO_PREFIX", "contest2026")
    context = env("REQUIRED_CONTEXT", "cla/signature")
    min_age = int(env("MIN_AGE_MINUTES", "30") or "30")
    dry_run = env_flag("DRY_RUN")

    prs = collect_open_prs(read_token, org, prefix)
    now = datetime.now(timezone.utc)

    stuck, too_fresh = [], []
    for pr in prs:
        if context in pr["contexts"]:
            continue
        # Anchor the age on whichever happened later: a fork branch can be days
        # old while the PR was opened seconds ago, and vice versa.
        age = (now - max(pr["created_at"], pr["committed_at"])).total_seconds() / 60
        pr["age_minutes"] = int(age)
        (too_fresh if age < min_age else stuck).append(pr)

    retried, escalate, blocked = [], [], []
    for pr in stuck:
        if already_retried(read_token, org, pr):
            escalate.append(pr)
        elif dry_run or not write_token:
            blocked.append(pr)
        else:
            post_retry(write_token, org, pr, context)
            retried.append(pr)

    lines = [
        f"## contest CLA watchdog — `{prefix}*` in `{org}`",
        "",
        f"- open PRs scanned: **{len(prs)}**",
        f"- missing `{context}`: **{len(stuck)}**"
        + (f" (plus {len(too_fresh)} younger than {min_age}min, ignored)" if too_fresh else ""),
    ]
    if retried:
        lines += ["", f"### Re-triggered `/check-cla` ({len(retried)})", ""]
        lines += [f"- {p['url']} — head `{p['oid'][:8]}`, stuck {p['age_minutes']}min" for p in retried]
        lines += ["", "The next pass verifies whether the status showed up."]
    if blocked:
        why = "dry run" if dry_run else "no write token available"
        lines += ["", f"### Would re-trigger `/check-cla` — skipped, {why} ({len(blocked)})", ""]
        lines += [f"- {p['url']} — head `{p['oid'][:8]}`, stuck {p['age_minutes']}min" for p in blocked]
    if escalate:
        lines += [
            "",
            f"### Needs a human ({len(escalate)})",
            "",
            "`/check-cla` was already retried for these head commits and the status is"
            " still missing, so the repository is dropping Actions events entirely."
            " Reset Actions on it and re-trigger:",
            "",
        ]
        for p in escalate:
            lines += [
                f"- {p['url']} — head `{p['oid'][:8]}`, stuck {p['age_minutes']}min",
                "  ```bash",
                f"  R={org}/{p['repo']}",
                "  WF=$(gh api repos/$R/actions/workflows \\",
                "         --jq '.workflows[]|select(.path==\".github/workflows/cla.yml\")|.id')",
                "  gh api -X PUT repos/$R/actions/workflows/$WF/disable",
                "  gh api -X PUT repos/$R/actions/workflows/$WF/enable",
                "  gh api -X PUT repos/$R/actions/permissions -F enabled=false",
                "  gh api -X PUT repos/$R/actions/permissions -F enabled=true -f allowed_actions=all",
                f"  gh api -X POST repos/$R/issues/{p['number']}/comments -f body='/check-cla'",
                "  ```",
            ]
    if not stuck:
        lines += ["", "No stuck PR found."]
    write_summary(lines)

    if escalate:
        print(f"::error::{len(escalate)} contest PR(s) still missing {context} after an automatic retry")
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except urllib.error.HTTPError as exc:
        print(f"::error::HTTP {exc.code} {exc.reason} for {exc.url}")
        sys.exit(2)
    except Exception as exc:  # noqa: BLE001 - surface any failure as a red run
        print(f"::error::{type(exc).__name__}: {exc}")
        sys.exit(2)
