import os

def get_subfolder_names(path):
    try:
        # 경로에 있는 하위 폴더 이름만 반환
        subfolders = [
            name for name in os.listdir(path)
            if os.path.isdir(os.path.join(path, name))
        ]
        return subfolders
    except FileNotFoundError:
        print(f"Error: The directory '{path}' does not exist.")
        return []
    except PermissionError:
        print(f"Error: Permission denied for accessing '{path}'.")
        return []

# 사용 예시
directory_path = r"D:/Unity Projects"
subfolder_names = get_subfolder_names(directory_path)
print("Subfolder Names:")
for name in subfolder_names:
    print(name)