from PIL import Image
import json
import os
import numpy
import random
import time

COLOURS = {}
SOCKETS = 5
TILES = []
PROBABILITIES = {}

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

FINAL = []

def generate_image(grid, image_width, image_height):
    factorX = image_width // grid.width
    factorY = image_height // grid.height
    new_image = Image.new("RGB", (image_width, image_height), color = (255, 0, 0))
    for position, cell in grid.grid.items():
        if cell.tile:
            tile_image = cell.tile.image
            imageX = position[0] *  factorX
            imageY = position[1] * factorY
            new_image.paste(tile_image.resize((factorX, factorY)), (imageX, imageY))

    new_image.show()
    new_image.save(f"{image_width}x{image_height}.png")

def add_colours(colours):
    to_return = ""
    for colour in colours:
        if colour not in COLOURS:
            COLOURS[colour] = len(COLOURS)

        to_return += str(COLOURS[colour])

    return to_return

def scan_images(directory):
    prob_file = open(f"{directory}\\probabilities.json", "rb")
    PROBABILITIES = json.load(prob_file)

    for file in os.listdir(os.fsencode(directory)):
        filename = os.fsdecode(file)

        if not filename.endswith(".png"): continue

        image = Image.open(f"{directory}/{filename}").convert("RGB")
        step = image.size[0] / SOCKETS

        up_colours = []
        for socket in range(SOCKETS):
            up_colours.append(image.getpixel((socket * step, 0)))

        right_colours = []
        for socket in range(SOCKETS):
            right_colours.append(image.getpixel((image.size[0]-1, socket * step)))

        down_colours = []
        for socket in range(SOCKETS):
            down_colours.append(image.getpixel((image.size[0] - (socket * step) - 1, image.size[0]-1)))

        left_colours = []
        for socket in range(SOCKETS):
            left_colours.append(image.getpixel((0, image.size[0] - (socket * step) - 1)))

        prob = PROBABILITIES[filename] if filename in PROBABILITIES else 0.5
        tile = Tile(image, filename, prob, add_colours(up_colours), add_colours(right_colours), add_colours(down_colours), add_colours(left_colours))
        if filename == "final.png": FINAL.append(tile)
        TILES.append(tile)

    prob_file.close()

def inverse_direction(direction):
    if direction == UP: return DOWN
    elif direction == DOWN: return UP
    elif direction == LEFT: return RIGHT
    elif direction == RIGHT: return LEFT

class Tile:

    def __init__(self, image, filename, probability, up, right, down, left) -> None:
        self.image = image
        self.filename = filename
        self.probability = probability
        self.up = up
        self.right = right
        self.down = down
        self.left = left

    def check_side(self, socketID, side):
        if side == UP:
            if socketID == self.up[::-1]: return True

        elif side == DOWN:
            if socketID == self.down[::-1]: return True

        elif side == LEFT:
            if socketID == self.left[::-1]: return True

        elif side == RIGHT:
            if socketID == self.right[::-1]: return True

        return False
    
    def get_side(self, side):
        if side == UP: return self.up
        elif side == DOWN: return self.down
        elif side == LEFT: return self.left
        elif side == RIGHT: return self.right

    def __repr__(self) -> str:
        return f"Tile ({self.filename}) -> [UP: '{self.up}', RIGHT: '{self.right}', DOWN: '{self.down}', LEFT: '{self.left}', PROB: {self.probability}]\n"
    
class Cell:

    def __init__(self, grid, x, y, tile = None) -> None:
        self.grid = grid
        self.tile = tile
        self.x = x
        self.y = y
        self.collapsed = False
        self.options = TILES.copy()

    @property
    def entropy(self):
        return len(self.options)
    
    def collapse(self):
        try:
            tile = numpy.random.choice(self.options, 1, [tile.probability for tile in self.options])[0]
            self.tile = tile
            self.collapsed = True
            self.grid.back_propergate(self)
            return True

        except:
            self.tile = FINAL[0]
            self.collapsed = True
            return False

    def __repr__(self) -> str:
        return str(self.collapsed)

class Grid:

    def __init__(self, width, height) -> None:
        self.width = width
        self.height = height
        self.grid = {}
        self.collapsed = 0

        self.generate_blank()

    def generate_blank(self):
        self.collapsed = 0
        for x in range(self.width):
            for y in range(self.height):
                self.grid[(x, y)] = Cell(self, x, y)

    def get_lowest_entropies(self):
        entropies = {}
        for cell in self.grid.values():
            if cell.collapsed: continue
            if cell.entropy not in entropies:
                entropies[cell.entropy] = [cell]

            else:
                entropies[cell.entropy].append(cell)

        return entropies[sorted(entropies)[0]]

    def collapse_cell(self):
        cell = random.choice(self.get_lowest_entropies())
        if cell.collapse():
            self.collapsed += 1

        else:
            self.collapsed = (self.width * self.height)

    def back_propergate(self, cell):
        for dir in [UP, DOWN, LEFT, RIGHT]:
            if (cell.x + dir[0], cell.y + dir[1]) not in self.grid: continue

            cell_to_check = self.grid[(cell.x + dir[0], cell.y + dir[1])]
            inv_dir = inverse_direction(dir)
            for opt in cell_to_check.options.copy():
                if not opt.check_side(cell.tile.get_side(dir), inv_dir):
                    cell_to_check.options.remove(opt)

    def wave_function(self):
        while self.collapsed < (self.width * self.height):
            self.collapse_cell()

        return self.grid

    def __repr__(self) -> str:
        return str(self.grid.values())

if __name__ == "__main__":
    
    start = time.time()
    scan_images(r"C:\Users\qwg34651\Documents\GitHub\Python-collapsed-Wave-Function\\tiles")
    scan_time = time.time()

    grid = Grid(200, 200)
    grid.wave_function()
    collapse_time = time.time()
    generate_image(grid, 1000, 1000)
    end = time.time()

    print(f"SCAN IMAGES: {scan_time - start}")
    print(f"WAVE FUNCTION@ {collapse_time- scan_time}")
    print(f"IMAGE GEN {end - collapse_time}")