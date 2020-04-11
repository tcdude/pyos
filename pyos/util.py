"""
Utility functions for multiplayer.
"""

import datetime
import hashlib
import struct
from typing import List, Tuple, Union

__author__ = 'Tiziano Bettio'
__copyright__ = """
Copyright (c) 2020 Tiziano Bettio

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

__license__ = 'MIT'
__version__ = '0.3'

HASHFUNC = hashlib.sha3_384
HASHSIZE = HASHFUNC().digest_size
STARTDT = datetime.datetime(2020, 1, 1)


def generate_hash(value: Union[str, bytes]) -> bytes:
    """Returns a hash of the provided value."""
    if isinstance(value, str):
        value = value.encode('utf8')
    return HASHFUNC(value).digest()


def timestamp():
    """Returns the number of seconds passed since STARTDT."""
    return int((datetime.datetime.utcnow() - STARTDT).total_seconds + 0.5)


def encode_id(idx: int) -> bytes:
    """Returns an id (unsigned int) as bytes."""
    try:
        ret = struct.pack('<I', idx)
    except struct.error as err:
        raise ValueError(f'Unable to pack data: {err}')
    return ret


def parse_id(data: bytes) -> int:
    """Returns an id from bytes."""
    try:
        ret, = struct.unpack('<I', data)
    except struct.error as err:
        raise ValueError(f'Unable to unpack data: {err}')
    return ret


def parse_game_type(game_type: bytes) -> Tuple[int, int]:
    """Parse an encoded game_type and return draw count, score type."""
    try:
        val, = struct.unpack('<B', game_type)
    except struct.error as err:
        raise ValueError(f'Unable to unpack data: {err}')
    score = val >> 4
    draw = val - (score << 4)
    return draw, score


def encode_game_type(draw: int, score: int) -> bytes:
    """Parse an encoded game_type and return draw count, score type."""
    val = draw + (score << 4)
    try:
        ret = struct.pack('<B', val)
    except struct.error as err:
        raise ValueError(f'Unable to pack data: {err}')
    return ret


def parse_result(result: bytes) -> Tuple[float, int, int]:
    """Parse an encoded result and return duration, points and moves."""
    try:
        duration, points, moves = struct.unpack('<fHH', result)
    except struct.error as err:
        raise ValueError(f'Unable to unpack data: {err}')
    return duration, points, moves


def encode_result(result: Tuple[float, int, int]) -> bytes:
    """Encodes a result to bytes."""
    try:
        ret = struct.pack('<fHH', *result)
    except struct.error as err:
        raise ValueError(f'Unable to pack data: {err}')
    return ret


def encode_daydeal(draw_count: int, dayoffset: int) -> bytes:
    """Encode daydeal information to bytes."""
    try:
        ret = struct.pack('<BH', draw_count, dayoffset)
    except struct.error as err:
        raise ValueError(f'Unable to pack data: {err}')
    return ret


def encode_leaderboard(rank: int, points: int, userid: int) -> bytes:
    """Encodes a leaderboard entry to bytes."""
    try:
        ret = struct.pack('<III', rank, points, userid)
    except struct.error as err:
        raise ValueError(f'Unable to pack data: {err}')
    return ret


def parse_leaderboard(data: bytes) -> List[Tuple[int, int, int]]:
    """Parse leaderboard reply to a list."""
    dlen = len(data)
    if dlen % 12:
        return []
    ret = []
    for i in range(dlen // 12):
        start = i * 12
        try:
            ret.append(struct.unpack('<III', data[start: start + 12]))
        except struct.error as err:
            raise ValueError(f'Unable to unpack data: {err}')
    return ret


def encode_challenge_req(rounds: int, challenge_id: int) -> bytes:
    """Encodes challenge request data to bytes."""
    try:
        ret = struct.pack('<BI', rounds, challenge_id)
    except struct.error as err:
        raise ValueError(f'Unable to pack data: {err}')
    return ret


def parse_challenge_status(data: bytes) -> Tuple[int, bool, int, int, int]:
    """Parse challenge status from bytes."""
    try:
        challenge_id, status, user_id = struct.unpack('<IBI', data)
    except struct.error as err:
        raise ValueError(f'Unable to unpack data: {err}')
    rounds = status >> 4
    status -= rounds << 4
    roundno = status >> 1
    waiting = status - (roundno << 1) > 0
    return challenge_id, waiting, roundno, rounds, user_id


def encode_challenge_status(challenge_id: int, waiting: bool, roundno: int,
                            rounds: int) -> bytes:
    """Encodes challenge status data to bytes."""
    enc = 1 if waiting else 0
    enc += roundno << 1
    enc += rounds << 4
    try:
        ret = struct.pack('<IB', challenge_id, enc)
    except struct.error as err:
        raise ValueError(f'Unable to pack data: {err}')
    return ret


def parse_challenge_round(data: bytes) -> Tuple[int, int]:
    """Parses a challenge round request."""
    try:
        challenge_id, roundno = struct.unpack('<IB', data)
    except struct.error as err:
        raise ValueError(f'Unable to unpack data: {err}')
    return challenge_id, roundno


def encode_challenge_round(draw: int, chtype: int,
                           res_user: Tuple[float, int, int],
                           res_other: Tuple[float, int, int]) -> bytes:
    """Encodes challenge round data to bytes."""
    first = draw + (chtype << 4)
    try:
        game_type = struct.pack('<B', first)
    except struct.error as err:
        raise ValueError(f'Unable to pack data: {err}')
    return game_type + encode_result(res_user) + encode_result(res_other)


def parse_accept(data: bytes) -> Tuple[int, bool, bytes]:
    """Parse challenge accept request."""
    try:
        challenge_id, accept = struct.unpack('<I?', data[:5])
    except struct.error as err:
        raise ValueError(f'Unable to unpack data: {err}')
    if accept and len(data) == 6:
        return challenge_id, accept, data[5:]
    return challenge_id, False, b''


def encode_accept(challenge_id: int, decision: bool) -> bytes:
    """Encode challenge accept request."""
    try:
        ret = struct.pack('<I?', challenge_id, decision)
    except struct.error as err:
        raise ValueError(f'Unable to pack data: {err}')
    return ret


def parse_challenge_result(data: bytes) -> Tuple[int, int]:
    """Parse challenge result."""
    try:
        val, = struct.unpack('<B', data)
    except struct.error as err:
        raise ValueError(f'Unable to unpack data: {err}')
    other = val >> 4
    user = val - (other << 4)
    return user, other


def encode_challenge_result(result: Tuple[int, int]) -> bytes:
    """Encode challenge result to bytes."""
    try:
        ret = struct.pack('<B', result[0] + (result[1] << 4))
    except struct.error as err:
        raise ValueError(f'Unable to pack data: {err}')
    return ret


def parse_hash(data: str) -> bytes:
    """Parse hash string to bytes digest."""
    values = data.split(',')
    if len(values) != HASHSIZE // 4:
        raise ValueError('Wrong length of csv list')
    try:
        ret = struct.pack('<' + 'I' * (HASHSIZE // 4), *values)
    except struct.error as err:
        raise ValueError(f'Unable to pack data: {err}')
    return ret


def encode_hash(data: bytes) -> str:
    """Encode hash byte-string to csv string."""
    try:
        ret = struct.unpack('<' + 'I' * (HASHSIZE // 4), data)
    except struct.error as err:
        raise ValueError(f'Unable to unpack data: {err}')
    return ','.join([str(i) for i in ret])
