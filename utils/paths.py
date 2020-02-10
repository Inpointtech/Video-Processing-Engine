"""Utility for defining the necessary paths."""

import os

from video_processing_engine.utils.common import parent_path
from video_processing_engine.vars import models

models_path = os.path.join(parent_path, 'models/')
caffe_model = os.path.join(models_path, models.FACE_CAFFEMODEL)
prototext = os.path.join(models_path, models.FACE_PROTOTEXT)
