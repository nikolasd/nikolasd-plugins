#!/usr/bin/env bash
# Builds a Git Town stack main > trunk > feat with a bare "origin" in .origin/. feat is
# checked out in the workspace and trunk in the worktree wt-trunk/. origin/main then gets a
# commit that neither trunk nor feat has, so a correct sync merges into trunk inside
# wt-trunk/ (a branch plain `git town sync` skips) and then into feat.
set -euo pipefail

# The harness seeds an empty repo; replace it with this fixture.
for _ in 1 2 3; do
  git_dir=$(git rev-parse --git-dir 2>/dev/null) || break
  rm -rf "$git_dir"
done

g() { git -c user.email=eval@example.invalid -c user.name=Eval -c init.defaultBranch=main "$@"; }

g init -q --bare .origin
g init -q .
git config user.email eval@example.invalid
git config user.name Eval
git remote add origin "$PWD/.origin"
printf '.origin/\nwt-trunk/\n.upstream-clone/\n' >> .git/info/exclude

cat > git-town.toml <<'TOML'
[branches]
main = "main"

[sync]
feature-strategy = "merge"
TOML
echo readme > README.md
g add -A
g commit -q -m init
g push -q -u origin main
g checkout -q -b trunk
g push -q -u origin trunk
g checkout -q -b feat
echo feat > feat.txt
g add feat.txt
g commit -q -m "feat work"
g push -q -u origin feat
git config git-town-branch.trunk.parent main
git config git-town-branch.feat.parent trunk
g worktree add -q wt-trunk trunk

# Someone else merges into main.
g clone -q .origin .upstream-clone
(
  cd .upstream-clone
  echo main > main.txt
  g add main.txt
  g commit -q -m "merged on main"
  g push -q origin main
)
rm -rf .upstream-clone

# Make `git` usable for the agent inside the eval sandbox on macOS (see handoff/guards-non-git/setup.sh).
REAL_GIT=/Library/Developer/CommandLineTools/usr/bin/git
case "${HOME:-}" in
  /private/tmp/e-*|/tmp/e-*)
    if [ -x "$REAL_GIT" ]; then
      mkdir -p "$HOME/.eval-bin"
      printf '#!/bin/sh\nexec "%s" "$@"\n' "$REAL_GIT" > "$HOME/.eval-bin/git"
      chmod +x "$HOME/.eval-bin/git"
      for f in .zshenv .zshrc .bashrc .bash_profile; do
        printf 'export PATH="%s:$PATH"\n' "$HOME/.eval-bin" > "$HOME/$f"
      done
    fi
    ;;
esac
