import os
import time
import subprocess

def is_git_repo(directory: str) -> bool:
    """주어진 디렉터리가 Git 저장소인지 확인"""
    try:
        result = subprocess.run(
            ["git", "-C", directory, "rev-parse", "--is-inside-work-tree"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return result.stdout.strip().lower() == "true"
    except subprocess.CalledProcessError:
        return False


def remove_index_lock(directory: str) -> bool:
    """index.lock 파일을 제거"""
    lock_file = os.path.join(directory, ".git", "index.lock")
    if os.path.exists(lock_file):
        try:
            os.remove(lock_file)
            print(f"[INFO] {lock_file} 파일을 제거했습니다.")
            return True
        except Exception as e:
            print(f"[ERROR] {lock_file} 파일을 제거하지 못했습니다: {e}")
            return False
    return False


def has_uncommitted_changes(directory: str) -> bool:
    """주어진 Git 저장소에 커밋되지 않은 변경사항이 있는지 확인"""
    try:
        result = subprocess.run(
            ["git", "-C", directory, "status", "--porcelain"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        # 출력 내용이 비어있지 않다면 변경사항이 있는 것
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        return False


def commit_changes(directory: str, commit_message: str = "Auto-commit changes"):
    """Git 저장소에서 변경사항을 모두 스테이지하고 커밋"""
    try:
        # 모든 변경사항 스테이지
        subprocess.run(["git", "-C", directory, "add", "."], check=True)

        # 커밋
        subprocess.run(["git", "-C", directory, "commit", "-m", commit_message], check=True)
        print(f"[INFO] '{directory}' 경로에서 변경사항을 커밋했습니다.")
    except subprocess.CalledProcessError as e:
        if "index.lock" in str(e):
            print("[WARNING] index.lock 문제가 감지되었습니다. 자동 복구를 시도합니다.")
            if remove_index_lock(directory):
                print("[INFO] 다시 작업을 시도합니다...")
                time.sleep(1)  # 잠시 대기 후 재시도
                commit_changes(directory, commit_message)
        else:
            print(f"[ERROR] '{directory}' 경로에서 커밋에 실패했습니다: {e}")


def is_in_blacklist(project_name: str, blacklist_list: list[str]) -> bool:
    """
    프로젝트 이름이 블랙리스트에 포함되어 있는지 확인
    블랙리스트 문자열들을 양쪽 공백 제거 후(트림) 비교
    """
    for item in blacklist_list:
        trimmed_item = item.strip()
        if project_name == trimmed_item:
            return True
    return False


def get_project_not_blacklisted(dir: str, blacklist: list):
    for entry in os.scandir(dir):
        if not entry.is_dir():
            continue

        if is_in_blacklist(entry.name, blacklist):
            print(f"[SKIP] '{entry.name}'은(는) 블랙리스트에 포함되어 처리하지 않습니다.")
            continue

        yield entry.path, entry.name


def fix(project: tuple):
    project_path, project_name = project

    """프로젝트 경로를 확인하고 변경사항이 있으면 커밋"""
    if not os.path.isdir(project_path):
        print(f"[ERROR] 경로가 유효하지 않습니다: {project_path}")
        return

    if not is_git_repo(project_path):
        print(f"[INFO] '{project_path}'는 Git 저장소가 아닙니다.")
        return

    if has_uncommitted_changes(project_path):
        print(f"[INFO] '{project_path}'에서 커밋되지 않은 변경사항이 있습니다. 커밋을 수행합니다.")
        commit_changes(project_path)
    else:
        print(f"[INFO] '{project_path}'에는 커밋되지 않은 변경사항이 없습니다.")


if __name__ == "__main__":
    is_test = False
    if is_test:
        fix((r"D:\Unity Projects\CharDemo", r"CharDemo"))
    else:
        project_dir = r"D:\Unity Projects"  # 프로젝트 부모 경로
        blacklist = [
            "90. 개인 연습",
            "91. 개인 작업",
            "92. 버림",
            "98. Others",
            "AMASSPlayer-main",
            "AMASSPlayer-main_2",
            "AnimationCurveExtractAndRecord",
            "BoneHierarchy",
            "Bowling Scene",
            "Catchball_도형9",
            "Catchball8",
            "GestureNet",
            "IKPlayground",
            "IoTMockUp",
            "J_AMASSPlayer",
            "J_AMASSPlayer6",
            "LeanWalkTest",
            "portals-urp",
            "pun2testforik",
            "ReliableNetworkProject",
            "SentisTest",
            "SMPL2GameRig",
            "SMPLX-Unity",
            "TrigonIK",
            "uma2",
            "VR",
            "VRDemo"
        ]
        for entry in get_project_not_blacklisted(project_dir, blacklist):
            fix(entry)
