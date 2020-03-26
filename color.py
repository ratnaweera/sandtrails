"""
Simple RGB class
"""

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
