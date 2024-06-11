import arcade
import math
from constants import *

class Bullet(arcade.SpriteCircle):
    def __init__(self, plane, time):
        super().__init__(2, arcade.color.YELLOW)
        self.center_x = plane.center_x
        self.center_y = plane.center_y
        self.angle = plane.angle
        self.change_x = math.cos(math.radians(self.angle)) * BULLET_SPEED
        self.change_y = math.sin(math.radians(self.angle)) * BULLET_SPEED
        self.start_time = time