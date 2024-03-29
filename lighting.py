"""
This class allows to configure n sections in a LED strip loop.
All sections are of equal length. A section's color can be defined.
The LEDs color is determined by the color of the section. 
Blurring between the section's color can be enabled.
"""

import cfg
from color import Color

if cfg.val['simulate_led_hw']:
    from led_nohw import Leds
else:
    from led import Leds

DEFAULT_COLOR = Color(0, 0, 0)


class Section:

    def __init__(self, color):
        self.color = color

    @classmethod
    def fromRGB(cls, r, g, b):
        return Section(Color(r, g, b))

    @classmethod
    def fromColor(cls, color):
        return Section(color)

    @classmethod
    def fromHex(cls, hexcode):
        return Section(Color.fromHex(hexcode))


class Lighting:

    def __init__(self, hw):
        self.hw = hw
        self.nrOfPixels = hw.getNrOfPixels()
        self.list = [Section.fromColor(DEFAULT_COLOR)]
        self.blur = False

    def init(self):
        self.hw.init()

    def finalize(self):
        self.hw.finalize()

    def setSectionList(self, sectionList, blur):
        self.list = sectionList
        self.blur = blur
        self.update()

    def getSectionList(self):
        return self.list

    def update(self):
        for i in range(self.nrOfPixels):
            color = self.getColor(i)
            self.hw.set(i, color.r, color.g, color.b)
        self.hw.update()

    def getColor(self, i):
        return self.__getLed(i)

    def __getLed(self, i):
        sectionLength = self.nrOfPixels / len(self.list)
        sectionNr = (int)(i / sectionLength)
        fraction = (i % sectionLength) / sectionLength
        section = self.list[sectionNr % len(self.list)]
        if self.blur:
            nextSection = self.list[(sectionNr + 1) % len(self.list)]
            interpolatedColor = section.color.interpolate(nextSection.color, fraction)
            return interpolatedColor
        else:
            return section.color


if __name__ == "__main__":

    import time

    leds = Leds(cfg.val['led_brightness'])
    lighting = Lighting(leds)
    lighting.init()

    # sectionList = (Section.fromRGB(255, 0, 0), Section.fromRGB(0, 255, 0), Section.fromRGB(255, 0, 255))
    sectionList = (Section.fromRGB(255, 0, 0), Section.fromRGB(0, 255, 0))
    lighting.setSectionList(sectionList, False)
    lighting.update()
    time.sleep(2)
    lighting.hw.brightness_decrease(0.01, 1)

    lighting.finalize()
