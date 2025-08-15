# ✅ GitHub Repo Creation Script – Full Test Checklist

_Last updated: 2025-08-07_

Use this checklist to verify that every feature in your `quick-create-github-repo.sh` script works as expected under different conditions.

---

## 🧪 Basic Environment Setup

- [ ] `gh` CLI is installed and authenticated (`gh auth status`)
- [ ] `git` is installed
- [ ] Script is executable (`chmod +x quick-create-github-repo.sh`)

---

## 📁 Folder State Scenarios

### When the directory is empty

- [ ] Project scaffold is automatically created
- [ ] `README.md` contains placeholder text
- [ ] `CHANGELOG.md` is created with Keep a Changelog format
- [ ] `CONTRIBUTING.md` is created
- [ ] `CODE_OF_CONDUCT.md` is created
- [ ] `SECURITY.md` is created
- [ ] `docs/index.md` is created
- [ ] `tests/test_placeholder.txt` is created
- [ ] `.github/ISSUE_TEMPLATE.md` is created
- [ ] `.github/PULL_REQUEST_TEMPLATE.md` is created
- [ ] `.editorconfig` is offered and created if user agrees
- [ ] `.gitattributes` is created

### When the directory is not empty

- [ ] Script does NOT overwrite existing files
- [ ] `.editorconfig` prompt is skipped if file exists
- [ ] `.gitattributes` is skipped if already present
- [ ] All standard scaffold files are skipped if already present
- [ ] Scaffold is NOT triggered (unless empty)

---

## 🧾 Repo Setup Prompts

- [ ] Repo name prompt works and uses folder name if blank
- [ ] Description prompt is stored correctly
- [ ] Visibility selection (Public/Private) works
- [ ] Gitignore template prompt works and merges correctly with existing .gitignore
- [ ] License selection is passed to `gh repo create` correctly
- [ ] Topics prompt accepts comma-separated list
- [ ] Remote type (HTTPS/SSH) sets the correct URL
- [ ] README creation prompt works as expected
- [ ] CHANGELOG creation prompt works as expected

---

## 🔧 Git Logic

### When no Git repo exists

- [ ] Git repo is initialized
- [ ] Files are added and committed
- [ ] Remote origin is added
- [ ] Push to remote completes successfully

### When Git repo exists

- [ ] Script skips `git init`
- [ ] Script detects existing commit and skips add/commit
- [ ] Remote `origin` is not overwritten
- [ ] Handles pull/rebase properly
- [ ] Force-push prompt appears on merge conflict
- [ ] Push succeeds on clean rebase

---

## 🌐 Remote Interaction

- [ ] GitHub repo is created
- [ ] Repository opens in browser if selected
- [ ] GitHub topics are set if provided using GitHub API

---

### 🆕 Additional Logic to Check

- [ ] `gh_user` is retrieved dynamically using `gh api`
- [ ] Gitignore template is merged with existing .gitignore, not overwritten
- [ ] Commit prompt guards against accidental pushes with no commit
Skips commit if user says no, exits safely ?
- [ ] Rebase is attempted before push; fallback to `--force-with-lease` only on user approval
- [ ] Existing `.gitignore` is backed up as `.gitignore.bak` before merging

---

## 🧹 Cleanup and Safety

- [ ] All optional prompts are honored
- [ ] Errors (e.g., duplicate repo name) are caught gracefully
- [ ] Script aborts safely if required input or setup is missing

---

**Total checks:** Fill as features expand.

Happy testing! ✅
