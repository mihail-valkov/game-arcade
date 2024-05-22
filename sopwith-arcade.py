import arcade
import math
from arcade.experimental import Shadertoy


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Sopwith Game with Arcade"
PLANE_SPEED_MIN = 2
PLANE_SPEED_MAX = 10
PLANE_SIZE = 128
TILT_ANGLE = 1
TERRAIN_BUFFER = 400  # Additional buffer for smooth terrain rendering
AIR_RESISTANCE = 0.98  # Air resistance factor
MAX_EXPLOSIONS = 10

# Define the Explosion class to store position and start time
class Explosion:
    def __init__(self, position, camera_pos, start_time):
        self.position = position
        self.orig_position = position
        self.camera_pos = camera_pos
        self.start_time = start_time

class SopwithGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.SKY_BLUE)
        self.camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.gui_camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.plane_sprite = None
        self.plane_speed = 0
        self.plane_angle = 0
        self.terrain_points = []
        self.targets = arcade.SpriteList()
        self.bullets = arcade.SpriteList()
        self.bombs = arcade.SpriteList()
        self.plane_flipped = False
        self.up_pressed = False
        self.down_pressed = False
        self.left_pressed = False
        self.right_pressed = False
        self.prev_plane_x = 0.
        self.textbox_time = arcade.Text("Time: 0", 0, 0, arcade.color.BLACK, 14)
        self.textbox_score = arcade.Text("Score: 0", 20, SCREEN_HEIGHT - 20, arcade.color.YELLOW, 14)
        # List to store active explosions
        self.explosions = []
        # Initialize time
        self.time = 0.0
        self.setup()
        self.time = 0.
        self.sky_shape = None
        self.score = 0

        self.load_shader()

    def setup(self):
        self.plane_texture = arcade.load_texture("plane.png")
        self.plane_texture_flipped = arcade.load_texture("plane.png", flipped_vertically=True)
        self.plane_sprite = arcade.Sprite(scale=0.25)
        self.plane_sprite.texture = self.plane_texture
        self.SetSize()
        self.load_terrain()
        self.load_targets()
        self.plane_sprite.center_y = self.get_y_from_terrain(self.plane_sprite.center_x) + self.plane_sprite.height / 2
        self.setup_sounds()
        


    def SetSize(self):
        self.plane_sprite.width = 64
        self.plane_sprite.height = 32

    def setup_sounds(self):
        return
        self.plane_sound = arcade.load_sound("plane.wav")
        self.fire_sound = arcade.load_sound("fire.wav")
        self.bomb_sound = arcade.load_sound("bomb.wav")
        self.crash_sound = arcade.load_sound("crash.wav")
        arcade.play_sound(self.plane_sound, looping=True)

    def load_terrain(self):
        with open("terrain.txt") as f:
            for line in f:
                if line.startswith("#"):
                    continue
                x, y, color = map(int, line.split(","))
                self.terrain_points.append((x, y, color))
        self.terrain_texture = arcade.load_texture("terrain.png")

    def load_targets(self):
        target_images = ["target1.png", "target2.png", "target3.png", "target4.png", "target5.png"]
        with open("landscape.txt") as f:
            for line in f:
                if line.startswith("#"):
                    continue
                x, targetN = map(int, line.split(","))
                y = self.get_y_from_terrain(x)
                target_image = target_images[targetN % len(target_images)]
                target = arcade.Sprite(target_image, center_x=x, scale=0.4)
                target.bottom = y
                self.targets.append(target)

    def get_y_from_terrain(self, x):
        # Simple linear interpolation for now
        for i in range(len(self.terrain_points) - 1):
            x1, y1, _ = self.terrain_points[i]
            x2, y2, _ = self.terrain_points[i + 1]
            if x1 <= x <= x2:
                t = (x - x1) / (x2 - x1)
                return y1 + t * (y2 - y1)
        return 0  # Default to 0 if not found

    def on_draw(self):

        self.channel0.use()
        self.channel0.clear()
        #self.channel1.use()
        #self.channel1.clear()

        self.camera.use()
        arcade.start_render()
        self.draw_terrain()
        self.plane_sprite.draw()
        self.targets.draw()
        self.bullets.draw()
        self.bombs.draw()

        self.gui_camera.use()
        self.textbox_time.draw()
        self.textbox_score.draw()

        self.use()
        self.clear()

        self.renderShader()

    def renderShader(self):
        # Prepare data for the shader
        active_explosions = [exp for exp in self.explosions if self.time - exp.start_time <= 1.9]
        for exp in active_explosions:
            exp.position = (
                exp.orig_position[0] - self.camera.position[0],
                exp.orig_position[1] - self.camera.position[1])
            
            #+ (self.camera.position.y - exp.camera_pos.y)
            
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
        self.textbox_time.text = f"{positions_tuple[0]}"
        #self.textbox_time.update()
        self.shadertoy.program["explodeTimes"] = times_tuple
        self.shadertoy.program["numExplosions"] = num_explosions

        self.shadertoy.render(time=self.time)

    def load_shader(self):
        # Size of the window
        window_size = self.get_size()

        # Create the shader toy, passing in a path for the shader source
        shader_file_path = "multiExplosion.glsl"

        self.shadertoy = Shadertoy.create_from_file(window_size, shader_file_path)

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

    def draw_terrain(self):
        

        color_list = [
            (113, 255, 113),
            (123, 215, 120),
            (120, 255, 110),
            arcade.color.SEA_BLUE,
            arcade.color.DEEP_SKY_BLUE]  # Define your color list here

        start_x = self.camera.position[0] - TERRAIN_BUFFER
        end_x = self.camera.position[0] + SCREEN_WIDTH + TERRAIN_BUFFER

        if self.sky_shape is None:
            self.sky_shape = self.draw_textured_polygon(
            [
                (self.camera.position.x, 0),
                (self.camera.position.x, SCREEN_HEIGHT),
                (SCREEN_WIDTH + self.camera.position.x, SCREEN_HEIGHT),
                (SCREEN_WIDTH + self.camera.position.x, 0)
            ],
            [
                arcade.color.SKY_BLUE, 
                arcade.color.DEEP_SKY_BLUE,
                arcade.color.DEEP_SKY_BLUE, 
                arcade.color.SKY_BLUE,
            ])
        else:
            self.sky_shape.center_x = self.camera.position.x
            
        self.sky_shape.draw()

        visible_terrain = [point for point in self.terrain_points if start_x <= point[0] <= end_x]

        if visible_terrain:
            x0, y0, c0 = visible_terrain[0]
            for x1, y1, c1 in visible_terrain[1:]:
                vertices = [(x0, 0), (x0, y0), (x1, y1), (x1, 0)]
                shape = self.draw_textured_polygon(vertices, [arcade.color.DARK_GREEN, color_list[c0], color_list[c1], arcade.color.DARK_GREEN])
                shape.draw()
                x0, y0, c0 = x1, y1, c1

    def draw_textured_polygon(self, vertices, colors):
        vertex_list = arcade.create_rectangles_filled_with_colors(vertices, colors)
        shape = arcade.ShapeElementList()
        shape.append(vertex_list)
        return shape

        # Draw the texture over the polygon
        """ for i in range(len(vertices) - 1):
            x0, y0 = vertices[i]
            x1, y1 = vertices[i + 1]
            width = ((x1 - x0)**2 + (y1 - y0)**2)**0.5/2
            height = max(y0, y1)
            angle = 0#math.degrees(math.atan2(y1 - y0, x1 - x0))
            arcade.draw_texture_rectangle((x0 + x1) / 2, height / 2, width, height, self.terrain_texture, angle,) """
            #arcade.draw_scaled_texture_rectangle((x0 + x1) / 2, height / 2, self.terrain_texture, 1, angle)


    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self.up_pressed = True
        elif key == arcade.key.DOWN:
            self.down_pressed = True
        elif key == arcade.key.LEFT:
            self.left_pressed = True
            self.plane_speed = max(PLANE_SPEED_MIN, self.plane_speed - 1)
        elif key == arcade.key.RIGHT:
            self.right_pressed = True
            self.plane_speed = min(PLANE_SPEED_MAX, self.plane_speed + 1)
        elif key == arcade.key.PERIOD:
            self.plane_flipped = not self.plane_flipped
            self.plane_sprite.texture = self.plane_texture_flipped if self.plane_flipped else self.plane_texture
            self.SetSize()
        elif key == arcade.key.B:
            self.drop_bomb()
        elif key == arcade.key.SPACE:
            self.fire_bullet()

    def on_key_release(self, key, modifiers):
        if key == arcade.key.UP:
            self.up_pressed = False
        elif key == arcade.key.DOWN:
            self.down_pressed = False
        elif key == arcade.key.LEFT:
            self.left_pressed = False
        elif key == arcade.key.RIGHT:
            self.right_pressed = False

    def drop_bomb(self):
        bomb = arcade.Sprite("bomb.png", scale=0.3)
        bomb.center_x = self.plane_sprite.center_x
        bomb.center_y = self.plane_sprite.center_y
        bomb.change_x = self.plane_sprite.change_x
        bomb.change_y = self.plane_sprite.change_y
        bomb.angle = self.plane_sprite.angle
        if self.plane_flipped:
            bomb.angle -= 180
  
        self.bombs.append(bomb)
        arcade.play_sound(self.bomb_sound)

    def fire_bullet(self):
        bullet = arcade.SpriteSolidColor(5, 5, arcade.color.YELLOW)
        bullet.center_x = self.plane_sprite.center_x
        bullet.center_y = self.plane_sprite.center_y
        bullet.angle = self.plane_sprite.angle
        bullet.change_x = math.cos(math.radians(bullet.angle)) * 10
        bullet.change_y = math.sin(math.radians(bullet.angle)) * 10
        self.bullets.append(bullet)
        arcade.play_sound(self.fire_sound)

    def update(self, delta_time):

        self.time += delta_time

        if self.up_pressed:
            self.plane_angle += TILT_ANGLE
        if self.down_pressed:
            self.plane_angle -= TILT_ANGLE
        if self.left_pressed:
            pass
        if self.right_pressed:
            pass

        self.textbox_score.text = f"Score: {self.score}"

        self.plane_sprite.angle = self.plane_angle
        self.plane_sprite.change_x = math.cos(math.radians(self.plane_angle)) * self.plane_speed
        self.plane_sprite.change_y = math.sin(math.radians(self.plane_angle)) * self.plane_speed
        self.plane_sprite.update()
        self.bullets.update()
        self.update_bombs(delta_time)
        self.check_collisions()
        self.check_crash()
        self.scroll_viewport()

    def update_bombs(self, delta_time):
        gravity = -9.8  # Gravity constant
        for bomb in self.bombs:
            bomb.change_y += gravity * delta_time
            bomb.change_x *= AIR_RESISTANCE  # Apply air resistance to the x velocity
            bomb.update()

    def check_collisions(self):
        for bullet in self.bullets:
            hit_list = arcade.check_for_collision_with_list(bullet, self.targets)
            if hit_list:
                bullet.remove_from_sprite_lists()
                for target in hit_list:
                    self.addExplosion(target)
                    target.remove_from_sprite_lists()
                    self.score += 10
        for bomb in self.bombs:
            hit_list = arcade.check_for_collision_with_list(bomb, self.targets)
            if hit_list:
                #self.addExplosion(bomb)
                bomb.remove_from_sprite_lists()
                for target in hit_list:
                    self.addExplosion(target)
                    target.remove_from_sprite_lists()
                    self.score += 10
            if bomb.bottom <= self.get_y_from_terrain(bomb.center_x):
                self.addExplosion(bomb)
                bomb.remove_from_sprite_lists()

    def addExplosion(self, sprite: arcade.Sprite):
        if len(self.explosions) == MAX_EXPLOSIONS:
            self.explosions.pop(0)
        new_explosion = Explosion(
            sprite.position, 
            self.camera.position,
            self.time)
        self.explosions.append(new_explosion)

    def check_crash(self):
        if self.plane_speed > 0:
            if self.plane_sprite.bottom + 2 < self.get_y_from_terrain(self.plane_sprite.center_x):
                self.plane_speed = 0
                self.score -= 100
                self.addExplosion(self.plane_sprite)

    def scroll_viewport(self):
        # Calculate the relative position of the plane on the screen
        plane_screen_x = self.plane_sprite.center_x - self.camera.position[0]

        if self.prev_plane_x - self.plane_sprite.center_x < -1:  # Moving forward
            camera_pos_x = self.plane_sprite.center_x - SCREEN_WIDTH * 0.2
            self.camera.move_to((camera_pos_x, self.camera.position[1]), 0.1)
        elif self.prev_plane_x - self.plane_sprite.center_x > 1:  # Moving backward
            camera_pos_x = self.plane_sprite.center_x - SCREEN_WIDTH * 0.8
            self.camera.move_to((camera_pos_x, self.camera.position[1]), 0.1)
        else:
            camera_pos_x = self.plane_sprite.center_x - SCREEN_WIDTH // 2
            #self.camera.move_to((camera_pos_x, self.camera.position[1]), 0.1)

        # Update the previous plane position
        self.prev_plane_x = self.plane_sprite.center_x

    """ def scroll_viewport(self):
        # Calculate the relative position of the plane on the screen
        plane_screen_x = self.plane_sprite.center_x - self.camera.position[0]


        if self.prev_plane_x - self.plane_sprite.center_x < -1:  # Moving forward
            self.textbox_time.text = f"Moving forward {self.prev_plane_x - self.plane_sprite.center_x}"
            
            if plane_screen_x > SCREEN_WIDTH * 0.6:
                camera_pos_x = self.plane_sprite.center_x + 150 
                self.camera.move_to((camera_pos_x, self.camera.position[1]), 0.03)
        elif self.prev_plane_x - self.plane_sprite.center_x > 1:  # Moving backward
            self.textbox_time.text = f"Moving back {self.prev_plane_x - self.plane_sprite.center_x}"
            
            #self.textbox_time.update()
            if plane_screen_x < SCREEN_WIDTH * 0.4:
                camera_pos_x = self.plane_sprite.center_x - SCREEN_WIDTH - 150
                self.camera.move_to((camera_pos_x, self.camera.position[1]), 0.03)

        # Update the previous plane position
        self.prev_plane_x = self.plane_sprite.center_x """
        

def main():
    window = SopwithGame()
    arcade.run()

if __name__ == "__main__":
    main()
