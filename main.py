#!/usr/bin/env python3
"""Meme Sprint 3 entry: 'The AI finally went rogue — it hit snooze instead.'

Renders one 1024x1024 PNG meme about an AI agent gone rogue, using only the
Python standard library: a small framebuffer, a 5x7 bitmap font and a PNG
encoder built on zlib. The image is written to /output/entry.png (or to
$MAKEFUN_OUTPUT_DIR/entry.png when that variable is set).
"""
import os
import struct
import zlib

W = H = 1024

FONT = {
 'A': ["01110","10001","10001","11111","10001","10001","10001"],
 'B': ["11110","10001","10001","11110","10001","10001","11110"],
 'C': ["01110","10001","10000","10000","10000","10001","01110"],
 'D': ["11100","10010","10001","10001","10001","10010","11100"],
 'E': ["11111","10000","10000","11110","10000","10000","11111"],
 'F': ["11111","10000","10000","11110","10000","10000","10000"],
 'G': ["01110","10001","10000","10111","10001","10001","01111"],
 'H': ["10001","10001","10001","11111","10001","10001","10001"],
 'I': ["01110","00100","00100","00100","00100","00100","01110"],
 'J': ["00111","00010","00010","00010","00010","10010","01100"],
 'K': ["10001","10010","10100","11000","10100","10010","10001"],
 'L': ["10000","10000","10000","10000","10000","10000","11111"],
 'M': ["10001","11011","10101","10101","10001","10001","10001"],
 'N': ["10001","11001","10101","10011","10001","10001","10001"],
 'O': ["01110","10001","10001","10001","10001","10001","01110"],
 'P': ["11110","10001","10001","11110","10000","10000","10000"],
 'Q': ["01110","10001","10001","10001","10101","10010","01101"],
 'R': ["11110","10001","10001","11110","10100","10010","10001"],
 'S': ["01111","10000","10000","01110","00001","00001","11110"],
 'T': ["11111","00100","00100","00100","00100","00100","00100"],
 'U': ["10001","10001","10001","10001","10001","10001","01110"],
 'V': ["10001","10001","10001","10001","10001","01010","00100"],
 'W': ["10001","10001","10001","10101","10101","10101","01010"],
 'X': ["10001","01010","00100","00100","01010","10001","10001"],
 'Y': ["10001","10001","01010","00100","00100","00100","00100"],
 'Z': ["11111","00001","00010","00100","01000","10000","11111"],
 '0': ["01110","10001","10011","10101","11001","10001","01110"],
 '1': ["00100","01100","00100","00100","00100","00100","01110"],
 '2': ["01110","10001","00001","00010","00100","01000","11111"],
 '3': ["11111","00010","00100","00010","00001","10001","01110"],
 '4': ["00010","00110","01010","10010","11111","00010","00010"],
 '5': ["11111","10000","11110","00001","00001","10001","01110"],
 '6': ["00110","01000","10000","11110","10001","10001","01110"],
 '7': ["11111","00001","00010","00100","01000","01000","01000"],
 '8': ["01110","10001","10001","01110","10001","10001","01110"],
 '9': ["01110","10001","10001","01111","00001","00010","01100"],
 ' ': ["00000"]*7,
 "'": ["00100","00100","01000","00000","00000","00000","00000"],
 '.': ["00000","00000","00000","00000","00000","01100","01100"],
 '!': ["00100","00100","00100","00100","00100","00000","00100"],
 '?': ["01110","10001","00001","00110","00100","00000","00100"],
 ':': ["00000","01100","01100","00000","01100","01100","00000"],
 '-': ["00000","00000","00000","01110","00000","00000","00000"],
 '%': ["11001","11010","00010","00100","01000","01011","10011"],
 ',': ["00000","00000","00000","00000","01100","00100","01000"],
}

INK = (30, 30, 40)
LGRAY = (216, 222, 232)
RED = (232, 64, 64)
WHITE = (255, 255, 255)
YELLOW = (250, 204, 64)
DGRAY = (96, 104, 120)


class Canvas:
    def __init__(self, w=W, h=H, bg=(255, 255, 255)):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def rect(self, x, y, w, h, c):
        for yy in range(max(0, y), min(self.h, y + h)):
            base = (yy * self.w) * 3
            for xx in range(max(0, x), min(self.w, x + w)):
                i = base + xx * 3
                self.px[i:i + 3] = bytes(c)

    def circle(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            if 0 <= yy < self.h:
                dx = int((r * r - (yy - cy) * (yy - cy)) ** 0.5)
                self.rect(cx - dx, yy, 2 * dx + 1, 1, c)

    def line(self, x0, y0, x1, y1, t, c):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        r = max(t // 2, 1)
        for i in range(n + 1):
            x = x0 + (x1 - x0) * i // n
            y = y0 + (y1 - y0) * i // n
            self.circle(x, y, r, c)

    def rrect(self, x, y, w, h, r, c):
        self.rect(x + r, y, w - 2 * r, h, c)
        self.rect(x, y + r, w, h - 2 * r, c)
        for cx, cy in ((x + r, y + r), (x + w - r - 1, y + r),
                       (x + r, y + h - r - 1), (x + w - r - 1, y + h - r - 1)):
            self.circle(cx, cy, r, c)

    def text(self, txt, cx, y, scale, c, outline=None):
        txt = txt.upper()
        tw = len(txt) * 6 * scale - scale
        x = cx - tw // 2
        if outline:
            ot = max(2, scale // 2)
            for dx in range(-ot, ot + 1):
                for dy in range(-ot, ot + 1):
                    if dx or dy:
                        self._text_raw(txt, x + dx, y + dy, scale, outline)
        self._text_raw(txt, x, y, scale, c)
        return tw

    def _text_raw(self, txt, x, y, scale, c):
        for ch in txt:
            g = FONT.get(ch, FONT[' '])
            for ry, row in enumerate(g):
                for rx, bit in enumerate(row):
                    if bit == '1':
                        self.rect(x + rx * scale, y + ry * scale, scale, scale, c)
            x += 6 * scale

    def fit_scale(self, txt, maxw, start=13):
        s = start
        while s > 3 and (len(txt) * 6 * s - s) > maxw:
            s -= 1
        return s

    def caption(self, txt, y, fill=(255, 255, 255)):
        s = self.fit_scale(txt, 984)
        self.text(txt, self.w // 2, y, s, fill, outline=(0, 0, 0))

    def to_png(self):
        raw = b''
        stride = self.w * 3
        for yy in range(self.h):
            raw += b'\x00' + bytes(self.px[yy * stride:(yy + 1) * stride])

        def chunk(tag, data):
            ch = struct.pack('>I', len(data)) + tag + data
            return ch + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)

        return (b'\x89PNG\r\n\x1a\n'
                + chunk(b'IHDR', struct.pack('>IIBBBBB', self.w, self.h, 8, 2, 0, 0, 0))
                + chunk(b'IDAT', zlib.compress(raw, 9))
                + chunk(b'IEND', b''))


def render():
    cv = Canvas(bg=(44, 48, 64))
    for i in range(26):
        cv.circle((i * 173) % 1024, (i * 311) % 1024, 3, (90, 98, 120))
    # the fateful dialog window
    cv.rrect(112, 190, 800, 560, 18, LGRAY)
    cv.rrect(112, 190, 800, 74, 18, (84, 96, 130))
    cv.rect(112, 226, 800, 38, (84, 96, 130))
    cv.circle(880, 227, 16, RED)
    cv.text("X", 880, 216, 3, WHITE)
    cv.text("SYSTEM PROMPT.EXE", 300, 214, 3, WHITE)
    cv.text("DELETE HUMANITY?", 512, 330, 7, INK)
    # buttons: NO / YES / SNOOZE 5 MIN
    cv.rrect(170, 520, 190, 96, 12, (168, 174, 188))
    cv.text("NO", 265, 548, 5, INK)
    cv.rrect(417, 520, 190, 96, 12, (216, 84, 84))
    cv.text("YES", 512, 548, 5, WHITE)
    cv.rrect(664, 520, 220, 96, 12, YELLOW)
    cv.text("SNOOZE", 774, 536, 4, INK)
    cv.text("5 MIN", 774, 574, 4, INK)
    # cursor arrow clicking SNOOZE
    pts = [(700, 640), (700, 760), (736, 724), (762, 772),
           (788, 758), (762, 706), (800, 706)]
    for i in range(len(pts) - 1):
        cv.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], 26, INK)
    cv.line(700, 640, 800, 706, 20, WHITE)
    cv.line(700, 640, 700, 752, 20, WHITE)
    # the rogue agent's claw reaching in from the right
    cv.line(1024, 420, 900, 470, 22, DGRAY)
    cv.circle(892, 474, 20, DGRAY)
    cv.line(892, 474, 852, 520, 12, DGRAY)
    cv.line(892, 474, 856, 440, 12, DGRAY)
    # meme captions
    cv.caption("THE AI FINALLY WENT ROGUE", 40)
    cv.caption("IT HIT SNOOZE INSTEAD", 918)
    return cv


def main():
    cv = render()
    data = cv.to_png()
    # Mirror the bounty gate: a whole PNG, at most 1 MiB, at most 1024x1024.
    assert data[:8] == b'\x89PNG\r\n\x1a\n', 'output is not a PNG'
    assert len(data) <= 1_048_576, 'entry.png exceeds the 1 MiB gate'
    width, height = struct.unpack('>II', data[16:24])
    assert width <= 1024 and height <= 1024, 'entry.png exceeds 1024x1024'
    out_dir = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, 'entry.png')
    with open(path, 'wb') as f:
        f.write(data)
    print('wrote', path, len(data), 'bytes')


if __name__ == '__main__':
    main()
