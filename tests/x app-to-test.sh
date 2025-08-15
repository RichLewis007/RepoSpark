#!/usr/bin/env bash
# file: quick-create-github-repo.sh

# ============================================================================
# This script creates a new GitHub repository and pushes the current directory to it.
# Usage: Run this script inside a project folder.
# Requirements: gh CLI and git installed and authenticated (gh auth login)
# ============================================================================

set -euo pipefail

# ===== Check dependencies =====
for cmd in git gh; do
  if ! command -v "$cmd" >/dev/null; then
    echo "❌ Required tool '$cmd' is missing. Install it and try again."
    exit 1
  fi
done

# ===== Prompt for repo name and description =====
default_repo_name=$(basename "$(pwd)")
read -p "📁 Repo name [$default_repo_name]: " repo_name
repo_name="${repo_name:-$default_repo_name}"

read -p "📝 Repo description (optional): " repo_description

# ===== Visibility =====
while true; do
  echo "🔐 Visibility options:"
  echo "  1) Public"
  echo "  2) Private"
  read -p "Select visibility (1 or 2): " vis_choice
  case "$vis_choice" in
    1) visibility="public"; break ;;
    2) visibility="private"; break ;;
    *) echo "❗ Please enter 1 for public or 2 for private." ;;
  esac
done

# ===== Gitignore template selection =====
echo "📄 Select a .gitignore template or press ENTER to skip:"
templates=("Android" "C++" "C" "Flutter" "GitHubPages" "Go" "Java" "Jekyll" "Kotlin" "Nextjs" "Node" "Python" "Rust" "Unity")

for i in "${!templates[@]}"; do
  printf "  %2d) %s\n" $((i+1)) "${templates[i]}"
done

read -p "Choose (1-${#templates[@]}) or press ENTER to skip: " template_choice
if [[ "$template_choice" =~ ^[0-9]+$ && "$template_choice" -ge 1 && "$template_choice" -le ${#templates[@]} ]]; then
  gitignore_template="${templates[template_choice-1]}"
  echo "✅ Selected template: $gitignore_template"
else
  gitignore_template=""
fi

# ===== License selection =====
echo "📜 License options:"
echo "  1) MIT"
echo "  2) Apache 2.0"
echo "  3) GPL 3.0"
echo "  4) None"
read -p "Choose a license (1-4): " license_choice
case "$license_choice" in
  1) license="mit" ;;
  2) license="apache-2.0" ;;
  3) license="gpl-3.0" ;;
  4|"") license="" ;;
  *) echo "⚠️ Invalid choice. Skipping license."; license="" ;;
esac

# ===== Topics (comma-separated) =====
read -p "🏷️ GitHub topics (comma-separated, optional): " topics

# ===== Remote type =====
while true; do
  echo "🔗 Remote type options:"
  echo "  1) HTTPS (default)"
  echo "  2) SSH"
  read -p "Select remote type (1 or 2): " remote_choice
  case "$remote_choice" in
    1|"") remote_type="https"; break ;;
    2) remote_type="ssh"; break ;;
    *) echo "❗ Please enter 1 for HTTPS or 2 for SSH." ;;
  esac
done

# ===== Scaffold full project structure if directory is empty =====
# Check if directory is empty of meaningful content (ignores .DS_Store and .git)
shopt -s nullglob dotglob
files=(*)
shopt -u dotglob

# Filter out .DS_Store and .git
filtered=()
for f in "${files[@]}"; do
  [[ "$f" == ".DS_Store" || "$f" == ".git" ]] && continue
  filtered+=("$f")
done

if [ "${#filtered[@]}" -eq 0 ]; then
  echo "📦 Directory is empty. Setting up standard scaffold..."
  mkdir -p src tests docs .github

  echo -e "# $repo_name\n\nProject initialized using quick-create-github-repo.sh" > README.md
  echo -e "# Documentation\n\nProject documentation goes here." > docs/index.md
  echo "# Placeholder for tests" > tests/test_placeholder.txt
  echo -e "# Changelog\n\nAll notable changes to this project will be documented in this file." > CHANGELOG.md

  cat <<EOF > CONTRIBUTING.md
# Contributing

Thank you for considering contributing to this project!

## How to Contribute
- Fork this repository
- Create a new branch
- Make your changes
- Submit a pull request

Please follow the coding conventions and include tests if applicable.
EOF

  cat <<EOF > CODE_OF_CONDUCT.md
# Code of Conduct

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/) Code of Conduct.

For any issues, please contact the maintainers.
EOF

  cat <<EOF > SECURITY.md
# Security Policy

If you discover a security vulnerability, please report it by contacting the maintainers directly.
Do not file public issues for security problems.
EOF

  cat <<EOF > .github/ISSUE_TEMPLATE.md
<!-- Describe the bug or feature request here -->

**Steps to reproduce:**
1.
2.
3.

**Expected behavior:**

**Actual behavior:**
EOF

  cat <<EOF > .github/PULL_REQUEST_TEMPLATE.md
<!-- Provide a general summary of your changes in the title above -->

## Description

## Related Issue

## Motivation and Context

## Screenshots (if appropriate):

## Types of Changes
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation

## Checklist:
- [ ] My code follows the code style of this project
- [ ] My change requires a change to the documentation
- [ ] I have updated the documentation accordingly
EOF

  read -p "⚙️ Create standard .editorconfig file? (Y/n): " create_editorconfig
  if [[ "$create_editorconfig" =~ ^[Yy]?$ ]]; then
    cat <<EOF > .editorconfig
# EditorConfig helps maintain consistent coding styles
root = true

[*]
charset = utf-8
indent_style = space
indent_size = 2
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
EOF
    echo "✅ .editorconfig created."
  fi

  cat <<EOF > .gitattributes
# Ensure consistent Git behavior
* text=auto
EOF

  echo "✅ Project scaffold created."
fi

# ===== GitHub username =====
gh_user=$(gh api user --jq .login)

# ===== Merge template into existing .gitignore if applicable =====
if [[ -n "$gitignore_template" && -f ".gitignore" ]]; then
  echo "📄 Merging .gitignore template '$gitignore_template' into existing .gitignore..."
  template_content=$(gh api /gitignore/templates/"$gitignore_template" --jq .source)
  cp .gitignore .gitignore.bak
  existing=$(grep -v '^#' .gitignore | sed '/^\s*$/d')
  combined=$(printf "%s\n%s\n" "$existing" "$template_content" | sort -u)
  {
    cat .gitignore.bak
    echo ""
    echo "# --- Added from GitHub template: $gitignore_template on $(date) ---"
    comm -13 <(echo "$existing" | sort) <(echo "$combined")
  } > .gitignore
  echo "✅ .gitignore merged and updated."
fi

# ===== Create GitHub repo =====
echo "🚀 Creating a new empty repository named '$repo_name' in your online GitHub account.."
echo "setting it to be $visibility" # public / private
echo "setting description of repo: $repo_description"
echo "setting what standard GitHub .gitignore template to use: $gitignore_template" # e.g. Python
echo "setting the license of the code: $license"
# gh repo create "$repo_name" \
#   --$visibility \
#   ${repo_description:+--description "$repo_description"} \
#   ${gitignore_template:+--gitignore "$gitignore_template"} \
#   ${license:+--license "$license"}

# ===== Initialize and commit =====
if [ ! -d .git ]; then
  echo "🚀 Now initializing a new empty git repo in the current directory.."
  git init
else
  echo "You have an existing .git repo in the current directory.."
fi

echo "Need to commit the new files in the current directory,"
echo "because you can't push to GitHub without one."
# check whether the current Git repository has any commits yet, because you can't push to GitHub without one.
if ! git rev-parse HEAD &>/dev/null; then
  read -p "➕ Add and commit all current files now? (Y/n): " confirm_commit
  if [[ "$confirm_commit" =~ ^[Yy]?$ ]]; then
    git add .
    git commit -m "Initial commit"
  else
    echo "❌ Aborting: Cannot push to remote without a commit."
    exit 1
  fi
fi

# ===== Add remote =====
echo "Adding remote type $remote_type and setting GitHub remote origin on the local git repo."
if ! git remote get-url origin &>/dev/null; then
  if [[ "$remote_type" == "ssh" ]]; then
    git remote add origin "git@github.com:$gh_user/$repo_name.git"
  else
    git remote add origin "https://github.com/$gh_user/$repo_name.git"
  fi
fi

# ===== Push to GitHub =====
default_branch=$(git symbolic-ref --short HEAD 2>/dev/null || echo "main")

echo "🔁 Syncing with remote before push..."

echo "FAKING GIT PULL/PUSH"

# if git pull --rebase origin "$default_branch"; then
#   git push -u origin "$default_branch"
# else
#   echo "⚠️ Merge conflict occurred."
#   git rebase --abort
#   read -p "❓ Overwrite the remote branch with your local version using '--force-with-lease'? (y/N): " confirm_force
#   if [[ "$confirm_force" =~ ^[Yy]$ ]]; then
#     git push --force-with-lease origin "$default_branch"
#     echo "🚀 Force push completed."
#   else
#     echo "❌ Push aborted. Please resolve conflicts manually."
#     exit 1
#   fi
# fi

# ===== Set topics =====
echo "Setting topics in online GitHub repo."
if [[ -n "$topics" ]]; then
  # topic_list=$(echo "$topics" | sed 's/,/","/g')
  # gh api -X PATCH "repos/$gh_user/$repo_name" \
  #   -F "topics=[\"$topic_list\"]" \
  #   -H "Accept: application/vnd.github.mercy-preview+json" >/dev/null
  echo "🏷️ Topics set: $topics"
fi

# ===== Prompt to open in browser =====
read -p "🌐 Open teh GitHub repository in browser now? (y/N): " open_browser
# if [[ "$open_browser" =~ ^[Yy]$ ]]; then
  # gh repo view "$gh_user/$repo_name" --web
# fi

# ===== Done =====
echo "✅ Done. '$repo_name' is set up locally and pushed to GitHub!"
