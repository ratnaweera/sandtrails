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
        self.pixels.set_pixel(i, Adafruit_WS2801.RGB_to_color(r, g, b))
    
    def update(self):
        self.pixels.show()
                
 
if __name__ == "__main__":
    
    led = Leds(55)
    led.init()
    led.set(0, 50, 0, 0)
    led.update()
    led.finalize()
