import arcade
import math
import random

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Sopwith Game with Arcade"
PLANE_SPEED_INCREMENT = 0.1
PLANE_MIN_SPEED = 1
PLANE_MAX_SPEED = 10
BOMB_SPEED = 7
BULLET_SPEED = 10
GROUND_HEIGHT = 100
ENEMY_TARGET_SIZE = 20
FRICTION = 0.99
SOUND_VOLUME = 0.5

class Bomb(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__(center_x=x, center_y=y)
        self.texture = arcade.make_soft_square_texture(10, arcade.color.BLACK, outer_alpha=255)
        self.change_y = -BOMB_SPEED
        #self.bomb_sound = arcade.load_sound("sounds/bomb_drop.wav")

    def update(self):
        super().update()
        if self.bottom < 0:
            self.kill()

    def on_create(self):
        arcade.play_sound(self.bomb_sound, SOUND_VOLUME)

class Bullet(arcade.Sprite):
    def __init__(self, x, y, angle):
        super().__init__(center_x=x, center_y=y)
        self.texture = arcade.make_soft_square_texture(5, arcade.color.YELLOW, outer_alpha=255)
        self.angle = angle
        self.change_x = BULLET_SPEED * math.cos(math.radians(self.angle))
        self.change_y = BULLET_SPEED * math.sin(math.radians(self.angle))
        #self.bullet_sound = arcade.load_sound("sounds/bullet_fire.wav")

    def update(self):
        super().update()
        if self.left > SCREEN_WIDTH or self.right < 0 or self.top > SCREEN_HEIGHT or self.bottom < 0:
            self.kill()

    def on_create(self):
        arcade.play_sound(self.bullet_sound, SOUND_VOLUME)

class Plane(arcade.Sprite):
    def __init__(self, image_file, scale):
        super().__init__(image_file, scale)
        self.change_x = PLANE_MIN_SPEED
        self.change_y = 0
        self.angle = 0
        #self.crash_sound = arcade.load_sound("sounds/plane_crash.wav")

    def update(self):
        # Update plane position based on speed and angle
        self.center_x += self.change_x * math.cos(math.radians(self.angle))
        self.center_y += self.change_x * math.sin(math.radians(self.angle))

        # Screen wrapping logic
        if self.left > SCREEN_WIDTH:
            self.right = 0
        elif self.right < 0:
            self.left = SCREEN_WIDTH
        if self.top > SCREEN_HEIGHT:
            self.bottom = SCREEN_HEIGHT
        elif self.bottom < 0:
            self.top = 0

    def on_crash(self):
        arcade.play_sound(self.crash_sound, SOUND_VOLUME)
        self.kill()

class EnemyTarget(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__(center_x=x, center_y=y)
        self.texture = arcade.make_soft_square_texture(ENEMY_TARGET_SIZE, arcade.color.RED, outer_alpha=255)

class SopwithGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        self.background_x = 0
        self.all_sprites = arcade.SpriteList()
        self.bombs = arcade.SpriteList()
        self.bullets = arcade.SpriteList()
        self.enemy_targets = arcade.SpriteList()
        self.game_over = False

        self.plane = Plane("images/plane.png", 0.5)
        self.plane.center_x = SCREEN_WIDTH // 2
        self.plane.center_y = SCREEN_HEIGHT // 2
        self.all_sprites.append(self.plane)

        # Load terrain and place enemy targets
        self.terrain_points = self.load_terrain('data/terrain.txt')
        self.place_enemy_targets('data/landscape.txt')

    def load_terrain(self, filename):
        points = []
        with open(filename, 'r') as file:
            lines = file.readlines()
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    x, y = map(int, line.split(','))
                    points.append((x, y))
        return points

    def place_enemy_targets(self, filename):
        with open(filename, 'r') as file:
            lines = file.readlines()
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    x, _ = map(int, line.split(','))
                    y = self.get_terrain_height_at(x)
                    enemy = EnemyTarget(x, y + ENEMY_TARGET_SIZE // 2)
                    self.all_sprites.append(enemy)
                    self.enemy_targets.append(enemy)

    def get_terrain_height_at(self, x):
        # Find the two points surrounding the x coordinate
        for i in range(len(self.terrain_points) - 1):
            x1, y1 = self.terrain_points[i]
            x2, y2 = self.terrain_points[i + 1]
            if x1 <= x <= x2:
                # Linear interpolation
                t = (x - x1) / (x2 - x1)
                return y1 + t * (y2 - y1)
        return 0

    def on_draw(self):
        arcade.start_render()
        self.draw_background()
        self.all_sprites.draw()

    def draw_background(self):
        # Fill the entire screen with sky color
        arcade.draw_lrtb_rectangle_filled(0, SCREEN_WIDTH, SCREEN_HEIGHT, 0, arcade.color.SKY_BLUE)

        # Adjust background scrolling based on plane's position
        if self.plane.center_x >= SCREEN_WIDTH * 0.6:
            self.background_x += self.plane.change_x
        elif self.plane.center_x <= SCREEN_WIDTH * 0.4 and self.background_x > 0:
            self.background_x -= self.plane.change_x

        # Draw the filled terrain
        terrain_points = [(x - self.background_x, y) for x, y in self.terrain_points]
        terrain_points.append((terrain_points[-1][0], 0))
        terrain_points.append((terrain_points[0][0], 0))
        arcade.draw_polygon_filled(terrain_points, arcade.color.GREEN)

    def update(self, delta_time):
        self.all_sprites.update()
        self.bombs.update()
        self.bullets.update()

        # Check for bomb collisions with enemy targets
        for bomb in self.bombs:
            hit_list = arcade.check_for_collision_with_list(bomb, self.enemy_targets)
            if hit_list:
                bomb.kill()
                for target in hit_list:
                    target.kill()

        # Check for bullet collisions with enemy targets
        for bullet in self.bullets:
            hit_list = arcade.check_for_collision_with_list(bullet, self.enemy_targets)
            if hit_list:
                bullet.kill()
                for target in hit_list:
                    target.kill()

        # Check for plane collision with the ground
        terrain_height = self.get_terrain_height_at(self.plane.center_x + self.background_x)
        if self.plane.center_y < terrain_height:
            self.plane.on_crash()
            self.game_over = True

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self.plane.angle += 5
        elif key == arcade.key.DOWN:
            self.plane.angle -= 5
        elif key == arcade.key.LEFT:
            self.plane.change_x = max(self.plane.change_x - PLANE_SPEED_INCREMENT, PLANE_MIN_SPEED)
        elif key == arcade.key.RIGHT:
            self.plane.change_x = min(self.plane.change_x + PLANE_SPEED_INCREMENT, PLANE_MAX_SPEED)
        elif key == arcade.key.PERIOD:
            self.plane.angle += 180
        elif key == arcade.key.B:
            bomb = Bomb(self.plane.center_x, self.plane.center_y)
            bomb.on_create()
            self.all_sprites.append(bomb)
            self.bombs.append(bomb)
        elif key == arcade.key.SPACE:
            bullet = Bullet(self.plane.center_x, self.plane.center_y, self.plane.angle)
            bullet.on_create()
            self.all_sprites.append(bullet)
            self.bullets.append(bullet)

def main():
    game = SopwithGame()
    arcade.run()

if __name__ == "__main__":
    main()
