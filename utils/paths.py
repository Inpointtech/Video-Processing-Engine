"""Utility for defining the necessary paths."""

import os

# TODO(xames3): Remove suppressed pyright warnings.
# pyright: reportMissingTypeStubs=false
from video_processing_engine.utils.common import parent_path
from video_processing_engine.vars import models

# Models used in the video processing engine.
models_path = os.path.join(parent_path, 'models')
caffe_model = os.path.join(models_path, models.FACE_CAFFEMODEL)
prototext = os.path.join(models_path, models.FACE_PROTOTEXT)
# Path where all the downloaded files are stored.
downloads = os.path.join(parent_path, 'downloads')
