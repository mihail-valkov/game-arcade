import arcade
import math
import time
from arcade.experimental import Shadertoy

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Sopwith Game with Arcade"
PLANE_SPEED_MIN = 2.5
PLANE_SPEED_MAX = 8
PLANE_SCALE = 0.27
TARGET_SCALE = 0.45
TILT_ANGLE = 2
TERRAIN_BUFFER = 400  # Additional buffer for smooth terrain rendering
AIR_RESISTANCE = 0.985  # Air resistance factor
MAX_EXPLOSIONS = 10
BULLET_SPEED = 12
BOMB_DROP_INTERVAL = 0.5  # Time interval between bomb drops
EXPLOSION_DURATION = 1.5  # Duration of the explosion effect
BULLET_FADE_TIME = 1.5  # Duration for which a bullet stays active
TARGET_SHOOT_INTERVAL = 2.0  # Time interval between target shots

BACKGROUND_LAYER_1_SPEED = 0.7  # Speed for the first background layer
BACKGROUND_LAYER_2_SPEED = 0.5  # Speed for the second background layer

# Determine the relative drop point in the plane's local coordinate system
BOMB_DROP_OFFSET_X = -10  # offset from the plane's center in the x-direction
BOMB_DROP_OFFSET_Y = -10  # offset from the plane's center in the y-direction
BOMB_SCALE = 0.3

DEBUG_DRAW = False
DRAW_FPS = True
DEBUG_COLOR = (255, 0, 0, 64)


class ParalaxBackgroundLayer:
    def __init__(self, image1, image2, scroll_speed):
        self.background1 = image1
        self.background2 = image2
        self.scroll_speed = scroll_speed
        self.background1_start = 0
        self.background2_start = image1.width

    def draw_background(self, camera: arcade.Camera, y=0):
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
        if (
            self.background1_start + distance - camera.position.x > -self.background1.width
            and self.background1_start + distance - camera.position.x < SCREEN_WIDTH
        ):
            arcade.draw_lrwh_rectangle_textured(
                self.background1_start + distance,
                y,
                self.background1.width,
                self.background1.height,
                self.background1,
            )
        if (
            self.background2_start + distance - camera.position.x > -self.background2.width
            and self.background2_start + distance - camera.position.x < SCREEN_WIDTH
        ):
            arcade.draw_lrwh_rectangle_textured(
                self.background2_start + distance,
                y,
                self.background2.width,
                self.background1.height,
                self.background2,
            )


# Define the Explosion class to store position and start time
class Explosion:
    def __init__(self, position, size, camera_pos, start_time):
        self.position = position
        self.size = size
        self.orig_position = position
        self.camera_pos = camera_pos
        self.start_time = start_time
        self.sprite = None

    # method kill to remove the sprite from the sprite list
    def kill(self):
        if self.sprite is not None:
            self.sprite.kill()
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
        delayed_explosions = [
            exp for exp in explosions if time - exp.start_time < 0
        ]
        active_explosions = [
            exp for exp in explosions if 0 <= time - exp.start_time <= EXPLOSION_DURATION
        ]

        for exp in active_explosions:
            exp.position = (
                exp.orig_position[0] - camera_position[0],
                exp.orig_position[1] - camera_position[1],
            )

        positions = [exp.position for exp in active_explosions]
        sizes = [exp.size for exp in active_explosions]
        times = [exp.start_time for exp in active_explosions]

        positions_flat = [
            coord for pos in positions for coord in pos
        ] + [0.0, 0.0] * (10 - len(positions))
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
        self.target_bullets = arcade.SpriteList()
        self.bullets = arcade.SpriteList()
        self.bombs = arcade.SpriteList()
        self.prev_bomb_time = 0
        self.plane_flipped = False
        self.up_pressed = False
        self.down_pressed = False
        self.left_pressed = False
        self.right_pressed = False
        self.prev_plane_x = 0.0
        self.textbox_debug = arcade.Text("Time: 0", 0, 0, arcade.color.LIGHT_PINK, 14)
        self.textbox_score = arcade.Text(
            "Score: 0", 20, SCREEN_HEIGHT - 20, arcade.color.YELLOW, 14
        )
        self.explosions = []
        self.explosion_sprites = None
        self.time = 0.0
        self.sky_shape = None
        self.score = 0
        self.shader_manager = ShaderManager(self.get_size())
        self.setup()
        self.start_time = time.time()
        self.frame_count = 0
        self.fps = 0
        self.plane_crashed = False
        self.curr_plane_explosion = None
        self.plane_size = (0, 0)
        self.flipped_hit_box_points = []

    def setup(self):
        self.explosion_sprites = arcade.SpriteList()
        self.load_terrain()
        self.setup_plane()
        self.load_targets()
        self.setup_sounds()

    def setup_plane(self):
        self.plane_texture = arcade.load_texture("plane.png")
        self.plane_texture_flipped = arcade.load_texture(
            "plane.png", flipped_vertically=True
        )

        self.plane_sprite = arcade.Sprite(texture=self.plane_texture, scale=PLANE_SCALE)

        self.set_plane_texture()

        self.plane_sprite.center_y = (
            self.get_y_from_terrain(self.plane_sprite.center_x)
            + self.plane_sprite.height / 2
            + 5
        )

    def set_plane_texture(self):
        self.plane_sprite.texture = (
            self.plane_texture_flipped if self.plane_flipped else self.plane_texture
        )

        hit_box_points = [
            (-108, 3),
            (-115, 15),
            (-108, 38),
            (-95, 42),
            (-78, 35),
            (-60, 18),
            (35, 28),
            (42, 48),
            (90, 50),
            (90, 30),
            (105, 31),
            (105, 53),
            (110, 53),
            (110, -45),
            (100, -15),
            (90, -15),
            (90, -45),
            (73, -56),
            (58, -45),
            (50, -15),
        ]

        if self.plane_flipped:
            if len(self.flipped_hit_box_points) == 0:
                self.flipped_hit_box_points = [(x, -y) for x, y in hit_box_points]
            self.plane_sprite.set_hit_box(self.flipped_hit_box_points)
        else:
            self.plane_sprite.set_hit_box(hit_box_points)

    def setup_sounds(self):
        return
        self.plane_sound = arcade.load_sound("plane.wav")
        self.fire_sound = arcade.load_sound("fire.wav")
        self.bomb_sound = arcade.load_sound("bomb.wav")
        self.crash_sound = arcade.load_sound("crash.wav")
        arcade.play_sound(self.plane_sound, looping=True)

    def draw_background_layers(self):
        self.paralaxBackground1.draw_background(
            self.camera, SCREEN_HEIGHT - self.background_layer_2.height
        )
        self.paralaxBackground2.draw_background(self.camera, 30)

    def load_terrain(self):
        self.background_layer_1 = arcade.load_texture("background_layer_1.png")
        self.background_layer_1_2 = arcade.load_texture("background_layer_1_2.png")
        self.background_layer_2 = arcade.load_texture("background_layer_2.png")
        self.background_layer_2_2 = arcade.load_texture("background_layer_2_2.png")

        self.paralaxBackground1 = ParalaxBackgroundLayer(
            self.background_layer_1, self.background_layer_1_2, BACKGROUND_LAYER_1_SPEED
        )
        self.paralaxBackground2 = ParalaxBackgroundLayer(
            self.background_layer_2, self.background_layer_2_2, BACKGROUND_LAYER_2_SPEED
        )

        with open("terrain.txt") as f:
            for line in f:
                if line.startswith("#"):
                    continue
                x, y, color = map(int, line.split(","))
                self.terrain_points.append((x, y, color))

    def load_targets(self):
        target_images = [
            "target1.png",
            "target2.png",
            "target3.png",
            "target4.png",
            "target5.png",
        ]
        with open("landscape.txt") as f:
            for line in f:
                if line.startswith("#"):
                    continue
                x, targetN = map(int, line.split(","))
                y = self.get_y_from_terrain(x)
                target_image = target_images[targetN % len(target_images)]
                target = arcade.Sprite(target_image, center_x=x, scale=TARGET_SCALE)
                target.bottom = y
                target.shoot_interval = TARGET_SHOOT_INTERVAL * (targetN + 1) / len(
                    target_images
                )  # Different intervals for different targets
                target.last_shot_time = 0
                self.targets.append(target)

    def get_y_from_terrain(self, x):
        for i in range(len(self.terrain_points) - 1):
            x1, y1, _ = self.terrain_points[i]
            x2, y2, _ = self.terrain_points[i + 1]
            if x1 <= x <= x2:
                t = (x - x1) / (x2 - x1)
                return y1 + t * (y2 - y1)
        return 0  # Default to 0 if not found

    def on_draw(self):
        self.shader_manager.channel0.use()
        self.shader_manager.channel0.clear()
        self.camera.use()
        arcade.start_render()
        self.draw_sky()
        self.draw_background_layers()
        self.draw_terrain()

        self.plane_sprite.draw()
        if DEBUG_DRAW:
            self.plane_sprite.draw_hit_box(DEBUG_COLOR)

        self.targets.draw()
        self.bullets.draw()
        self.target_bullets.draw()
        self.bombs.draw()
        if DEBUG_DRAW:
            self.bombs.draw_hit_boxes(DEBUG_COLOR)

        if DEBUG_DRAW:
            self.draw_explosion_zones()  # Draw the explosion kill zones

        self.gui_camera.use()
        if DEBUG_DRAW:
            self.textbox_debug.draw()
        self.textbox_score.draw()

        self.use()
        self.clear()

        self.shader_manager.render(self.time, self.explosions, self.camera.position)
        if DRAW_FPS:
            self.draw_fps()

        if DEBUG_DRAW:
            angle = math.radians(self.plane_angle)
            bomb_x = self.plane_sprite.center_x + BOMB_DROP_OFFSET_X * math.cos(
                angle
            ) - BOMB_DROP_OFFSET_Y * math.sin(angle)
            bomb_y = self.plane_sprite.center_y + BOMB_DROP_OFFSET_X * math.sin(
                angle
            ) + BOMB_DROP_OFFSET_Y * math.cos(angle)
            arcade.draw_circle_filled(
                bomb_x - self.camera.position.x,
                bomb_y - self.camera.position.y,
                2,
                DEBUG_COLOR,
            )

    def draw_explosion_zones(self):
        for explosion in self.explosions:
            if (
                self.time >= explosion.start_time
                and self.time <= explosion.start_time + EXPLOSION_DURATION
            ):
                if explosion.sprite is not None:
                    explosion.sprite.draw()
                    if DEBUG_DRAW:
                        explosion.sprite.draw_hit_box(DEBUG_COLOR)

    def draw_fps(self):
        current_time = time.time()
        self.frame_count += 1
        if current_time - self.start_time > 1:
            self.fps = self.frame_count / (current_time - self.start_time)
            self.start_time = current_time
            self.frame_count = 0
        arcade.draw_text(
            f"FPS: {self.fps:.2f}",
            SCREEN_WIDTH - 100,
            10,
            arcade.color.GREEN_YELLOW,
            12,
        )

    def draw_terrain(self):
        color_list = [
            (113, 255, 113),
            (123, 215, 120),
            (120, 255, 110),
            arcade.color.SEA_BLUE,
            arcade.color.DEEP_SKY_BLUE,
        ]

        start_x = self.camera.position[0] - TERRAIN_BUFFER
        end_x = self.camera.position[0] + SCREEN_WIDTH + TERRAIN_BUFFER

        visible_terrain = [
            point for point in self.terrain_points if start_x <= point[0] <= end_x
        ]

        if visible_terrain:
            x0, y0, c0 = visible_terrain[0]
            for x1, y1, c1 in visible_terrain[1:]:
                vertices = [(x0, 0), (x0, y0), (x1, y1), (x1, 0)]
                shape = self.draw_textured_polygon(
                    vertices,
                    [
                        arcade.color.DARK_GREEN,
                        color_list[c0],
                        color_list[c1],
                        arcade.color.DARK_GREEN,
                    ],
                )
                shape.draw()
                x0, y0, c0 = x1, y1, c1

    def draw_sky(self):
        if self.sky_shape is None:
            self.sky_shape = self.draw_textured_polygon(
                [(0, 0), (0, SCREEN_HEIGHT), (SCREEN_WIDTH, SCREEN_HEIGHT), (SCREEN_WIDTH, 0)],
                [
                    arcade.color.SKY_BLUE,
                    arcade.color.DEEP_SKY_BLUE,
                    arcade.color.DEEP_SKY_BLUE,
                    arcade.color.SKY_BLUE,
                ],
            )

        self.sky_shape.center_x = self.camera.position.x
        self.sky_shape.draw()

    def draw_textured_polygon(self, vertices, colors):
        vertex_list = arcade.create_rectangles_filled_with_colors(vertices, colors)
        shape = arcade.ShapeElementList()
        shape.append(vertex_list)
        return shape

    def on_key_press(self, key, modifiers):
        if self.plane_crashed:
            return  # Do nothing if the plane has crashed

        if key == arcade.key.UP:
            self.up_pressed = True
        elif key == arcade.key.DOWN:
            self.down_pressed = True
        elif key == arcade.key.LEFT:
            self.left_pressed = True
            self.plane_speed = max(PLANE_SPEED_MIN, self.plane_speed - 1)
        elif key == arcade.key.RIGHT:
            self.right_pressed = True
            if self.plane_speed == 0:
                self.plane_speed = PLANE_SPEED_MIN
            else:
                self.plane_speed = min(PLANE_SPEED_MAX, self.plane_speed + 1)
        elif key == arcade.key.PERIOD:
            self.plane_flipped = not self.plane_flipped
            self.set_plane_texture()
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
        # only if interval has passed
        if self.time - self.prev_bomb_time < BOMB_DROP_INTERVAL:
            return
        bomb = arcade.Sprite("bomb.png", BOMB_SCALE)

        # Rotate the drop point to the plane's angle to get the world coordinates
        angle = math.radians(self.plane_angle)
        bomb_x = self.plane_sprite.center_x + BOMB_DROP_OFFSET_X * math.cos(
            angle
        ) - BOMB_DROP_OFFSET_Y * math.sin(angle)
        bomb_y = self.plane_sprite.center_y + BOMB_DROP_OFFSET_X * math.sin(
            angle
        ) + BOMB_DROP_OFFSET_Y * math.cos(angle)

        bomb.center_x = bomb_x
        bomb.center_y = bomb_y

        bomb.change_x = self.plane_sprite.change_x * 1.1
        bomb.change_y = self.plane_sprite.change_y * 0.8

        bomb.angle = self.plane_sprite.angle + 80

        if self.plane_flipped:
            bomb.angle -= 180

        self.bombs.append(bomb)
        self.prev_bomb_time = self.time
        arcade.play_sound(self.bomb_sound)

    def fire_bullet(self):
        bullet = arcade.SpriteSolidColor(5, 5, arcade.color.YELLOW)
        bullet.center_x = self.plane_sprite.center_x
        bullet.center_y = self.plane_sprite.center_y
        bullet.angle = self.plane_sprite.angle
        bullet.change_x = math.cos(math.radians(bullet.angle)) * BULLET_SPEED
        bullet.change_y = math.sin(math.radians(bullet.angle)) * BULLET_SPEED
        bullet.start_time = self.time
        self.bullets.append(bullet)
        arcade.play_sound(self.fire_sound)

    def update(self, delta_time):
        self.time += delta_time

        if self.up_pressed:
            self.plane_angle += TILT_ANGLE
        if self.down_pressed:
            self.plane_angle -= TILT_ANGLE

        self.textbox_score.text = f"Score: {self.score}"

        if not self.plane_crashed:
            self.plane_sprite.angle = self.plane_angle
            self.plane_sprite.change_x = math.cos(math.radians(self.plane_angle)) * self.plane_speed
            self.plane_sprite.change_y = math.sin(math.radians(self.plane_angle)) * self.plane_speed

        # Prevent the plane from flying outside the top of the screen
        if self.plane_sprite.top > SCREEN_HEIGHT:
            self.plane_sprite.top = SCREEN_HEIGHT

        # Check if self.curr_plane_explosion has ended and reset it
        if self.curr_plane_explosion is not None and self.time - self.curr_plane_explosion.start_time > EXPLOSION_DURATION:
            self.curr_plane_explosion = None

        self.plane_sprite.update()
        self.bullets.update()
        self.update_bombs(delta_time)
        self.update_target_bullets(delta_time)
        self.check_collisions()
        self.check_crash(delta_time)
        self.scroll_viewport()

        for explosion in self.explosions:
            if self.time > explosion.start_time + EXPLOSION_DURATION:
                explosion.kill()

    def update_bombs(self, delta_time):
        gravity = -5.0  # Gravity constant
        for bomb in self.bombs:
            bomb.change_y += gravity * delta_time
            bomb.change_x *= AIR_RESISTANCE  # Apply air resistance to the x velocity
            # make bomb angle to face the ground
            # convert bomb angle to 0-360, even if it is negative and then decrease it gradually to 0
            bomb.angle = (bomb.angle + 360) % 360
            if bomb.angle > 180:
                bomb.angle = min(360, bomb.angle + 45.0 * delta_time)
            else:
                bomb.angle = max(0.0, bomb.angle - 45.0 * delta_time)

            bomb.update()

    def update_target_bullets(self, delta_time):
        gravity = -2.0  # Gravity constant for target bullets
        for bullet in self.target_bullets:
            bullet.change_y += gravity * delta_time
            bullet.change_x *= AIR_RESISTANCE  # Apply air resistance to the x velocity
            bullet.update()

            if bullet.top < 0 or bullet.bottom > SCREEN_HEIGHT:
                bullet.remove_from_sprite_lists()

    def check_collisions(self):
        for bullet in self.bullets:
            if (
                bullet.bottom <= self.get_y_from_terrain(bullet.center_x)
                or bullet.top < 0
                or bullet.right - self.camera.position[0] < 0
                or bullet.left - self.camera.position[0] > SCREEN_WIDTH
                or self.time - bullet.start_time > BULLET_FADE_TIME  # Remove bullets after a certain time
            ):
                bullet.remove_from_sprite_lists()
            else:
                hit_list = arcade.check_for_collision_with_list(bullet, self.targets)
                if hit_list:
                    bullet.remove_from_sprite_lists()
                    for target in hit_list:
                        self.add_explosion(target, 0.02)
                        target.remove_from_sprite_lists()
                        self.score += 10
        for bomb in self.bombs:
            hit_list = arcade.check_for_collision_with_list(bomb, self.targets)
            if hit_list:
                self.add_explosion(bomb)
                bomb.remove_from_sprite_lists()
                for target in hit_list:
                    self.add_explosion(target, 0.05)
                    target.remove_from_sprite_lists()
                    self.score += 10
            # Check for collision between the plane and the bomb
            if self.time - self.prev_bomb_time > 0.1 and arcade.check_for_collision(bomb, self.plane_sprite):
                self.plane_crashed = True
                self.plane_speed = 0
                self.score -= 100
                self.curr_plane_explosion = self.add_explosion(self.plane_sprite, 0.05)
                self.add_explosion(bomb)
                bomb.remove_from_sprite_lists()

            if bomb.bottom <= self.get_y_from_terrain(bomb.center_x):
                self.add_explosion(bomb)
                bomb.remove_from_sprite_lists()

        # Check for collision between the plane and target bullets
        for bullet in self.target_bullets:
            if arcade.check_for_collision(bullet, self.plane_sprite):
                self.plane_crashed = True
                self.plane_speed = 0
                self.score -= 100
                self.curr_plane_explosion = self.add_explosion(self.plane_sprite, 0.05)
                self.add_explosion(bullet)
                bullet.remove_from_sprite_lists()

    def add_explosion(self, sprite: arcade.Sprite, delay: float = 0.0):
        explosion_size = (sprite.width + sprite.height) / 80
        if len(self.explosions) == MAX_EXPLOSIONS:
            self.explosions.pop(0)
        new_explosion = Explosion(
            sprite.position,
            explosion_size,
            self.camera.position,
            self.time + delay,
        )
        self.explosions.append(new_explosion)
        return new_explosion

    def check_crash(self, delta_time):
        if not self.plane_crashed:
            if self.plane_sprite.bottom + 2 < self.get_y_from_terrain(self.plane_sprite.center_x):
                self.plane_crashed = True
                self.plane_speed = 0
                self.score -= 100
                self.curr_plane_explosion = self.add_explosion(self.plane_sprite)

        # Check collision with targets
        if not self.plane_crashed:
            hit_list = arcade.check_for_collision_with_list(self.plane_sprite, self.targets)
            if hit_list:
                self.plane_crashed = True
                self.plane_speed = 0
                self.score -= 100
                for target in hit_list:
                    self.add_explosion(target, 0.02)
                    target.remove_from_sprite_lists()

        # Check if the plane is near any active explosions
        if not self.plane_crashed:
            for explosion in self.explosions:
                # check if the explosion is not the same as the one that killed the plane and continue
                if self.curr_plane_explosion is not None and explosion.orig_position == self.curr_plane_explosion.orig_position:
                    continue

                if self.is_explosion_active(explosion):
                    # distance = math.hypot(self.plane_sprite.center_x - explosion.orig_position[0], self.plane_sprite.center_y - explosion.orig_position[1])
                    kill_radius = self.get_kill_radius(explosion)
                    # self.textbox_debug.text = f"Distance: {distance:.2f}, Kill radius: {(200 * explosion.size * (abs(explosion.start_time - self.time) / EXPLOSION_DURATION)):.2f}"
                    explosion_sprite = explosion.sprite
                    kill_radius = max(3, int(kill_radius))
                    if explosion_sprite is None:
                        explosion_sprite = arcade.SpriteCircle(kill_radius, (255, 0, 0, 32))
                        explosion_sprite.center_x = explosion.orig_position[0]
                        explosion_sprite.center_y = explosion.orig_position[1]
                        explosion.sprite = explosion_sprite
                        # self.explosion_sprites.append(explosion_sprite)

                    explosion_sprite.texture = arcade.make_circle_texture(
                        kill_radius, (255, 0, 0, 32)
                    )
                    explosion_sprite.set_hit_box(explosion_sprite.texture.hit_box_points)
                    explosion_sprite.update()

                    if arcade.are_polygons_intersecting(
                        self.plane_sprite.get_adjusted_hit_box(),
                        explosion_sprite.get_adjusted_hit_box(),
                    ):
                        # if arcade.check_for_collision(self.plane_sprite, explosion_sprite):
                        self.plane_crashed = True
                        self.plane_speed = 0
                        self.score -= 100
                        self.curr_plane_explosion = self.add_explosion(self.plane_sprite, 0.1)
                        break

        # If the plane has crashed, apply gravity and air resistance
        if self.plane_crashed:
            self.plane_sprite.change_y -= 2.0 * delta_time  # Gravity
            # change also the plane angle to face the ground
            self.plane_sprite.angle = min(160, self.plane_sprite.angle - 25.0 * delta_time)
            self.plane_sprite.change_x *= AIR_RESISTANCE
            self.plane_sprite.update()
            # if the plane hits the ground then stop
            if self.plane_sprite.bottom <= self.get_y_from_terrain(self.plane_sprite.center_x):
                # set plane to initial position as in setup_plane
                self.plane_sprite.change_x = 0
                self.plane_sprite.change_y = 0
                self.plane_sprite.angle = 0
                self.plane_sprite.center_y = (
                    15 + self.get_y_from_terrain(self.plane_sprite.center_x) + self.plane_sprite.height / 2
                )
                self.plane_crashed = False

    def is_explosion_active(self, explosion):
        return self.time >= explosion.start_time and self.time <= explosion.start_time + EXPLOSION_DURATION

    def get_kill_radius(self, explosion):
        elapsed_time = self.time - explosion.start_time
        normalized_time = elapsed_time / EXPLOSION_DURATION
        eased_time = 1 - (1 - normalized_time) ** 8  # easing
        return 140 * explosion.size * eased_time

    def scroll_viewport(self):
        # Calculate the relative position of the plane on the screen

        """ if self.prev_plane_x - self.plane_sprite.center_x < -1:  # Moving forward
            camera_pos_x = self.plane_sprite.center_x - SCREEN_WIDTH * 0.3
            self.camera.move_to((camera_pos_x, self.camera.position[1]), 0.5)
        elif self.prev_plane_x - self.plane_sprite.center_x > 1:  # Moving backward
            camera_pos_x = self.plane_sprite.center_x - SCREEN_WIDTH * 0.7
            self.camera.move_to((camera_pos_x, self.camera.position[1]), 0.5)
        else:
            camera_pos_x = self.plane_sprite.center_x - SCREEN_WIDTH // 2 
            self.camera.move_to((camera_pos_x, self.camera.position[1]), 0.5) """

        camera_pos_x = self.plane_sprite.center_x - SCREEN_WIDTH // 2
        self.camera.move_to((camera_pos_x, self.camera.position[1]), 0.5)

        # Update the previous plane position
        self.prev_plane_x = self.plane_sprite.center_x


def main():
    window = SopwithGame()
    arcade.run()


if __name__ == "__main__":
    main()
