"""
This class allows to configure n sections in a LED strip loop.
All sections are of equal length. A section's color can be defined.
The LEDs color is determined by the color of the section. 
Blurring between the section's color can be enabled.
"""

from ledemulator import LedEmulator

def interpolate(a, b, fraction):
    return (int)(a * (1 - fraction) + b * (fraction))


class Color:
    
    def __init__(self, r, g, b):
        assert (0 <= r <= 255) and (0 <= g <= 255) and (0 <= b <= 255), "Color RGB value out of range: {}, {}, {}".format(r, g, b)
        self.r = r
        self.g = g
        self.b = b

    def interpolate(self, other, fraction):
        assert 0 <= fraction <= 1.0, "Fraction out of range: {}".format(fraction)
        return Color.interpolateColor(self, other, fraction)
        
    @staticmethod
    def interpolateColor(a, b, fraction):
        return Color(interpolate(a.r, b.r, fraction), interpolate(a.g, b.g, fraction), interpolate(a.b, b.b, fraction))
    
    def __str__(self):
        return "Color: " + str(self.r) + ", " + str(self.g) + ", " + str(self.b)
    
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.r == other.r and self.g == other.g and self.b == other.b
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)
    
    
class Section:
    
    def __init__(self, r, g, b):
        self.color = Color(r, g, b)
    
        
class LedConfig:
    
    def __init__(self, hw):
        self.hw = hw
        self.nrOfPixels = hw.getNrOfPixels()
    
    def init(self):
        self.hw.init();

    def finalize(self):
        self.hw.finalize();
        
    def setSectionList(self, sectionList, blur):
        self.list = sectionList
        self.blur = blur
        self.update()
        
    def update(self):
        for i in range(self.nrOfPixels):
            color = self.getColor(i)
            self.hw.set(i, color.r, color.g, color.b)
        self.hw.update()

    def getColor(self, i):
        return self.__getLed(i)
    
    def __getLed(self, i):
        sectionLength = self.nrOfPixels / len(self.list)
        sectionNr = (int) (i / sectionLength)
        fraction = (i % sectionLength) / sectionLength
        section = self.list[sectionNr % len(self.list)]
        if self.blur:
            nextSection = self.list[(sectionNr + 1) % len(self.list)]
            interpolatedColor = section.color.interpolate(nextSection.color, fraction)
            print(str(fraction) + " " + str(section.color) + " " + str(nextSection.color) + " -> " + str(interpolatedColor))
            return interpolatedColor
        else:
            return section.color
                
 
if __name__ == "__main__":

    c1 = Color(255, 0, 0)
    c2 = Color(0, 255, 0)
    c3 = Color(255, 0, 255)
    
    assert c1.interpolate(c2, 0) == c1
    assert c1.interpolate(c2, 1) == c2
    assert c2.interpolate(c1, 0) == c2
    assert c3.interpolate(c3, 0.65) == c3
    assert c1.interpolate(c2, 0.5) == Color(127, 127, 0)
    assert c3.interpolate(c1, 0.5) == Color(255, 0, 127)
    
    ledEmulator = LedEmulator(25)
    ledConfig = LedConfig(ledEmulator)
    ledConfig.init()
    
    sectionList = (Section(255, 0, 0), Section(0, 255, 0), Section(255, 0, 255))
    ledConfig.setSectionList(sectionList, True)
    ledConfig.update()

    ledConfig.finalize()
    
    
