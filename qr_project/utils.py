# written by Pang Yuyan,31808748
def _get_bit(x: int, i: int) -> bool:
    return (x >> i) & 1 != 0

class DataTooLongError(ValueError):
    pass
