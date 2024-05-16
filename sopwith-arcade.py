import arcade

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Sopwith Game with Arcade"
PLANE_SPEED = 5
BOMB_SPEED = 7
SCROLL_SPEED = 5
GROUND_HEIGHT = 100
ENEMY_TARGET_SIZE = 20

class Bomb(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__(center_x=x, center_y=y)
        self.texture = arcade.make_soft_square_texture(5, arcade.color.RED, outer_alpha=255)
        self.change_y = -BOMB_SPEED

    def update(self):
        super().update()
        if self.bottom < 0:
            self.kill()

class Plane(arcade.Sprite):
    def __init__(self, image_file, scale):
        super().__init__(image_file, scale)
        self.change_y = 0
        self.in_flight = False

    def update(self):
        self.center_y += self.change_y
        if self.top > SCREEN_HEIGHT:
            self.top = SCREEN_HEIGHT
        elif self.bottom < 0:
            self.bottom = 0

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
        self.enemy_targets = arcade.SpriteList()

        self.plane = Plane("plane.png", 0.5)
        self.plane.center_x = SCREEN_WIDTH // 2
        self.plane.center_y = SCREEN_HEIGHT // 2
        self.all_sprites.append(self.plane)

        # Load terrain and place enemy targets
        self.terrain_points = self.load_terrain('terrain.txt')
        self.place_enemy_targets('landscape.txt')

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
        targets = []
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

        # Draw the filled terrain
        terrain_points = [(x - self.background_x, y) for x, y in self.terrain_points]
        terrain_points.append((terrain_points[-1][0], 0))
        terrain_points.append((terrain_points[0][0], 0))
        arcade.draw_polygon_filled(terrain_points, arcade.color.GREEN)

    def update(self, delta_time):
        self.all_sprites.update()
        if self.plane.in_flight:
            self.background_x += SCROLL_SPEED
            for enemy in self.enemy_targets:
                enemy.center_x -= SCROLL_SPEED

        # Check for bomb collisions with enemy targets
        for bomb in self.bombs:
            hit_list = arcade.check_for_collision_with_list(bomb, self.enemy_targets)
            if hit_list:
                bomb.kill()
                for target in hit_list:
                    target.kill()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self.plane.change_y = PLANE_SPEED
            self.plane.in_flight = True
        elif key == arcade.key.DOWN:
            self.plane.change_y = -PLANE_SPEED
        elif key == arcade.key.SPACE:
            bomb = Bomb(self.plane.center_x, self.plane.bottom)
            self.all_sprites.append(bomb)
            self.bombs.append(bomb)

    def on_key_release(self, key, modifiers):
        if key == arcade.key.UP or key == arcade.key.DOWN:
            self.plane.change_y = 0

def main():
    game = SopwithGame()
    arcade.run()

if __name__ == "__main__":
    main()
