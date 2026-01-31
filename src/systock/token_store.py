# src/systock/token_store.py

from abc import ABC, abstractmethod
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

# [선택] 라이브러리가 설치되어 있을 때만 import
try:
    import keyring
except ImportError:
    keyring = None

try:
    import redis
except ImportError:
    redis = None


class TokenStore(ABC):
    """토큰 저장소 추상 클래스"""

    @abstractmethod
    def save(self, token: str, expired_at: str, acc_no: str):
        pass

    @abstractmethod
    def load(self, acc_no: str) -> Optional[Tuple[str, datetime]]:
        """
        리턴값: (access_token, 만료시간datetime) 또는 None
        """
        pass


# -----------------------------------------------------------
# 1. 파일(JSON) 저장소 (기본값)
# -----------------------------------------------------------
class FileTokenStore(TokenStore):
    def __init__(self, file_path: str = "kis_token.json"):
        self.file_path = file_path
        self.logger = logging.getLogger("systock.store.file")

    def save(self, token: str, expired_at: str, acc_no: str):
        # 여러 계좌를 파일 하나에 저장하기 위해 구조 변경 가능하지만,
        # 여기선 간단히 파일 하나에 한 계좌(혹은 덮어쓰기)로 구현
        data = {
            "access_token": token,
            "expired_at": expired_at,
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            self.logger.warning(f"토큰 파일 저장 실패: {e}")

    def load(self, acc_no: str) -> Optional[Tuple[str, datetime]]:
        if not os.path.exists(self.file_path):
            return None
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            token = data.get("access_token")
            expired_str = data.get("expired_at")
            if not token or not expired_str:
                return None

            return token, datetime.strptime(expired_str, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None


# -----------------------------------------------------------
# 2. OS Keyring 저장소 (보안 강화)
# -----------------------------------------------------------
class KeyringTokenStore(TokenStore):
    def __init__(self, service_name: str = "systock"):
        if keyring is None:
            raise ImportError("keyring 라이브러리가 필요합니다. (pip install keyring)")
        self.service_name = service_name

    def save(self, token: str, expired_at: str, acc_no: str):
        # keyring은 문자열만 저장 가능하므로 JSON 문자열로 변환
        data = json.dumps({"token": token, "expired_at": expired_at})
        keyring.set_password(self.service_name, acc_no, data)

    def load(self, acc_no: str) -> Optional[Tuple[str, datetime]]:
        data_str = keyring.get_password(self.service_name, acc_no)
        if not data_str:
            return None
        try:
            data = json.loads(data_str)
            return data["token"], datetime.strptime(
                data["expired_at"], "%Y-%m-%d %H:%M:%S"
            )
        except:
            return None


# -----------------------------------------------------------
# 3. Redis 저장소 (프로/서버용)
# -----------------------------------------------------------
class RedisTokenStore(TokenStore):
    def __init__(self, host="localhost", port=6379, db=0, password=None):
        if redis is None:
            raise ImportError("redis 라이브러리가 필요합니다. (pip install redis)")
        self.r = redis.Redis(host=host, port=port, db=db, password=password)

    def save(self, token: str, expired_at: str, acc_no: str):
        key = f"systock:token:{acc_no}"
        # 만료 시간까지 남은 초 계산 (TTL 설정용)
        exp_dt = datetime.strptime(expired_at, "%Y-%m-%d %H:%M:%S")
        ttl = int((exp_dt - datetime.now()).total_seconds())

        if ttl > 0:
            data = json.dumps({"token": token, "expired_at": expired_at})
            self.r.setex(key, ttl, data)  # 자동 폭파 설정

    def load(self, acc_no: str) -> Optional[Tuple[str, datetime]]:
        key = f"systock:token:{acc_no}"
        data_bytes = self.r.get(key)
        if not data_bytes:
            return None
        try:
            data = json.loads(data_bytes)
            return data["token"], datetime.strptime(
                data["expired_at"], "%Y-%m-%d %H:%M:%S"
            )
        except:
            return None
