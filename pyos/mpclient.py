"""
Provides the multiplayer client that handles interaction with the pyosserver.
"""

from dataclasses import dataclass
import socket
import ssl
import struct
from typing import List, Tuple, Union

from foolysh.tools import config
from loguru import logger

import util

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

REQ = [struct.pack('<B', i) for i in range(256)]
SUCCESS = REQ[1]
FAIL = REQ[0]
Result = Tuple[float, int, int]


class MPError(Exception):
    """Base class for exceptions in this module."""


class NotConnectedError(MPError):
    """
    Exception raised when information was requested but no connection could be
    established.
    """


class CouldNotLoginError(MPError):
    """
    Exception raised when information was requested that requires a login, but
    login failed.
    """


@dataclass
class Challenge:
    """Representation of a challenge."""
    challenge_id: int
    waiting: bool
    roundno: int
    rounds: int
    userid: int


@dataclass
class GameType:
    """Representation of a game type."""
    draw: int
    score: int


class MultiplayerClient:
    """Provides communication means with the pyosserver."""
    # pylint: disable=too-many-public-methods
    def __init__(self, cfg_file: str):
        self.cfg = config.Config(cfg_file)
        self._conn: ssl.SSLSocket = None

    def connect(self) -> bool:
        """Attempts to connect to the server."""
        ctx = ssl.create_default_context()
        server = self.cfg.get('mp', 'server')
        port = self.cfg.getint('mp', 'port')
        addrinfo = socket.getaddrinfo(server, port, proto=socket.IPPROTO_TCP)
        for addr in addrinfo:
            conn = ctx.wrap_socket(socket.socket(addr[0]),
                                   server_hostname=server)
            conn.settimeout(1)
            try:
                conn.connect((server, port))
            except socket.timeout:
                logger.warning('Unable to connect')
                return False
            except OSError:  # Most likely wrong protocol family
                continue
            else:
                self._conn = conn
                logger.info('Connection established')
                return True
        self._conn = None
        return False

    def close(self) -> None:
        """Close the connection."""
        if self._conn is None:
            return
        self._conn.close()
        self._conn = None

    def new_user(self, username: str, password: str) -> bool:
        """One time user setup to create an account."""
        self._verify_connected(need_login=False)
        self._conn.sendall(REQ[0] + f'{username}'.encode('utf8'))
        data = self._recv()
        if len(data) != util.HASHSIZE + 1:
            logger.warning(f'Got bad response "{data}"')
            return False
        logger.debug('Got temporary password, sending response')
        pwhash = util.generate_hash(password)
        self._conn.sendall(REQ[0] + pwhash)
        data = self._recv()
        if data != REQ[0] + SUCCESS:
            logger.warning('Request failed')
            return False
        logger.info('New account created successfully')
        self.cfg.set('mp', 'user', username)
        self.cfg.set('mp', 'password', util.encode_hash(pwhash))
        self.cfg.save()
        return True

    def login(self) -> bool:
        """Login with locally stored username/password."""
        self._verify_connected(need_login=False)
        self._conn.sendall(REQ[1])
        data = self._recv()
        if len(data) != util.HASHSIZE + 1:
            logger.warning(f'Got bad response "{data}"')
            return False
        self.cfg.reload()
        username = self.cfg.get('mp', 'user')
        if not username:
            logger.warning('No username set in config')
            return False
        username = util.generate_hash(username)
        password = util.parse_hash(self.cfg.get('mp', 'password'))
        password = util.generate_hash(password + data[1:])
        self._conn.sendall(REQ[1] + username + password)
        data = self._recv()
        if data != REQ[1] + SUCCESS:
            logger.warning('Unable to login')
            return False
        logger.info('Login successful')
        return True

    def friend_request(self, otheruser: str) -> bool:
        """Start a friend request."""
        self._verify_connected()
        req = REQ[2] + util.generate_hash(otheruser)
        self._conn.sendall(req)
        data = self._recv()
        if data != REQ[2] + SUCCESS:
            return False
        return True

    def pending_sent_friend_request(self, timestamp: int = 0) -> List[int]:
        """Retrieve pending sent friend requests."""
        self._verify_connected()
        self._conn.sendall(REQ[3] + util.encode_id(timestamp))
        data = self._recv()
        return self._userid_list(data)

    def get_friend_list(self, timestamp: int = 0) -> List[int]:
        """Retrieve friend list."""
        self._verify_connected()
        self._conn.sendall(REQ[4] + util.encode_id(timestamp))
        data = self._recv()
        return self._userid_list(data)

    def get_blocked_list(self, timestamp: int = 0) -> List[int]:
        """Retrieve blocked users list."""
        self._verify_connected()
        self._conn.sendall(REQ[5] + util.encode_id(timestamp))
        data = self._recv()
        return self._userid_list(data)

    def reply_friend_request(self, userid: int, decision: bool) -> bool:
        """Reply to a pending friend request."""
        self._verify_connected()
        req = REQ[6]
        req += util.encode_id(userid)
        req += REQ[0 if decision else 1]
        self._conn.sendall(req)
        data = self._recv()
        if data != REQ[6] + SUCCESS:
            return False
        return True

    def unblock_user(self, userid: int, decision: bool) -> bool:
        """Unblock a previously blocked user."""
        self._verify_connected()
        req = REQ[7]
        req += util.encode_id(userid)
        req += REQ[0 if decision else 1]
        self._conn.sendall(req)
        data = self._recv()
        if data != REQ[7] + SUCCESS:
            return False
        return True

    def remove_friend(self, userid: int) -> bool:
        """Remove a friend."""
        self._verify_connected()
        req = REQ[8]
        req += util.encode_id(userid)
        self._conn.sendall(req)
        data = self._recv()
        if data != REQ[8] + SUCCESS:
            return False
        return True

    def block_user(self, userid: int) -> bool:
        """Block a user."""
        self._verify_connected()
        req = REQ[9]
        req += util.encode_id(userid)
        self._conn.sendall(req)
        data = self._recv()
        if data != REQ[9] + SUCCESS:
            return False
        return True

    def set_draw_count_pref(self, pref: int) -> bool:
        """Set own draw count preference."""
        self._verify_connected()
        self._conn.sendall(REQ[10] + REQ[pref])
        data = self._recv()
        if data != REQ[10] + SUCCESS:
            return False
        return True

    def get_draw_count_pref(self, userid: int = 0) -> int:
        """Get a users draw count preference. Returns `4` if unsuccessful."""
        self._verify_connected()
        req = REQ[11]
        req += util.encode_id(userid)
        self._conn.sendall(req)
        data = self._recv()
        if len(data) != 2:
            return 4
        return data[1]

    def change_password(self, newpwd: str) -> bool:
        """Change the users password."""
        self._verify_connected()
        password = util.parse_hash(self.cfg.get('mp', 'password'))
        req = REQ[12] + password + util.generate_hash(newpwd)
        self._conn.sendall(req)
        data = self._recv()
        if data != REQ[12] + SUCCESS:
            return False
        pwhash = util.generate_hash(newpwd)
        self.cfg.set('mp', 'password', util.encode_hash(pwhash))
        self.cfg.save()
        return True

    def change_username(self, newname: str) -> bool:
        """Change the users name."""
        self._verify_connected()
        self._conn.sendall(REQ[13] + f'{newname}'.encode('utf8'))
        data = self._recv()
        if data != REQ[13] + SUCCESS:
            return False
        self.cfg.set('mp', 'user', newname)
        self.cfg.save()
        return True

    def get_username(self, userid: int) -> str:
        """Retrieve a username by userid."""
        ret = 'N/A'
        self._verify_connected()
        self._conn.sendall(REQ[14] + util.encode_id(userid))
        data = self._recv()
        if len(data) > 3:
            ret = data[1:].decode('utf8')
        return ret

    def pending_recv_friend_request(self, timestamp: int = 0) -> List[int]:
        """Retrieve pending received friend requests."""
        self._verify_connected()
        self._conn.sendall(REQ[15] + util.encode_id(timestamp))
        data = self._recv()
        return self._userid_list(data)

    def daily_best_score(self, draw: int, dayoffset: int) -> Result:
        """Retrieve best score for a daily deal."""
        self._verify_connected()
        req = REQ[64] + util.encode_daydeal(draw, dayoffset)
        self._conn.sendall(req)
        data = self._recv()
        if len(data) != 9:
            return 0.0, 0, 0
        return util.parse_result(data[1:])

    def leaderboard(self, offset: int) -> List[Tuple[int, int, int]]:
        """
        Retrieve up to 10 entries from the leaderboard where rank > `offset`.
        """
        self._verify_connected()
        req = REQ[65] + util.encode_id(offset)
        self._conn.sendall(req)
        data = self._recv()
        if len(data) <= 1:
            return []
        return util.parse_leaderboard(data[1:])

    def userranking(self) -> Tuple[int, int]:
        """Retrieve the users current rank and points in the leaderboard."""
        self._verify_connected()
        self._conn.sendall(REQ[66])
        data = self._recv()
        if len(data) != 9:
            return 0, 0
        try:
            return struct.unpack('<II', data[1:])
        except struct.error as err:
            logger.error(f'Unable to unpack data: {err}')
            return 0, 0

    def submit_daydeal_score(self, draw: int, dayoffset: int,
                             result: Result) -> bool:
        """Submit own daydeal score."""
        self._verify_connected()
        req = REQ[67] + util.encode_daydeal(draw, dayoffset)
        req += util.encode_result(result)
        self._conn.sendall(req)
        data = self._recv()
        if data != REQ[67] + SUCCESS:
            return False
        return True

    def start_challenge(self, userid: int, rounds: int) -> bool:
        """Start a new challenge."""
        self._verify_connected()
        req = REQ[128] + util.encode_id(userid) + struct.pack('<B', rounds)
        self._conn.sendall(req)
        data = self._recv()
        if data != REQ[128] + SUCCESS:
            return False
        return True

    def pending_challenge_req_in(self, timestamp: int = 0
                                 ) -> List[Tuple[int, int, int]]:
        """Retrieve pending incoming challenge requests."""
        self._verify_connected()
        self._conn.sendall(REQ[129] + util.encode_id(timestamp))
        data = self._recv()
        dlen = len(data) - 1
        if dlen % 9:
            return []
        ret = []
        for i in range(dlen // 9):
            start = i * 9 + 1
            try:
                ret.append(struct.unpack('<BII', data[start:start + 9]))
            except struct.error as err:
                logger.error(f'Unable to unpack data: {err}')
        return ret

    def pending_challenge_req_out(self, timestamp: int = 0
                                  ) -> List[Tuple[int, int, int]]:
        """Retrieve pending outgoing challenge requests."""
        self._verify_connected()
        self._conn.sendall(REQ[136] + util.encode_id(timestamp))
        data = self._recv()
        dlen = len(data) - 1
        if dlen % 9:
            return []
        ret = []
        for i in range(dlen // 9):
            start = i * 9 + 1
            try:
                ret.append(struct.unpack('<BII', data[start:start + 9]))
            except struct.error as err:
                logger.error(f'Unable to unpack data: {err}')
        return ret

    def active_challenges(self, timestamp: int = 0
                          ) -> List[Challenge]:
        """
        Retrieve active challenges.

        Returns:
            List of Tuple: challenge_id, waiting, roundno, rounds, userid
        """
        self._verify_connected()
        self._conn.sendall(REQ[130] + util.encode_id(timestamp))
        data = self._recv()
        dlen = len(data) - 1
        if dlen % 9:
            return []
        ret = []
        for i in range(dlen // 9):
            start = i * 9 + 1
            try:
                challenge = Challenge(
                    *util.parse_challenge_status(data[start:start + 9]))
            except ValueError as err:
                logger.error(f'Unable to unpack data: {err}')
                return []
            ret.append(challenge)
        return ret

    def challenge_round(self, challenge_id: int, roundno: int
                        ) -> Union[Tuple[GameType, Result, Result], None]:
        """Retrieve information about a challenge round."""
        self._verify_connected()
        req = REQ[131] + util.encode_id(challenge_id)
        try:
            req += struct.pack('<B', roundno)
        except struct.error as err:
            logger.error(f'Unable to pack data: {err}')
            return None
        self._conn.sendall(req)
        data = self._recv()
        if len(data) != 18:
            return None
        gamet = GameType(*util.parse_game_type(data[1:2]))
        resuser = util.parse_result(data[2:10])
        resother = util.parse_result(data[10:])
        return gamet, resuser, resother

    def accept_challenge(self, challenge_id: int, decision: bool,
                         gamet: GameType = None) -> int:
        """Accept or decline a challenge request."""
        self._verify_connected()
        req = REQ[132] + util.encode_accept(challenge_id, decision)
        req += util.encode_game_type(gamet.draw, gamet.score)
        self._conn.sendall(req)
        data = self._recv()
        if decision and len(data) == 5:
            try:
                seed, = struct.unpack('<i', data[1:])
            except struct.error as err:
                logger.error(f'Unable to unpack seed: {err}')
                return 0
            return seed
        if not decision and data.decode('utf8') == REQ[132] + SUCCESS:
            return 1
        return 0

    def submit_round_result(self, challenge_id: int, roundno: int,
                            result: Result) -> bool:
        """Submit the result of a challenge round."""
        self._verify_connected()
        req = REQ[133]
        try:
            req += struct.pack('<IB', challenge_id, roundno)
        except struct.error as err:
            logger.error(f'Unable to pack data: {err}')
            return False
        req += util.encode_result(result)
        self._conn.sendall(req)
        data = self._recv()
        if data != REQ[133] + SUCCESS:
            return False
        return True

    def new_round(self, challenge_id: int, gamet: GameType) -> int:
        """Start a new round in a challenge."""
        self._verify_connected()
        req = REQ[134] + util.encode_id(challenge_id)
        req += util.encode_game_type(gamet.draw, gamet.score)
        self._conn.sendall(req)
        data = self._recv()
        if len(data) != 5:
            return 0
        try:
            seed, = struct.unpack('<i', data[1:])
        except struct.error as err:
            logger.error(f'Unable to unpack seed: {err}')
            return 0
        return seed

    def challenge_result(self, challenge_id: int) -> Tuple[int, int]:
        """Retrieve a final result of a challenge."""
        res = -1, -1
        self._verify_connected()
        req = REQ[135] + util.encode_id(challenge_id)
        self._conn.sendall(req)
        data = self._recv()
        if len(data) == 2 and data != REQ[135] + FAIL:
            res = util.parse_challenge_result(data[1:])
        return res

    def get_round_seed(self, challenge_id: int, roundno: int) -> int:
        """Retrieve the game seed for a given challenge round."""
        res = 0
        self._verify_connected()
        req = REQ[137] + util.encode_id(challenge_id)
        try:
            req += struct.pack('<B', roundno)
        except struct.error as err:
            logger.error(f'Unable to pack roundno: {err}')
            return res
        self._conn.sendall(req)
        data = self._recv()
        if len(data) != 5:
            return res
        try:
            res, = struct.unpack('<i', data[1:])
        except struct.error as err:
            logger.error(f'Unable to unpack seed: {err}')
        return res

    def pending(self, timestamp: int = 0) -> List[int]:
        """Retrieve a list of pending information to be retrieved."""
        ret = []
        self._verify_connected()
        self._conn.sendall(REQ[192] + util.encode_id(timestamp))
        data = self._recv()
        if len(data) > 1 and data != REQ[192] + FAIL:
            ret = list(data[1:])
        return ret

    def ping_pong(self) -> bool:
        """Ping Pong mechanism to verify the connection is still alive."""
        self._verify_connected()
        req = REQ[255]
        self._conn.sendall(req)
        return self._recv() == req

    @staticmethod
    def _userid_list(data: bytes) -> List[int]:
        if len(data) < 5 or len(data[1:]) % 4:
            return []
        ret = []
        for i in range(len(data[1:]) // 4):
            start = i * 4
            ret.append(util.parse_id(data[start:start + 4]))
        return ret

    def _verify_connected(self, need_login: bool = True) -> None:
        if not self.connected:
            if not self.connect():
                raise NotConnectedError
            if not need_login:
                return
            if self.cfg.get('mp', 'user').strip() and self.login():
                return
            raise CouldNotLoginError

    def _recv(self):
        try:
            data = self._conn.recv(self.cfg.getint('mp', 'bufsize',
                                                   fallback=4096))
        except socket.timeout:
            self._conn.close()
            self._conn = None
            return b''
        if not data:
            self._conn.close()
            self._conn = None
        return data

    @property
    def connected(self) -> bool:
        """Returns whether the client is connected."""
        return self._conn is not None
