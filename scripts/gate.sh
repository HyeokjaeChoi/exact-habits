#!/bin/sh
# Local quality gates. One script holds the checks.
# The git hooks, the Claude Code hooks and CI call this script.
#
#   scripts/gate.sh fast            format the staged files, then run the fast checks (pre-commit)
#   scripts/gate.sh full            fast checks, the Exact commit check, the web tests (pre-push)
#   scripts/gate.sh check           fast checks only (Claude Code Stop hook)
#   scripts/gate.sh ci              checks that need no Exact checkout (CI)
#   scripts/gate.sh format <file>…  format the named .contract and .ts files
#
# The checks read the working tree, not the index and not the pushed commits.
set -eu
cd "$(dirname "$0")/.."
# A git hook sets these variables. They break git and Exact in other directories.
unset GIT_DIR GIT_WORK_TREE GIT_PREFIX
export PATH="$HOME/.bun-1.4.2/bin:$HOME/.cargo/bin:$PATH" EXACT_FEEDBACK=0

fail() {
  echo "gate: $*" >&2
  exit 1
}

need_modules() {
  [ -x node_modules/.bin/oxfmt ] && [ -x node_modules/.bin/oxlint ] ||
    fail "node_modules is missing. Run: bun install"
}

# Format the named files. Skip generated files and other file types.
format() {
  for file in "$@"; do
    file=${file#"$PWD"/}
    [ -f "$file" ] || continue
    case $file in
      /* | .exact/* | node_modules/* | app.contract.d.ts) ;;
      *.contract) bun exact.mjs contract fmt "$file" ;;
      *.ts) need_modules && node_modules/.bin/oxfmt "$file" ;;
    esac
  done
}

format_staged() {
  staged=$(git diff --cached --name-only --diff-filter=ACMR -- '*.contract' '*.ts')
  [ -n "$staged" ] || return 0
  for file in $staged; do
    git diff --quiet -- "$file" ||
      fail "$file is only partly staged. The hook does not format it. Stage the full file, or commit the other part first."
  done
  # shellcheck disable=SC2086
  format $staged
  # shellcheck disable=SC2086
  git add -- $staged
}

lint() {
  need_modules
  node_modules/.bin/oxlint
}

check() {
  # --errors-only: `exact:content` reports one warning today. Block errors only.
  bun exact.mjs contract build app.contract --json --errors-only ||
    fail "contract build reports the errors above."
  lint
  bun test
}

exact_commit() {
  want=$(cat .exact-commit)
  have=$(git -C "${EXACT:-.exact/checkout}" rev-parse HEAD)
  case $have in
    "$want"*) ;;
    *) fail "the Exact checkout is at $have. .exact-commit pins $want. Check out the pinned commit, or change .exact-commit in a PR." ;;
  esac
}

case ${1:-} in
  fast)
    need_modules
    format_staged
    check
    ;;
  full)
    check
    exact_commit # before the web tests: it takes 10 ms, the web tests take 45 s
    bun exact.mjs test web
    ;;
  check) check ;;
  ci)
    need_modules
    # shellcheck disable=SC2046
    node_modules/.bin/oxfmt --check $(git ls-files '*.ts')
    lint
    bun test
    ;;
  format)
    shift
    format "$@"
    ;;
  *) fail "usage: scripts/gate.sh fast|full|check|ci|format <file>…" ;;
esac
