"""
title: File I/O Tool
author: Claude Code
version: 0.3.0
license: MIT
description: A tool to securely read, write, search, and modify files within a sandboxed workspace.
"""

import os
import json
import re
import fnmatch
import subprocess
from pydantic import BaseModel, Field
from typing import Callable, Any, List, Optional

# --- Helper Classes ---

class WorkspaceHelper:
    """Manages secure file operations within a defined workspace."""
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        if self.workspace_path:
            os.makedirs(self.workspace_path, exist_ok=True)

    def is_configured(self) -> bool:
        return bool(self.workspace_path)

    def get_secure_path(self, file_path: str) -> (str | None):
        if not self.is_configured(): return None
        workspace_real_path = os.path.realpath(self.workspace_path)
        user_provided_path = os.path.normpath(file_path)
        if os.path.isabs(user_provided_path): return None
        full_path = os.path.join(workspace_real_path, user_provided_path)
        full_real_path = os.path.realpath(full_path)
        if not full_real_path.startswith(workspace_real_path): return None
        return full_real_path

# --- Main Tools Class ---

class Tools:
    class Valves(BaseModel):
        WORKSPACE_PATH: str = Field(
            default="/tmp/claude_workspace",
            description="The secure base directory for all file operations."
        )

    def __init__(self):
        self.valves = self.Valves()
        self.workspace = WorkspaceHelper(self.valves.WORKSPACE_PATH)

    async def _emit(self, event_emitter: Any, description: str, status: str = "in_progress", done: bool = False):
        """A simple helper to emit status events."""
        if event_emitter:
            await event_emitter({
                "type": "status",
                "data": {"status": status, "description": description, "done": done},
            })

    async def read_file(self, file_path: str, __event_emitter__: Any = None) -> str:
        if not self.workspace.is_configured(): return json.dumps({"error": "WORKSPACE_PATH is not configured."})
        secure_path = self.workspace.get_secure_path(file_path)
        if not secure_path: return json.dumps({"error": f"Access denied for '{file_path}'."})

        await self._emit(__event_emitter__, f"Reading file: {file_path}...")
        try:
            with open(secure_path, 'r', encoding='utf-8') as f: content = f.read()
            await self._emit(__event_emitter__, "File Read", status="complete", done=True)
            return content
        except FileNotFoundError: return json.dumps({"error": f"File not found: '{file_path}'."})
        except Exception as e: return json.dumps({"error": f"Error reading file: {str(e)}"})

    async def write_file(self, file_path: str, content: str, __event_emitter__: Any = None) -> str:
        if not self.workspace.is_configured(): return json.dumps({"error": "WORKSPACE_PATH is not configured."})
        secure_path = self.workspace.get_secure_path(file_path)
        if not secure_path: return json.dumps({"error": f"Access denied for '{file_path}'."})

        await self._emit(__event_emitter__, f"Writing to file: {file_path}...")
        try:
            os.makedirs(os.path.dirname(secure_path), exist_ok=True)
            with open(secure_path, 'w', encoding='utf-8') as f: f.write(content)
            await self._emit(__event_emitter__, "File Written", status="complete", done=True)
            return json.dumps({"success": f"Successfully wrote to '{file_path}'."})
        except Exception as e: return json.dumps({"error": f"Error writing file: {str(e)}"})

    async def list_items(self, path: str = ".", __event_emitter__: Any = None) -> str:
        if not self.workspace.is_configured(): return json.dumps({"error": "WORKSPACE_PATH is not configured."})
        secure_path = self.workspace.get_secure_path(path)
        if not secure_path or not os.path.isdir(secure_path): return json.dumps({"error": f"Path '{path}' is not a valid directory."})

        await self._emit(__event_emitter__, f"Listing items in: {path}...")
        try:
            items = os.listdir(secure_path)
            directories = [i for i in items if os.path.isdir(os.path.join(secure_path, i))]
            files = [i for i in items if os.path.isfile(os.path.join(secure_path, i))]
            await self._emit(__event_emitter__, "Listed Items", status="complete", done=True)
            return json.dumps({"directories": directories, "files": files})
        except Exception as e: return json.dumps({"error": f"Error listing items: {str(e)}"})

    async def patch_file(self, file_path: str, regex_pattern: str, replacement_string: str, replace_all: bool = False, __event_emitter__: Any = None) -> str:
        if not self.workspace.is_configured(): return json.dumps({"error": "WORKSPACE_PATH is not configured."})
        secure_path = self.workspace.get_secure_path(file_path)
        if not secure_path or not os.path.isfile(secure_path): return json.dumps({"error": f"File not found or access denied for '{file_path}'."})

        await self._emit(__event_emitter__, f"Patching file: {file_path}...")
        try:
            with open(secure_path, 'r', encoding='utf-8') as f: content = f.read()
            count = 0 if replace_all else 1
            new_content, num_replacements = re.subn(regex_pattern, replacement_string, content, count=count)
            if num_replacements == 0: return json.dumps({"message": "Pattern not found."})
            with open(secure_path, 'w', encoding='utf-8') as f: f.write(new_content)
            await self._emit(__event_emitter__, "File Patched", status="complete", done=True)
            return json.dumps({"success": f"Patched {num_replacements} occurrence(s) in '{file_path}'."})
        except re.error as e: return json.dumps({"error": f"Invalid regex: {e}"})
        except Exception as e: return json.dumps({"error": f"Error patching file: {str(e)}"})

    async def search_content(self, regex_pattern: str, start_path: str = ".", include_patterns: Optional[List[str]] = None, exclude_patterns: Optional[List[str]] = None, __event_emitter__: Any = None) -> str:
        if not self.workspace.is_configured(): return json.dumps({"error": "WORKSPACE_PATH is not configured."})
        secure_start_path = self.workspace.get_secure_path(start_path)
        if not secure_start_path or not os.path.isdir(secure_start_path): return json.dumps({"error": f"Start path '{start_path}' is not valid."})

        await self._emit(__event_emitter__, f"Searching in '{start_path}'...")
        matches = {}
        try:
            compiled_regex = re.compile(regex_pattern)
            for dirpath, _, filenames in os.walk(secure_start_path):
                for filename in filenames:
                    file_rel_path = os.path.relpath(os.path.join(dirpath, filename), self.workspace.workspace_path)
                    if include_patterns and not any(fnmatch.fnmatch(file_rel_path, p) for p in include_patterns): continue
                    if exclude_patterns and any(fnmatch.fnmatch(file_rel_path, p) for p in exclude_patterns): continue
                    file_abs_path = os.path.join(dirpath, filename)
                    try:
                        with open(file_abs_path, 'r', encoding='utf-8', errors='ignore') as f:
                            for line_num, line in enumerate(f, 1):
                                if compiled_regex.search(line):
                                    if file_rel_path not in matches: matches[file_rel_path] = []
                                    matches[file_rel_path].append({"line": line_num, "content": line.strip()})
                    except Exception: continue
            await self._emit(__event_emitter__, "Search Complete", status="complete", done=True)
            return json.dumps(matches if matches else {"message": "No matches found."})
        except re.error as e: return json.dumps({"error": f"Invalid regex: {e}"})
        except Exception as e: return json.dumps({"error": f"Error during search: {str(e)}"})

    async def apply_diff_patch(self, file_path: str, diff_content: str, __event_emitter__: Any = None) -> str:
        if not self.workspace.is_configured(): return json.dumps({"error": "WORKSPACE_PATH is not configured."})
        secure_path = self.workspace.get_secure_path(file_path)
        if not secure_path or not os.path.isfile(secure_path): return json.dumps({"error": f"File not found or access denied for '{file_path}'."})

        await self._emit(__event_emitter__, f"Applying diff patch to: {file_path}...")
        try:
            with open(secure_path, 'r', encoding='utf-8') as f: original_lines = f.readlines()
            diff_lines = diff_content.splitlines()
            new_lines = list(original_lines)
            while diff_lines and (diff_lines[0].startswith('---') or diff_lines[0].startswith('+++')): diff_lines.pop(0)
            offset = 0
            for line in diff_lines:
                if line.startswith('@@'):
                    match = re.search(r'@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@', line)
                    if not match: return json.dumps({"error": "Invalid diff hunk header."})
                    original_start_line, offset = int(match.group(1)) - 1, 0
                    current_pos = original_start_line
                elif line.startswith('-'):
                    line_content = line[1:] + '\n'
                    if current_pos < len(new_lines) and new_lines[current_pos] == line_content:
                        new_lines.pop(current_pos)
                        offset -= 1
                    else: return json.dumps({"error": f"Patch mismatch at line {current_pos + 1}."})
                elif line.startswith('+'):
                    new_lines.insert(current_pos, line[1:] + '\n')
                    offset += 1
                    current_pos += 1
                elif line.startswith(' '): current_pos += 1
            with open(secure_path, 'w', encoding='utf-8') as f: f.writelines(new_lines)
            await self._emit(__event_emitter__, "Patch Applied", status="complete", done=True)
            return json.dumps({"success": f"Successfully applied diff patch to '{file_path}'."})
        except Exception as e: return json.dumps({"error": f"Error applying patch: {str(e)}"})

    async def _run_git_command(self, command: List[str], path: str, event_emitter: Any) -> str:
        secure_path = self.workspace.get_secure_path(path)
        if not secure_path or not os.path.isdir(secure_path):
            return json.dumps({"error": f"Invalid path for git operation: '{path}'."})

        await self._emit(event_emitter, f"Running git {' '.join(command)} in '{path}'...")
        try:
            process = subprocess.run(['git'] + command, cwd=secure_path, capture_output=True, text=True, check=False)
            if process.returncode != 0: return json.dumps({"error": process.stderr.strip()})
            await self._emit(event_emitter, "Git command successful", status="complete", done=True)
            return process.stdout.strip()
        except Exception as e: return json.dumps({"error": f"Failed to run git command: {str(e)}"})

    async def git_clone(self, repo_url: str, clone_to: str, __event_emitter__: Any = None) -> str:
        return await self._run_git_command(['clone', repo_url, clone_to], "", __event_emitter__)

    async def git_status(self, path: str = ".", __event_emitter__: Any = None) -> str:
        return await self._run_git_command(['status'], path, __event_emitter__)

    async def git_pull(self, path: str = ".", __event_emitter__: Any = None) -> str:
        return await self._run_git_command(['pull'], path, __event_emitter__)

    async def git_add(self, path: str, files: str = ".", __event_emitter__: Any = None) -> str:
        return await self._run_git_command(['add', files], path, __event_emitter__)

    async def git_commit(self, path: str, message: str, __event_emitter__: Any = None) -> str:
        return await self._run_git_command(['commit', '-m', message], path, __event_emitter__)

    async def git_push(self, path: str, remote: str = 'origin', branch: str = 'main', __event_emitter__: Any = None) -> str:
        return await self._run_git_command(['push', remote, branch], path, __event_emitter__)

    async def git_log(self, path: str, count: int = 10, __event_emitter__: Any = None) -> str:
        return await self._run_git_command(['log', f'-n{count}'], path, __event_emitter__)

    async def git_diff(self, path: str, file: Optional[str] = None, __event_emitter__: Any = None) -> str:
        command = ['diff']
        if file: command.append(file)
        return await self._run_git_command(command, path, __event_emitter__)
