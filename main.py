import pygame as pg
import numpy as np
import pygame.camera

# Class for working with katakana letters
class Matrix:
    def __init__(self, app, font_size=11, raindrop_speed=2, density=3):
        self.app = app
        self.FONT_SIZE = font_size
        self.SIZE = self.ROWS, self.COLS = app.HEIGHT // font_size, app.WIDTH // font_size
        self.katakana = np.array([chr(int('0x30a0', 16) + i) for i in range(96)] + ['' for _ in range(30)])
        self.font = pg.font.SysFont('ms mincho', font_size, bold=True)
        
        # Initialize matrix of characters and raindrop positions
        self.matrix = np.random.choice(self.katakana, self.SIZE)
        self.char_intervals = np.random.randint(20, 50, size=self.SIZE)  # Increased intervals for less frequent changes
        self.prerendered_chars = self.get_prerendered_chars()
        
        # Initialize raindrop positions
        self.raindrop_positions = np.random.randint(0, self.ROWS, (self.COLS, density))
        self.raindrop_speed = raindrop_speed  # Speed at which raindrop effect moves down
        self.density = density  # Density of raindrops in each column

    def get_frame(self):
        # Capture a frame from the webcam
        image = self.app.cam.get_image()
        image = pg.transform.scale(image, self.app.RES)
        return image

    def get_prerendered_chars(self):
        # Pre-render characters in different shades of green
        char_colors = [(0, green, 0) for green in range(256)]
        prerendered_chars = {}
        for char in self.katakana:
            for color in char_colors:
                prerendered_chars[(char, color)] = self.font.render(char, True, color)
        return prerendered_chars

    def run(self):
        # Main loop to update and draw characters
        frames = pg.time.get_ticks()
        self.change_chars(frames)
        self.shift_brightness(frames)
        self.draw()

    def change_chars(self, frames):
        # Change characters at intervals
        mask = np.argwhere(frames % self.char_intervals == 0)
        new_chars = np.random.choice(self.katakana, mask.shape[0])
        self.matrix[mask[:, 0], mask[:, 1]] = new_chars

    def shift_brightness(self, frames):
        # Shift brightness of raindrops
        if frames % self.raindrop_speed == 0:
            for col in range(self.COLS):
                self.raindrop_positions[col] = (self.raindrop_positions[col] + 1) % self.ROWS

    def draw(self):
        # Draw characters with brightness effects
        frame = self.get_frame()
        for x in range(self.COLS):
            for y in range(self.ROWS):
                char = self.matrix[y, x]
                if char:
                    pos = x * self.FONT_SIZE, y * self.FONT_SIZE
                    if pos[0] < frame.get_width() and pos[1] < frame.get_height():
                        # Get average brightness from the webcam frame
                        color = frame.get_at((pos[0], pos[1]))
                        red, green, blue = color[:3]
                        avg_color = (red + green + blue) // 3
                        avg_color = 220 if 100 < avg_color < 220 else avg_color
                        brightness = max(0, avg_color)
                        
                        # Apply raindrop effect
                        drop_brightness = max(0, 255 - min([abs(raindrop_y - y) for raindrop_y in self.raindrop_positions[x]]) * 15)
                        final_brightness = min(brightness, drop_brightness)
                        bright_color = (0, final_brightness, 0)
                        
                        # Render character with adjusted brightness
                        char_surface = self.prerendered_chars[(char, bright_color)]
                        char_surface.set_alpha(final_brightness + 60)
                        self.app.surface.blit(char_surface, pos)

# Main application
class MatrixVision:
    def __init__(self):
        self.RES = self.WIDTH, self.HEIGHT = 1536, 864
        pg.init()
        self.screen = pg.display.set_mode(self.RES)
        self.surface = pg.Surface(self.RES)
        self.clock = pg.time.Clock()
        self.matrix = Matrix(self)

        pg.camera.init()
        self.cam = pg.camera.Camera(pg.camera.list_cameras()[0])
        self.cam.start()

    def draw(self):
        # Draw the matrix effect
        self.surface.fill(pg.Color('black'))
        self.matrix.run()
        self.screen.blit(self.surface, (0, 0))

    def run(self):
        while True:
            self.draw()
            [exit() for i in pg.event.get() if i.type == pg.QUIT]
            pg.display.flip()
            pg.display.set_caption(str(self.clock.get_fps()))
            self.clock.tick(60)

if __name__ == "__main__":
    app = MatrixVision()
    app.run()