import arcade
import math
from constants import *

class Plane(arcade.Sprite):
    def __init__(self):
        super().__init__("plane.png", PLANE_SCALE)
        self.health = MAX_HEALTH
        self.angle = 0
        self.speed = 0
        self.health = 10
        self.flipped = False
        self.texture_flipped = arcade.load_texture("plane.png", flipped_vertically=True)
        self.setup_hit_box()
        
    def setup_hit_box(self):
        hit_box_points = [
            (-108, 3), (-115, 15), (-108, 38), (-95, 42), 
            (-78, 35), (-60, 18), (35, 28), (42, 48), (90, 50), 
            (90, 30), (105, 31), (105, 53), (110, 53), (110, -45), 
            (100, -15), (90, -15), (90, -45), (73, -56),
            (58, -45), (50, -15)
        ]
        if self.flipped:
            hit_box_points = [(x, -y) for x, y in hit_box_points]
        self.set_hit_box(hit_box_points)

    def flip(self):
        self.flipped = not self.flipped
        self.texture = self.texture_flipped if self.flipped else self.original_texture
        self.setup_hit_box()
