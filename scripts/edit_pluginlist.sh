#!/bin/bash

# --- Configuration ---
# Directory containing the markdown files to search
# Can be overridden by the first script argument. Defaults to './docs' if not specified.
MARKDOWN_DIR="${1:-./data/my-neovim-pluginlist/}"
# Path to the Python script for category lookup
PYTHON_SCRIPT="scripts/find_section_end.py"
# Path to the shell script for insertion
INSERT_SCRIPT="scripts/insert_plugin.sh" # Assuming insert.sh is in the same dir or PATH

# --- Pre-checks ---
# Check if markdown directory exists
if [ ! -d "$MARKDOWN_DIR" ]; then
  echo "Error: Markdown directory not found: '$MARKDOWN_DIR'" >&2
  echo "Please specify the correct directory as the first argument." >&2
  exit 1
fi

# Check if python script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
  echo "Error: Python script not found: '$PYTHON_SCRIPT'" >&2
  exit 1
fi

 # Check if insert script exists and is executable
if [ ! -x "$INSERT_SCRIPT" ]; then
  echo "Error: Insert script not found or not executable: '$INSERT_SCRIPT'" >&2
  exit 1
fi

echo "Using Markdown directory: $MARKDOWN_DIR"
echo "Starting processing..."
echo "--------------------"

# --- Process Data from Standard Input ---
# IFS='|' splits fields based on pipe. read -r prevents backslash interpretation.
# The underscores capture the leading/trailing empty fields from "|...|" format.
processed_count=0
inserted_count=0
not_found_count=0

while IFS='|' read -r _ url category description _; do
  # Trim leading/trailing whitespace from extracted fields (more robustly: sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
  url=$(echo "$url" | xargs)
  category=$(echo "$category" | xargs)

  # Skip if URL or category is empty
  if [ -z "$url" ] || [ -z "$category" ]; then
    # echo "Skipping invalid line: URL='$url', Category='$category'" >&2
    continue
  fi

  ((processed_count++))
  echo "[${processed_count}] Processing:"
  echo "  URL:      $url"
  echo "  Category: $category"

  # Execute find_section_end.py to get filename and line number
  # Keep stderr to see potential uv run errors
  # Pass category as first arg, search directory as second
  echo "  Searching for category location..." >&2
  location_output=$(uv run "$PYTHON_SCRIPT" "$category" "$MARKDOWN_DIR"/*.md 2>/dev/null) # Suppress python script stderr if needed, or remove 2>/dev/null
  script_exit_status=$?

  # Check if script succeeded (exit 0) and output is not "Not found" and not empty
  if [ $script_exit_status -eq 0 ] && [ "$location_output" != "Not found" ] && [ -n "$location_output" ]; then
    echo "  Location found: $location_output"
    # Execute insert.sh
    echo "  Executing: $INSERT_SCRIPT \"$url\" \"$location_output\"" >&2
    "$INSERT_SCRIPT" "$url" "$location_output"
    insert_exit_status=$?

    if [ $insert_exit_status -eq 0 ]; then
        ((inserted_count++))
        echo "  insert.sh succeeded" >&2
    else
        echo "  Warning: insert.sh failed (status: $insert_exit_status)" >&2
    fi
  else
    ((not_found_count++))
    echo "  Warning: Location for category '$category' not found." >&2
  fi
  echo "--------------------"

done

echo "Processing finished."
echo "Total lines processed: $processed_count"
echo "Insertions succeeded: $inserted_count"
echo "Locations not found: $not_found_count"

exit 0
