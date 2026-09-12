from rugby_selector.models.position import position_label, position_name


def test_playing_position_names():
    assert position_name(1) == "Prop"
    assert position_name(2) == "Hooker"
    assert position_name(4) == "Second Row"
    assert position_name(8) == "No 8."
    assert position_name(12) == "Centre"
    assert position_name(15) == "Full Back"


def test_positions_after_fullback_are_bench():
    assert position_name(16) == "Bench"
    assert position_label(16) == "Bench"
