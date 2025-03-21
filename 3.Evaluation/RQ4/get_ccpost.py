import os
import git
from idna import decode
from unidiff import PatchSet, UnidiffParseError

encoding_format = "ISO-8859-1"

def apply_diff_in_memory(repo_path, commit_hash, file_path, diff_path):
    repo = git.Repo(repo_path)

    commit = repo.commit(commit_hash)
    file_content_at_commit = commit.tree[file_path].data_stream.read().decode('utf-8', errors='replace').splitlines(keepends=True)

    try:
        with open(diff_path, 'r', encoding='utf-8', errors='replace') as f:
            diff_content = f.read().rstrip('\n')
            patch = PatchSet(diff_content)
    except UnidiffParseError as e:
        print(f"Error parsing diff file: {e}")
        print("Please check the diff file format.")
        return None

    modified_content = file_content_at_commit.copy()
    offset = 0

    for patched_file in patch:
        if patched_file.path == file_path:
            for hunk in patched_file:
                for line in hunk:
                    if line.is_removed:
                        if line.source_line_no is None:
                            print("Warning: source_line_no is None for removed line, skipping")
                            continue
                        modified_content[line.source_line_no-1] = ""

            modified_content = "".join(modified_content).splitlines(keepends=True)
            for hunk in patched_file:
                for line in hunk:
                    if line.is_added:
                        if line.target_line_no is None:
                            modified_content.append(line.value)
                        else:
                            modified_content.insert(line.target_line_no-1, line.value)
    

    return ''.join(modified_content)