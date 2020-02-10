"""Module to define colors for detection overlays."""

import random

red = [48, 59, 255]
blue = [255, 122, 0]
green = [100, 217, 76]
yellow = [0, 204, 255]
orange = [0, 149, 255]
teal = [250, 200, 90]
purple = [214, 86, 88]
pink = [85, 45, 255]
white = [255, 255, 255]
black = [0, 0, 0]

colors_list = [red, blue, green, yellow, orange, teal, purple, pink, black]
random_color = random.choice(colors_list)
