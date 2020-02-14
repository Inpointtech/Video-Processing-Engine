"""Demonstration stage."""

import os

import questionary
import time
from moviepy.editor import VideoFileClip as vfc
from video_processing_engine.utils.common import now

from video_processing_engine.core.process.trim import compress_video, trim_num_parts, trim_video
from video_processing_engine.utils.aws import access_file, create_s3_bucket, upload_to_bucket
from video_processing_engine.utils.common import toast
from video_processing_engine.utils.generate import (bucket_name, order_name,
                                                    filename, video_type)
from video_processing_engine.utils.local import create_copy, rename_file
from video_processing_engine.utils.options import (answer, ask_numbers,
                                                   confirm, select_file)
from video_processing_engine.utils.common import file_size
from video_processing_engine.core.process.trim import calc_bitrate
from video_processing_engine.utils.hasher import hash_extension
from video_processing_engine.tests.old.recon import user_cutting_vedio

country_code = answer('Please enter the country code ')
customer_id = ask_numbers('Please enter the customer id ')
contract_id = ask_numbers('Please enter the contract id ')
order_id = ask_numbers('Please enter the order id ')
store_id = ask_numbers('Please enter the store id ')

base_folder = '/home/xames3/Desktop/video_processing_engine/tests/dummy_videos'

bucket = bucket_name(country_code, customer_id, contract_id, order_id, store_id)
area_code = answer('Please enter the area code ')
camera_id = ask_numbers('Please enter the camera id ')
timestamp = None
trim = confirm(
    f'"Bucket name: {bucket}" is generated for this order, do you want to start video processing?')
print('\n? [Note]: A copy of the original video will be created and all operations would be performed on a cloned video.\n')
if not trim:
  toast('Alert', 'Terminating...')
  exit(0)
else:
  name = select_file('Select video file to process ', base_folder)
  display_name = os.path.basename(name)
  extension = os.path.splitext(name)[1][1:]
  codec = dict(map(reversed, hash_extension.items()))[extension]
  print(f'? Stats for original video: {display_name}')
  print(f'? Length of original video: {float(vfc(name).duration) / 60} mins.')
  print(f'? Bitrate of original video: {calc_bitrate(name)} kbps')
  print(f'? Codec used by original video: {codec}')
  print(f'? Space occupied by original video: {file_size(name)}')
  compress = confirm('Do you want to compress the clone video?')
  trimmed = confirm('Do you want to trim the clone video?')
  if trimmed:
    trim_compress = confirm('Do you need to compress the trimmed videos?')
  else:
    trim_compress = False
  vid_type = video_type(compress, trimmed, trim_compress)
  original = rename_file(name, filename(bucket, order_name(area_code, camera_id,
                                                           timestamp), 'aaaa'))
  create_copy(original)
  clone = rename_file(original, filename(bucket, order_name(area_code,
                                                            camera_id, timestamp),
                                         vid_type))
  if compress:
    compressed_clone = compress_video(clone)
    display_name = os.path.basename(compressed_clone)
    extension = os.path.splitext(compressed_clone)[1][1:]
    codec = dict(map(reversed, hash_extension.items()))[extension]
    print(f'? Stats of compressed video: {display_name}')
    print(f'? Length of compressed video: {float(vfc(compressed_clone).duration) / 60} mins.')
    print(f'? Bitrate of compressed video: {calc_bitrate(compressed_clone)} kbps')
    print(f'? Codec used by compressed video: {codec}')
    print(f'? Space occupied by compressed video: {file_size(compressed_clone)}')
    if compress and trim_compress:
      num = ask_numbers(
          'Please enter the number of clips you want to trim the video into ')
      toast('Initiate trimming',
            f'Started trimming of {name} in {num} equal parts.')
      trim_num_parts(clone, int(num), local=True)
  elif trimmed:
    num = ask_numbers(
        'Please enter the number of clips you want to trim the video into ')
    toast('Initiate trimming',
          f'Started trimming of {name} in {num} equal parts.')
    trim_num_parts(clone, int(num), local=True)
  # print(bucket)
  # create_s3_bucket(access_key='AKIAR4DHCUP262T3WIUX', secret_key='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', bucket_name=bucket)
  # time.sleep(3.0)
  toast('Success!', f'"{bucket}" bucket created on S3.')
  # clone = '/home/xames3/Desktop/video_processing_engine/tests/dummy_videos/eA00010101001P01021420Q2056acc.mp4'
  # urls = []
  # for file in sorted(os.listdir(os.path.splitext(clone)[0])):
  #   file = os.path.join(os.path.splitext(clone)[0], file)
  #   url = upload_to_bucket('AKIAR4DHCUP262T3WIUX', 'B2ii3+34AigsIx0wB1ZU01WLNY6DYRbZttyeTo+5', bucket, file)
  #   urls.append(url)
  # print(urls)
  # read_files = confirm('Do you want to read/download files from S3?')
  # if read_files:
  #   for url in urls:
  #     access_file('AKIAR4DHCUP262T3WIUX', 'B2ii3+34AigsIx0wB1ZU01WLNY6DYRbZttyeTo+5', url, bucket)
