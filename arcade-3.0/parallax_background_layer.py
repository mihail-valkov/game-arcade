import arcade
from constants import *

class ParallaxBackgroundLayer():
    def __init__(self, image_file1, image_file2, scroll_speed):
        self.background1 = arcade.load_texture(image_file1)
        self.background2 = arcade.load_texture(image_file2)
        self.scroll_speed = scroll_speed
        self.background1_start = 0
        self.background2_start = self.background1.width
        self.background3_start = self.background2_start + self.background2.width
        self.background4_start = self.background3_start + self.background1.width

    def draw_background(self, camera: arcade.camera.Camera2D, y = 0):
        distance = camera.left * self.scroll_speed

        temp = camera.left * (1 - self.scroll_speed)

        total_width = (self.background1.width + self.background2.width) * 2

        if temp > self.background1_start + self.background1.width:
            self.background1_start += total_width
        elif temp < self.background1_start - self.background2.width:
            self.background1_start -= total_width

        if temp > self.background2_start + self.background2.width:
            self.background2_start += total_width
        elif temp < self.background2_start - self.background1.width:
            self.background2_start -= total_width

        if temp > self.background3_start + self.background1.width:
            self.background3_start += total_width
        elif temp < self.background3_start - self.background2.width:
            self.background3_start -= total_width

        if temp > self.background4_start + self.background2.width:
            self.background4_start += total_width
        elif temp < self.background4_start - self.background1.width:
            self.background4_start -= total_width

        # Draw the background only if bounds intersect with the viewport
        #if True:
        if self.background1_start + distance - camera.left > -self.background1.width and self.background1_start + distance - camera.left < camera.projection_width:
            arcade.draw_lbwh_rectangle_textured(self.background1_start + distance, y, self.background1.width, self.background1.height, self.background1)
        if self.background2_start + distance - camera.left > -self.background2.width and self.background2_start + distance - camera.left < camera.projection_width:
            arcade.draw_lbwh_rectangle_textured(self.background2_start + distance, y, self.background2.width, self.background2.height, self.background2)
        if self.background3_start + distance - camera.left > -self.background1.width and self.background3_start + distance - camera.left < camera.projection_width:
            arcade.draw_lbwh_rectangle_textured(self.background3_start + distance, y, self.background1.width, self.background1.height, self.background1)
        if self.background4_start + distance - camera.left > -self.background2.width and self.background4_start + distance - camera.left < camera.projection_width:
            arcade.draw_lbwh_rectangle_textured(self.background4_start + distance, y, self.background2.width, self.background2.height, self.background2)
