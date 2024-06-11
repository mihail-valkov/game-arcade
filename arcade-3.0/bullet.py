import arcade
import math
from constants import *

class Bullet(arcade.SpriteCircle):
    def __init__(self, plane, time):
        super().__init__(2, arcade.color.YELLOW)
        self.center_x = plane.center_x
        self.center_y = plane.center_y
        angle = (360 - plane.angle) % 360
        self.change_x = math.cos(math.radians(angle)) * BULLET_SPEED
        self.change_y = math.sin(math.radians(angle)) * BULLET_SPEED
        self.start_time = time