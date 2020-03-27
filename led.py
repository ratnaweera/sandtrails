"""
This class deals with the hardware-specific aspects of the LEDs.
"""

import RPi.GPIO as GPIO
 
# Import the WS2801 module.
import Adafruit_WS2801
import Adafruit_GPIO.SPI as SPI

# Alternatively specify a hardware SPI connection on /dev/spidev0.0:
SPI_PORT   = 0
SPI_DEVICE = 0

# Scale all the color values. 1 = no reduction, 0 = dark
BRIGHTNESS_REDUCTION = 0.5

def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)


class Leds:
 
    def __init__(self, nrOfPixels):
        self.pixels = Adafruit_WS2801.WS2801Pixels(nrOfPixels, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE), gpio=GPIO)

    def init(self):
        self.pixels.clear()
        self.pixels.show()
        
    def finalize(self):
        pass

    def getNrOfPixels(self):
        return self.pixels.count()
    
    def set(self, i, r, g, b):
        rl, gl, bl = Leds.adjustBrightness(r, g, b, BRIGHTNESS_REDUCTION)
        self.pixels.set_pixel(i, Adafruit_WS2801.RGB_to_color(rl, gl, bl))

    @staticmethod
    def clampRGB(r, g, b):
        return (clamp(r, 0, 255), clamp(g, 0, 255), clamp(b, 0, 255))
    
    @staticmethod
    def adjustBrightness(r, g, b, factor):
        return Leds.clampRGB(r * factor, g * factor, b * factor)
        
    def update(self):
        self.pixels.show()
                
 
if __name__ == "__main__":
    
    assert Leds.adjustBrightness(100, 200, 300, 0.5) == (50, 100, 150)
    assert Leds.adjustBrightness(100, 200, 300, 1.0) == (100, 200, 255)

    led = Leds(10)
    led.init()
    led.set(0, 50, 0, 0)
    led.set(1, 0, 50, 0)
    led.set(2, 0, 0, 50)
    led.update()
    led.finalize()
