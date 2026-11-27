#!/usr/bin/env python3
"""Learning loop for the AI review: turn how people answered past findings into lesson proposals.

  collect --out DIR           Read PRs merged in the last 30 days (gh): every AI finding thread (hidden marker) with its
                              outcome, replies and reactions, and the inline comments people wrote (and whether the AI
                              had a finding at the same place). Writes feedback.json, prints a markdown metrics table.
                              No model. Sets `count` in $GITHUB_OUTPUT: threads + uncovered human comments.
  propose --feedback FILE --out FILE
                              Model pass (read-only tools). Returns {title, body, edits} as data.
  apply --proposal FILE       No model, no key. Applies the edits to the Lessons block of REVIEW.md only, checks the result
                              and writes .review-learn/title.txt and body.md when something changed.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import review  # noqa: E402

REVIEW_MD = Path("REVIEW.md")
BEGIN, END = "<!-- lessons:begin -->", "<!-- lessons:end -->"
LEARN_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["title", "body", "edits"],
    "properties": {"title": {"type": "string"}, "body": {"type": "string"},
                   "edits": {"type": "array", "maxItems": 25, "items": {
                       "type": "object", "additionalProperties": False, "required": ["path", "old", "new"],
                       "properties": {"path": {"type": "string"}, "old": {"type": "string"}, "new": {"type": "string"}}}}},
}
HUMAN = re.compile(r"OWNER|MEMBER|COLLABORATOR")


def reaction_count(group_list, content):
    for g in group_list or []:
        if g.get("content") == content:
            return (g.get("reactors") or {}).get("totalCount", 0)
    return 0


def outcome(t):
    up, down = t["reactions"]["up"], t["reactions"]["down"]
    if down > up or (down == 0 and t["replies"] and t["state"] == "open"):
        return "rejected"
    if t["state"] in ("resolved", "outdated") or up > down:
        return "accepted"
    return "open"


def collect_pr(repo, number):
    threads = []
    for t in review.review_threads(repo, number):
        nodes = (t.get("comments") or {}).get("nodes") or []
        if not nodes:
            continue
        m = review.FINDING_MARK.search(nodes[0].get("body") or "")
        if not m:
            continue
        state = "resolved" if t.get("isResolved") else "outdated" if t.get("isOutdated") else "open"
        item = {"pr": number, "fp": m.group(1), "category": m.group(2), "severity": m.group(3), "path": t.get("path"), "line": t.get("line"),
                "state": state, "title": review.clip((nodes[0].get("body") or "").split("\n", 1)[0], 200),
                "reactions": {"up": reaction_count(nodes[0].get("reactionGroups"), "THUMBS_UP"), "down": reaction_count(nodes[0].get("reactionGroups"), "THUMBS_DOWN")},
                "replies": [{"user": (r.get("author") or {}).get("login"), "body": review.clip(r.get("body"), 600)} for r in nodes[1:]]}
        item["outcome"] = outcome(item)
        threads.append(item)
    return threads


def human_comments(repo, number, threads):
    out = []
    comments = review.gh_json("api", "--paginate", f"repos/{repo}/pulls/{number}/comments", default=[]) or []
    for c in comments:
        user = c.get("user") or {}
        if user.get("type") == "Bot" or not HUMAN.search(c.get("author_association") or "") or c.get("in_reply_to_id"):
            continue
        line = c.get("line") or c.get("original_line") or 0
        covered = any(t["path"] == c.get("path") and t["line"] and abs((t["line"] or 0) - line) <= 5 for t in threads)
        out.append({"pr": number, "path": c.get("path"), "line": line, "user": user.get("login"), "body": review.clip(c.get("body"), 600), "covered": covered})
    return out


def metrics_markdown(threads, humans, prs):
    out = [f"## AI review feedback, last 30 days\n", f"{len(prs)} merged PR(s), {len(threads)} AI finding thread(s), {len(humans)} human inline comment(s).\n"]
    cats = sorted({t["category"] for t in threads})
    if threads:
        out.append("| Category | Findings | Accepted | Rejected | Open | Acceptance (accepted / decided) |\n|---|---|---|---|---|---|")
        for c in cats + ["all"]:
            rows = [t for t in threads if c == "all" or t["category"] == c]
            a, r, o = (sum(1 for t in rows if t["outcome"] == k) for k in ("accepted", "rejected", "open"))
            out.append(f"| {c} | {len(rows)} | {a} | {r} | {o} | {review_pct(a, a + r)} |")
    missed = [h for h in humans if not h["covered"]]
    out.append(f"\nHuman comments the AI did not cover: {len(missed)} of {len(humans)}.")
    out.append("\nOutcome rules: accepted = resolved, outdated by a code change, or more 👍 than 👎; rejected = more 👎, or a person replied and the thread stayed open.")
    return "\n".join(out)


def review_pct(a, b):
    return "n/a" if not b else f"{a / b * 100:.0f}%"


def cmd_collect(a):
    repo = os.environ["REPO"]
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=30)).strftime("%Y-%m-%d")
    prs = review.gh_json("pr", "list", "--repo", repo, "--state", "merged", "--search", f"merged:>={since}", "--limit", "100", "--json", "number,mergedAt", default=[]) or []
    threads, humans = [], []
    for pr in prs:
        t = collect_pr(repo, pr["number"])
        threads += t
        humans += human_comments(repo, pr["number"], t)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "feedback.json").write_text(json.dumps({"since": since, "prs": [p["number"] for p in prs], "threads": threads, "human_comments": humans}, indent=1), encoding="utf-8")
    md = metrics_markdown(threads, humans, prs)
    print(md)
    count = len(threads) + sum(1 for h in humans if not h["covered"])
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write(f"count={count}\n")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(md + "\n")
    return 0


def cmd_propose(a):
    prompt = (review.HERE / "prompts" / "learn.md").read_text(encoding="utf-8") + f"\n\nFeedback file: `{a.feedback}`.\n"
    out, meta = review.call_claude(prompt, LEARN_SCHEMA, effort=review.CONFIG["verifier_effort"], max_turns=40, label="learn")
    Path(a.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"proposal: {len(out.get('edits', []))} edit(s), cost_usd={meta.get('cost_usd')}")
    return 0


def lessons_block(text):
    i, j = text.find(BEGIN), text.find(END)
    if i < 0 or j < i or text.count(BEGIN) != 1 or text.count(END) != 1:
        raise review.ReviewError("REVIEW.md must hold exactly one lessons:begin and one lessons:end marker.")
    return text[: i + len(BEGIN)], text[i + len(BEGIN): j], text[j:]


def cmd_apply(a):
    prop = json.loads(Path(a.proposal).read_text(encoding="utf-8"))
    edits = prop.get("edits") or []
    if not edits:
        print("The proposal has no edits; nothing to open.")
        return 0
    title, body = (prop.get("title") or "").strip(), (prop.get("body") or "").strip()
    if not title or "\n" in title or len(title) > 120 or not body or len(body) > 3000:
        raise review.ReviewError("A proposal with edits needs a one-line title (<= 120 chars) and a body (<= 3000 chars).")
    original = REVIEW_MD.read_text(encoding="utf-8")
    pre, block, post = lessons_block(original)
    for e in edits:
        if e.get("path") != "REVIEW.md" or not e.get("old"):
            raise review.ReviewError("Edits may only change REVIEW.md and must give the exact old text.")
        if block.count(e["old"]) != 1:
            raise review.ReviewError(f"An edit's old text must occur exactly once inside the lessons block: {e['old'][:60]!r}")
        block = block.replace(e["old"], review.redact(e["new"]), 1)
    lines = [l for l in block.splitlines() if l.strip() and not l.strip().startswith("<!--")]
    if len(lines) > 20 or any(not re.match(r"- L\d+ \([a-z]+\): .{10,300}\. Evidence: PR #\d+", l) for l in lines):
        raise review.ReviewError("Lessons must be at most 20 lines of the form '- L<n> (<category>): <rule>. Evidence: PR #<n>'.")
    if not lines:
        block = "\n<!-- No lessons yet. -->\n"
    elif not block.startswith("\n"):
        block = "\n" + block
    if not block.endswith("\n"):
        block += "\n"
    new = pre + block + post
    if new == original:
        print("The edits change nothing.")
        return 0
    REVIEW_MD.write_text(new, encoding="utf-8")
    d = Path(".review-learn")
    d.mkdir(exist_ok=True)
    (d / "title.txt").write_text(title + "\n", encoding="utf-8")
    (d / "body.md").write_text(review.redact(body) + "\n", encoding="utf-8")
    print(f"Applied {len(edits)} edit(s) to the lessons block.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect"); c.add_argument("--out", required=True)
    p = sub.add_parser("propose"); p.add_argument("--feedback", required=True); p.add_argument("--out", required=True)
    x = sub.add_parser("apply"); x.add_argument("--proposal", required=True)
    a = ap.parse_args(argv)
    try:
        return {"collect": cmd_collect, "propose": cmd_propose, "apply": cmd_apply}[a.cmd](a)
    except review.ReviewError as e:
        print(f"::error::{e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
