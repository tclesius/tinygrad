import unittest, struct
from extra.png import PNG

RED = struct.pack("BBBB", 255, 0, 0, 255)
GREEN = struct.pack("BBBB", 0, 255, 0, 255)
BLUE = struct.pack("BBBB", 0, 0, 255, 255)
WHITE = struct.pack("BBBB", 255, 255, 255, 255)

class TestPNG(unittest.TestCase):
  def test_png_encode_decode(self):
    w, h = 2, 2
    rgba = bytes(
        [
            *RED,
            *GREEN,
            *BLUE,
            *WHITE,
        ]
    )
    png = PNG.encode(w, h, rgba)
    w2, h2, rgba2 = PNG.decode(png)
    self.assertEqual(w, w2)
    self.assertEqual(h, h2)
    self.assertEqual(rgba, rgba2)