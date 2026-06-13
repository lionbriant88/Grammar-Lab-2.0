"""健康检查测试"""

import pytest
import requests
import time


BASE_URL = "http://127.0.0.1:18765"


def test_health_endpoint():
    """测试 /health 接口"""
    # 等待服务启动
    for _ in range(30):  # 最多等 30 秒
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=2)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] in ["ok", "error"]
            assert "model_loaded" in data
            assert "version" in data
            
            if data["model_loaded"]:
                print(f"✓ 模型已加载，版本: {data.get('model_version', 'unknown')}")
            else:
                print("⚠ 模型未加载")
            
            return
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    
    pytest.fail("服务启动超时")


if __name__ == "__main__":
    test_health_endpoint()
    print("✓ 健康检查测试通过")
