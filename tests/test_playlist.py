import pytest
from playlist import Playlist, RepeatMode

# basic properties

def test_len_and_contains_basic():
    pl = Playlist(["Andersen", "Beethoven", "Chaplin", "Dvorak"])
    assert len(pl) == 4
    assert "Andersen" in pl
    assert "X" not in pl


def test_find_getitem():
    pl = Playlist(["Andersen", "Beethoven", "Chaplin", "Dvorak"])
    # find
    assert pl.find("Beethoven") == 1
    assert pl.find("X") is None
    # getitem
    assert pl[0] == "Andersen"
    assert pl[1] == "Beethoven"
    assert pl[-1] == "Dvorak"


def test_getitem_slices():
    pl = Playlist(["Andersen", "Beethoven", "Chaplin", "Dvorak"])
    assert pl[1:3] == ["Beethoven", "Chaplin"]
    assert pl[::-1] == ["Dvorak", "Chaplin", "Beethoven", "Andersen"]

def test_getitem_errors():
    pl = Playlist(["Andersen", "Beethoven", "Chaplin", "Dvorak"])
    with pytest.raises(IndexError):
        _ = pl[10]
    with pytest.raises(IndexError):
        _ = pl[-10]
    with pytest.raises(TypeError):
        _ = pl[1.0]  # not int or slice


def test_iter_ignores_shuffle():
    pl = Playlist(["Andersen", "Beethoven", "Chaplin"])
    assert list(iter(pl)) == ["Andersen", "Beethoven", "Chaplin"]
    pl.shuffle(seed=0)
    assert list(iter(pl)) == ["Andersen", "Beethoven", "Chaplin"]


# add

def test_add_basic():
    pl = Playlist(["Andersen"])
    pl.add("Beethoven")
    assert len(pl) == 2
    assert pl.tracks == ["Andersen", "Beethoven"]
    assert pl.order == [0, 1]


def test_add_duplicate():
    pl = Playlist(["Andersen"])
    with pytest.warns(UserWarning, match=r"Track is already in playlist: 'Andersen'!"):
        pl.add("Andersen")
    assert len(pl) == 1
    assert pl.order == [0]


def test_add_in_shuffle_after_started():
    pl = Playlist(["Andersen", "Beethoven", "Chaplin"])
    _ = pl.next()  # Andersen
    _ = pl.next()  # Beethoven
    cur_before = pl.current()
    pl.shuffle(seed=123)
    assert pl.current() == cur_before
    pl.rng.seed(9)
    pl.add("Dvorak")
    assert "Dvorak" in pl
    assert pl.current() == cur_before
    new_id = len(pl) - 1
    assert new_id in pl.order
    assert len(pl.order) == 4


def test_add_in_shuffle_before_start():
    pl = Playlist(["Andersen", "Beethoven", "Chaplin"])
    pl.shuffle(seed=0)  # not started yet
    pl.rng.seed(1)
    pl.add("Dvorak")
    assert "Dvorak" in pl
    assert len(pl.order) == 4
    assert pl.current() is None


# next/previous core

def test_next_previous_repeat_off():
    pl = Playlist(["Andersen", "Beethoven"])
    assert pl.current() is None
    assert pl.next() == "Andersen"
    assert pl.next() == "Beethoven"
    assert pl.next() is None
    pl.unshuffle()
    pl.current_track = 0
    assert pl.previous() is None


def test_repeat_all_wrap():
    pl = Playlist(["Andersen", "Beethoven", "Chaplin", "Dvorak"])
    pl.set_repeat(RepeatMode.ALL)
    pl.current_track = len(pl.order) - 1  # point to Dvorak
    assert pl.current() == "Dvorak"
    assert pl.next() == "Andersen"
    pl.current_track = 0
    assert pl.previous() == "Dvorak"


def test_repeat_one_sticks():
    pl = Playlist(["Andersen", "Beethoven"])
    pl.set_repeat("one")
    assert pl.next() == "Andersen"  # fixes cursor at 0
    assert pl.next() == "Andersen"
    assert pl.previous() == "Andersen"


def test_single_track_all_modes():
    pl = Playlist(["Andersen"])
    # off
    assert pl.next() == "Andersen"
    assert pl.next() is None
    # one
    pl.current_track = -1
    pl.set_repeat("one")
    assert pl.next() == "Andersen"
    assert pl.next() == "Andersen"
    assert pl.previous() == "Andersen"
    assert pl.previous() == "Andersen"
    # all
    pl.set_repeat("all")
    pl.current_track = 0
    assert pl.next() == "Andersen"
    assert pl.next() == "Andersen"
    assert pl.previous() == "Andersen"
    assert pl.previous() == "Andersen"


def test_previous_from_not_started_with_repeat_all_and_one():
    pl = Playlist(["Andersen", "Beethoven"])
    pl.set_repeat("all")
    assert pl.previous() == "Beethoven"
    pl2 = Playlist(["Andersen", "Beethoven"])
    pl2.set_repeat("one")
    assert pl2.previous() == "Andersen"
    assert pl2.current() == "Andersen"


def test_next_previous_on_empty():
    pl = Playlist()
    assert pl.next() is None
    assert pl.previous() is None


# shuffle / unshuffle

def test_shuffle_deterministic_before_start():
    pl = Playlist(["Andersen", "Beethoven", "Chaplin", "Dvorak"])
    pl.shuffle(seed=42)
    assert pl.order == [2, 1, 3, 0]
    assert pl.current() is None


def test_shuffle_deterministic_after_started():
    pl = Playlist(["Andersen", "Beethoven", "Chaplin", "Dvorak"])
    _ = pl.next()   # Andersen
    _ = pl.next()   # Beethoven
    pl.shuffle(seed=7)
    assert pl.order == [3, 1, 0, 2] 
    assert pl.current() == "Beethoven"


def test_unshuffle_preserves_current():
    pl = Playlist(["Andersen", "Beethoven", "Chaplin"])
    _ = pl.next()  # Andersen
    _ = pl.next()  # Beethoven
    cur = pl.current()
    pl.shuffle(seed=1)
    pl.unshuffle()
    assert pl.order == [0, 1, 2]
    assert pl.current() == cur


def test_shuffle_unshuffle_flags_on_various_sizes():
    one = Playlist(["Andersen"])
    one.shuffle()
    assert one.shuffled is True
    one.unshuffle()
    assert one.shuffled is False

    empty = Playlist()
    empty.shuffle()
    assert empty.shuffled is True
    empty.unshuffle()
    assert empty.shuffled is False
    assert empty.order == []
    assert empty.current() is None


# remove

def test_remove_current_middle():
    pl = Playlist(["Andersen", "Beethoven", "Chaplin", "Dvorak"])
    _ = pl.next()  # Andersen
    _ = pl.next()  # Beethoven
    assert pl.current() == "Beethoven"
    removed = pl.remove(1)
    assert removed == "Beethoven"
    assert pl.current() == "Chaplin"
    assert pl.order_view() == ["Andersen", "Chaplin", "Dvorak"]


def test_remove_current_when_it_was_last():
    pl = Playlist(["Andersen", "Beethoven", "Chaplin"])
    _ = pl.next()  # Andersen
    _ = pl.next()  # Beethoven
    _ = pl.next()  # Chaplin
    assert pl.current() == "Chaplin"
    removed = pl.remove(2)
    assert removed == "Chaplin"
    assert pl.current() == "Beethoven"
    assert pl.order_view() == ["Andersen", "Beethoven"]


def test_remove_before_or_after_current_adjusts_properly():
    pl = Playlist(["Andersen", "Beethoven", "Chaplin", "Dvorak"])
    _ = pl.next()  # Andersen
    _ = pl.next()  # Beethoven
    removed = pl.remove(0)  # remove before current
    assert removed == "Andersen"
    assert pl.current() == "Beethoven"
    removed = pl.remove(2)  # remove after current
    assert removed == "Dvorak"
    assert pl.current() == "Beethoven"


def test_remove_on_empty_raises():
    pl = Playlist()
    with pytest.raises(IndexError):
        pl.remove(0)


def test_remove_last_remaining_makes_empty():
    pl = Playlist(["Andersen"])
    _ = pl.next()
    removed = pl.remove(0)
    assert removed == "Andersen"
    assert len(pl) == 0
    assert pl.order == []
    assert pl.current() is None


def test_remove_negative_index():
    pl = Playlist(["Andersen", "Beethoven", "Chaplin"])
    removed = pl.remove(-1)
    assert removed == "Chaplin"
    assert pl.tracks == ["Andersen", "Beethoven"]
    assert pl.order == [0, 1]


# move

def test_move_preserves_play_order():
    pl = Playlist(["Andersen", "Beethoven", "Chaplin", "Dvorak"])
    pl.shuffle(seed=7)
    names_before = [pl.tracks[i] for i in pl.order]
    pl.move(0, 2)  # move Andersen to index 2
    assert pl.tracks == ["Beethoven", "Chaplin", "Andersen", "Dvorak"]
    names_after = [pl.tracks[i] for i in pl.order]
    assert names_before == names_after  # play order preserved


def test_move_with_negative_indices_preserves_current():
    pl = Playlist(["Andersen", "Beethoven", "Chaplin", "Dvorak"])
    _ = pl.next()  # Andersen
    _ = pl.next()  # Beethoven
    cur = pl.current()
    pl.move(-4, -2)  # move Andersen to index 2
    assert pl.tracks == ["Beethoven", "Chaplin", "Andersen", "Dvorak"]
    assert pl.current() == cur
    assert sorted(pl.order) == [0, 1, 2, 3]


def test_move_invalid_positions_and_empty():
    pl = Playlist(["Andersen"])
    with pytest.raises(IndexError):
        pl.move(0, 5)
    with pytest.raises(IndexError):
        pl.move(2, 0)
    pl_empty = Playlist()
    with pytest.raises(IndexError):
        pl_empty.move(0, 0)


# repeat mode

def test_set_repeat_variants():
    pl = Playlist(["Andersen"])
    pl.set_repeat("all")
    assert pl.repeat_mode == RepeatMode.ALL
    pl.set_repeat(RepeatMode.ONE)
    assert pl.repeat_mode == RepeatMode.ONE
    with pytest.raises(ValueError):
        pl.set_repeat("weird")
