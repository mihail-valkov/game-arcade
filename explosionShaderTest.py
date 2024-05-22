import arcade
import numpy as np
from arcade.experimental import Shadertoy

# Define the Explosion class to store position and start time
class Explosion:
    def __init__(self, position, start_time):
        self.position = position
        self.start_time = start_time

class MyGame(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        #create rectangle shape for the background
        self.background = arcade.create_rectangle_filled(width/2, height/2 + 150, width, height, arcade.color.SKY_BLUE)
        # Load the shader
        self.load_shader((width, height))

        # List to store active explosions
        self.explosions = []

        # Initialize time
        self.time = 0.0

    def load_shader(self, window_size):
        
        self.shadertoy = Shadertoy.create_from_file(self.get_size(), "multiExplosion.glsl")
    
        # Create the channels 0 and 1 frame buffers.
        # Make the buffer the size of the window, with 4 channels (RGBA)
        self.channel0 = self.shadertoy.ctx.framebuffer(
            color_attachments=[self.shadertoy.ctx.texture(window_size, components=4)]
        )
        self.channel1 = self.shadertoy.ctx.framebuffer(
            color_attachments=[self.shadertoy.ctx.texture(window_size, components=4)]
        )

        # Assign the frame buffers to the channels
        self.shadertoy.channel_0 = self.channel0.color_attachments[0]
        self.shadertoy.channel_1 = self.channel1.color_attachments[0]

    def on_draw(self):

        arcade.start_render()

        # Draw your game here
        # ...
        self.channel0.use()
        self.channel0.clear()
        
        self.background.draw()
        
        # Prepare data for the shader
        active_explosions = [exp for exp in self.explosions if self.time - exp.start_time <= 1.0]
        positions = [exp.position for exp in active_explosions]
        times = [exp.start_time for exp in active_explosions]

        # Ensure the arrays are the correct length and type
        positions_flat = [coord for pos in positions for coord in pos] + [0.0, 0.0] * (10 - len(positions))
        times_array = times + [0.0] * (10 - len(times))
        num_explosions = len(active_explosions)

        # Convert to tuples
        positions_tuple = tuple(positions_flat)
        times_tuple = tuple(times_array)

        # Pass data to the shader
        self.shadertoy.program["explodePositions"] = positions_tuple
        self.shadertoy.program["explodeTimes"] = times_tuple
        self.shadertoy.program["numExplosions"] = num_explosions

        self.use()
        self.clear()
       
        # Use the shader to draw the explosions
        self.shadertoy.render(time=self.time)

    def on_update(self, delta_time):
        self.time += delta_time
        """ for explosion in self.explosions:
            explosion.start_time = delta_time """

    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE:
            # Simulate an explosion at a random position
            x, y = arcade.rand_in_rect((15,15), self.size[0] - 15, self.size[1] - 15)
            new_explosion = Explosion((x, y), self.time)
            self.explosions.append(new_explosion)

    def on_mouse_press(self, x, y, button, modifiers):
        # Trigger an explosion at the mouse click coordinates
        new_explosion = Explosion((x, y), self.time)
        self.explosions.append(new_explosion)

# Create and run the game
def main():
    game = MyGame(800, 600, "Shader Explosion Example")
    arcade.run()

if __name__ == "__main__":
    main()
