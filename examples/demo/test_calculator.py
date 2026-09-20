from calculator import add


def test_sum():
    assert add(2, 3) == 5
    assert add(-2, 3) == 1
    assert add(0, 0) == 0
