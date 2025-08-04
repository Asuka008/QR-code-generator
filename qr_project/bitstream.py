# This code was written by Ding Sihan,31808904
class _BitStream(list[int]):
    def append_bits(self, val: int, n: int) -> None:
        if (n < 0) or (val >> n != 0):
            raise ValueError("Value out of range")
        self.extend(((val >> i) & 1) for i in reversed(range(n)))
