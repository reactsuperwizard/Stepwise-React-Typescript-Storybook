from dataclasses import dataclass

import pytest

from apps.core.celery.throttle import get_task_wait, parse_rate


@pytest.mark.django_db
def test_parse_rate():
    assert parse_rate('1/s') == (1, 1)
    assert parse_rate('5/s') == (5, 1)
    assert parse_rate('10/2s') == (10, 2)
    assert parse_rate('10/m') == (10, 60)
    assert parse_rate('10/2m') == (10, 120)
    assert parse_rate('5/h') == (5, 60 * 60)
    assert parse_rate('20/4h') == (20, 60 * 60 * 4)


@dataclass
class Task:
    name: str


@pytest.mark.django_db
class TestGetTaskWait:
    def test_global_throttle(self):
        task = Task(name='test-task')
        rate = '2/5s'

        assert get_task_wait(task=task, rate=rate) == 0

        assert get_task_wait(task=task, rate=rate) == 0

        assert 4.9 <= get_task_wait(task=task, rate=rate) <= 5

        assert 7.4 <= get_task_wait(task=task, rate=rate) <= 7.5

        assert 9.9 <= get_task_wait(task=task, rate=rate) <= 10

        assert 12.4 <= get_task_wait(task=task, rate=rate) <= 12.5

    def test_throttle_per_key(self):
        task = Task(name='test-task')
        rate = '1/5s'

        assert get_task_wait(task=task, rate=rate, key='first') == 0

        assert get_task_wait(task=task, rate=rate, key='second') == 0

        assert 4 <= get_task_wait(task=task, rate=rate, key='first') <= 5

        assert 4 <= get_task_wait(task=task, rate=rate, key='second') <= 5
