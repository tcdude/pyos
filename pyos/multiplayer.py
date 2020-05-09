"""
Service that handles communication with the pyosserver and the app thread.
"""

import datetime
import os
import socket
import struct
import sys
from typing import Callable, Dict, List, Tuple

from foolysh.tools import config
from loguru import logger

import common
import mpclient
import mpdb
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

_BYTES = [struct.pack('<B', i) for i in range(256)]
SEP = chr(0) * 3
SUCCESS = _BYTES[0]
FAILURE = _BYTES[1]
ILLEGAL_REQUEST = _BYTES[2]
WRONG_FORMAT = _BYTES[3]
NO_CONNECTION = _BYTES[4]
NOT_LOGGED_IN = _BYTES[5]


class Multiplayer:
    """Multiplayer service."""
    def __init__(self, cfg_file: str) -> None:
        self.cfg = config.Config(cfg_file)
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.mpc = mpclient.MultiplayerClient(cfg_file)
        self.mpdbh = mpdb.MPDBHandler(common.MPDATAFILE)
        self._login = False
        self._first_sync = True
        self._handler_methods: Dict[int, Callable] = {
            0: self._new_account, 1: self._change_username,
            2: self._change_password, 3: self._sync_relations,
            4: self._reply_friend_request, 5: self._unblock_user,
            6: self._block_user, 7: self._remove_friend,
            8: self._set_draw_count_pref,
            9: self._update_daily_deal_best_scores,
            10: self._update_challenge_leaderboard,
            11: self._update_user_ranking, 12: self._submit_ddscore,
            13: self._start_challenge, 14: self._sync_challenges,
            15: self._submit_challenge_round_result,
            16: self._friend_request,
            17: self._challenge_stats,
            18: self._update_single_user,
            19: self._reject_challenge,
            20: self._accept_challenge}
        logger.debug('Multiplayer initialized')

    def start(self):
        """Start listening."""
        uds = self.cfg.get('mp', 'uds')
        try:
            os.unlink(uds)
        except OSError:
            if os.path.exists(uds):
                raise
        logger.debug('Start listening')
        self.sock.bind(uds)
        self.sock.listen()
        while True:
            conn, _ = self.sock.accept()
            logger.debug('New connection')
            if not self.handle(conn):
                break
            conn.close()
        logger.debug('Stopping service')
        self.sock.close()
        try:
            os.unlink(uds)
        except OSError:
            pass
        sys.exit(0)

    def handle(self, conn) -> bool:
        """Handle a request and return whether to keep listening."""
        data = conn.recv(self.cfg.getint('mp', 'bufsize', fallback=4096))
        if not data:
            logger.debug('No data')
            return True  # Client side probably disconnected
        req = data[0]
        if req == 255:  # Stop service
            logger.debug('Received stop request')
            conn.settimeout(1)
            try:
                conn.sendall(SUCCESS)
            except socket.timeout:
                logger.error('Unable to confirm stop request.')
            conn.close()
            return False
        if req == 254:  # NOP
            logger.debug('NOP')
            conn.sendall(SUCCESS)
            return True
        if req in self._handler_methods:
            logger.debug(f'Valid request {req}')
            if not self.mpc.connected and not self.mpc.connect():
                conn.sendall(NO_CONNECTION)
            else:
                conn.sendall(self._handler_methods[req](data[1:]))
        else:
            logger.warning(f'Invalid request {req}')
            conn.sendall(ILLEGAL_REQUEST)
        return True

    def _new_account(self, data: bytes) -> bytes:
        try:
            username, password = data.decode('utf8').split(SEP, 1)
        except ValueError:
            return WRONG_FORMAT
        if self.mpc.new_user(username, password):
            logger.debug('New Account request was successful')
            return SUCCESS
        logger.warning('New Account request failed')
        return FAILURE

    def _change_username(self, data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        username = data.decode('utf8')
        if self.mpc.change_username(username):
            return SUCCESS
        return FAILURE

    def _change_password(self, data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        password = data.decode('utf8')
        if self.mpc.change_password(password):
            return SUCCESS
        return FAILURE

    def _sync_relations(self, unused_data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        return self._sync_local_database()

    def _reply_friend_request(self, data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        try:
            userid, decision = data.decode('utf8').split(SEP, 1)
            userid, decision = int(userid), int(decision) > 0
        except (ValueError, TypeError):
            return WRONG_FORMAT
        try:
            self.mpc.reply_friend_request(userid, decision)
        except mpclient.NotConnectedError:
            return NO_CONNECTION
        except mpclient.CouldNotLoginError:
            return NOT_LOGGED_IN
        return SUCCESS

    def _unblock_user(self, data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        try:
            userid, decision = data.decode('utf8').split(SEP, 1)
            userid, decision = int(userid), ord(decision) > 0
        except (ValueError, TypeError):
            return WRONG_FORMAT
        try:
            self.mpc.unblock_user(userid, decision)
        except mpclient.NotConnectedError:
            return NO_CONNECTION
        except mpclient.CouldNotLoginError:
            return NOT_LOGGED_IN
        return SUCCESS

    def _block_user(self, data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        try:
            userid = int(data.decode('utf8'))
        except ValueError:
            return WRONG_FORMAT
        try:
            self.mpc.block_user(userid)
        except mpclient.NotConnectedError:
            return NO_CONNECTION
        except mpclient.CouldNotLoginError:
            return NOT_LOGGED_IN
        return SUCCESS

    def _remove_friend(self, data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        try:
            userid = int(data.decode('utf8'))
        except ValueError:
            return WRONG_FORMAT
        try:
            self.mpc.remove_friend(userid)
        except mpclient.NotConnectedError:
            return NO_CONNECTION
        except mpclient.CouldNotLoginError:
            return NOT_LOGGED_IN
        return SUCCESS

    def _set_draw_count_pref(self, data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        try:
            pref = int(data.decode('utf8'))
        except ValueError:
            return WRONG_FORMAT
        try:
            self.mpc.set_draw_count_pref(pref)
        except mpclient.NotConnectedError:
            return NO_CONNECTION
        except mpclient.CouldNotLoginError:
            return NOT_LOGGED_IN
        self.mpdbh.draw_count_preference = pref
        return SUCCESS

    def _update_daily_deal_best_scores(self, unused_data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        today = datetime.datetime.utcnow()
        start_i = today - common.START_DATE - datetime.timedelta(days=9)
        for i in range(10):
            for k in (1, 3):
                try:
                    res = self.mpc.daily_best_score(k, start_i + i)
                except mpclient.NotConnectedError:
                    return NO_CONNECTION
                except mpclient.CouldNotLoginError:
                    return NOT_LOGGED_IN
                if sum(res) == 0:
                    return FAILURE
                self.mpdbh.update_dd_score(k, start_i + i, res)
        return SUCCESS

    def _update_challenge_leaderboard(self, data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        try:
            start, end = data.decode('utf8').split(SEP, 1)
            start, end = int(start), int(end)
        except ValueError:
            return WRONG_FORMAT
        i = start
        while i < end:
            try:
                res = self.mpc.leaderboard(i)
            except mpclient.NotConnectedError:
                return NO_CONNECTION
            except mpclient.CouldNotLoginError:
                return NOT_LOGGED_IN
            i += len(res)
            if res:
                ret = self._update_lb_entries(res)
                if ret != SUCCESS:
                    return ret
            else:
                break
        return SUCCESS

    def _update_lb_entries(self, res: List[Tuple[int, int, int]]) -> bytes:
        for i in res:
            username = self.mpdbh.get_username(i[2])
            if not username:
                try:
                    self.mpc.get_username(i[2])
                except mpclient.NotConnectedError:
                    return NO_CONNECTION
                except mpclient.CouldNotLoginError:
                    return NOT_LOGGED_IN
            self.mpdbh.update_leaderboard(i[0], i[1], username)
        return SUCCESS

    def _update_user_ranking(self, unused_data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        try:
            rank, points = self.mpc.userranking()
        except mpclient.NotConnectedError:
            return NO_CONNECTION
        except mpclient.CouldNotLoginError:
            return NOT_LOGGED_IN
        self.mpdbh.update_user_ranking(rank, points)
        return SUCCESS

    def _submit_ddscore(self, data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        try:
            draw, dayoffset = data[:-8].decode('utf8').split(SEP, 1)
            draw, dayoffset = int(draw), int(dayoffset)
            result = util.parse_result(data[-8:])
        except ValueError:
            return WRONG_FORMAT
        try:
            if not self.mpc.submit_daydeal_score(draw, dayoffset, result):
                return FAILURE
        except mpclient.NotConnectedError:
            return NO_CONNECTION
        except mpclient.CouldNotLoginError:
            return NOT_LOGGED_IN
        return SUCCESS

    def _start_challenge(self, data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        try:
            userid, rounds = data.decode('utf8').split(SEP, 1)
            userid, rounds = int(userid), int(rounds)
        except ValueError:
            return WRONG_FORMAT
        try:
            if not self.mpc.start_challenge(userid, rounds):
                return FAILURE
        except mpclient.NotConnectedError:
            return NO_CONNECTION
        except mpclient.CouldNotLoginError:
            return NOT_LOGGED_IN
        return SUCCESS

    def _sync_challenges(self, unused_data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        return self._sync_local_database()

    def _submit_challenge_round_result(self, data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        try:
            challenge_id, roundno = data[:-8].decode('utf8').split(SEP, 1)
            challenge_id, roundno = int(challenge_id), int(roundno)
            result = util.parse_result(data[-8:])
        except ValueError:
            return WRONG_FORMAT
        try:
            if not self.mpc.submit_round_result(challenge_id, roundno, result):
                return FAILURE
        except mpclient.NotConnectedError:
            return NO_CONNECTION
        except mpclient.CouldNotLoginError:
            return NOT_LOGGED_IN
        return SUCCESS

    def _friend_request(self, data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        username = data.decode('utf8')
        if self.mpc.friend_request(username):
            return SUCCESS
        return FAILURE

    def _challenge_stats(self, data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        try:
            otherid = int(data.decode('utf8'))
        except ValueError:
            return WRONG_FORMAT
        won, lost, draw = self.mpc.challenge_stats(otherid)
        if won == lost == draw == 0:
            return FAILURE
        if self.mpdbh.update_user(otherid, stats=(won, lost, draw)):
            return SUCCESS
        return FAILURE

    def _update_single_user(self, data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        try:
            otherid = int(data.decode('utf8'))
        except ValueError:
            return WRONG_FORMAT
        username = self.mpc.get_username(otherid)
        draw_count_preference = self.mpc.get_draw_count_pref(otherid)
        logger.debug(f'user {otherid} {draw_count_preference}')
        rank, points = self.mpc.userranking(otherid)
        if self.mpdbh.update_user(otherid, username=username,
                                  draw_count_preference=draw_count_preference,
                                  rank=rank, points=points):
            return SUCCESS
        return FAILURE

    def _reject_challenge(self, data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        try:
            challenge_id = int(data.decode('utf8'))
        except ValueError:
            return WRONG_FORMAT
        if self.mpc.accept_challenge(challenge_id, False) == 1:
            if not self.mpdbh.reject_challenge(challenge_id):
                logger.error('Something went wrong while updating local DB')
            return SUCCESS
        return FAILURE

    def _accept_challenge(self, data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        try:
            chid, draw, score = data.decode('utf8').split(SEP)
            challenge_id = int(chid)
            draw = int(draw)
            score = int(score)
        except ValueError:
            return WRONG_FORMAT
        gamet = mpclient.GameType(draw, score)
        seed = self.mpc.accept_challenge(challenge_id, True, gamet)
        if seed > 0:
            if not self.mpdbh.add_challenge_round(challenge_id, 1, draw, score,
                                                  seed):
                logger.error('Something went wrong during add_challenge_round')
            return SUCCESS
        return FAILURE

    def _check_login(self) -> bool:
        if self._login and self.mpc.connected:
            return True
        try:
            res = self.mpc.login()
        except (mpclient.NotConnectedError, mpclient.CouldNotLoginError):
            res = False
        self._login = res
        self._sync_local_database()
        return res

    def _sync_local_database(self) -> bytes:
        timestamp = 0 if self._first_sync else self.mpdbh.timestamp
        self._first_sync = False
        now = util.timestamp()
        ret = SUCCESS
        try:
            reqs = self.mpc.pending(timestamp)
            self._prune_user()
        except mpclient.NotConnectedError:
            ret = NO_CONNECTION
        except mpclient.CouldNotLoginError:
            ret = NOT_LOGGED_IN
        if ret == SUCCESS and sum([i in reqs for i in (3, 4, 5, 14, 15)]) > 0:
            if not self._update_user(timestamp, 14 in reqs):
                ret = FAILURE
        if ret == SUCCESS and 129 in reqs or 130 in reqs or 136 in reqs:
            if not self._update_challenges(timestamp):
                ret = FAILURE
        try:
            pref = self.mpc.get_draw_count_pref()
        except mpclient.NotConnectedError:
            ret = NO_CONNECTION
        except mpclient.CouldNotLoginError:
            ret = NOT_LOGGED_IN
        if ret == SUCCESS:
            self.mpdbh.update_draw_count_pref(pref)
            self.mpdbh.update_timestamp(now)
        self._prune_challenge()
        return ret

    def _update_user(self, timestamp, update_names: bool) -> bool:
        check = ((0, self.mpc.pending_sent_friend_request),
                 (1, self.mpc.pending_recv_friend_request),
                 (2, self.mpc.get_friend_list), (3, self.mpc.get_blocked_list))
        skip = []
        for rtype, meth in check:
            try:
                res = meth(timestamp)
            except (mpclient.NotConnectedError, mpclient.CouldNotLoginError):
                return False
            for i in res:
                logger.debug(f'Updating user with id {i} rtype {rtype}')
                try:
                    username = self.mpc.get_username(i)
                    draw_count_preference = self.mpc.get_draw_count_pref(i)
                    rank, points = self.mpc.userranking(i)
                except (mpclient.NotConnectedError,
                        mpclient.CouldNotLoginError):
                    return False
                self.mpdbh.update_user(i, username, rtype,
                                       draw_count_preference, rank, points)
        for i in self.mpdbh.userids:
            if i in skip:
                continue
            if update_names:
                try:
                    username = self.mpc.get_username(i)
                    dpref = self.mpc.get_draw_count_pref(i)
                    rank, points = self.mpc.userranking(i)
                except (mpclient.NotConnectedError,
                        mpclient.CouldNotLoginError):
                    return False
                self.mpdbh \
                    .update_user(i, username, draw_count_preference=dpref,
                                 rank=rank, points=points)
        return True

    def _prune_user(self) -> None:
        for i in self.mpdbh.userids:
            if not self.mpc.active_relation(i):
                logger.debug(f'Relation became inactive {i}')
                if not self.mpdbh.delete_user(i):
                    logger.warning(f'Unable to delete inactive user {i}')

    def _update_challenges(self, timestamp) -> bool:
        check = ((0, self.mpc.pending_challenge_req_out),
                 (1, self.mpc.pending_challenge_req_in),
                 (2, self.mpc.active_challenges))
        challenge_ids = []
        for status, meth in check:
            logger.debug(f'Checking challenges with status {status}')
            try:
                res = meth(timestamp)
            except (mpclient.NotConnectedError, mpclient.CouldNotLoginError):
                return False
            for i in res:
                if status < 2:
                    rounds, challenge_id, otherid = i
                    roundno = 0
                else:
                    challenge_id = i.challenge_id
                    roundno = i.roundno
                    rounds = i.rounds
                    otherid = i.userid
                challenge_ids.append(challenge_id)
                self.mpdbh.update_challenge(challenge_id, otherid, rounds,
                                            status, True)
                if not self._update_challenge_rounds(challenge_id, roundno):
                    return False
        logger.debug(f'Updated challenges {repr(challenge_ids)}')
        return True

    def _update_challenge_rounds(self, challenge_id: int, roundno: int) -> bool:
        for i in range(roundno):
            try:
                res = self.mpc.challenge_round(challenge_id, i + 1)
            except (mpclient.NotConnectedError, mpclient.CouldNotLoginError):
                return False
            if res is None:
                continue
            try:
                seed = self.mpc.get_round_seed(challenge_id, i + 1)
            except (mpclient.NotConnectedError, mpclient.CouldNotLoginError):
                return False
            gametype, resuser, resother = res
            self.mpdbh.update_challenge_round(challenge_id, i + 1,
                                              gametype.draw, gametype.score,
                                              seed, resuser, resother)
        return True

    def _prune_challenge(self) -> None:
        logger.debug('Pruning challenges')
        for i, _ in self.mpdbh.chwaiting:
            if self.mpc.challenge_active(i):
                continue
            logger.debug(f'Challenge {i} marked as inactive')
            self.mpdbh.inactive_challenge(i)


if __name__ == '__main__':
    try:
        import android  # pylint: disable=unused-import
        CFG = 'com.tizilogic.pyos/files/.foolysh/foolysh.ini'
    except ImportError:
        CFG = '.foolysh/foolysh.ini'
    Multiplayer(CFG).start()
