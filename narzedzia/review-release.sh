#!/bin/sh
set -eu

cd "$(dirname "$0")/.."

printf '%s\n' '==> Forbidden local/audit artifacts'
forbidden="$(git status --porcelain | awk '{print $2}' | grep -E '(^|/)_audit|\.db($|-wal$|-shm$)|\.sqlite($|-wal$|-shm$)|\.(bak|old|orig|tmp)$' || true)"
if [ -n "$forbidden" ]; then
  printf '%s\n' "$forbidden" >&2
  echo 'STOP: usuń lokalne/audytowe artefakty przed stagingiem.' >&2
  exit 1
fi
echo 'OK — brak lokalnych baz, audytów i backupów w working tree.'

printf '\n%s\n' '==> Release checks'
./narzedzia/release-check.sh

printf '\n%s\n' '==> Optional browser/performance checks before a major release'
echo 'python3 narzedzia/audyt-chrome.py'
echo 'python3 narzedzia/audyt-csp.py'
echo 'python3 narzedzia/audyt-runtime.py'
echo 'python3 narzedzia/audyt-performance.py'

printf '\n%s\n' '==> New/untracked files'
git ls-files --others --exclude-standard | sort

printf '\n%s\n' '==> Modified tracked files'
git diff --name-status

printf '\n%s\n' '==> Generated/source parity reminder'
echo 'Źródła zrodla/*.html + generator + wygenerowane HTML/CSS/JS/sitemap/feed powinny wejść razem.'

printf '\n%s\n' '==> Final working-tree status'
git status --short

echo
echo 'Review finished. Script did not stage, commit, push or deploy anything.'
