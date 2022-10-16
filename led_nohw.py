"""
This class deals with the hardware-specific aspects of the LEDs.
"""

import logging
import cfg


def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)


class Leds:
 
    def __init__(self, nrOfPixels):
        self.nrOfPixels = nrOfPixels

    def init(self):
        logging.warning('Missing LED hardware: LED emulator started')
        
    def finalize(self):
        pass

    def getNrOfPixels(self):
        return self.nrOfPixels
    
    def set(self, i, r, g, b):
        rl, gl, bl = Leds.adjustBrightness(r, g, b, cfg.val['led_brightness'])
        logging.info("Set LED " + str(i) + ": " + str((rl, gl, bl)))

    def brightness_decrease(self, wait=0.01, step=1):
        logging.info('LED simulator: Brightness decrease')

    @staticmethod
    def clampRGB(r, g, b):
        return (clamp(r, 0, 255), clamp(g, 0, 255), clamp(b, 0, 255))
    
    @staticmethod
    def adjustBrightness(r, g, b, factor):
        return Leds.clampRGB(int(round(r * factor)), int(round(g * factor)), int(round(b * factor)))
        
    def update(self):
        logging.info("LED update")
        pass
                
 
if __name__ == "__main__":
    
    assert Leds.adjustBrightness(100, 200, 300, 0.5) == (50, 100, 150)
    assert Leds.adjustBrightness(100, 200, 300, 1.0) == (100, 200, 255)

    led = Leds(cfg.val['nr_of_leds'])
    led.init()
    led.set(0, 50, 0, 0)
    led.set(1, 0, 50, 0)
    led.set(2, 0, 0, 50)
    led.update()
    led.finalize()
