def test_load():
    import chparse

    with open(r'tests/Test.chart') as f:
        c = chparse.load(f)
        assert c is not None
