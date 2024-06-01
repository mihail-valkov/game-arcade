import arcade
import random
import numpy as np
from arcade.experimental import Shadertoy

EXPLOSION_DURATION = 1.5

# Define the Explosion class to store position and start time
class Explosion:
    def __init__(self, position, size, camera_pos, start_time):
        self.position = position
        self.size = size
        self.orig_position = position
        self.camera_pos = camera_pos
        self.start_time = start_time
        self.sprite = None

class ShaderManager:
    def __init__(self, window_size):
        self.shadertoy = Shadertoy.create_from_file(window_size, "multiExplosion.glsl")

        self.channel0 = self.shadertoy.ctx.framebuffer(
            color_attachments=[self.shadertoy.ctx.texture(window_size, components=4)]
        )
        self.channel1 = self.shadertoy.ctx.framebuffer(
            color_attachments=[self.shadertoy.ctx.texture(window_size, components=4)]
        )

        self.shadertoy.channel_0 = self.channel0.color_attachments[0]
        self.shadertoy.channel_1 = self.channel1.color_attachments[0]

    def render(self, time, explosions, camera_position):
        delayed_explosions = [exp for exp in explosions if time - exp.start_time < 0]  
        active_explosions = [exp for exp in explosions if 0 <= time - exp.start_time <= EXPLOSION_DURATION]

        for exp in active_explosions:
            exp.position = (
                exp.orig_position[0] - camera_position[0],
                exp.orig_position[1] - camera_position[1]
            )
        
        positions = [exp.position for exp in active_explosions]
        sizes = [exp.size for exp in active_explosions]
        times = [exp.start_time for exp in active_explosions]

        positions_flat = [coord for pos in positions for coord in pos] + [0.0, 0.0] * (10 - len(positions))
        sizes_array = sizes + [0.0] * (10 - len(times))
        times_array = times + [0.0] * (10 - len(times))
        num_explosions = len(active_explosions)

        active_explosions += delayed_explosions

        positions_tuple = tuple(positions_flat)
        sizes_tuple = tuple(sizes_array)
        times_tuple = tuple(times_array)

        self.shadertoy.program["explodePositions"] = positions_tuple
        self.shadertoy.program["explosionSizes"] = sizes_tuple
        self.shadertoy.program["explodeTimes"] = times_tuple
        self.shadertoy.program["numExplosions"] = num_explosions

        self.shadertoy.render(time=time)


class MyGame(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        #create rectangle shape for the background
        self.background = arcade.create_rectangle_filled(width/2, height/2 + 150, width, height, arcade.color.DEEP_SKY_BLUE)
        # Load the shader
        self.camera = arcade.Camera(800, 600)

        self.load_shader((width, height))

        # List to store active explosions
        self.explosions = []

        # Initialize time
        self.time = 0.0

    def load_shader(self, window_size):
        self.shader_manager = ShaderManager(window_size)

    def on_draw(self):

        arcade.start_render()

        # Draw your game here
        # ...
        self.shader_manager.channel0.use()
        self.shader_manager.channel0.clear()
        
        self.background.draw()
        
        self.use()
        self.clear()

        self.shader_manager.render(self.time, self.explosions, (0, 0))

    def on_update(self, delta_time):
        self.time += delta_time
        """ for explosion in self.explosions:
            explosion.start_time = delta_time """

    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE:
            # Simulate an explosion at a random position
            x, y = arcade.rand_in_rect((15,15), self.size[0] - 15, self.size[1] - 15)
            new_explosion = Explosion((x, y), start_time=self.time)
            self.explosions.append(new_explosion)

    def on_mouse_press(self, x, y, button, modifiers):
        # Trigger an explosion at the mouse click coordinates
        new_explosion = Explosion((x, y), 2., self.camera.position, start_time=self.time)
        self.explosions.append(new_explosion)

# Create and run the game
def main():
    game = MyGame(800, 600, "Shader Explosion Example")
    arcade.run()

if __name__ == "__main__":
    main()
