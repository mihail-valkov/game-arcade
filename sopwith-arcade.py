import arcade
import math
import time
from constants import *
from parallax_background_layer import ParallaxBackgroundLayer
from shader_manager import ShaderManager
from plane import Plane
from bullet import Bullet
from explosion import *

class SopwithGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.SKY_BLUE)
        self.camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.gui_camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.plane = Plane()
        self.terrain_points = []
        self.targets = arcade.SpriteList()
        self.bullets = arcade.SpriteList()
        self.bombs = arcade.SpriteList()
        self.target_bullets = arcade.SpriteList()
        self.prev_bomb_time = 0
        self.up_pressed = False
        self.down_pressed = False
        self.left_pressed = False
        self.right_pressed = False
        self.prev_plane_x = 0
        self.textbox_debug = arcade.Text("Time: 0", 0, 0, arcade.color.LIGHT_PINK, 14)
        self.textbox_score = arcade.Text("Score: 0", 20, SCREEN_HEIGHT - 20, arcade.color.YELLOW, 14)
        self.textbox_health = arcade.Text(f"Health: {MAX_HEALTH}", 680, SCREEN_HEIGHT - 20, arcade.color.GREEN, 14)
        self.explosions = []
        self.reset_timer = 0
        self.explosion_sprites = None
        self.time = 0.0
        self.sky_shape = None
        self.score = 0
        self.shader_manager = ShaderManager(self.get_size())
        self.debug_sprites = arcade.SpriteList()
        self.setup()
        self.start_time = time.time()
        self.frame_count = 0
        self.fps = 0
        self.plane_crashed = False
        self.curr_plane_explosion = None
        self.flipped_hit_box_points = []

    def setup(self):
        self.explosion_sprites = arcade.SpriteList()
        self.load_terrain()
        self.setup_plane()
        self.load_targets()
        self.setup_sounds()

    def setup_plane(self):
        self.plane.health = MAX_HEALTH
        self.plane.center_y = self.get_y_from_terrain(self.plane.center_x) + self.plane.height / 2 + 5

    def setup_sounds(self):
        return
        self.plane_sound = arcade.load_sound("plane.wav")
        self.fire_sound = arcade.load_sound("fire.wav")
        self.bomb_sound = arcade.load_sound("bomb.wav")
        self.crash_sound = arcade.load_sound("crash.wav")
        arcade.play_sound(self.plane_sound, looping=True)

    def draw_background_layers(self):
        self.parallaxBackground1.draw_background(self.camera, SCREEN_HEIGHT - self.background_layer_2.height)
        self.parallaxBackground2.draw_background(self.camera, 30)

    def load_terrain(self):
        self.background_layer_1 = arcade.load_texture("background_layer_1.png")
        self.background_layer_1_2 = arcade.load_texture("background_layer_1_2.png")
        self.background_layer_2 = arcade.load_texture("background_layer_2.png")
        self.background_layer_2_2 = arcade.load_texture("background_layer_2_2.png")

        self.parallaxBackground1 = ParallaxBackgroundLayer(self.background_layer_1, self.background_layer_1_2, BACKGROUND_LAYER_1_SPEED)
        self.parallaxBackground2 = ParallaxBackgroundLayer(self.background_layer_2, self.background_layer_2_2, BACKGROUND_LAYER_2_SPEED)

        with open("terrain.txt") as f:
            for line in f:
                if line.startswith("#"):
                    continue
                x, y, color = map(int, line.split(","))
                self.terrain_points.append((x, y, color))

    def load_targets(self):
        target_images = ["target1.png", "target2.png", "target3.png", "target4.png", "target5.png"]
        with open("landscape.txt") as f:
            for line in f:
                if line.startswith("#"):
                    continue
                x, targetN = map(int, line.split(","))
                y = self.get_y_from_terrain(x)
                target_image = target_images[targetN % len(target_images)]
                target = arcade.Sprite(target_image, center_x=x, scale=TARGET_SCALE)
                target.bottom = y
                target.shoot_interval = 2.0
                target.last_shot_time = 0
                self.targets.append(target)

    def get_y_from_terrain(self, x):
        for i in range(len(self.terrain_points) - 1):
            x1, y1, _ = self.terrain_points[i]
            x2, y2, _ = self.terrain_points[i + 1]
            if x1 <= x <= x2:
                t = (x - x1) / (x2 - x1)
                return y1 + t * (y2 - y1)
        return 0

    def on_draw(self):
        self.shader_manager.channel0.use()
        self.shader_manager.channel0.clear()
        self.camera.use()
        arcade.start_render()
        self.draw_sky()
        self.draw_background_layers()
        self.draw_terrain()

        self.plane.draw()
        if DEBUG_DRAW:
            self.plane.draw_hit_box(DEBUG_COLOR)

        self.targets.draw()
        self.bullets.draw()
        self.bombs.draw()
        self.target_bullets.draw()
        if DEBUG_DRAW:
            self.bombs.draw_hit_boxes(DEBUG_COLOR)

        if DEBUG_DRAW:
            self.draw_explosion_zones()
            self.debug_sprites.draw()

        self.gui_camera.use()
        if DEBUG_DRAW:
            self.textbox_debug.draw()
        self.textbox_score.draw()
        self.textbox_health.draw()

        self.use()
        self.clear()

        self.shader_manager.render(self.time, self.explosions, self.camera.position)
        if DRAW_FPS:
            self.draw_fps()

        if DEBUG_DRAW:
            angle = math.radians(self.plane.angle)
            bomb_x = self.plane.center_x + BOMB_DROP_OFFSET_X * math.cos(angle) - BOMB_DROP_OFFSET_Y * math.sin(angle)
            bomb_y = self.plane_sprite.center_y + BOMB_DROP_OFFSET_X * math.sin(angle) + BOMB_DROP_OFFSET_Y * math.cos(angle)
            arcade.draw_circle_filled(bomb_x - self.camera.position.x, bomb_y - self.camera.position.y, 2, DEBUG_COLOR)

    def draw_explosion_zones(self):
        for explosion in self.explosions:
            if self.time >= explosion.start_time and self.time <= explosion.start_time + EXPLOSION_DURATION:
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
        arcade.draw_text(f"FPS: {self.fps:.2f}", SCREEN_WIDTH - 100, 10, arcade.color.GREEN_YELLOW, 12)

    def draw_terrain(self):
        color_list = [
            (113, 255, 113),
            (123, 215, 120),
            (120, 255, 110),
            arcade.color.SEA_BLUE,
            arcade.color.DEEP_SKY_BLUE
        ]

        start_x = self.camera.position[0] - TERRAIN_BUFFER
        end_x = self.camera.position[0] + SCREEN_WIDTH + TERRAIN_BUFFER

        visible_terrain = [point for point in self.terrain_points if start_x <= point[0] <= end_x]

        if visible_terrain:
            x0, y0, c0 = visible_terrain[0]
            for x1, y1, c1 in visible_terrain[1:]:
                vertices = [(x0, 0), (x0, y0), (x1, y1), (x1, 0)]
                shape = self.draw_textured_polygon(vertices, [arcade.color.DARK_GREEN, color_list[c0], color_list[c1], arcade.color.DARK_GREEN])
                shape.draw()
                x0, y0, c0 = x1, y1, c1

    def draw_sky(self):
        if self.sky_shape is None:
            self.sky_shape = self.draw_textured_polygon([
                (0, 0),
                (0, SCREEN_HEIGHT),
                (SCREEN_WIDTH, SCREEN_HEIGHT),
                (SCREEN_WIDTH, 0)],[
                arcade.color.SKY_BLUE,
                arcade.color.DEEP_SKY_BLUE,
                arcade.color.DEEP_SKY_BLUE,
                arcade.color.SKY_BLUE,
            ])

        self.sky_shape.center_x = self.camera.position.x
        self.sky_shape.draw()

    def draw_textured_polygon(self, vertices, colors):
        vertex_list = arcade.create_rectangles_filled_with_colors(vertices, colors)
        shape = arcade.ShapeElementList()
        shape.append(vertex_list)
        return shape

    def on_key_press(self, key, modifiers):
        if self.plane_crashed:
            return

        if key == arcade.key.UP:
            self.up_pressed = True
        elif key == arcade.key.DOWN:
            self.down_pressed = True
        elif key == arcade.key.LEFT:
            self.left_pressed = True
            self.plane.speed = max(PLANE_SPEED_MIN, self.plane.speed - 1)
        elif key == arcade.key.RIGHT:
            self.right_pressed = True
            if self.plane.speed == 0:
                self.plane.speed = max(1, PLANE_SPEED_MIN)
            else:
                self.plane.speed = min(PLANE_SPEED_MAX, self.plane.speed + 1)
        elif key == arcade.key.PERIOD:
            self.plane.flipped = not self.plane.flipped
            self.plane.set_texture()
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

        angle = math.radians(self.plane.angle)
        bomb_x = self.plane.center_x + BOMB_DROP_OFFSET_X * math.cos(angle) - BOMB_DROP_OFFSET_Y * math.sin(angle)
        bomb_y = self.plane.center_y + BOMB_DROP_OFFSET_X * math.sin(angle) + BOMB_DROP_OFFSET_Y * math.cos(angle)
        
        bomb.center_x = bomb_x
        bomb.center_y = bomb_y

        bomb.change_x = self.plane.change_x * 1.1
        bomb.change_y = self.plane.change_y * 1.1

        bomb.angle = self.plane.angle + 80

        if self.plane.flipped:
            bomb.angle -= 180

        self.bombs.append(bomb)
        self.prev_bomb_time = self.time
        arcade.play_sound(self.bomb_sound)

    def fire_bullet(self):
        bullet = Bullet(self.plane, self.time)
        self.bullets.append(bullet)
        arcade.play_sound(self.fire_sound)

    def target_fire_bullet(self, target):
        bullet_speed = BULLET_SPEED

        bullet = arcade.SpriteCircle(3, arcade.color.RED)
        bullet.center_x = target.center_x
        bullet.center_y = target.center_y

        leading_position = self.calculate_leading_position(target, self.plane, bullet_speed, GRAVITY)

        bullet.angle = math.degrees(math.atan2(
            leading_position[1] - target.center_y,
            leading_position[0] - target.center_x
        ))

        bullet.change_x = math.cos(math.radians(bullet.angle)) * bullet_speed
        bullet.change_y = math.sin(math.radians(bullet.angle)) * bullet_speed

        bullet.start_time = self.time
        self.target_bullets.append(bullet)
        #arcade.play_sound(self.fire_sound)

    def calculate_leading_position(self, target, plane, bullet_speed, gravity):
        target_position = plane.position
        target_velocity = (plane.change_x, plane.change_y)
        target_distance = math.dist(target.position, target_position)

        # Calculate the time it would take for the bullet to reach the target without gravity
        time_to_reach = target_distance / bullet_speed

        # Adjust the leading position by the target's velocity over that time
        aim_position = (
            target_position[0] + target_velocity[0] * time_to_reach,
            target_position[1] + target_velocity[1] * time_to_reach
        )

        # Calculate the effect of gravity over the time it takes for the bullet to reach the target
        gravity_effect = 0.5 * gravity * (time_to_reach ** 2) / 25
        aim_position = (
            aim_position[0],
            aim_position[1] - gravity_effect
        )

        #set debug text to aim position, gravity effect and time to reach format everything with .2f
        if DEBUG_DRAW:
            self.textbox_debug.text = f"Aim: {aim_position[0]:.2f}, {aim_position[1]:.2f} | Plane pos {plane.position[0]:.2f}, {plane.position[1]:.2f} Gravity Eff: {gravity_effect:.2f} | Time: {time_to_reach:.2f}"
            sprite = None
            for s in self.debug_sprites:
                if s.target == target:
                    sprite = s
                    break
            if sprite is None:
                sprite = arcade.SpriteCircle(3, arcade.color.YELLOW)
                self.debug_sprites.append(sprite)
                sprite.target = target
                sprite.center_x = aim_position[0]
                sprite.center_y = aim_position[1]
                sprite.decay = BULLET_FADE_TIME

        return aim_position

    def update(self, delta_time):
        self.time += delta_time

        if self.up_pressed and self.plane.top < SCREEN_HEIGHT:
            self.plane.angle += TILT_ANGLE
        if self.down_pressed:
            self.plane.angle -= TILT_ANGLE

        self.textbox_score.text = f"Score: {self.score}"
        self.textbox_health.text = f"Health: {self.plane.health}"

        if not self.plane_crashed:
            self.plane.angle = self.plane.angle
            self.plane.change_x = math.cos(math.radians(self.plane.angle)) * self.plane.speed
            self.plane.change_y = math.sin(math.radians(self.plane.angle)) * self.plane.speed
            for target in self.targets:
                #check if target is in the screen and within range to shoot
                if (math.hypot(target.center_x - self.plane.center_x, target.center_y - self.plane.center_y) < TARGET_SHOOT_RANGE):
                    if self.time - target.last_shot_time > target.shoot_interval:
                        self.target_fire_bullet(target)
                        target.last_shot_time = self.time

        # Prevent the plane from flying outside the top of the screen
        if self.plane.top > SCREEN_HEIGHT:
            self.plane.top = SCREEN_HEIGHT

        # Check if self.curr_plane_explosion has ended and reset it        
        if self.curr_plane_explosion is not None and self.time - self.curr_plane_explosion.start_time > EXPLOSION_DURATION:
            self.curr_plane_explosion = None

        self.plane.update()
        self.update_bullets(delta_time)
        self.update_bombs(delta_time)
        self.update_target_bullets(delta_time)
        self.check_collisions()
        self.check_crash(delta_time)
        self.scroll_viewport()

        for explosion in self.explosions:
            if self.time > explosion.start_time + EXPLOSION_DURATION:
                explosion.kill()

        for s in self.debug_sprites:
            s.decay -= delta_time
            if s.decay <= 0:
                s.kill()
        self.debug_sprites.update()

    def update_bombs(self, delta_time):
        for bomb in self.bombs:
            bomb.change_y += GRAVITY * delta_time
            bomb.change_x *= AIR_RESISTANCE
            bomb.angle = (bomb.angle + 360) % 360
            if bomb.angle > 180:
                bomb.angle = min(360, bomb.angle + 45.0 * delta_time)
            else:
                bomb.angle = max(0., bomb.angle - 45.0 * delta_time)
            bomb.update()

    def update_bullets(self, delta_time):
        for bullet in self.bullets:
            bullet.change_y += GRAVITY * delta_time
            bullet.change_x *= AIR_RESISTANCE
            bullet.change_y *= AIR_RESISTANCE
        self.bullets.update()

    def update_target_bullets(self, delta_time):
        for bullet in self.target_bullets:
            if (self.time - bullet.start_time >= BULLET_FADE_TIME):
                bullet.remove_from_sprite_lists()
                continue
            bullet.change_y *= AIR_RESISTANCE
            bullet.change_x *= AIR_RESISTANCE
            bullet.change_y += GRAVITY * delta_time
            normalized_time = (self.time - bullet.start_time) / BULLET_FADE_TIME
            bullet.color = (255, 0, 0, max(1, 255 - 255 * ((normalized_time) ** 8)))
            bullet.update()

    def check_collisions(self):
        for bullet in self.bullets:
            if (bullet.bottom <= self.get_y_from_terrain(bullet.center_x) or 
                bullet.top < 0 or bullet.right - self.camera.position[0] < 0 or 
                bullet.left - self.camera.position[0] > SCREEN_WIDTH or
                self.time - bullet.start_time > BULLET_FADE_TIME):
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
            if (self.time - self.prev_bomb_time > 0.15 and arcade.check_for_collision(bomb, self.plane)):
                self.crash_plane(self.plane, 0.1)
                self.add_explosion(bomb)
                bomb.remove_from_sprite_lists()

            if bomb.bottom <= self.get_y_from_terrain(bomb.center_x):
                self.add_explosion(bomb)
                bomb.remove_from_sprite_lists()

        for bullet in self.target_bullets:
            if self.time - bullet.start_time > BULLET_FADE_TIME:
                bullet.remove_from_sprite_lists()
                continue
            if arcade.check_for_collision(bullet, self.plane):
                self.decrease_health(1)
                self.curr_plane_explosion = self.add_explosion(bullet)
                bullet.remove_from_sprite_lists()
            for bomb in self.bombs:
                if arcade.check_for_collision(bullet, bomb):
                    bullet.remove_from_sprite_lists()
                    bomb.remove_from_sprite_lists()
                    self.add_explosion(bomb)

    def decrease_health(self, amount: int):
        self.plane.health -= amount
        if self.plane.health <= 0:
            self.crash_plane(self.plane, 0.1)

    def add_explosion(self, sprite: arcade.Sprite, delay: float = 0.0):
        explosion_size = (sprite.width + sprite.height) / 80
        if len(self.explosions) == MAX_EXPLOSIONS:
            self.explosions.pop(0)
        new_explosion = Explosion(
            sprite.position,
            explosion_size,
            self.camera.position,
            self.time + delay)
        self.explosions.append(new_explosion)
        return new_explosion

    def check_crash(self, delta_time):
        if not self.plane_crashed:
            if self.plane.bottom + 2 < self.get_y_from_terrain(self.plane.center_x):
                self.crash_plane(self.plane)

        # Check collision with targets
        hit_list = arcade.check_for_collision_with_list(self.plane, self.targets)
        if hit_list:
            self.crash_plane(self.plane)
            for target in hit_list:
                self.add_explosion(target, 0.02)
                target.remove_from_sprite_lists()

        # Check if the plane is near any active explosions
        if not self.plane_crashed:
            for explosion in self.explosions:
                if self.curr_plane_explosion is not None and explosion.orig_position == self.curr_plane_explosion.orig_position:
                    continue

                if self.is_explosion_active(explosion):
                    kill_radius = self.get_kill_radius(explosion)
                    explosion_sprite = explosion.sprite
                    kill_radius = max(3, int(kill_radius))
                    if explosion_sprite is None:
                        explosion_sprite = arcade.SpriteCircle(kill_radius, (255, 0, 0, 32))
                        explosion_sprite.center_x = explosion.orig_position[0]
                        explosion_sprite.center_y = explosion.orig_position[1]
                        explosion.sprite = explosion_sprite

                    explosion_sprite.texture = arcade.make_circle_texture(kill_radius, (255, 0, 0, 32))
                    explosion_sprite.set_hit_box(explosion_sprite.texture.hit_box_points)
                    explosion_sprite.update()

                    if not self.plane_crashed and self.curr_plane_explosion is None:
                        if arcade.are_polygons_intersecting(self.plane.get_adjusted_hit_box(), explosion_sprite.get_adjusted_hit_box()):
                            self.crash_plane(self.plane, 0.1)
                            break

        # If the plane has crashed, apply gravity and air resistance
        if self.plane_crashed:
            if self.reset_timer > 0:
                self.reset_plane(delta_time)
            else:
                self.plane.change_y -= 2.0 * delta_time
                self.plane.angle = min(160, self.plane.angle - 25.0 * delta_time)
                self.plane.change_x *= AIR_RESISTANCE
                if self.plane.bottom <= self.get_y_from_terrain(self.plane.center_x):
                    self.reset_plane(delta_time)
                    self.add_explosion(self.plane, 0.1)

    def crash_plane(self, sprite: arcade.Sprite, delay: float = 0.0):
        if not self.plane_crashed:
            self.plane_crashed = True
            self.plane.speed = 0
            self.score -= 100
            explosion = self.add_explosion(sprite, delay)
            if self.curr_plane_explosion is None:
                self.curr_plane_explosion = explosion

    def reset_plane(self, delta_time: float):
        self.plane.speed = 0
        self.plane.change_x = 0
        self.plane.change_y = 0

        self.reset_timer += delta_time

        if self.reset_timer >= 3:
            self.reset_timer = 0
            self.plane_crashed = False
            self.plane.health = MAX_HEALTH
            self.plane.speed = 0
            self.plane.angle = 0
            self.plane.center_x = 0
            self.plane.center_y = 10 + self.get_y_from_terrain(self.plane.center_x) + self.plane.height / 2

    def is_explosion_active(self, explosion):
        return self.time >= explosion.start_time and self.time <= explosion.start_time + EXPLOSION_DURATION

    def get_kill_radius(self, explosion):
        elapsed_time = self.time - explosion.start_time
        normalized_time = elapsed_time / EXPLOSION_DURATION
        eased_time = 1 - (1 - normalized_time) ** 8
        return 140 * explosion.size * eased_time

    def scroll_viewport(self):
        camera_pos_x = self.plane.center_x - SCREEN_WIDTH // 2

        """ if self.prev_plane_x - self.plane_sprite.center_x < -1:  # Moving forward
            camera_pos_x = self.plane_sprite.center_x - SCREEN_WIDTH * 0.3
            self.camera.move_to((camera_pos_x, self.camera.position[1]), 0.5)
        elif self.prev_plane_x - self.plane_sprite.center_x > 1:  # Moving backward
            camera_pos_x = self.plane_sprite.center_x - SCREEN_WIDTH * 0.7
            self.camera.move_to((camera_pos_x, self.camera.position[1]), 0.5)
        else:
            camera_pos_x = self.plane_sprite.center_x - SCREEN_WIDTH // 2 
            self.camera.move_to((camera_pos_x, self.camera.position[1]), 0.5) """

        self.camera.move_to((camera_pos_x, self.camera.position[1]), 0.5)
        self.prev_plane_x = self.plane.center_x

def main():
    window = SopwithGame()
    arcade.run()

if __name__ == "__main__":
    main()
