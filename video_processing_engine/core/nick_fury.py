import json
import threading
import time
from uuid import uuid4
from datetime import timedelta

from video_processing_engine.core.bugsbunny import log, now, spin, phase_one

_log = log(__file__)


class SpawnTheSheep(object):

  def __init__(self):
    super(SpawnTheSheep, self).__init__()
    self.active = []
    self.lock = threading.Lock()

  def spawn(self, name: str):
    with self.lock:
      self.active.append(name)

  def despawn(self, name: str):
    with self.lock:
      self.active.remove(name)


def sheep(threads: threading.Semaphore, json_obj: dict) -> None:
  """Sheep thread object.
  
  Args:
    threads: Thread semaphore object (thread count).
    json_obj: JSON dictionary which Admin sends to VPE.
  """
  with threads:
    name = threading.currentThread().getName()
    pool.spawn(name)
    update_time = None

    try:
      run_date = now().strftime('%Y-%m-%d')
      while True:
        start_time = json_obj['start_time']
        timezone = json_obj.get('camera_timezone', 'UTC')
        start_time = update_time if update_time else start_time
        _start_time = f'{run_date} {start_time}'
        _log.info('Video processing engine is scheduled to start '
                  f'at {_start_time}.')

        while True:
          if str(now()) == str(_start_time):
            # spin(json.dumps(json_obj), run_date, now(), _log)
            phase_one(json.dumps(json_obj), run_date, now(), _log)
            _log.info('Updating next run cycle.')
            run_date = now() + timedelta(days=1)
            run_date = run_date.strftime('%Y-%m-%d')
            update_time = None
            break

          time.sleep(1.0)
    except KeyboardInterrupt:
      _log.error('Video processing engine sheep interrupted.')
      pool.despawn(name)
    except Exception as _error:
      _log.exception(_error)
    finally:
      pool.despawn(name)

pool = SpawnTheSheep()
threads = threading.Semaphore(2000)

orders = []

while True:
  for idx in orders:
    agl = ''.join([idx['customer_id'], idx['area_code'],
                  idx['camera_id'], str(uuid4())[:8]])
    t = threading.Thread(target=sheep, name=f'order_{agl}',
                         args=(threads, idx))
    t.start()
  else:
    orders.append('New value')
