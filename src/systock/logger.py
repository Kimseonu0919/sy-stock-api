import os
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime


def setup_logger(name: str = "systock") -> logging.Logger:
    """
    애플리케이션 전역 로거 설정
    - 콘솔: INFO 레벨 (간단한 정보)
    - 파일: DEBUG 레벨 (상세 정보, 날짜별 자동 회전)
    """
    logger = logging.getLogger(name)

    # 이미 설정된 경우 중복 설정 방지
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # 1. 포맷 설정
    # 예: [2023-10-25 14:00:01] [INFO] 주문 전송 완료 (Samsung)
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 2. 콘솔 핸들러 (화면 출력용)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 3. 파일 핸들러 (기록 저장용)
    # logs 폴더가 없으면 생성
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 날짜별로 파일 분리 (매일 자정에 새로운 파일 생성)
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"{log_dir}/systock_{today}.log"

    file_handler = TimedRotatingFileHandler(
        filename=filename,
        when="midnight",
        interval=1,
        backupCount=30,  # 30일치 보관
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
