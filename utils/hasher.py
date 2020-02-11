"""Utility for generating the raw hashes."""

import string
import itertools

# Dictionary for characters from range 0 - 25.
hash_26 = {k: v for k, v in enumerate(string.ascii_uppercase, start=1)}
# Dictionary for characters from range 0 - 51.
hash_52 = {k: v for k, v in enumerate(string.ascii_letters)}
# Dictionary for characters from range 0 - 2703
temp = itertools.product(string.ascii_letters, string.ascii_letters)
hash_2704 = {k: v for k, v in enumerate(list(map(''.join, temp)))}
# Dictionary for hashing area.
hash_area = {'P': 'Parking lot',
             'G': 'Garage',
             'C': 'Counter',
             'K': 'Kitchen',
             'L': 'Lobby',
             'A': 'Aisle',
             'B': 'Basement',
             'F': 'Cafeteria',
             'O': 'Outdoor area',
             'W': 'Workdesk',
             'M': 'Meeting/conference room',
             'R': 'Reception desk',
             'X': 'Exit',
             'N': 'Entrance',
             'E': 'Extras'}
# Dictionary for hashing codecs and extensions.
hash_extension = {'libx264': 'mp4',
                  'mpeg4': 'mp4',
                  'rawvideo': 'avi',
                  'png': 'avi',
                  'libvorbis': 'ogv',
                  'libvpx': 'webm'}
