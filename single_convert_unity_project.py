#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
단일 유니티 프로젝트를 Git repository로 초기화하고 클론하는 스크립트

입력받은 프로젝트 디렉터리에 대해:
1) .gitignore 설정 및 Git 초기화
2) 최종적으로 Git Clone하여 출력 디렉터리에 복제

Usage:
  python single_convert_unity_project.py --project_path "C:/UnityProjects/MyProject" --output_path "C:/Output"

※ 주의사항
- Git이 설치되어 있어야 하며, PATH에 등록되어 있어야 합니다.
"""

# cmd /v:on /c "set PROJ_NAME=VRMirror&& python -m single_convert_unity_project --project_path "D:\1. Projects\1. Unity\!PROJ_NAME!" --output_path "E:\Unity\projects\!PROJ_NAME!""

import sys
import argparse
from pathlib import Path
import unity_git_utils as utils

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
        description="Convert a single Unity project with Git initialization and .gitignore, then clone it."
    )
    parser.add_argument(
        "--project_path",
        required=True,
        help="Path to the Unity project directory to be converted"
    )
    parser.add_argument(
        "--output_path",
        required=True,
        help="Path where the cloned project will be saved"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force clone even if output path already exists (will remove existing directory)"
    )
    return parser.parse_args()

# ============================================================================
# 메인 함수
# ============================================================================

def main():
    """메인 실행 함수"""
    args = parse_args()
    
    project_path = Path(args.project_path)
    output_path = Path(args.output_path)
    force = args.force
    
    # ========================================================================
    # 입력 검증
    # ========================================================================
    
    if not project_path.is_dir():
        logger.error(f"Project directory does not exist: {project_path}")
        sys.exit(1)
    
    logger.info("=" * 70)
    logger.info(f"Project Path:  {project_path}")
    logger.info(f"Output Path:   {output_path}")
    logger.info(f"Force Mode:    {'ON' if force else 'OFF'}")
    logger.info("=" * 70)
    
    # ========================================================================
    # Step 1: Git 초기화 및 .gitignore 설정
    # ========================================================================
    
    logger.info("\n[STEP 1] Initializing Git repository and setting up .gitignore...")
    logger.info("-" * 70)
    
    # utils 모듈을 사용하여 처리 (verbose_logger를 전달하여 상세 로그 출력 유지)
    success, msg = utils.init_and_commit_project(project_path, verbose_logger=logger)
    if not success:
        logger.error(f"Failed: {msg}")
        sys.exit(1)
    
    # ========================================================================
    # Step 2: 클론 수행
    # ========================================================================
    
    logger.info("\n[STEP 2] Cloning project to output path...")
    logger.info("-" * 70)
    
    # utils 모듈 사용
    success, msg = utils.clone_project(project_path, output_path, force=force, verbose_logger=logger)
    if not success:
        logger.error(f"Failed: {msg}")
        sys.exit(1)
    
    # ========================================================================
    # 완료
    # ========================================================================
    
    logger.info("\n" + "=" * 70)
    logger.info("[SUCCESS] Project conversion and cloning completed successfully!")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()