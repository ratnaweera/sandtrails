"""
This class emulates a LED strip loop. It displays the LEDs as circles on a window.
"""

from graphics import GraphWin, Circle, Point, color_rgb

LED_RADIUS = 7
LED_MARGIN = 5
WINDOW_MARGIN = (10, 10, 10, 10)  # top, right, bottom, left

class LedEmulator:
 
    def __init__(self, nrOfPixels):
        self.nrOfPixels = nrOfPixels
        self.leds = [None] * nrOfPixels

    def init(self):
        width = WINDOW_MARGIN[1] + WINDOW_MARGIN[3] + (2 * LED_RADIUS + LED_MARGIN) * self.nrOfPixels - LED_MARGIN
        height = WINDOW_MARGIN[0] + WINDOW_MARGIN[2] + 2 * LED_RADIUS
        self.win = GraphWin('LED emulator', width, height)

    def finalize(self):
        self.win.getMouse()
        self.win.close()
    
    def set(self, i, r, g, b):
        self.leds[i] = (r, g, b)
        
    def update(self):
        for i in range(self.nrOfPixels):
            self.__drawLed(i, self.leds[i])  
        
    def getNrOfPixels(self):
        return self.nrOfPixels

    def __drawLed(self, i, color):
        x = WINDOW_MARGIN[3] + i * (2 * LED_RADIUS + LED_MARGIN)
        y = WINDOW_MARGIN[0]
        l = Circle(Point(x, y), LED_RADIUS)
        l.setFill(color_rgb(*color))
        #l.setWidth(2)
        l.draw(self.win)
               
 
if __name__ == "__main__":
    
    emulator = LedEmulator(3)
    emulator.init()
    emulator.set(0, 255, 0, 0)
    emulator.set(1, 0, 255, 0)
    emulator.set(2, 255, 0, 255)
    emulator.update()
    emulator.finalize()