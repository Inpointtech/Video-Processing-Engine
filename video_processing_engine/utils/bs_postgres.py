"""Utility for working with the PostgresSQL database."""

from typing import Union

from peewee import *

db = PostgresqlDatabase('bitstreamuatdb_20200328_pool1', user='uatuser',
                        password='admin@123', host='161.35.1.43')

__db_connect = None


class BaseModel(Model):
  class Meta:
    database = db


class VideoMapping(BaseModel):
  order_id = IntegerField() # Foreign Key references to PK of CCOrder.
  video_id = CharField()
  video_url = CharField()
  video_file_name = CharField()
  is_used_for_survey = BooleanField(default=False)

  class Meta:
    db_table = u'bitstreamapp_video_mapping'


def create_video_map_obj(order_id: Union[int, str], video_id: int,
                         video_url: str, video_file_name: str) -> None:
  VideoMapping.create(order_id=order_id, video_id=video_id,
                      video_url=video_url, video_file_name=video_file_name)


def connectPsqlDB():
  print('Connecting to PostgresSQL database...')

  global __db_connect
  __db_connect = db.connect()


if not __db_connect:
  connectPsqlDB()
