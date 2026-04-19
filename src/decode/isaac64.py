import struct

ISAAC_WORDS = 256
ISAAC_WORD_SIZE = 8

class Isaac64:
    def __init__(self):
        self.m = [0] * ISAAC_WORDS
        self.a = 0
        self.b = 0
        self.c = 0
        self.r = [0] * ISAAC_WORDS

    def seed(self, seed_value):
        for i in range(ISAAC_WORDS):
            self.m[i] = 0
        self.m[0] = seed_value & 0xFFFFFFFFFFFFFFFF
        self._init_state()

    def _init_state(self):
        self.a = 0
        self.b = 0
        self.c = 0
        for _ in range(4):
            self._refill()

    def _refill(self):
        self.c += 1
        self.b += self.c
        for i in range(ISAAC_WORDS):
            x = self.m[i]
            mix = self._mix(i)
            self.m[i] = y = (mix + self.m[(i + 128) % ISAAC_WORDS]) & 0xFFFFFFFFFFFFFFFF
            self.r[i] = x + y & 0xFFFFFFFFFFFFFFFF

    def _mix(self, i):
        a = self.a
        b = self.b
        x = self.m[i]
        a = (a ^ (a << 21)) & 0xFFFFFFFFFFFFFFFF
        a = (a - (a >> 35)) & 0xFFFFFFFFFFFFFFFF
        a = (a - b) & 0xFFFFFFFFFFFFFFFF
        b = (x + a) & 0xFFFFFFFFFFFFFFFF
        self.a = a
        self.b = b
        return b

    def generate_keystream(self, decode_key, length=131072):
        self.seed(decode_key)
        keystream = bytearray()
        while len(keystream) < length:
            self._refill()
            for i in range(ISAAC_WORDS):
                if len(keystream) >= length:
                    break
                word = self.r[i]
                word_bytes = struct.pack('<Q', word)
                for b in word_bytes:
                    if len(keystream) < length:
                        keystream.append(b)
        return bytes(keystream[:length][::-1])
