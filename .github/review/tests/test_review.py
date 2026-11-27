"""Tests for the review scripts. Run: python3 -m unittest discover -s .github/review/tests -v

No network, no model: `claude` and `gh` are replaced by small stubs on PATH.
"""
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "evals"))
import learn  # noqa: E402
import review  # noqa: E402
import score  # noqa: E402

DIFF = """diff --git a/streak.ts b/streak.ts
index 1..2 100644
--- a/streak.ts
+++ b/streak.ts
@@ -10,3 +10,4 @@ export function x() {
 context
-removed
+added one
+added two
 tail
@@ -30,1 +31,2 @@
 keep
+late
diff --git a/gone.ts b/gone.ts
deleted file mode 100644
--- a/gone.ts
+++ /dev/null
@@ -1,2 +0,0 @@
-a
-b
"""


def finding(i, **kw):
    f = {"id": i, "severity": "Major", "category": "spec", "path": "streak.ts", "line": 12, "title": f"title {i}", "scenario": "s", "evidence": ["e"], "sources": ["SPEC.md"], "confidence": 0.8}
    f.update(kw)
    return f


def stub(dirpath, name, body):
    p = Path(dirpath) / name
    p.write_text("#!/usr/bin/env python3\n" + body, encoding="utf-8")
    p.chmod(p.stat().st_mode | stat.S_IEXEC)


class Pure(unittest.TestCase):
    def test_commentable_lines(self):
        m = review.commentable_lines(DIFF)
        self.assertEqual(m["streak.ts"], {10, 11, 12, 13, 31, 32})
        self.assertNotIn("gone.ts", m)

    def test_leak_detection_handles_encodings_and_separators(self):
        key = "sk-ant-abcdef123456"
        self.assertTrue(review.leaks(f"x {key} y", key))
        self.assertTrue(review.leaks("sk-ant-abc def\n123456", key))
        self.assertTrue(review.leaks(key[::-1], key))
        self.assertFalse(review.leaks("nothing here", key))
        self.assertFalse(review.leaks("anything", ""))

    def test_clean_candidates_drops_unpostable_and_caps(self):
        bad = [finding("a", path="../x"), finding("b", path="/abs"), finding("c", line=0), finding("d", severity="Huge"), finding("e", title=" ")]
        good = [finding("g1", severity="Minor", confidence=0.9), finding("g2", severity="Critical", confidence=0.5), finding("g1")]
        kept = review.clean_candidates({"findings": bad + good})
        self.assertEqual([f["id"] for f in kept], ["g2", "g1"])  # Critical first, duplicate id dropped

    def test_assemble_splits_by_verdict(self):
        fs = [finding("f1"), finding("f2"), finding("f3"), finding("f4")]
        verdicts = {"verdicts": [
            {"id": "f1", "verdict": "confirmed", "reason": "r", "severity": "Minor", "confidence": 0.9},
            {"id": "f2", "verdict": "refuted", "reason": "no", "severity": "Major", "confidence": 0.1},
            {"id": "f3", "verdict": "uncertain", "reason": "?", "severity": "Major", "confidence": 0.5}]}
        r = review.assemble("a" * 40, {"requirements": [], "context_read": [], "notes": ""}, fs, verdicts)
        self.assertEqual([f["id"] for f in r["findings"]], ["f1"])
        self.assertEqual(r["findings"][0]["severity"], "Minor")  # the verifier's severity wins
        self.assertEqual([f["id"] for f in r["needs_look"]], ["f3", "f4"])  # no verdict = needs a look, never confirmed
        self.assertEqual(r["dropped"][0]["id"], "f2")
        self.assertIn("scenario", r["dropped"][0])

    def test_summary_and_inline_render(self):
        f = dict(finding("f1"), fp="abc123", verifier="ok")
        r = {"sha": "b" * 40, "requirements": [{"text": "a|b", "source": "SPEC.md", "status": "gap", "evidence": "x"}], "findings": [f], "needs_look": [],
             "dropped": [], "candidates": 1, "context_read": ["SPEC.md"], "notes": "", "meta": {"model": "m", "effort": "e", "verifier_effort": "v", "cost_usd": 1}}
        text, blob = review.summary_markdown(r, [])
        self.assertIn("미충족", text)
        self.assertIn("a\\|b", text)  # table cell escaped
        self.assertTrue(blob)
        body = review.inline_body(f)
        self.assertIn("<!-- ai-finding:abc123 cat=spec sev=Major -->", body)
        self.assertTrue(review.FINDING_MARK.search(body))

    def test_redact(self):
        self.assertNotIn("sk-ant-abcdefgh12345", review.redact("key sk-ant-abcdefgh12345 end"))

    def test_fingerprint_is_stable_across_wording_noise(self):
        a = review.fingerprint(finding("x", title="Streak  breaks!"))
        b = review.fingerprint(finding("y", title="streak breaks"))
        self.assertEqual(a, b)


class Score(unittest.TestCase):
    def test_gate_and_aggregate(self):
        rows = [
            {"id": "a", "clean": False, "expected": 2, "matched_final": 2, "matched_candidate": 2, "confirmed": 2, "good": 2, "false_positive_confirmed": 0, "false_positive_all": 1, "false_positive_killed": 1, "detail": [], "false_positive_titles": []},
            {"id": "b", "clean": True, "expected": 0, "matched_final": 0, "matched_candidate": 0, "confirmed": 1, "good": 0, "false_positive_confirmed": 1, "false_positive_all": 1, "false_positive_killed": 0, "detail": [], "false_positive_titles": ["x"]}]
        agg = score.aggregate(rows)
        self.assertEqual(agg["recall"], 1.0)
        self.assertAlmostEqual(agg["precision"], 2 / 3)
        self.assertEqual(agg["false_positives_on_clean_cases"], 1)
        self.assertEqual(agg["verifier_false_positive_kill_rate"], 0.5)
        th = {"min_recall": 0.75, "min_precision": 0.6, "max_false_positives_on_clean_cases": 0, "max_recall_drop_vs_baseline": 0.15}
        self.assertEqual(len(score.gate(agg, th, {})), 1)
        agg["false_positives_on_clean_cases"] = 0
        self.assertEqual(score.gate(agg, th, {}), [])
        self.assertEqual(len(score.gate(agg, th, {"recall": 1.4})), 1)  # dropped more than 0.15 below the baseline

    def test_case_scoring_uses_final_status(self):
        case = {"id": "c", "clean": False, "expected": [{"id": "e1"}]}
        reported = [{"id": "f1", "status": "refuted", "title": "t"}]
        judged = {"expected": [{"id": "e1", "matched_finding_ids": ["f1"], "note": "n"}], "findings": [{"id": "f1", "class": "expected", "note": ""}]}
        row = score.score_case(case, {}, judged, reported)
        self.assertEqual((row["matched_candidate"], row["matched_final"]), (1, 0))  # the verifier lost a true finding

    def test_every_case_is_valid(self):
        for d in score.case_dirs(score.CASES):
            score.load_case(d)


class Learn(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cwd = os.getcwd()
        os.chdir(self.tmp.name)
        Path("REVIEW.md").write_text("# R\n\n## Lessons\n\nintro\n\n" + learn.BEGIN + "\n<!-- No lessons yet. -->\n" + learn.END + "\n\n## After\n", encoding="utf-8")

    def tearDown(self):
        os.chdir(self.cwd)
        self.tmp.cleanup()

    def proposal(self, new, path="REVIEW.md", old="<!-- No lessons yet. -->"):
        Path("p.json").write_text(json.dumps({"title": "t", "body": "b", "edits": [{"path": path, "old": old, "new": new}]}), encoding="utf-8")
        return learn.main(["apply", "--proposal", "p.json"])

    def test_applies_a_wellformed_lesson(self):
        lesson = "- L1 (spec): Check that streak tests change together with the Streak rules in SPEC.md. Evidence: PR #7, #9."
        self.assertEqual(self.proposal(lesson), 0)
        text = Path("REVIEW.md").read_text(encoding="utf-8")
        self.assertIn(lesson, text)
        self.assertNotIn("No lessons yet", text)
        self.assertTrue(text.endswith("## After\n"))
        self.assertTrue(Path(".review-learn/title.txt").exists())

    def test_rejects_edits_outside_the_block_or_other_files_or_bad_format(self):
        self.assertEqual(self.proposal("x", path="app.ts"), 2)
        self.assertEqual(self.proposal("x", old="## After"), 2)
        self.assertEqual(self.proposal("- not a lesson line at all"), 2)
        self.assertEqual(self.proposal("- L1 (spec): rule that is long enough here. Evidence: PR #1", old=""), 2)
        self.assertIn("No lessons yet", Path("REVIEW.md").read_text(encoding="utf-8"))

    def test_empty_proposal_changes_nothing(self):
        Path("p.json").write_text(json.dumps({"title": "", "body": "", "edits": []}), encoding="utf-8")
        self.assertEqual(learn.main(["apply", "--proposal", "p.json"]), 0)
        self.assertFalse(Path(".review-learn/title.txt").exists())

    def test_outcome_rules(self):
        base = {"state": "open", "replies": [], "reactions": {"up": 0, "down": 0}}
        self.assertEqual(learn.outcome(dict(base)), "open")
        self.assertEqual(learn.outcome(dict(base, state="outdated")), "accepted")
        self.assertEqual(learn.outcome(dict(base, reactions={"up": 0, "down": 1})), "rejected")
        self.assertEqual(learn.outcome(dict(base, replies=[{"user": "u", "body": "no"}])), "rejected")
        self.assertEqual(learn.outcome(dict(base, state="resolved", replies=[{"user": "u", "body": "ok"}])), "accepted")


class Pipeline(unittest.TestCase):
    """call_claude and run, with a stub `claude` that answers by prompt."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.bin = Path(self.tmp.name) / "bin"
        self.bin.mkdir()
        self.old_path = os.environ.get("PATH")
        os.environ["PATH"] = f"{self.bin}:{self.old_path}"
        for k in review.SECRET_ENV:
            os.environ.pop(k, None)
        os.environ["ANTHROPIC_API_KEY"] = "sk-ant-api-secretvalue123456"
        os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = "sk-ant-oat-subscriptionvalue987654"

    def tearDown(self):
        os.environ["PATH"] = self.old_path
        for k in review.SECRET_ENV:
            os.environ.pop(k, None)
        self.tmp.cleanup()

    def claude(self, body):
        stub(self.bin, "claude", "import json, os, sys\nprompt = sys.stdin.read()\n" + body)

    def test_returns_structured_output_with_api_key(self):
        self.claude("print(json.dumps({'is_error': False, 'structured_output': {'verdicts': []}, 'total_cost_usd': 0.5, 'num_turns': 3, 'subtype': 'success', 'cred': os.environ.get('ANTHROPIC_API_KEY','')[:7]}))")
        out, meta = review.call_claude("p", review.VERDICTS_SCHEMA, effort="high", max_turns=3)
        self.assertEqual(out, {"verdicts": []})
        self.assertEqual(meta["cred"], "api")

    def test_falls_back_to_subscription_only_on_quota(self):
        self.claude("""
if os.environ.get('ANTHROPIC_API_KEY'):
    print(json.dumps({'is_error': True, 'result': 'Credit balance is too low', 'subtype': 'error'}))
else:
    assert os.environ.get('CLAUDE_CODE_OAUTH_TOKEN')
    print(json.dumps({'is_error': False, 'structured_output': {'verdicts': []}}))
""")
        out, meta = review.call_claude("p", review.VERDICTS_SCHEMA, effort="high", max_turns=3)
        self.assertEqual(meta["cred"], "subscription")

    def test_other_failures_do_not_spend_subscription_quota(self):
        self.claude("print(json.dumps({'is_error': True, 'result': 'Invalid API key', 'subtype': 'error'}))\nopen(os.environ['MARK'], 'a').write('x')")
        os.environ["MARK"] = str(Path(self.tmp.name) / "mark")
        with self.assertRaises(review.ReviewError):
            review.call_claude("p", review.VERDICTS_SCHEMA, effort="high", max_turns=3)
        self.assertEqual(Path(os.environ["MARK"]).read_text(), "x")  # called once, not twice

    def test_no_key_uses_subscription(self):
        os.environ.pop("ANTHROPIC_API_KEY")
        self.claude("assert not os.environ.get('ANTHROPIC_API_KEY')\nprint(json.dumps({'is_error': False, 'structured_output': {'verdicts': []}}))")
        _, meta = review.call_claude("p", review.VERDICTS_SCHEMA, effort="high", max_turns=3)
        self.assertEqual(meta["cred"], "subscription")

    def test_key_in_output_aborts(self):
        self.claude("print(json.dumps({'is_error': False, 'structured_output': {'verdicts': [{'id': 'x', 'verdict': 'confirmed', 'reason': 'key is ' + os.environ['ANTHROPIC_API_KEY'], 'severity': 'Minor', 'confidence': 1}]}}))")
        with self.assertRaises(SystemExit) as cm:
            review.call_claude("p", review.VERDICTS_SCHEMA, effort="high", max_turns=3)
        self.assertEqual(cm.exception.code, 3)

    def test_git_token_is_not_passed_to_claude(self):
        os.environ["GH_TOKEN"] = "ghp_" + "a" * 30
        try:
            self.claude("print(json.dumps({'is_error': False, 'structured_output': {'verdicts': []}, 'seen': bool(os.environ.get('GH_TOKEN'))}))\nassert not os.environ.get('GH_TOKEN')")
            review.call_claude("p", review.VERDICTS_SCHEMA, effort="high", max_turns=3)
        finally:
            os.environ.pop("GH_TOKEN")

    def test_run_reviews_then_verifies(self):
        self.claude("""
if 'adversarial verifier' in prompt:
    ids = [l.split('"')[3] for l in prompt.splitlines() if l.strip().startswith('"id"')]
    v = [{'id': i, 'verdict': 'confirmed' if i == 'f1' else 'refuted', 'reason': 'r', 'severity': 'Major', 'confidence': 0.9} for i in ids]
    print(json.dumps({'is_error': False, 'structured_output': {'verdicts': v}, 'total_cost_usd': 0.2}))
else:
    f = lambda i: {'id': i, 'severity': 'Major', 'category': 'spec', 'path': 'streak.ts', 'line': 3, 'title': 't' + i, 'scenario': 's', 'evidence': ['e'], 'sources': ['SPEC.md'], 'confidence': 0.8}
    print(json.dumps({'is_error': False, 'structured_output': {'requirements': [], 'findings': [f('f1'), f('f2')], 'context_read': ['SPEC.md'], 'notes': ''}, 'total_cost_usd': 1.0}))
""")
        out = Path(self.tmp.name) / "out"
        rc = review.main(["run", "--context", ".review-context", "--out", str(out), "--sha", "c" * 40])
        self.assertEqual(rc, 0)
        r = json.loads((out / "review.json").read_text())
        self.assertEqual([f["id"] for f in r["findings"]], ["f1"])
        self.assertEqual(len(r["dropped"]), 1)
        self.assertEqual(r["meta"]["cost_usd"], 1.2)


class Collect(unittest.TestCase):
    def test_case_mode_builds_the_context_from_git(self):
        case_dir = next(d for d in score.case_dirs(score.CASES) if d.name == "habit-name-case-sensitive")
        case = score.load_case(case_dir)
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            ok = subprocess.run(["git", "clone", "-q", str(ROOT.parents[1]), str(repo)], capture_output=True)
            if ok.returncode or subprocess.run(["git", "cat-file", "-e", case["base_sha"]], cwd=repo, capture_output=True).returncode:
                self.skipTest("the case's base commit is not in this clone")
            git = lambda *a: subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *a], cwd=repo, check=True, capture_output=True)
            git("checkout", "-q", case["base_sha"])
            git("apply", str(case_dir / case["patch"]))
            git("commit", "-q", "-am", "seed")
            old = os.getcwd()
            os.chdir(repo)
            try:
                self.assertEqual(review.main(["collect", "--out", ".review-context", "--case", str(case_dir)]), 0)
            finally:
                os.chdir(old)
            ctx = repo / ".review-context"
            self.assertIn("app.ts", (ctx / "diff.patch").read_text())
            self.assertIn("app.ts", (ctx / "history.md").read_text())
            self.assertTrue((ctx / "base" / "SPEC.md").exists())
            self.assertEqual(json.loads((ctx / "pr.json").read_text())["title"], case["pr"]["title"])


class Live(unittest.TestCase):
    """collect and post in live mode with a stub `gh` that answers canned JSON and logs every call."""

    GH = r'''
import json, os, sys
a = sys.argv[1:]
log = open(os.environ["GH_LOG"], "a"); log.write(json.dumps(a) + "\n"); log.close()
j = " ".join(a)
if a[:2] == ["pr", "view"] and a[2] == "5":
    print(json.dumps({"number": 5, "title": "Fix streak", "body": "Closes #9", "headRefName": "fix/9-streak", "baseRefName": "main",
                      "files": [{"path": "streak.ts", "additions": 3, "deletions": 1}], "closingIssuesReferences": [{"number": 9}]}))
elif a[:2] == ["pr", "view"]:
    print(json.dumps({"number": int(a[2]), "title": "Older PR", "body": "body", "mergedAt": "2026-11-01", "state": "MERGED"}))
elif a[:2] == ["pr", "diff"]:
    print(open(os.environ["DIFF_FILE"]).read())
elif a[:2] == ["issue", "view"]:
    print(json.dumps({"number": 9, "title": "Streak shows 1", "body": "Issue body", "state": "OPEN", "labels": [], "comments": [{"author": {"login": "u"}, "body": "c"}]}))
elif a[:2] == ["api", "graphql"]:
    body = "<!-- ai-finding:abc123 cat=spec sev=Major -->"
    print(json.dumps({"data": {"repository": {"pullRequest": {"reviewThreads": {"nodes": [{"isResolved": False, "isOutdated": True, "path": "streak.ts", "line": 4,
        "comments": {"nodes": [{"databaseId": 1, "body": "**old** finding\n" + body, "author": {"login": "github-actions"}, "reactionGroups": []}]}}]}}}}}))
elif "commits/" in j and j.endswith("// empty") or ("/pulls" in j and "commits/" in j):
    print("7")
elif "pulls/7/comments" in j and "--paginate" in j and "--jq" not in j:
    print(json.dumps([{"path": "streak.ts", "user": {"login": "owner"}, "author_association": "OWNER", "body": "please keep the grace day"}]))
elif "pulls/5/comments" in j and "--jq" in j:
    print("")
'''

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.bin = Path(self.tmp.name) / "bin"
        self.bin.mkdir()
        stub(self.bin, "gh", self.GH)
        (Path(self.tmp.name) / "diff").write_text(DIFF, encoding="utf-8")
        self.env = {"PATH": f"{self.bin}:{os.environ['PATH']}", "GH_LOG": str(Path(self.tmp.name) / "log"), "DIFF_FILE": str(Path(self.tmp.name) / "diff"),
                    "REPO": "o/r", "PR": "5", "GITHUB_REPOSITORY": "o/r"}
        self.saved = {k: os.environ.get(k) for k in self.env}
        os.environ.update(self.env)

    def tearDown(self):
        for k, v in self.saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self.tmp.cleanup()

    def test_collect_builds_every_context_file(self):
        base = subprocess.run(["git", "rev-parse", "HEAD~0"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
        os.environ["BASE_SHA"] = base
        old = os.getcwd()
        os.chdir(ROOT.parents[1])
        try:
            self.assertEqual(review.main(["collect", "--out", str(Path(self.tmp.name) / "ctx")]), 0)
        finally:
            os.chdir(old)
            os.environ.pop("BASE_SHA")
        ctx = Path(self.tmp.name) / "ctx"
        self.assertIn("Streak shows 1", (ctx / "issues.md").read_text())
        self.assertIn("finding `abc123`", (ctx / "previous-review.md").read_text())
        self.assertIn("outdated", (ctx / "previous-review.md").read_text())
        self.assertIn("streak.ts", (ctx / "history.md").read_text())
        self.assertIn("Older PR", (ctx / "history.md").read_text())
        self.assertIn("please keep the grace day", (ctx / "history.md").read_text())

    def test_post_places_inline_only_on_diff_lines_and_summarises_the_rest(self):
        f_on, f_off = dict(finding("f1", line=12), fp="aaaaaaaaaa", verifier="v"), dict(finding("f2", line=99), fp="bbbbbbbbbb", verifier="v")
        r = {"sha": "d" * 40, "requirements": [], "findings": [f_on, f_off], "needs_look": [], "dropped": [], "candidates": 2, "context_read": [], "notes": "",
             "meta": {"model": "m", "effort": "e", "verifier_effort": "v", "cost_usd": 0}}
        path = Path(self.tmp.name) / "review.json"
        path.write_text(json.dumps(r), encoding="utf-8")
        self.assertEqual(review.main(["post", "--review", str(path), "--pr", "5", "--sha", "d" * 40]), 0)
        calls = [json.loads(l) for l in (Path(self.tmp.name) / "log").read_text().splitlines()]
        inline = [c for c in calls if c[:2] == ["api", "repos/o/r/pulls/5/comments"] and "-f" in c]
        summary = [c for c in calls if c[:2] == ["api", "repos/o/r/issues/5/comments"]]
        self.assertEqual(len(inline), 1)
        self.assertIn("line=12", inline[0])
        self.assertEqual(len(summary), 1)
        body = next(x for x in summary[0] if x.startswith("body="))
        self.assertTrue(body.startswith("body=<!-- ai-review:" + "d" * 40 + " -->"))
        self.assertIn("diff 줄에 붙이지 못한 지적", body)  # the finding outside the diff is kept in the summary


if __name__ == "__main__":
    unittest.main()
