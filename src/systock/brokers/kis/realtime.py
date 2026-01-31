# src/systock/brokers/kis/realtime.py

class KisRealtimeMixin:
    """실시간 웹소켓 기능"""
    
    async def connect_websocket(self):
        """웹소켓 연결 (구현 예정)"""
        self.logger.info("웹소켓 연결 시도...")
        pass