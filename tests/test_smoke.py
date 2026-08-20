"""Smoke test: the loop_doctor package imports cleanly."""


def test_import() -> None:
    import loop_doctor

    assert loop_doctor.__name__ == "loop_doctor"
