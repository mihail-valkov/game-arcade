import arcade
from constants import *

class ParallaxBackgroundLayer():
    def __init__(self, image1, image2, scroll_speed):
        self.background1 = image1
        self.background2 = image2
        self.scroll_speed = scroll_speed
        self.background1_start = 0
        self.background2_start = image1.width

    def draw_background(self, camera: arcade.Camera, y = 0):
        distance = camera.position.x * self.scroll_speed

        temp = camera.position.x * (1 - self.scroll_speed)

        if temp > self.background1_start + self.background1.width:
            self.background1_start += self.background1.width + self.background2.width
        elif temp < self.background1_start - self.background2.width:
            self.background1_start -= self.background1.width + self.background2.width

        if temp > self.background2_start + self.background2.width:
            self.background2_start += self.background1.width + self.background2.width
        elif temp < self.background2_start - self.background1.width:
            self.background2_start -= self.background1.width + self.background2.width

        # Draw the background only if bounds intersect with the viewport
        if self.background1_start + distance - camera.position.x > -self.background1.width and self.background1_start + distance - camera.position.x < SCREEN_WIDTH:
            arcade.draw_lrwh_rectangle_textured(self.background1_start + distance, y, self.background1.width, self.background1.height, self.background1)
        if self.background2_start + distance - camera.position.x > -self.background2.width and self.background2_start + distance - camera.position.x< SCREEN_WIDTH:
            arcade.draw_lrwh_rectangle_textured(self.background2_start + distance, y, self.background2.width, self.background1.height, self.background2)
