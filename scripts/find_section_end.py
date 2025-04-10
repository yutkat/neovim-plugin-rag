import sys
from markdown_it import MarkdownIt
from pathlib import Path

def find_section_end_line(filepath, hierarchy):
    """
    Finds the end line number of a specified section in a Markdown file.

    The section ends just before the next heading at any level,
    or at the end of the file if no subsequent heading exists.

    Args:
        filepath (str or Path): The path to the Markdown file.
        hierarchy (list[str]): The list of header titles defining the section
                                (e.g., ["Section A"] or ["Section A", "Sub A1"]).
                                Assumes Level 2 is the first element.

    Returns:
        int | None: The 1-based line number where the section ends (the line
                    *before* the next heading starts), or the total number of lines
                    if the section goes to the end, or None if the section
                    is not found. Returns 0-based index internally, converts at the end.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
            content = "".join(lines)
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error reading file {filepath}: {e}", file=sys.stderr)
        return None

    if not lines:
        return 0 # Empty file case

    md = MarkdownIt()
    try:
        tokens = md.parse(content)
    except Exception as e:
        print(f"Error parsing Markdown file {filepath}: {e}", file=sys.stderr)
        return None


    current_path = []
    target_token_index = -1
    found_target_token = None

    # --- Pass 1: Find the start token of the target section ---
    for i, token in enumerate(tokens):
        if token.type == "heading_open":
            level = int(token.tag[1])
            title = ""
            # The actual title is in the next inline token
            if i + 1 < len(tokens) and tokens[i + 1].type == "inline":
                title = tokens[i + 1].content.strip()
            else:
                # Should not happen with valid markdown, but handle gracefully
                continue # Skip if heading has no title

            # Update current path based on the level
            # Ensure path length matches level - 1 for parent assignment
            current_path = current_path[:level - 1] + [title]

            # We only compare from level 2 onwards as specified by the user input format
            path_to_compare = current_path[1:] if len(current_path) > 1 else []

            # Check if the current path matches the desired hierarchy
            if path_to_compare == hierarchy:
                target_token_index = i
                found_target_token = token
                break # Found the target heading, no need to continue this loop

    # --- If the target section was not found ---
    if target_token_index == -1:
        return None

    # --- Pass 2: Find the *next* heading after the target ---
    next_heading_start_line_0based = -1
    for i in range(target_token_index + 1, len(tokens)):
        if tokens[i].type == "heading_open":
            # Found the first heading that comes after our target section
            next_heading_start_line_0based = tokens[i].map[0]
            break

    # --- Determine the end line ---
    if next_heading_start_line_0based != -1:
        # The section ends on the line just before the next heading starts.
        # token.map[0] gives the 0-based index of the line containing the heading.
        # So, this value directly represents the 0-based index of the end line.
        # Example: Next heading on line 6 (0-based index 5), map[0] is 5.
        return next_heading_start_line_0based
    else:
        # No subsequent heading found, the section goes to the end of the file.
        # Return the total number of lines (which is 1-based index of last line + 1).
        # Or, if we want the index *of* the last line, return len(lines) - 1?
        # Let's return the line number *after* the last line, consistent with map[0].
        return len(lines)


# --- Main execution logic ---
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: python {Path(__file__).name} <Level2 / Level3 / ...> <filename1> [<filename2> ...]", file=sys.stderr)
        print("Example: python find_section_end.py \"Section A / Sub A1\" document.md", file=sys.stderr)
        sys.exit(1)

    hierarchy_path = sys.argv[1]
    filenames = sys.argv[2:]

    # Ensure hierarchy is correctly parsed, even if empty
    hierarchy = [h.strip() for h in hierarchy_path.split(" / ") if h.strip()]
    if not hierarchy:
         print("Error: Hierarchy path cannot be empty.", file=sys.stderr)
         sys.exit(1)

    found_in_any_file = False
    for filename in filenames:
        # Pass the hierarchy list directly
        end_line_0based = find_section_end_line(Path(filename), hierarchy)

        if end_line_0based is not None:
            # Convert 0-based line index to 1-based line number for output
            print(f"{filename}:{end_line_0based}") # User requested 5, map[0] returns 5 for line 6.
            found_in_any_file = True
            break # Stop after finding in the first file

    if not found_in_any_file:
        print("Not found")
        # sys.exit(1) # Exit with error code if not found across all files? Optional.
