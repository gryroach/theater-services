import time

from redis import Redis

from functional.settings import test_settings

if __name__ == "__main__":
    redis = Redis(
        host=test_settings.redis_host,
        port=test_settings.redis_port,
        socket_connect_timeout=1,
    )
    while True:
        if redis.ping():
            break
        time.sleep(1)
