import warnings
from enum import Enum
from typing import Iterable, Optional, Union
import random


class RepeatMode(str, Enum):
    """Playlist repeat modes.

    Members:
        OFF: Disable repeating and playing stops after the last track.
        ALL: Loops the playlist.
        ONE: Repeats the current track indefinitely.

    Examples:
        >>> mode = RepeatMode.ALL
        >>> mode.value
        'all'
        >>> mode == "all"
        True
    """

    OFF = "off"
    ALL = "all"
    ONE = "one"


class Playlist:
    """Playlist class.

    Args:
        tracks: optional iterable of initial tracks in the playlist.

    Attributes:
        tracks (list[str]): list of tracks in original order.
        order (list[int]): current play order as indices for tracks.
        current_track (int): order index. -1 means that playing is not started.
        repeat_mode (RepeatMode): current repeat mode.
        shuffled (bool): whether shuffle mode is on.
        rng (random.Random): random generator used for shuffling.
    """

    def __init__(self, tracks: Optional[Iterable[str]] = None):
        self.tracks: list[str] = list(tracks) if tracks else []
        self.order: list[int] = list(range(len(self)))
        self.current_track: int = -1
        self.repeat_mode: RepeatMode = RepeatMode.OFF
        self.shuffled: bool = False
        self.rng: random.Random = random.Random()

    def __len__(self) -> int:
        """Returns the number of tracks in the playlist
        
        Examples:
            >>> p = Playlist(["track_1", "track_2", "track_3"])
            >>> len(p)
            3
            >>> Playlist().__len__()
            0
        """
        return len(self.tracks)
    
    def __iter__(self):
        """Iterate over tracks in the original playlist order.

        Examples:
            >>> p = Playlist(["track_1", "track_2", "track_3"])
            >>> list(iter(p))
            ['track_1', 'track_2', 'track_3']
            >>> [t for t in p]
            ['track_1', 'track_2', 'track_3']
        """
        return iter(self.tracks)
    
    def __getitem__(self, key):
        """Index or slice into the playlist in the original order.

        Args:
            key: int index (supports negatives) or slice.

        Returns:
            str for int index, or list[str] for slice.

        Raises:
            TypeError: if key is not int or slice.
            IndexError: if int index is out of range.

        Examples:
            >>> p = Playlist(["track_1", "track_2", "track_3"])
            >>> p[0]
            'track_1'
            >>> p[-1]
            'track_3'
            >>> p[0:2]
            ['track_1', 'track_2']
        """
        if isinstance(key, slice):
            return self.tracks[key]
        if isinstance(key, int):
            try:
                return self.tracks[key]
            except IndexError:
                raise IndexError("Position is out of range!")
        raise TypeError("Indices must be integers or slices!")

    def __contains__(self, track: str) -> bool:
        """Returns True if 'track' exists in the playlist or False
            in another case.

        Examples:
            >>> p = Playlist(["track_1", "track_2"])
            >>> "track_1" in p
            True
            >>> "track_3" in p
            False
        """
        return track in self.tracks

    def _norm_index(self, pos: int) -> int:
        """Normalizes a possibly negative index and checks correct bounds.

        Converts a negative index into a non-negative index relative to
        the original order (self.tracks) and validates that it is
        within [0, len(self) - 1].

        Args:
            pos: index in the original order (can be negative).

        Returns:
            int: normalized non-negative index in the range
            [0, len(self) - 1].

        Raises:
            IndexError: if the playlist is empty or the index is out of range.

        Examples:
            >>> p = Playlist(["track_1", "track_2", "track_3"])
            >>> p._norm_index(-1)
            2
            >>> p._norm_index(0)
            0
        """
        n = len(self)
        if n == 0:
            raise IndexError("Playlist is empty!")
        if not -n <= pos < n:
            raise IndexError("Position is out of range!")
        return pos if pos >= 0 else pos + n

    def _current_id(self) -> Optional[int]:
        """Returns current track id in self.tracks (or None if there's no current track).

        The method transforms self.current_track (order) into the corresponding track id
        (in original playlist). 

        Returns:
            Optional[int]: The current track id, or None if playing has not
            started or there is no current track.

        Examples:
            >>> p = Playlist(["track_1", "track_2", "track_3"])
            >>> p._current_id() is None
            True
            >>> _ = p.next()  # start playing
            >>> p._current_id() in {0, 1, 2}
            True
        """
        return self.order[self.current_track] if 0 <= self.current_track < len(self.order) else None
    
    @staticmethod
    def _remap_order(order: list[int], mapping: dict[int, int]) -> list[int]:
        """Builds a new play order by applying an id mapping.

        Applies the old_id -> new_id mapping to each element of order and
        returns the remapped list. Elements not present in mapping (e.g. a
        removed track) are skipped.

        Args:
            order (list[int]): current sequence of track ids in play order.
            mapping (dict[int, int]): mapping from old track ids to new track ids
                after operations like removal or reordering.

        Returns:
            list[int]: New sequence of track ids after remapping, excluding IDs not
            covered by mapping.

        Examples:
            >>> order = [2, 0, 3, 1]
            >>> mapping = {0: 0, 1: 1, 3: 2}
            >>> Playlist._remap_order(order, mapping)
            [0, 2, 1]
        """
        return [mapping[i] for i in order if i in mapping]


    def find(self, track: str) -> Optional[int]:
        """Finds the index of 'track' in the original order.

        Args:
            track: track name to search for.

        Returns:
            The original index if found or None otherwise.

        Examples:
            >>> p = Playlist(["track_1", "track_2", "track_3"])
            >>> p.find("track_2")
            1
            >>> p.find("track_5") is None
            True
        """
        for i, t in enumerate(self.tracks):
            if t == track:
                return i
        return None

    def add(self, track: str) -> None:
        """Appends a track to the playlist.

        If the track already exists in the playlist, emit a warning and
        do nothing. If shuffle is on, the new track is inserted at a random 
        position in the current order. 

        Args:
            track: track name to add.

        Returns:
            None

        Examples:
            >>> p = Playlist(["track_1"])
            >>> p.add("track_2")
            >>> p.tracks
            ['track_1', 'track_2']
        """
        idx = self.find(track)
        if idx is not None:
            warnings.warn(f"Track is already in playlist: {track!r}!")
            return

        self.tracks.append(track)
        new_id = len(self) - 1

        if self.shuffled and self.order:
            insert_pos = self.rng.randrange(len(self.order) + 1)
            self.order.insert(insert_pos, new_id)
            if 0 <= self.current_track < len(self.order):
                if insert_pos <= self.current_track:
                    self.current_track += 1
        else:
            self.order.append(new_id)

    def current(self) -> Optional[str]:
        """Returns the current track (or None if playing hasn't started).

        Examples:
            >>> p = Playlist(["track_1", "track_2"])
            >>> p.current() is None
            True
            >>> _ = p.next()
            >>> p.current() in {"track_1", "track_2"}
            True
        """
        if 0 <= self.current_track < len(self.order):
            return self.tracks[self.order[self.current_track]]
        return None

    def next(self) -> Optional[str]:
        """Goes to the next track according to the order.

        Returns:
            The next track name (or None if no next track and repeat is OFF).

        Examples:
            >>> p = Playlist(["track_1", "track_2"])
            >>> p.next() == "track_1"
            True
            >>> p.next() == "track_2"
            True
            >>> p.next() is None
            True
        """
        n = len(self.order)
        if n == 0:
            return None

        if self.repeat_mode == RepeatMode.ONE:
            if self.current_track == -1:
                self.current_track = 0
            return self.current()

        if self.current_track < n-1:
            self.current_track += 1
            return self.current()

        if self.repeat_mode == RepeatMode.ALL:
            self.current_track = 0
            return self.current()

        return None
    
    def previous(self) -> Optional[str]:
        """Goes to the previous track according to the current order.

        Returns:
            The previous track name (or None if no previous track and repeat is OFF).

        Examples:
            >>> p = Playlist(["track_1", "track_2"])
            >>> p.set_repeat("all")
            >>> p.previous()
            'track_2'
            >>> p.previous()
            'track_1'
            >>> p.set_repeat("off")
            >>> q = Playlist(["x"])
            >>> q.previous() is None
            True
        """
        n = len(self.order)
        if n == 0:
            return None

        if self.repeat_mode == RepeatMode.ONE:
            if self.current_track == -1:
                self.current_track = 0
            return self.current()

        if self.current_track > 0:
            self.current_track -= 1
            return self.current()

        if self.repeat_mode == RepeatMode.ALL:
            self.current_track = n - 1
            return self.current()

        return None

    def remove(self, pos: int) -> str:
        """Removes and returns a track by its original index.

        After removal, indices in 'order' are re-mapped. If the removed track
        was currently selected, the cursor stays at the same position so
        that the next track (shifted into this position) is picked up.

        Args:
            pos: index in the original order (supports negative indices).

        Returns:
            The removed track name.

        Raises:
            IndexError: if the playlist is empty or position is out of range.

        Examples:
            >>> p = Playlist(["track_1", "track_2", "track_3"])
            >>> _ = p.next()  # start playback at 'track_1'
            >>> p.remove(1)   # remove 'track_2'
            'track_2'
            >>> p.tracks
            ['track_1', 'track_3']
            >>> p.remove(-1)    # remove last
            'track_3'
            >>> p.tracks
            ['track_1']
        """
        pos = self._norm_index(pos)

        current_id = self._current_id()
        removed = self.tracks.pop(pos)

        # build mapping old_id -> new_id
        mapping = {}
        for old in range(len(self) + 1):
            if old == pos:
                continue
            new = old - 1 if old > pos else old
            mapping[old] = new

        self.order = self._remap_order(self.order, mapping)

        if not self.order:
            self.current_track = -1
            return removed

        if current_id is None:
            self.current_track = -1
        elif current_id == pos:
            if self.current_track >= len(self.order):
                self.current_track = len(self.order) - 1
        else:
            new_id = current_id - 1 if current_id > pos else current_id
            self.current_track = self.order.index(new_id)

        return removed

    def set_repeat(self, mode: Union[RepeatMode, str]) -> None:
        """Sets the repeat mode.

        Args:
            mode: 'off' | 'all' | 'one' (or RepeatMode).

        Raises:
            ValueError: if mode is invalid.

        Examples:
            >>> p = Playlist(["track_1"])
            >>> p.set_repeat("one")
            >>> _ = p.next()  # start
            >>> p.next() == "track_1"
            True
            >>> p.set_repeat(RepeatMode.ALL)
            >>> p.repeat_mode == RepeatMode.ALL
            True
        """
        if isinstance(mode, str):
            try:
                mode = RepeatMode(mode)
            except ValueError:
                raise ValueError(f"Unknown repeat mode: {mode!r}! Allowed: off|all|one.")
        self.repeat_mode = mode

    def shuffle(self, seed: Optional[int] = None) -> None:
        """Enables shuffle mode.

        Behavior:
            If playback has started, the current track stays at the same position.
            If playback hasn't started (current_track == -1), the order is just shuffled.

        Args:
            seed: optional random seed to make shuffling deterministic.
            
        Examples:
            >>> p = Playlist(["a", "b", "c", "d"])
            >>> p.shuffle(seed=42)
            >>> sorted(p.order) == [0, 1, 2, 3]
            True
            >>> _ = p.next()
            >>> cur = p.current()
            >>> p.shuffle(seed=42)  # current track stays at same position
            >>> p.current() == cur
            True
        """
        if seed is not None:
            self.rng.seed(seed)

        n = len(self.order)
        if n <= 1:
            self.shuffled = True
            return

        cur_id = self._current_id()
        ids = list(range(n))
        if cur_id is None:
            self.rng.shuffle(ids)
            self.order = ids
        else:
            ids.remove(cur_id)
            self.rng.shuffle(ids)
            self.order = ids[:self.current_track] + [cur_id] + ids[self.current_track:]

        self.shuffled = True

    def unshuffle(self) -> None:
        """Returns to a linear play order and saving current track.

        Examples:
            >>> p = Playlist(["a", "b", "c"])
            >>> p.shuffle(seed=0)
            >>> _ = p.next()
            >>> cur = p.current()
            >>> p.unshuffle()
            >>> p.order == [0, 1, 2]
            True
            >>> p.current() == cur
            True
        """
        if len(self) == 0:
            self.order = []
            self.current_track = -1
            self.shuffled = False
            return

        cur_id = self._current_id()
        self.order = list(range(len(self)))
        self.shuffled = False

        if cur_id is None:
            self.current_track = -1
        else:
            self.current_track = self.order.index(cur_id)

    def move(self, src: int, dst: int) -> None:
        """Moves a track in the original order without changing the relative order in 'order'.

        The mapping of original indices is updated, and 'order' is remapped accordingly.
        The 'current_track' pointer (as an index into 'order') remains valid.

        Args:
            src: source index in original order (supports negative indices).
            dst: destination index in original order (supports negative indices).

        Raises:
            IndexError: if positions are out of range.

        Examples:
            >>> p = Playlist(["a", "b", "c", "d"])
            >>> p.order
            [0, 1, 2, 3]
            >>> p.move(0, 2)   # original becomes ['b', 'c', 'a', 'd']
            >>> p.tracks
            ['b', 'c', 'a', 'd']
            >>> sorted(p.order) == [0, 1, 2, 3]
            True
            >>> p.order_view()
            ['a', 'b', 'c', 'd']
        """
        if len(self) == 0:
            raise IndexError("Playlist is empty!")
        src = self._norm_index(src)
        dst = self._norm_index(dst)
        if src == dst:
            return

        track = self.tracks.pop(src)
        self.tracks.insert(dst, track)

        # the order of tracks should stay unchanged
        n = len(self)
        ids = list(range(n))
        x = ids.pop(src)
        ids.insert(dst, x)
        remap = {old_id: new_idx for new_idx, old_id in enumerate(ids)}
        self.order = self._remap_order(self.order, remap)

    def order_view(self) -> list[str]:
        """Returns the list of tracks in the current play order

        Examples:
            >>> p = Playlist(["track_1", "track_2", "track_3"])
            >>> p.order_view()
            ['track_1', 'track_2', 'track_3']
            >>> p.shuffle(seed=0)
            >>> p.order_view()
            ['track_1', 'track_3', 'track_2']
        """
        return [self.tracks[i] for i in self.order]