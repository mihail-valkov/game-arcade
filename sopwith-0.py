import pygame
import sys

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60

# Setup the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Sopwith Game")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Clock
clock = pygame.time.Clock()

# Player properties
player_size = (60, 25)
player_pos = [50, SCREEN_HEIGHT - 60]
player_speed = 5

# Bullet properties
bullets = []
bullet_speed = 10

def draw_plane(position):
    pygame.draw.rect(screen, BLACK, (position[0], position[1], player_size[0], player_size[1]))

def draw_bullet(position):
    pygame.draw.rect(screen, BLACK, (position[0], position[1], 2, 5))

# Game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    
    # Key detection
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and player_pos[0] > 0:
        player_pos[0] -= player_speed
    if keys[pygame.K_RIGHT] and player_pos[0] < SCREEN_WIDTH - player_size[0]:
        player_pos[0] += player_speed
    if keys[pygame.K_UP] and player_pos[1] > 1:
        player_pos[1] -= player_speed
    if keys[pygame.K_DOWN] and player_pos[1] < SCREEN_HEIGHT - player_size[1]:
        player_pos[1] += player_speed
    if keys[pygame.K_SPACE]:
        bullets.append([player_pos[0] + player_size[0], player_pos[1] + player_size[1]//2])

    # Move bullets
    for bullet in bullets[:]:
        bullet[0] += bullet_speed
        if bullet[0] > SCREEN_WIDTH:
            bullets.remove(bullet)

    # Drawing
    screen.fill(WHITE)
    draw_plane(player_pos)
    for bullet in bullets:
        draw_bullet(bullet)
    
    pygame.display.flip()
    clock.tick(FPS)
