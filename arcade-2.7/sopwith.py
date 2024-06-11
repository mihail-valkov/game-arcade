import pygame

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
PLANE_SPEED = 5
BOMB_SPEED = 7
SCROLL_SPEED = 5
GROUND_HEIGHT = 100

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Sopwith Game')

# Load plane image
plane_image = pygame.image.load('plane.png')
plane_rect = plane_image.get_rect()

# Bomb class
class Bomb(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((5, 10))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def update(self):
        self.rect.y += BOMB_SPEED
        if self.rect.y > SCREEN_HEIGHT:
            self.kill()

# Plane class
class Plane(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.transform.scale(plane_image, (75, 40))
        self.rect = self.image.get_rect()
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.speed_y = 0
        self.in_flight = False

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            self.speed_y = -PLANE_SPEED
            self.in_flight = True
        elif keys[pygame.K_DOWN]:
            self.speed_y = PLANE_SPEED
        else:
            self.speed_y = 0

        self.rect.y += self.speed_y

        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT

# Enemy Target class
class EnemyTarget(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

def load_landscape(filename):
    targets = []
    with open(filename, 'r') as file:
        lines = file.readlines()
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                x, y = map(int, line.split(','))
                targets.append((x, y))
    return targets

# Main game loop
def main():
    running = True
    clock = pygame.time.Clock()
    background_x = 0

    plane = Plane()
    all_sprites = pygame.sprite.Group()
    bombs = pygame.sprite.Group()
    enemy_targets = pygame.sprite.Group()
    all_sprites.add(plane)

    # Load landscape and enemy targets from file
    target_positions = load_landscape('landscape.txt')
    for x, y in target_positions:
        enemy = EnemyTarget(x, y)
        all_sprites.add(enemy)
        enemy_targets.add(enemy)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bomb = Bomb(plane.rect.centerx, plane.rect.bottom)
                    all_sprites.add(bomb)
                    bombs.add(bomb)

        all_sprites.update()

        if plane.in_flight:
            background_x -= SCROLL_SPEED
            if background_x <= -SCREEN_WIDTH * 3:
                background_x = 0

        # Check for bomb collisions with enemy targets
        for bomb in bombs:
            hits = pygame.sprite.spritecollide(bomb, enemy_targets, True)
            if hits:
                bomb.kill()

        screen.fill(WHITE)
        
        # Draw scrolling ground
        ground_x = background_x % (SCREEN_WIDTH * 3)
        pygame.draw.rect(screen, GREEN, (ground_x, SCREEN_HEIGHT - GROUND_HEIGHT, SCREEN_WIDTH * 3, GROUND_HEIGHT))

        all_sprites.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == '__main__':
    main()
