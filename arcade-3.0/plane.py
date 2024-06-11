import arcade
import math
from constants import *
from arcade.hitbox import *

class Plane(arcade.Sprite):
    def __init__(self):
        super().__init__("plane.png", scale=PLANE_SCALE)
        self.health = MAX_HEALTH
        self.speed = 0
        self.health = 10
        self.flipped = False
        texture0 = arcade.load_texture("plane.png") # , hit_box_algorithm= PymunkHitBoxAlgorithm(detail=15.))
        texture1 = texture0.flip_top_bottom() # hit_box_algorithm= PymunkHitBoxAlgorithm(detail=15.))`
        self.textures.append(texture0)
        self.textures.append(texture1)
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

        self.hit_box = arcade.hitbox.HitBox(points=hit_box_points, scale=(self.scale, self.scale), position=(self.center_x, self.center_y))

    def flip(self):
        self.flipped = not self.flipped
        self.set_texture(1 if self.flipped else 0)
        self.setup_hit_box()
