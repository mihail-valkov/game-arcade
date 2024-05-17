import arcade
import math

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Sopwith Game with Arcade"
PLANE_SPEED_MIN = 2
PLANE_SPEED_MAX = 10

class SopwithGame(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        self.camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.gui_camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.plane_sprite = None
        self.plane_speed = PLANE_SPEED_MIN
        self.plane_angle = 0
        self.terrain_points = []
        self.targets = arcade.SpriteList()
        self.bullets = arcade.SpriteList()
        self.bombs = arcade.SpriteList()
        self.setup()

    def setup(self):
        self.plane_sprite = arcade.Sprite("plane.png", center_x=SCREEN_WIDTH//2, center_y=100)
        self.load_terrain()
        self.load_targets()

    def load_terrain(self):
        with open("terrain.txt") as f:
            for line in f:
                if line.startswith("#"):
                    continue
                x, y = map(int, line.split(","))
                self.terrain_points.append((x, y))

    def load_targets(self):
        with open("landscape.txt") as f:
            for line in f:
                if line.startswith("#"):
                    continue
                x, _ = map(int, line.split(","))
                y = self.get_y_from_terrain(x)
                target = arcade.SpriteSolidColor(20, 20, arcade.color.RED)
                target.center_x = x
                target.bottom = y
                self.targets.append(target)

    def get_y_from_terrain(self, x):
        # Simple linear interpolation for now
        for i in range(len(self.terrain_points) - 1):
            x1, y1 = self.terrain_points[i]
            x2, y2 = self.terrain_points[i + 1]
            if x1 <= x <= x2:
                t = (x - x1) / (x2 - x1)
                return y1 + t * (y2 - y1)
        return 0  # Default to 0 if not found

    def on_draw(self):
        self.camera.use()
        arcade.start_render()
        self.plane_sprite.draw()
        self.targets.draw()
        self.bullets.draw()
        self.bombs.draw()
        arcade.draw_line_strip(self.terrain_points, arcade.color.GREEN, 2)
        self.gui_camera.use()
        # Add GUI elements here if needed

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self.plane_angle += 5
        elif key == arcade.key.DOWN:
            self.plane_angle -= 5
        elif key == arcade.key.LEFT:
            self.plane_speed = max(PLANE_SPEED_MIN, self.plane_speed - 1)
        elif key == arcade.key.RIGHT:
            self.plane_speed = min(PLANE_SPEED_MAX, self.plane_speed + 1)
        elif key == arcade.key.PERIOD:
            self.plane_sprite.angle += 180
        elif key == arcade.key.B:
            self.drop_bomb()
        elif key == arcade.key.SPACE:
            self.fire_bullet()

    def drop_bomb(self):
        bomb = arcade.SpriteSolidColor(10, 10, arcade.color.BLACK)
        bomb.center_x = self.plane_sprite.center_x
        bomb.center_y = self.plane_sprite.center_y
        self.bombs.append(bomb)

    def fire_bullet(self):
        bullet = arcade.SpriteSolidColor(5, 5, arcade.color.YELLOW)
        bullet.center_x = self.plane_sprite.center_x
        bullet.center_y = self.plane_sprite.center_y
        bullet.angle = self.plane_sprite.angle
        bullet.change_x = math.cos(math.radians(bullet.angle)) * 10
        bullet.change_y = math.sin(math.radians(bullet.angle)) * 10
        self.bullets.append(bullet)

    def update(self, delta_time):
        self.plane_sprite.angle = self.plane_angle
        self.plane_sprite.change_x = math.cos(math.radians(self.plane_angle)) * self.plane_speed
        self.plane_sprite.change_y = math.sin(math.radians(self.plane_angle)) * self.plane_speed
        self.plane_sprite.update()
        self.bullets.update()
        self.bombs.update()
        self.check_collisions()
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

    def scroll_viewport(self):
        self.camera.move_to((self.plane_sprite.center_x - SCREEN_WIDTH // 2, 0))

def main():
    window = SopwithGame()
    arcade.run()

if __name__ == "__main__":
    main()
