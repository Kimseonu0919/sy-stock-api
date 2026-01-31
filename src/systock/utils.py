import time
import threading
from collections import deque  # [추가] 가장 빠른 큐 자료구조

class RateLimiter:
    """
    토큰 버킷 알고리즘 기반의 정교한 속도 제한기 (deque 최적화 적용)
    - 멀티 스레드 환경 안전 (Thread-Safe)
    - deque를 사용하여 오래된 기록 제거 속도 최적화 O(1)
    """
    def __init__(self, max_calls: int, period: float = 1.0):
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()  # [변경] list 대신 deque 사용
        self.lock = threading.Lock()

    def wait(self):
        """호출 가능할 때까지 대기(Sleep)하는 메서드"""
        with self.lock:
            while True:
                current_time = time.time()
                
                # 1. [최적화] 기간이 지난 오래된 기록을 앞에서부터 제거
                # filter나 리스트 컴프리헨션처럼 전체를 훑지 않고, 만료된 것만 쏙 빼냅니다.
                while self.calls and self.calls[0] <= current_time - self.period:
                    self.calls.popleft()

                # 2. 아직 여유가 있다면 통과
                if len(self.calls) < self.max_calls:
                    self.calls.append(current_time)
                    return # 대기 없이 리턴

                # 3. 꽉 찼다면, 가장 오래된 호출이 만료될 때까지 대기
                # (period - (현재시간 - 가장오래된시간))
                earliest_call = self.calls[0]
                sleep_time = self.period - (current_time - earliest_call)
                
                if sleep_time > 0:
                    time.sleep(sleep_time + 0.01) # 0.01초 여유 버퍼