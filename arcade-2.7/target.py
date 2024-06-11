import arcade
from constants import *

class Target(arcade.Sprite):
    def __init__(self, image, center_x, bottom):
        super().__init__(image, scale=TARGET_SCALE)
        self.center_x = center_x
        self.bottom = bottom
        self.shoot_interval = 2.0  # Each target will shoot every 2 seconds
        self.last_shot_time = 0  # Initialize the last shot time
