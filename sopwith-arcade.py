import arcade
import math

import arcade.color

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Sopwith Game with Arcade"
PLANE_SPEED_MIN = 2
PLANE_SPEED_MAX = 10
PLANE_SIZE = 128
TILT_ANGLE = 1
TERRAIN_BUFFER = 400  # Additional buffer for smooth terrain rendering

class SopwithGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.SKY_BLUE)
        self.camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.gui_camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.plane_sprite = None
        self.plane_speed = PLANE_SPEED_MIN
        self.plane_angle = 0
        self.terrain_points = []
        self.targets = arcade.SpriteList()
        self.bullets = arcade.SpriteList()
        self.bombs = arcade.SpriteList()
        self.plane_flipped = False
        self.setup()

    def setup(self):
        
        self.plane_texture = arcade.load_texture("plane.png")
        self.plane_texture_flipped = arcade.load_texture("plane.png", flipped_vertically=True)
        self.plane_sprite = arcade.Sprite(center_x=SCREEN_WIDTH // 2, center_y=100)
        self.plane_sprite.texture = self.plane_texture
        self.SetSize()
        self.load_terrain()
        self.load_targets()
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

    def load_targets(self):
        target_images = ["target1.png", "target2.png", "target3.png", "target4.png", "target5.png"]
        with open("landscape.txt") as f:
            for line in f:
                if line.startswith("#"):
                    continue
                x, _ = map(int, line.split(","))
                y = self.get_y_from_terrain(x)
                target_image = target_images[len(self.targets) % len(target_images)]
                target = arcade.Sprite(target_image, center_x=x)
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
        self.camera.use()
        arcade.start_render()
        self.draw_terrain()
        self.plane_sprite.draw()
        self.targets.draw()
        self.bullets.draw()
        self.bombs.draw()
        self.gui_camera.use()

    def draw_terrain(self):
        
        color_list = [(123, 255, 123), \
             (123, 255, 120),  \
             (120, 255, 120), \
             (120, 250, 120),  \
             (120, 250, 118)]  # Define your color list here
    
        start_x = self.camera.position[0] - TERRAIN_BUFFER
        end_x = self.camera.position[0] + SCREEN_WIDTH + TERRAIN_BUFFER
        visible_terrain = [point for point in self.terrain_points if start_x <= point[0] <= end_x]
            
        if visible_terrain:
            x0, y0, c0 = visible_terrain[0]
            for x1, y1, c1 in visible_terrain[1:]:
                #arcade.draw_polygon_outline([(x0, 0), (x0, y0), (x1, y1), (x1, 0)], color_list[c0])
                arcade.draw_polygon_filled([(x0, 0), (x0, y0), (x1, y1), (x1, 0)], color_list[c0])
                x0, y0, c0 = x1, y1, c1


    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:            
            self.plane_angle += TILT_ANGLE
        elif key == arcade.key.DOWN:
            self.plane_angle -= TILT_ANGLE
        elif key == arcade.key.LEFT:
            self.plane_speed = max(PLANE_SPEED_MIN, self.plane_speed - 1)
        elif key == arcade.key.RIGHT:
            self.plane_speed = min(PLANE_SPEED_MAX, self.plane_speed + 1)
        elif key == arcade.key.PERIOD:
            self.plane_flipped = not self.plane_flipped
            self.plane_sprite.texture = self.plane_texture_flipped if self.plane_flipped else self.plane_texture
            self.SetSize()
        elif key == arcade.key.B:
            self.drop_bomb()
        elif key == arcade.key.SPACE:
            self.fire_bullet()

    def drop_bomb(self):
        bomb = arcade.Sprite("bomb.png", scale=0.5)
        bomb.center_x = self.plane_sprite.center_x
        bomb.center_y = self.plane_sprite.center_y
        bomb.change_y = -5
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
        self.plane_sprite.angle = self.plane_angle
        self.plane_sprite.change_x = math.cos(math.radians(self.plane_angle)) * self.plane_speed
        self.plane_sprite.change_y = math.sin(math.radians(self.plane_angle)) * self.plane_speed
        self.plane_sprite.update()
        self.bullets.update()
        self.bombs.update()
        self.check_collisions()
        self.check_crash()
        self.scroll_viewport()

    def check_collisions(self):
        for bullet in self.bullets:
            hit_list = arcade.check_for_collision_with_list(bullet, self.targets)
            if hit_list:
                bullet.remove_from_sprite_lists()
                for target in hit_list:
                    target.remove_from_sprite_lists()
        for bomb in self.bombs:
            hit_list = arcade.check_for_collision_with_list(bomb, self.targets)
            if hit_list:
                bomb.remove_from_sprite_lists()
                for target in hit_list:
                    target.remove_from_sprite_lists()
            if bomb.bottom <= self.get_y_from_terrain(bomb.center_x):
                bomb.remove_from_sprite_lists()

    def check_crash(self):
        return
        if self.plane_sprite.bottom <= self.get_y_from_terrain(self.plane_sprite.center_x):
            arcade.play_sound(self.crash_sound)
            arcade.close_window()

    def scroll_viewport(self):
        self.camera.move_to((self.plane_sprite.center_x - SCREEN_WIDTH // 2, 0))

def main():
    window = SopwithGame()
    arcade.run()

if __name__ == "__main__":
    main()
