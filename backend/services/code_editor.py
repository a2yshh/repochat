import os
import re
import tempfile
import shutil
from typing import List, Dict, Optional
from difflib import unified_diff
from git import Repo

from services.llm_service import _get_async_client, MODEL, MAX_TOKENS


async def analyze_modification_intent(query: str, context_chunks: List[dict]) -> Dict:
    """
    Analyze user query to understand what code changes are needed.
    Returns: {
        "intent": "ui_improvement",
        "target_files": ["src/App.tsx", "styles/main.css"],
        "modification_type": "refactor",
        "description": "..."
    }
    """
    client = _get_async_client()
    
    # Build context
    file_list = "\n".join([f"- {chunk['file_path']}" for chunk in context_chunks[:10]])
    
    prompt = f"""You are a code analysis expert. Analyze this modification request and identify:
1. What files need to be changed
2. What type of modification (refactor, feature, bugfix, styling)
3. Detailed description of changes needed

Available files:
{file_list}

User Request: {query}

Respond in JSON format:
{{
    "intent": "brief intent description",
    "target_files": ["file1.tsx", "file2.css"],
    "modification_type": "refactor|feature|bugfix|styling",
    "description": "detailed change description",
    "priority": "high|medium|low"
}}
"""
    
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
    )
    
    # Parse JSON response
    import json
    try:
        result = json.loads(response.choices[0].message.content)
        return result
    except:
        return {
            "intent": "code modification",
            "target_files": [chunk['file_path'] for chunk in context_chunks[:3]],
            "modification_type": "refactor",
            "description": query
        }


async def generate_code_changes(
    file_path: str,
    file_content: str,
    modification_request: str,
    file_context: List[dict]
) -> str:
    """
    Generate modified code for a specific file.
    Returns the new file content.
    """
    client = _get_async_client()
    
    # Build context from related files
    context = "\n\n".join([
        f"--- {chunk['file_path']} ---\n{chunk['content']}"
        for chunk in file_context[:3]
    ])
    
    prompt = f"""You are an expert programmer. Modify this code based on the request.

Current File: {file_path}
Current Code: {file_content}
Related Context:{context}

Modification Request: {modification_request}

IMPORTANT RULES:
1. Return ONLY the complete modified code
2. Preserve all existing functionality
3. Follow the existing code style and patterns
4. Add comments for major changes
5. Ensure code is production-ready
6. Do NOT include explanations or markdown - just the raw code

Modified Code:
"""
    
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=MAX_TOKENS,
    )
    
    modified_code = response.choices[0].message.content.strip()
    
    # Remove markdown code blocks if present
    modified_code = re.sub(r'^```[\w]*\n', '', modified_code)
    modified_code = re.sub(r'\n```$', '', modified_code)
    
    return modified_code


def create_diff(original: str, modified: str, filepath: str) -> str:
    """
    Create a unified diff between original and modified code.
    """
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)
    
    diff = unified_diff(
        original_lines,
        modified_lines,
        fromfile=f"a/{filepath}",
        tofile=f"b/{filepath}",
        lineterm=''
    )
    
    return ''.join(diff)


def apply_modifications(
    repo_path: str,
    modifications: List[Dict],
    session_id: str
) -> Dict:
    """
    Apply code modifications to a repository.
    
    Args:
        repo_path: Path to original cloned repo
        modifications: List of {file_path, original_content, modified_content}
        session_id: Session ID for tracking
    
    Returns:
        {
            "modified_repo_path": "/path/to/modified/repo",
            "diffs": [{file, diff}],
            "summary": "..."
        }
    """
    # Create a copy of the repo for modifications
    modified_repo_path = tempfile.mkdtemp(prefix=f"repochat_modified_{session_id}_")
    shutil.copytree(repo_path, modified_repo_path, dirs_exist_ok=True)
    
    diffs = []
    files_changed = []
    
    for mod in modifications:
        file_path = mod['file_path']
        original_content = mod['original_content']
        modified_content = mod['modified_content']
        
        # Full path to file
        full_path = os.path.join(modified_repo_path, file_path)
        
        # Write modified content
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        
        # Generate diff
        diff = create_diff(original_content, modified_content, file_path)
        
        diffs.append({
            "file": file_path,
            "diff": diff,
            "additions": modified_content.count('\n') - original_content.count('\n')
        })
        
        files_changed.append(file_path)
    
    # Create summary
    summary = f"Modified {len(files_changed)} file(s): {', '.join(files_changed)}"
    
    return {
        "modified_repo_path": modified_repo_path,
        "diffs": diffs,
        "summary": summary,
        "files_changed": files_changed
    }


def create_patch_file(diffs: List[Dict], output_path: str):
    """
    Create a .patch file from diffs.
    """
    with open(output_path, 'w') as f:
        for diff_info in diffs:
            f.write(diff_info['diff'])
            f.write('\n\n')


def create_zip_archive(directory: str, output_path: str):
    """
    Create a zip archive of the modified repository.
    """
    shutil.make_archive(
        output_path.replace('.zip', ''),
        'zip',
        directory
    )