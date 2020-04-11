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

SUCCESS = chr(1)
FAIL = chr(0)
REQ = {i: chr(i) for i in range(256)}
Result = Tuple[float, int, int]


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
    def __init__(self, cfg: config.Config):
        self.cfg = cfg
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
            conn.settimeout(5)
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
        if not self._verify_connected():
            return False
        self._conn.sendall(f'{REQ[0]}{username}'.encode('utf8'))
        data = self._recv()
        if len(data) != util.HASHSIZE + 1:
            return False
        pwhash = util.generate_hash(password)
        self._conn.sendall(REQ[0].encode('utf8') + pwhash)
        data = self._recv()
        if data.decode('utf8') != REQ[0] + SUCCESS:
            return False
        self.cfg.set('mp', 'user', username)
        self.cfg.set('mp', 'password', util.encode_hash(pwhash))
        self.cfg.save()
        return True

    def login(self) -> bool:
        """Login with locally stored username/password."""
        if not self._verify_connected():
            return False
        self._conn.sendall(REQ[1].encode('utf8'))
        data = self._recv()
        if len(data) != util.HASHSIZE + 1:
            return False
        username = self.cfg.get('mp', 'user')
        if not username:
            return False
        username = util.generate_hash(username)
        password = util.parse_hash(self.cfg.get('mp', 'password'))
        password = util.generate_hash(password + data[1:])
        self._conn.sendall(REQ[1].encode('utf8') + username + password)
        data = self._recv()
        if data.decode('utf8') != REQ[1] + SUCCESS:
            return False
        return True

    def friend_request(self, otheruser: str) -> bool:
        """Start a friend request."""
        if not self._verify_connected():
            return False
        req = REQ[2].encode('utf8') + util.generate_hash(otheruser)
        self._conn.sendall(req)
        data = self._recv()
        if data.decode('utf8') != REQ[2] + SUCCESS:
            return False
        return True

    def pending_sent_friend_request(self, timestamp: int = 0) -> List[int]:
        """Retrieve pending sent friend requests."""
        if not self._verify_connected():
            return []
        self._conn.sendall(REQ[3].encode('utf8') + util.encode_id(timestamp))
        data = self._recv()
        return self._userid_list(data)

    def get_friend_list(self, timestamp: int = 0) -> List[int]:
        """Retrieve friend list."""
        if not self._verify_connected():
            return []
        self._conn.sendall(REQ[4].encode('utf8') + util.encode_id(timestamp))
        data = self._recv()
        return self._userid_list(data)

    def get_blocked_list(self, timestamp: int = 0) -> List[int]:
        """Retrieve blocked users list."""
        if not self._verify_connected():
            return []
        self._conn.sendall(REQ[5].encode('utf8') + util.encode_id(timestamp))
        data = self._recv()
        return self._userid_list(data)

    def reply_friend_request(self, userid: int, decision: bool) -> bool:
        """Reply to a pending friend request."""
        if not self._verify_connected():
            return False
        req = REQ[6].encode('utf8')
        req += util.encode_id(userid)
        req += chr(0 if decision else 1).encode('utf8')
        self._conn.sendall(req)
        data = self._recv()
        if data.decode('utf8') != REQ[6] + SUCCESS:
            return False
        return True

    def unblock_user(self, userid: int, decision: bool) -> bool:
        """Unblock a previously blocked user."""
        if not self._verify_connected():
            return False
        req = REQ[7].encode('utf8')
        req += util.encode_id(userid)
        req += chr(0 if decision else 1).encode('utf8')
        self._conn.sendall(req)
        data = self._recv()
        if data.decode('utf8') != REQ[7] + SUCCESS:
            return False
        return True

    def remove_friend(self, userid: int) -> bool:
        """Remove a friend."""
        if not self._verify_connected():
            return False
        req = REQ[8].encode('utf8')
        req += util.encode_id(userid)
        self._conn.sendall(req)
        data = self._recv()
        if data.decode('utf8') != REQ[8] + SUCCESS:
            return False
        return True

    def block_user(self, userid: int) -> bool:
        """Block a user."""
        if not self._verify_connected():
            return False
        req = REQ[9].encode('utf8')
        req += util.encode_id(userid)
        self._conn.sendall(req)
        data = self._recv()
        if data.decode('utf8') != REQ[9] + SUCCESS:
            return False
        return True

    def set_draw_count_pref(self, pref: int) -> bool:
        """Set own draw count preference."""
        if not self._verify_connected():
            return False
        self._conn.sendall(REQ[10].encode('utf8') + struct.pack('<B', pref))
        data = self._recv()
        if data.decode('utf8') != REQ[10] + SUCCESS:
            return False
        return True

    def get_draw_count_pref(self, userid: int = 0) -> int:
        """Get a users draw count preference. Returns `4` if unsuccessful."""
        if not self._verify_connected():
            return 4
        req = REQ[11].encode('utf8')
        req += util.encode_id(userid)
        self._conn.sendall(req)
        data = self._recv()
        if len(data) != 2:
            return 4
        return data[1]

    def change_password(self, newpwd: str) -> bool:
        """Change the users password."""
        if not self._verify_connected():
            return False
        password = util.parse_hash(self.cfg.get('mp', 'password'))
        req = REQ[12].encode('utf8') + password + util.generate_hash(newpwd)
        self._conn.sendall(req)
        data = self._recv()
        if data.decode('utf8') != REQ[12] + SUCCESS:
            return False
        return True

    def change_username(self, newname: str) -> bool:
        """Change the users name."""
        if not self._verify_connected():
            return False
        self._conn.sendall(f'{REQ[13]}{newname}'.encode('utf8'))
        data = self._recv()
        if data.decode('utf8') != REQ[13] + SUCCESS:
            return False
        return True

    def get_username(self, userid: int) -> str:
        """Retrieve a username by userid."""
        ret = 'N/A'
        if not self._verify_connected():
            return ret
        self._conn.sendall(REQ[14].encode('utf8') + util.encode_id(userid))
        data = self._recv()
        if len(data) > 3:
            ret = data[1:].decode('utf8')
        return ret

    def pending_recv_friend_request(self, timestamp: int = 0) -> List[int]:
        """Retrieve pending received friend requests."""
        if not self._verify_connected():
            return []
        self._conn.sendall(REQ[15].encode('utf8') + util.encode_id(timestamp))
        data = self._recv()
        return self._userid_list(data)

    def daily_best_score(self, draw: int, dayoffset: int) -> Result:
        """Retrieve best score for a daily deal."""
        if not self._verify_connected():
            return 0.0, 0, 0
        req = REQ[64].encode('utf8') + util.encode_daydeal(draw, dayoffset)
        self._conn.sendall(req)
        data = self._recv()
        if len(data) != 5:
            return 0.0, 0, 0
        return util.parse_result(data[1:])

    def leaderboard(self, offset: int) -> List[Tuple[int, int, int]]:
        """
        Retrieve up to 10 entries from the leaderboard where rank > `offset`.
        """
        if not self._verify_connected():
            return []
        req = REQ[65].encode('utf8') + util.encode_id(offset)
        self._conn.sendall(req)
        data = self._recv()
        if len(data) <= 1:
            return []
        return util.parse_leaderboard(data[1:])

    def userranking(self) -> Tuple[int, int]:
        """Retrieve the users current rank and points in the leaderboard."""
        if not self._verify_connected():
            return 0, 0
        self._conn.sendall(REQ[66].encode('utf8'))
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
        if not self._verify_connected():
            return False
        req = REQ[67] + util.encode_daydeal(draw, dayoffset)
        req += util.encode_result(result)
        self._conn.sendall(req)
        data = self._recv()
        if data.decode('utf8') != REQ[67] + SUCCESS:
            return False
        return True

    def start_challenge(self, userid: int, rounds: int) -> bool:
        """Start a new challenge."""
        if not self._verify_connected():
            return False
        req = REQ[128].encode('utf8') + util.encode_id(userid)
        req += struct.pack('<B', rounds)
        self._conn.sendall(req)
        data = self._recv()
        if data.decode('utf8') != REQ[128] + SUCCESS:
            return False
        return True

    def pending_challenge_req_in(self, timestamp: int = 0
                                 ) -> List[Tuple[int, int, int]]:
        """Retrieve pending incoming challenge requests."""
        if not self._verify_connected():
            return []
        self._conn.sendall(REQ[129].encode('utf8') + util.encode_id(timestamp))
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
        if not self._verify_connected():
            return []
        self._conn.sendall(REQ[136].encode('utf8') + util.encode_id(timestamp))
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
        if not self._verify_connected():
            return []
        self._conn.sendall(REQ[130].encode('utf8') + util.encode_id(timestamp))
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
        if not self._verify_connected():
            return None
        req = REQ[131].encode('utf8') + util.encode_id(challenge_id)
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
        if not self._verify_connected():
            return 0
        req = REQ[132].encode('utf8')
        req += util.encode_accept(challenge_id, decision)
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
        if not self._verify_connected():
            return False
        req = REQ[133].encode('utf8')
        try:
            req += struct.pack('<IB', challenge_id, roundno)
        except struct.error as err:
            logger.error(f'Unable to pack data: {err}')
            return False
        req += util.encode_result(result)
        self._conn.sendall(req)
        data = self._recv()
        if data.decode('utf8') != REQ[133] + SUCCESS:
            return False
        return True

    def new_round(self, challenge_id: int, gamet: GameType) -> int:
        """Start a new round in a challenge."""
        if not self._verify_connected():
            return 0
        req = REQ[134].encode('utf8') + util.encode_id(challenge_id)
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
        if not self._verify_connected():
            return res
        req = REQ[135].encode('utf8') + util.encode_id(challenge_id)
        self._conn.sendall(req)
        data = self._recv()
        if len(data) == 2 and data.decode('utf8') != REQ[135] + FAIL:
            res = util.parse_challenge_result(data[1:])
        return res

    def pending(self, timestamp: int = 0) -> List[int]:
        """Retrieve a list of pending information to be retrieved."""
        ret = []
        if not self._verify_connected():
            return ret
        self._conn.sendall(REQ[192].encode('utf8') + util.encode_id(timestamp))
        data = self._recv()
        if len(data) > 1 and data.decode('utf8') != REQ[192] + FAIL:
            ret = list(data[1:])
        return ret

    def ping_pong(self) -> bool:
        """Ping Pong mechanism to verify the connection is still alive."""
        if not self._verify_connected():
            return False
        req = REQ[255].encode('utf8')
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

    def _verify_connected(self) -> bool:
        if not self.connected:
            if not self.connect():
                return False
            if self.cfg.get('mp', 'user').strip():
                return self.login()
        return True

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