"""Module to define model names for inference."""

# OpenCV models path
FACE_PROTOTEXT = 'deploy.prototxt.txt'
FACE_CAFFEMODEL = 'res10_300x300_ssd_iter_140000.caffemodel'
TEXT_EAST_DETECTOR = 'frozen_east_text_detection.pb'
FRONTAL_HAAR = 'haarcascade_frontalface_default.xml'
FRONTAL_HAAR_2 = 'haarcascade_frontalface_alt2.xml'
PROFILE_HAAR = 'haarcascade_profileface.xml'
TF_PROTOTEXT = 'tf_ssd_deploy.prototxt'
TF_CAFFEMODEL = 'tf_ssd_deploy.caffemodel'

# Confidence scores
DETECTED_FACE_CONFIDENCE = 0.7
DETECTED_TEXT_CONFIDENCE = 0.6
DETECTED_MOTION_CONFIDENCE = 100

# References
REFERENCE_VIDEO = 'reference.mkv'
