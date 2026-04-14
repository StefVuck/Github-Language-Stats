#!/bin/bash
set -e

echo "=== GitHub Profile Language Analytics Action ==="

# Configure git
git config --global user.name "github-actions[bot]"
git config --global user.email "github-actions[bot]@users.noreply.github.com"
git config --global --add safe.directory /github/workspace

# Change to workspace directory
cd /github/workspace

# Convert comma-separated lists to JSON arrays
IFS=',' read -ra EXCLUDE_REPOS_ARRAY <<<"$EXCLUDE_REPOS"
IFS=',' read -ra EXCLUDE_LANGS_ARRAY <<<"$EXCLUDE_LANGUAGES"

# Build excluded repos JSON array
EXCLUDED_REPOS_JSON="[]"
if [ -n "$EXCLUDE_REPOS" ]; then
    EXCLUDED_REPOS_JSON="["
    for repo in "${EXCLUDE_REPOS_ARRAY[@]}"; do
        EXCLUDED_REPOS_JSON="${EXCLUDED_REPOS_JSON}\"${repo}\","
    done
    EXCLUDED_REPOS_JSON="${EXCLUDED_REPOS_JSON%,}]"
fi

# Build excluded languages JSON array
EXCLUDED_LANGS_JSON="[]"
if [ -n "$EXCLUDE_LANGUAGES" ]; then
    EXCLUDED_LANGS_JSON="["
    for lang in "${EXCLUDE_LANGS_ARRAY[@]}"; do
        EXCLUDED_LANGS_JSON="${EXCLUDED_LANGS_JSON}\"${lang}\","
    done
    EXCLUDED_LANGS_JSON="${EXCLUDED_LANGS_JSON%,}]"
fi

# Convert include_forks to boolean
INCLUDE_FORKS_BOOL="false"
if [ "$INCLUDE_FORKS" = "true" ]; then
    INCLUDE_FORKS_BOOL="true"
fi

# Convert dark_mode to boolean
DARK_MODE_BOOL="false"
if [ "$DARK_MODE" = "true" ]; then
    DARK_MODE_BOOL="true"
fi

# Build optional LOC flag
LOC_FLAG=""
if [ "$USE_LOC" = "true" ]; then
    LOC_FLAG="--loc"
fi

# Create config.json
cat >/action/config.json <<EOF
{
  "github_token": "$STATS_TOKEN",
  "excluded_repos": $EXCLUDED_REPOS_JSON,
  "include_forks": $INCLUDE_FORKS_BOOL,
  "excluded_languages": $EXCLUDED_LANGS_JSON,
  "hide_private_repo_names": false,
  "dark_mode": $DARK_MODE_BOOL
}
EOF

echo "Configuration created"
echo "Visualization types: $VISUALIZATION_TYPES"
echo "Output path: $OUTPUT_PATH"

# Create output directory in workspace
mkdir -p "$OUTPUT_PATH"

# Run the Python script
python /action/action_main.py \
    --types $VISUALIZATION_TYPES \
    --config /action/config.json \
    --output "$OUTPUT_PATH" \
    --top-repos "$TOP_REPOS_COUNT" \
    $LOC_FLAG

echo "Visualizations generated successfully"

# Check if there are changes to commit
if [ -n "$(git status --porcelain)" ]; then
    echo "Committing changes..."
    git add "$OUTPUT_PATH"/*.png
    git commit -m "$COMMIT_MESSAGE"
    git push
    echo "Changes committed and pushed"
else
    echo "No changes to commit"
fi

echo "=== Action completed successfully ==="
