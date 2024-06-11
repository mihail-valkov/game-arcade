class Explosion:
    def __init__(self, position, size, camera_pos, start_time):
        self.position = position
        self.size = size
        self.orig_position = position
        self.camera_pos = camera_pos
        self.start_time = start_time
        self.sprite = None
    
    def kill(self):
        if self.sprite is not None:
            self.sprite.kill()
            self.sprite = None
