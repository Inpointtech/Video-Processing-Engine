"""Utility for defining the necessary paths."""

import os

# TODO(xames3): Remove suppressed pyright warnings.
# pyright: reportMissingTypeStubs=false
from video_processing_engine.vars import models

# Parent directory path. All the references will be made relatively
# using the below defined parent directory.
parent_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Models used in the video processing engine.
models_path = os.path.join(parent_path, 'models')
caffe_model = os.path.join(models_path, models.FACE_CAFFEMODEL)
prototext = os.path.join(models_path, models.FACE_PROTOTEXT)

# Path where all the downloaded files are stored.
downloads = os.path.join(parent_path, 'downloads')

# Other paths
live_path = os.path.join(parent_path, 'live')