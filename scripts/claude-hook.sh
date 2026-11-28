#!/bin/sh
# Claude Code hooks (.claude/settings.json). Each hook reads its JSON input from stdin.
# Exit 2 sends stderr to the model. No hook starts an LLM.
set -eu
cd "$(dirname "$0")/.."
export PATH="$HOME/.bun-1.4.2/bin:$PATH"
input=$(cat)

case ${1:-} in
  session-start)
    git config core.hooksPath .githooks
    bun install >/dev/null
    ;;
  post-edit)
    file=$(printf %s "$input" | jq -r '.tool_input.file_path // empty')
    [ -n "$file" ] || exit 0
    out=$(scripts/gate.sh format "$file" 2>&1) || {
      echo "$out" >&2
      exit 2
    }
    ;;
  stop)
    # The model saw the failure one time already. Do not loop.
    [ "$(printf %s "$input" | jq -r '.stop_hook_active // false')" = false ] || exit 0
    [ -n "$(git status --porcelain)" ] || exit 0
    out=$(scripts/gate.sh check 2>&1) || {
      echo "$out" >&2
      exit 2
    }
    ;;
  pre-bash)
    command=$(printf %s "$input" | jq -r '.tool_input.command // empty')
    if printf %s "$command" | grep -Eq -- 'git .*(commit|push).*--no-verify|git .*commit[^|;&]* -[a-zA-Z]*n[a-zA-Z]*( |$)'; then
      echo "Blocked: do not skip the git hooks (--no-verify, commit -n). Fix the failure that scripts/gate.sh reports." >&2
      exit 2
    fi
    # The one allowed form sets the value that the repo needs.
    if printf %s "$command" | sed 's/git config core\.hooksPath \.githooks//g' |
      grep -Eiq -- 'git .*(config|-c) *.*core\.hookspath'; then
      echo "Blocked: do not change core.hooksPath. It must stay .githooks." >&2
      exit 2
    fi
    ;;
  *)
    echo "usage: scripts/claude-hook.sh session-start|post-edit|stop|pre-bash" >&2
    exit 1
    ;;
esac
