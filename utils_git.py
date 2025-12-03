#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
프로젝트 Git 변환을 위한 공통 유틸리티 모듈.
상수, 로깅 설정, Git 관련 핵심 로직을 포함합니다.
(범용성을 위해 하드코딩된 gitignore 상수를 제거하고 외부 주입 방식으로 변경됨)
"""

import logging
import subprocess
import shutil
from pathlib import Path
from typing import Tuple, List, Optional

# ============================================================================
# 로깅 설정
# ============================================================================

def setup_logging(name: str = __name__) -> logging.Logger:
    """공통 로깅 설정"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # 중복 핸들러 방지
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(levelname)s] %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

# ============================================================================
# Git 유틸리티 함수
# ============================================================================

def is_git_repo(directory: Path) -> bool:
    """디렉터리가 Git repository인지 확인"""
    git_dir = directory / ".git"
    return git_dir.is_dir()

def has_gitignore(directory: Path) -> bool:
    """디렉터리가 .gitignore 파일을 가지고 있는지 확인"""
    gitignore_path = directory / ".gitignore"
    return gitignore_path.is_file()

def run_git_command(git_args: List[str], cwd: Path) -> Tuple[bool, str]:
    """Git 명령어 실행"""
    try:
        result = subprocess.run(
            ["git", "-C", str(cwd)] + git_args,
            check=True,
            capture_output=True,
            text=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        return False, error_msg

# ============================================================================
# 핵심 로직 함수
# ============================================================================

def init_and_commit_project(
    project_path: Path, 
    gitignore_content: str, 
    verbose_logger: Optional[logging.Logger] = None
) -> Tuple[bool, str]:
    """
    프로젝트를 Git repository로 초기화하고 제공된 .gitignore 내용을 추가
    
    Args:
        project_path: 프로젝트 디렉터리 경로
        gitignore_content: .gitignore 파일에 기록할 내용
        verbose_logger: (선택) 진행 상황을 상세히 로그로 남길 로거.
        
    Returns:
        (성공 여부, 메시지)
    """
    project_name = project_path.name
    
    def log_info(msg):
        if verbose_logger:
            verbose_logger.info(msg)

    if not gitignore_content:
        return False, "Gitignore content is empty."

    if is_git_repo(project_path):
        # 이미 Git repository인 경우
        if has_gitignore(project_path):
            log_info(f"[SKIP] '{project_name}' is already a git repository with .gitignore")
            return True, f"'{project_name}' is already initialized"
        else:
            # .gitignore 추가
            log_info(f"[INFO] Adding .gitignore to existing git repository: '{project_name}'")
            gitignore_path = project_path / ".gitignore"
            gitignore_path.write_text(gitignore_content, encoding="utf-8")
            
            success, error = run_git_command(["add", ".gitignore"], project_path)
            if not success:
                return False, f"Failed to add .gitignore: {error}"
            
            success, error = run_git_command(["commit", "-m", "Add .gitignore"], project_path)
            if not success:
                return False, f"Failed to commit .gitignore: {error}"
            
            log_info(f"[DONE] .gitignore added and committed to '{project_name}'")
            return True, f"Added .gitignore to '{project_name}'"
    else:
        # 새로운 Git repository 초기화
        log_info(f"[INFO] Initializing git repository: '{project_name}'")
        
        success, error = run_git_command(["init"], project_path)
        if not success:
            return False, f"Failed to initialize git: {error}"
        
        # .gitignore 생성
        log_info(f"[INFO] Creating .gitignore: '{project_name}'")
        gitignore_path = project_path / ".gitignore"
        gitignore_path.write_text(gitignore_content, encoding="utf-8")
        
        # .gitignore 커밋
        success, error = run_git_command(["add", ".gitignore"], project_path)
        if not success:
            return False, f"Failed to add .gitignore: {error}"
        
        success, error = run_git_command(["commit", "-m", "Add .gitignore"], project_path)
        if not success:
            return False, f"Failed to commit .gitignore: {error}"
        
        # 나머지 파일들 커밋
        log_info(f"[INFO] Committing project files: '{project_name}'")
        success, error = run_git_command(["add", "."], project_path)
        if not success:
            return False, f"Failed to add files: {error}"
        
        success, error = run_git_command(["commit", "-m", "Initial commit"], project_path)
        if not success:
            return False, f"Failed to commit files: {error}"
        
        log_info(f"[DONE] Git repository initialized: '{project_name}'")
        return True, f"Git repository initialized for '{project_name}'"

def clone_project(project_path: Path, output_path: Path, force: bool = False, verbose_logger: Optional[logging.Logger] = None) -> Tuple[bool, str]:
    """
    프로젝트를 클론
    
    Args:
        project_path: 소스 프로젝트 디렉터리 경로
        output_path: 출력 경로 (클론될 최종 위치, 폴더명 포함)
        force: 기존 디렉터리가 있어도 강제로 클론할지 여부
        verbose_logger: (선택) 상세 로깅용 로거
        
    Returns:
        (성공 여부, 메시지)
    """
    project_name = project_path.name
    
    def log_info(msg):
        if verbose_logger:
            verbose_logger.info(msg)
    
    def log_warning(msg):
        if verbose_logger:
            verbose_logger.warning(msg)

    if not is_git_repo(project_path):
        return False, f"'{project_name}' is not a git repository"
    
    if output_path.exists():
        if not force:
            return False, f"Output path already exists: {output_path}\n  Use --force to overwrite"
        else:
            log_warning(f"[WARNING] Removing existing directory: {output_path}")
            shutil.rmtree(output_path)
    
    # 출력 경로의 부모 디렉터리 생성
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        log_info(f"[INFO] Cloning '{project_name}' to '{output_path}'")
        subprocess.run(
            ["git", "clone", str(project_path), str(output_path)],
            check=True,
            capture_output=True,
            text=True
        )
        log_info(f"[DONE] Successfully cloned to '{output_path}'")
        return True, f"Successfully cloned to '{output_path}'"
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        return False, f"Failed to clone: {error_msg}"