from queue import Queue
import threading
import time
import sys
import json

import sys
import logging
from logging import handlers


class errorLogger(object):
  """
      created only to record errors
  """
  LOG_FILENAME = '/home/xa/Desktop/video_processing_engine/video_processing_engine/logs/error.log'
  handler = handlers.TimedRotatingFileHandler(
      LOG_FILENAME, when="H", interval=12, backupCount=30)
  formatter = logging.Formatter(
      "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
  handler.setFormatter(formatter)
  try:
    def __init__(self):
      self.logger = logging.getLogger("ERROR")
      self.logger.setLevel(logging.INFO)
      self.logger.addHandler(self.handler)

    def wrDebugLog(self, msg=None,client_address=None):
      if msg not in [None, ""]:
        self.logger.info(msg)
  except Exception as e:
    print(e)


class DataLogger(object):
  LOG_FILENAME = '/home/xa/Desktop/video_processing_engine/video_processing_engine/logs/data.log' # path tfor log
  handler = handlers.TimedRotatingFileHandler(LOG_FILENAME, when="H", interval=12, backupCount=30)
  formatter = logging.Formatter(
      "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
  handler.setFormatter(formatter)
  try:
    def __init__(self):
      self.logger = logging.getLogger("CONSUMER")
      self.logger.setLevel(logging.INFO)
      self.logger.addHandler(self.handler)

    def wrDebugLog(self, msg=None,client_address=None):
      if msg not in [None, ""]:
        self.logger.info(msg)
  except Exception as e:
    print(e)


# example on how to use
# DataLogger = DataLogger()
# errorLogger = errorLogger()


def someProcessMethod(data):
  try:
    # some processing
    # some data logging if needed
    DataLogger.wrDebugLog(data)
  except Exception as e:
    #logginer error here
    error_msg = "some error msg u need to have "
    errorLogger.wrDebugLog(error_msg)

threadLimiter = threading.BoundedSemaphore(50)  # thread pool max-size
from video_processing_engine.core.turntable import spin

class myThread (threading.Thread):
  def __init__(self, data):
    threading.Thread.__init__(self)
    self.data = data

  def run(self):
    threadLimiter.acquire()
    try:
        self.Executemycode()
    finally:
        threadLimiter.release()

  def Executemycode(self):
    #print "Starting " + self.name
    # youMethodToProcess(self.data)
    spin(self.data)
    #print "Exiting " + self.name


def myConsumer(message):
    # some connection params if using consumer
    # thread log goes below
    counter = 0
    while threading.active_count() > 50:  # safety check for not letting thread creation goes out of control
        counter += 1
        test_error = "thread max limit reached :%s, counter Value : %s" % (
            threading.active_count(), counter)
        # errorLogger class used for logging, not mandatory
        errorLogger.wrDebugLog(test_error)
        time.sleep(1)
    test_error = "current thread count  :%s, counter Value : %s ThreadName : %s " % (
        threading.active_count(), counter, threading.current_thread().name)
    errorLogger.wrDebugLog(test_error)
    # some date that u need to pass as an argument for further calculation
    value = message
    thread = myThread(value)
    thread.start()

# simple thread concept to create multithreads
if __name__ == "__main__":

  json_obj_1 = {"country_code": "in",
              "customer_id": "0555",
              "contract_id": "44",
              "order_id": "33",
              "store_id": "221",
              "camera_id": "1",
              "area_code": "x",
              "use_stored": True,
              "access_mode": "azure",
              "public_url": "",
              "azure_account_name": "b0videoprocessingengine",
              "azure_account_key": "PWqNC8JKvd+aKu/SvkSunyv7Mx8oRTRuAOkz+vSu66IcbOzqxAEYswkB4PpMfK5RZiM7GhJlWXnts7ksmIn/pA==",
              "azure_container_name": "video-processing-engine-container",
              "azure_blob_name": "60 Minute Timer.mp4",
              "remote_username": False,
              "remote_password": False,
              "remote_public_address": False,
              "remote_file": False,
              "s3_access_key": "",
              "s3_secret_key": "",
              "s3_url": "",
              "teamviewer_file": "test.mp4",
              "s3_bucket_name": False,
              "start_time": "17:30:00",
              "end_time": "17:50:00",
              "camera_address": "192.168.0.5",
              "camera_port": "554",
              "camera_username": "admin",
              "camera_password": "user@1234",
              "timestamp_format": False,
              "select_sample": True,
              "sampling_rate": "5",
              "perform_compression": True,
              "perform_trimming": True,
              "trim_compressed": True,
              "trim_type": "trim_by_factor",
              "compression_ratio": "60",
              "number_of_clips": "24",
              "equal_distribution": True,
              "clip_length": 30,
              "trim_factor": "s",
              "last_clip": False,
              "sample_start_time": "17:40:00",
              "sample_end_time": "17:45:00",
              }
  json_obj_2 = {"country_code": "in",
              "customer_id": "0555",
              "contract_id": "44",
              "order_id": "33",
              "store_id": "221",
              "camera_id": "1",
              "area_code": "x",
              "use_stored": True,
              "access_mode": "azure",
              "public_url": "",
              "azure_account_name": "b0videoprocessingengine",
              "azure_account_key": "PWqNC8JKvd+aKu/SvkSunyv7Mx8oRTRuAOkz+vSu66IcbOzqxAEYswkB4PpMfK5RZiM7GhJlWXnts7ksmIn/pA==",
              "azure_container_name": "video-processing-engine-container",
              "azure_blob_name": "60 Minute Timer.mp4",
              "remote_username": False,
              "remote_password": False,
              "remote_public_address": False,
              "remote_file": False,
              "s3_access_key": "",
              "s3_secret_key": "",
              "s3_url": "",
              "teamviewer_file": "test.mp4",
              "s3_bucket_name": False,
              "start_time": "17:30:00",
              "end_time": "17:50:00",
              "camera_address": "192.168.0.5",
              "camera_port": "554",
              "camera_username": "admin",
              "camera_password": "user@1234",
              "timestamp_format": False,
              "select_sample": True,
              "sampling_rate": "5",
              "perform_compression": True,
              "perform_trimming": True,
              "trim_compressed": True,
              "trim_type": "trim_by_factor",
              "compression_ratio": "60",
              "number_of_clips": "24",
              "equal_distribution": True,
              "clip_length": 30,
              "trim_factor": "s",
              "last_clip": False,
              "sample_start_time": "17:40:00",
              "sample_end_time": "17:45:00",
              }
  json_obj_1 = json.dumps(json_obj_1)
  json_obj_2 = json.dumps(json_obj_2)
  json_obj = [json_obj_1, json_obj_2]
  print("basic python threads example")
  threadPool = 10
  for x, i in enumerate(json_obj): 
      threading.Thread(target=myConsumer, args=([i]), name='consumerThread-%s'%(x+1)) .start()
