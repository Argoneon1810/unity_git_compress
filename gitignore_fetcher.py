import requests
from pathlib import Path


def fetch_gitignore(
    project_type: str,
    try_fetch_from_github: bool = True
):
    local_dir = Path("frequently_used")
    
    local_dir.mkdir(parents=True, exist_ok=True)
    
    target_filename = f"{project_type}.gitignore".lower()

    try:
        for file_path in local_dir.iterdir():
            if file_path.is_file() and file_path.name.lower() == target_filename:
                return file_path.read_text(encoding="utf-8")
    except OSError:
        pass

    if not try_fetch_from_github:
        return None

    api_url = "https://api.github.com/gitignore/templates"
    headers = {"Accept": "application/vnd.github.v3+json"}
    
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        available_templates = response.json()
        
        target_lower = project_type.lower()
        found_template = None
        
        for template in available_templates:
            if template.lower() == target_lower:
                found_template = template
                break
        
        if found_template:
            detail_url = f"https://api.github.com/gitignore/templates/{found_template}"
            detail_resp = requests.get(detail_url, headers=headers)
            detail_resp.raise_for_status()
            
            gitignore_content = detail_resp.json().get('source')
            return gitignore_content
        else:
            return None

    except requests.exceptions.RequestException:
        return None


if __name__=="__main__":
    for candidate in ["python", "Unity"]:
        if gitignore_content := fetch_gitignore(candidate):
            print(f"✅ Found template for '{candidate}'.")
            print("-" * 20 + " .gitignore Content " + "-" * 20)
            
            preview = gitignore_content[:100] + "... (truncated)" if len(gitignore_content) > 100 else gitignore_content
            print(preview)
            print("-" * 60)
        else:
            print(f"❌ Could not find gitignore template for '{candidate}'.")