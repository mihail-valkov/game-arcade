# Constants for the game
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Sopwith Game with Arcade"
PLANE_SPEED_MIN = 2.5
PLANE_SPEED_MAX = 8
PLANE_SCALE = 0.25
TARGET_SCALE = 0.45
TILT_ANGLE = 2
GRAVITY = -4.0  # Gravity constant
TERRAIN_BUFFER = 350  # Additional buffer for smooth terrain rendering
AIR_RESISTANCE = 0.987  # Air resistance factor
MAX_EXPLOSIONS = 10
BULLET_SPEED = 10
BOMB_DROP_INTERVAL = 0.5  # Time interval between bomb drops
EXPLOSION_DURATION = 1.5  # Duration of the explosion effect
BULLET_FADE_TIME_PLANE = 1.5  # Time interval for plane bullets to fade away
BULLET_FADE_TIME_TARGET = 2.5  # Time interval for target bullets to fade away
TARGET_SHOOT_RANGE = 350  # Shooting range for the targets
MAX_HEALTH = 10

BACKGROUND_LAYER_1_SPEED = 0.7  # Speed for the first background layer
BACKGROUND_LAYER_2_SPEED = 0.5  # Speed for the second background layer

# Determine the relative drop point in the plane's local coordinate system
BOMB_DROP_OFFSET_X = -10  # offset from the plane's center in the x-direction
BOMB_DROP_OFFSET_Y = -10  # offset from the plane's center in the y-direction
BOMB_SCALE = 0.3

DEBUG_DRAW = False
DRAW_FPS = True
DEBUG_COLOR = (255, 0, 0, 64)
