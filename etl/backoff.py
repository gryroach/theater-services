from functools import wraps
from time import sleep

from logger import logger


def backoff(start_sleep_time=0.1, factor=2, border_sleep_time=10):
    """
    Функция для повторного выполнения функции через некоторое время,
    если возникла ошибка. Использует наивный экспоненциальный
    рост времени повтора (factor) до граничного времени ожидания (border_sleep_time)

    Формула:
        t = start_sleep_time * (factor ^ n), если t < border_sleep_time
        t = border_sleep_time, иначе
    :param start_sleep_time: начальное время ожидания
    :param factor: во сколько раз нужно увеличивать время ожидания на каждой итерации
    :param border_sleep_time: максимальное время ожидания
    :return: результат выполнения функции
    """

    def func_wrapper(func):
        @wraps(func)
        def inner(*args, **kwargs):
            n = 0
            while n < 10:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.error(f'Функция {func.__name__} упала с ошибкой %s', e)
                    n += 1
                    time_ = min(start_sleep_time * (factor ** n), border_sleep_time)
                    sleep(time_)

        return inner
    return func_wrapper
