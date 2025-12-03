import requests

def fetch_gitignore(project_type):
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

    except requests.exceptions.RequestException as e:
        return None

if __name__=="__main__":
    for candidate in ["python", "Unity"]:
        if gitignore_content:=fetch_gitignore("python"):
            print(f"✅ '{candidate}'에 해당하는 템플릿을 찾았습니다.")
            print("-" * 20 + " .gitignore Content " + "-" * 20)
            print(gitignore_content)
            print("-" * 60)
        else:
            print(f"❌ '{candidate}'에 해당하는 gitignore 템플릿을 찾을 수 없습니다.")