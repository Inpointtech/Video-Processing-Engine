"""Utility for defining the necessary paths."""

import os

from video_processing_engine.vars import models as md

# Parent directory path. All the references will be made relatively
# using the below defined parent directory.
parent_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Models used in the video processing engine.
models = os.path.join(parent_path, 'video_processing_engine/models')
caffemodel = os.path.join(models, md.FACE_CAFFEMODEL)
prototxt = os.path.join(models, md.FACE_PROTOTEXT)
frontal_haar = os.path.join(models, md.FRONTAL_HAAR)
frontal_haar_2 = os.path.join(models, md.FRONTAL_HAAR_2)
profile_haar = os.path.join(models, md.PROFILE_HAAR)

# Path where all the downloaded files are stored.
downloads = os.path.join(parent_path, 'downloads')

# Other paths
live = os.path.join(parent_path, 'live')
reports = os.path.join(parent_path, 'reports')
logs = os.path.join(parent_path, 'logs')
