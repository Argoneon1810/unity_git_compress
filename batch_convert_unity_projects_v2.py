#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
관리할 프로젝트들이 들어 있는 디렉터리(Projects 디렉터리)와, 
출력(클론)할 디렉터리(Output 디렉터리), 그리고 블랙리스트 목록을 입력받아
각 프로젝트별로 순차적으로:
1) 지정된 타입의 .gitignore 설정 및 Git 초기화
2) 최종적으로 Git Clone하여 Output 디렉터리에 복제

여러 프로젝트는 multiprocessing으로 병렬 처리됩니다.

Usage:
  python batch_convert_unity_projects_v2.py --projects_dir "C:/Projects" --output_dir "C:/Output" --type "Unity" --workers 4
"""

import sys
import argparse
from pathlib import Path
from typing import List, Tuple
from multiprocessing import Pool, cpu_count
import utils_git as utils
import gitignore_fetcher

# ============================================================================
# 로깅 설정
# ============================================================================

logger = utils.setup_logging(__name__)

# ============================================================================
# 인자 파싱
# ============================================================================

def parse_args() -> argparse.Namespace:
    """커맨드 라인 인자 파싱"""
    parser = argparse.ArgumentParser(
        description="Manage multiple projects with Git initialization and .gitignore (with multiprocessing support)."
    )
    parser.add_argument(
        "--projects_dir",
        required=True,
        help="Input directory where all the projects reside"
    )
    parser.add_argument(
        "--output_dir",
        required=True,
        help="Output directory where all the postprocessed projects will be saved"
    )
    parser.add_argument(
        "--blacklist",
        default="",
        help="Comma-separated list of project names to exclude from batch conversion"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help=f"Number of worker processes (default: CPU count)"
    )
    parser.add_argument(
        "--type",
        type=str,
        default="Unity",
        help="Project type to fetch appropriate .gitignore (default: Unity)"
    )
    return parser.parse_args()

# ============================================================================
# 유틸리티 함수
# ============================================================================

def is_in_blacklist(project_name: str, blacklist_list: List[str]) -> bool:
    """
    프로젝트 이름이 블랙리스트에 포함되어 있는지 확인
    """
    return any(project_name == item.strip() for item in blacklist_list)

def process_single_project(args: Tuple[Path, Path, List[str], str]) -> Tuple[str, bool]:
    """
    단일 프로젝트 처리 함수 (multiprocessing용)
    
    Git 초기화 및 커밋 → 클론을 연속으로 수행
    
    Args:
        args: (프로젝트_경로, 출력_디렉터리, 블랙리스트, gitignore_content)
        
    Returns:
        (프로젝트_이름, 성공_여부)
    """
    project_path, output_dir, blacklist_list, gitignore_content = args
    project_name = project_path.name
    
    # 블랙리스트 확인
    if is_in_blacklist(project_name, blacklist_list):
        logger.info(f"[SKIP] '{project_name}' is enlisted in the blacklist")
        return project_name, False
    
    # Step 1: Git 초기화 및 .gitignore 설정
    # verbose_logger를 넘기지 않아 내부 로그를 끄고 결과 메시지만 받음
    success, msg = utils.init_and_commit_project(project_path, gitignore_content=gitignore_content)
    
    # Batch 로직에 맞게 메시지 포맷팅 (기존 코드와의 호환성)
    if success:
        log_msg = f"[DONE] '{project_name}' → {msg}"
        logger.info(log_msg)
    else:
        logger.error(f"[ERROR] '{project_name}' → {msg}")
        return project_name, False
    
    # Step 2: 클론 수행
    clone_target = output_dir / project_name
    
    # Output path 존재 여부는 utils.clone_project 내부에서도 체크하지만, 
    # Batch 버전은 "SKIP" 메시지를 원하므로 미리 체크
    if clone_target.exists():
        logger.info(f"[SKIP] '{project_name}' → Output folder already exists: {clone_target}")
        return project_name, False

    success, msg = utils.clone_project(project_path, clone_target)
    
    if success:
        # utils.clone_project의 리턴 메시지를 사용하여 포맷팅
        logger.info(f"[DONE] Cloned '{project_name}' → '{clone_target}'")
    else:
        logger.error(f"[ERROR] '{project_name}' → {msg}")
        return project_name, False
    
    return project_name, True

# ============================================================================
# 메인 함수
# ============================================================================

def main():
    """메인 실행 함수"""
    args = parse_args()
    
    projects_dir = Path(args.projects_dir)
    output_dir = Path(args.output_dir)
    blacklist_str = args.blacklist.strip()
    workers = args.workers or cpu_count()
    project_type = args.type
    
    # 블랙리스트 파싱
    blacklist_list = [x for x in blacklist_str.split(",") if x.strip()] if blacklist_str else []
    
    # ========================================================================
    # 입력 검증
    # ========================================================================
    
    if not projects_dir.is_dir():
        logger.error(f"Projects Directory does not exist: {projects_dir}")
        sys.exit(1)
    
    # output_dir이 없으면 생성
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Projects Directory: {projects_dir}")
    logger.info(f"Output Directory: {output_dir}")
    logger.info(f"Project Type: {project_type}")
    logger.info(f"Blacklist: {blacklist_list if blacklist_list else 'None'}")
    logger.info(f"Workers: {workers}")
    logger.info("=" * 70)

    # ========================================================================
    # .gitignore 준비
    # ========================================================================
    
    logger.info(f"Fetching .gitignore for type: '{project_type}'...")
    gitignore_content = gitignore_fetcher.fetch_gitignore(project_type)
    
    if not gitignore_content:
        logger.error(f"Failed to fetch .gitignore for type '{project_type}'. Aborting.")
        sys.exit(1)
    
    logger.info(f"Successfully loaded .gitignore for '{project_type}'")
    logger.info("=" * 70)
    
    # ========================================================================
    # 처리할 프로젝트 목록 수집
    # ========================================================================
    
    projects_to_process = [
        p for p in projects_dir.iterdir()
        if p.is_dir() and not is_in_blacklist(p.name, blacklist_list)
    ]
    
    if not projects_to_process:
        logger.warning("No projects to process.")
        sys.exit(0)
    
    logger.info(f"Found {len(projects_to_process)} project(s) to process")
    logger.info("=" * 70)
    
    # ========================================================================
    # Multiprocessing으로 병렬 처리
    # ========================================================================
    
    # 각 프로젝트마다 (프로젝트_경로, 출력_디렉터리, 블랙리스트, gitignore_content) 튜플 생성
    process_args = [
        (project_path, output_dir, blacklist_list, gitignore_content)
        for project_path in projects_to_process
    ]
    
    with Pool(processes=workers) as pool:
        results = pool.map(process_single_project, process_args)
    
    # ========================================================================
    # 결과 요약
    # ========================================================================
    
    logger.info("=" * 70)
    successful = sum(1 for _, success in results if success)
    logger.info(f"Execution Complete: {successful}/{len(results)} projects processed successfully")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()