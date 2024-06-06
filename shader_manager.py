import arcade
from arcade.experimental import Shadertoy
from constants import *

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