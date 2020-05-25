"""
Service that handles communication with the pyosserver and the app thread.
"""

from dataclasses import dataclass, field
import datetime
import os
import selectors
import socket
import struct
import sys
import time
import traceback
from typing import Callable, Dict, List, Tuple

from foolysh.tools import config
from loguru import logger

import common
import mpclient
import mpdb
import stats
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

SELECTOR = selectors.DefaultSelector()
_BYTES = [struct.pack('<B', i) for i in range(256)]
SEP = chr(0) * 3
SUCCESS = _BYTES[0]
FAILURE = _BYTES[1]
ILLEGAL_REQUEST = _BYTES[2]
WRONG_FORMAT = _BYTES[3]
NO_CONNECTION = _BYTES[4]
NOT_LOGGED_IN = _BYTES[5]
UNHANDLED_EXCEPTION = _BYTES[6]
WAIT = 60


@dataclass
class MPSystems:
    """Holds system instances used by Multiplayer."""
    mpc: mpclient.MultiplayerClient
    mpdbh: mpdb.MPDBHandler
    stats: stats.Stats


@dataclass
class MPData:
    """Holds data attributes used by Multiplayer."""
    login: bool = False
    first_sync: bool = True
    result: Dict[socket.SocketType, bytes] = field(default_factory=dict)
    first_comm: bool = True
    lbupdate: int = 0
    lbrange: Tuple[int, int] = field(default_factory=tuple)
    chupdate: int = 0
    relupdate: int = 0
    dbsync: int = 0


class Multiplayer:
    """Multiplayer service."""
    def __init__(self, cfg_file: str) -> None:
        self.cfg = config.Config(cfg_file)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        mpc = mpclient.MultiplayerClient(cfg_file)
        mpdbh = mpdb.MPDBHandler(common.MPDATAFILE)
        sts = stats.Stats(common.DATAFILE)
        self.sys = MPSystems(mpc, mpdbh, sts)
        self.data = MPData()
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

    @logger.catch
    def start(self):
        """Start listening."""
        uds = self.cfg.get('mp', 'uds')
        try:
            os.unlink(uds)
        except OSError:
            if os.path.exists(uds):
                raise
        self.sock.bind(('localhost', 0))
        self.sock.listen()
        self.sock.setblocking(False)
        SELECTOR.register(self.sock, selectors.EVENT_READ, self.accept)
        port = self.sock.getsockname()[1]
        with open(uds, 'w') as fhandler:
            fhandler.write(f'{port}')
        logger.debug(f'Start listening on port {port}')
        while True:
            if not os.path.exists(uds):
                logger.warning('Port file deleted, exit service')
                sys.exit(0)
            events = SELECTOR.select(0.1)
            for key, _ in events:
                callback = key.data
                callback(key.fileobj)
            if self.data.first_comm or not self.sys.mpc.connected:
                continue
            self._send_unsent_results()
            now = time.time()
            lbu = now - self.data.lbupdate
            dbs = now - self.data.dbsync
            if lbu > WAIT and self.data.lbrange:
                start, end = self.data.lbrange
                self._update_challenge_leaderboard(
                    f'{start}{SEP}{end}'.encode('utf8'))
            if dbs > WAIT:
                self._sync_local_database()
                self.data.dbsync = now

    def accept(self, unused_conn) -> None:
        """Accepts and handles a new connection."""
        conn, _ = self.sock.accept()
        conn.setblocking(False)
        logger.debug('New connection')
        SELECTOR.register(conn, selectors.EVENT_READ, self.handle)

    @logger.catch
    def handle(self, conn) -> None:
        """Handle a request."""
        # pylint: disable=too-many-branches
        data = conn.recv(self.cfg.getint('mp', 'bufsize', fallback=4096))
        if not data:
            logger.debug('No data')
            SELECTOR.unregister(conn)
            conn.close()
            return
        req = data[0]
        if req == 255:
            self.stop(conn)
        elif req == 254:  # NOP
            logger.debug('NOP')
            account = self.cfg.get('mp', 'user', fallback='').strip()
            if self.sys.mpc.connected or (account and self._check_login()):
                logger.debug('NOP while client is connected')
                self.data.result[conn] = SUCCESS
            else:
                logger.warning('NOP while client is disconnected')
                self.data.result[conn] = NO_CONNECTION
        elif req in self._handler_methods:
            logger.debug(f'Valid request {req}')
            if not self.sys.mpc.connected and not self.sys.mpc.connect():
                self.data.result[conn] = NO_CONNECTION
            else:
                ret = FAILURE
                try:
                    ret = self._handler_methods[req](data[1:])
                except mpclient.NotConnectedError:
                    ret = NO_CONNECTION
                except mpclient.CouldNotLoginError:
                    ret = NOT_LOGGED_IN
                except Exception as err:  # pylint: disable=broad-except
                    logger.error(f'Unhandled Exception {err}\n'
                                 + traceback.format_exc())
                    ret = UNHANDLED_EXCEPTION
                self.data.result[conn] = ret
                logger.debug(f'Request {req} processed')
        else:
            logger.warning(f'Invalid request {req}')
            self.data.result[conn] = ILLEGAL_REQUEST
        SELECTOR.modify(conn, selectors.EVENT_WRITE, self.send_result)
        self.data.first_comm = False

    def send_result(self, conn) -> None:
        """Send the result of a request when the other side becomes readable."""
        if conn in self.data.result:
            conn.sendall(self.data.result.pop(conn))
        else:
            logger.warning('Called send_result but no result present!')
        SELECTOR.unregister(conn)
        conn.close()

    def stop(self, conn) -> None:
        """Stop and exit the service."""
        logger.debug('Received stop request')
        conn.setblocking(True)
        conn.settimeout(1)
        try:
            conn.sendall(SUCCESS)
        except socket.timeout:
            logger.error('Unable to confirm stop request')
        else:
            logger.info('Multiplayer Service stopped normally')
        conn.close()
        try:
            os.unlink(self.cfg.get('mp', 'uds'))
        except FileNotFoundError:
            pass
        sys.exit(0)

    def _new_account(self, data: bytes) -> bytes:
        try:
            username, password = data.decode('utf8').split(SEP, 1)
        except ValueError:
            return WRONG_FORMAT
        if self.sys.mpc.new_user(username, password):
            logger.debug('New Account request was successful')
            return SUCCESS
        logger.warning('New Account request failed')
        return FAILURE

    def _change_username(self, data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        username = data.decode('utf8')
        if self.sys.mpc.change_username(username):
            return SUCCESS
        return FAILURE

    def _change_password(self, data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        password = data.decode('utf8')
        if self.sys.mpc.change_password(password):
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
            self.sys.mpc.reply_friend_request(userid, decision)
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
            self.sys.mpc.unblock_user(userid, decision)
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
            self.sys.mpc.block_user(userid)
        except mpclient.NotConnectedError:
            return NO_CONNECTION
        except mpclient.CouldNotLoginError:
            return NOT_LOGGED_IN
        self.sys.mpdbh.update_user(userid, rtype=3)
        return SUCCESS

    def _remove_friend(self, data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        try:
            userid = int(data.decode('utf8'))
        except ValueError:
            return WRONG_FORMAT
        try:
            self.sys.mpc.remove_friend(userid)
        except mpclient.NotConnectedError:
            return NO_CONNECTION
        except mpclient.CouldNotLoginError:
            return NOT_LOGGED_IN
        self.sys.mpdbh.delete_user(userid)
        return SUCCESS

    def _set_draw_count_pref(self, data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        try:
            pref = int(data.decode('utf8'))
        except ValueError:
            return WRONG_FORMAT
        try:
            self.sys.mpc.set_draw_count_pref(pref)
        except mpclient.NotConnectedError:
            return NO_CONNECTION
        except mpclient.CouldNotLoginError:
            return NOT_LOGGED_IN
        self.sys.mpdbh.draw_count_preference = pref
        return SUCCESS

    def _update_daily_deal_best_scores(self, unused_data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        today = datetime.datetime.utcnow()
        start_i = today - common.START_DATE - datetime.timedelta(days=9)
        for i in range(10):
            for k in (1, 3):
                try:
                    res = self.sys.mpc.daily_best_score(k, start_i.days + i)
                except mpclient.NotConnectedError:
                    return NO_CONNECTION
                except mpclient.CouldNotLoginError:
                    return NOT_LOGGED_IN
                if sum(res) == 0:
                    continue
                self.sys.mpdbh.update_dd_score(k, start_i.days + i, res)
        return SUCCESS

    def _update_challenge_leaderboard(self, data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        try:
            start, end = data.decode('utf8').split(SEP, 1)
            start, end = int(start), int(end)
        except ValueError:
            return WRONG_FORMAT
        now = time.time()
        if now - self.data.lbupdate < WAIT:
            if not self.data.lbrange:
                self.data.lbrange = start, end
            elif self.data.lbrange[0] > start or self.data.lbrange[1] < end:
                self.data.lbrange = (min(start, self.data.lbrange[0]),
                                     max(end, self.data.lbrange[1]))
            else:
                return SUCCESS
        else:
            self.data.lbrange = start, end
        self.data.lbupdate = now
        i = start
        while i < end:
            try:
                res = self.sys.mpc.leaderboard(i)
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
            username = self.sys.mpdbh.get_username(i[2])
            if not username:
                try:
                    username = self.sys.mpc.get_username(i[2])
                except mpclient.NotConnectedError:
                    return NO_CONNECTION
                except mpclient.CouldNotLoginError:
                    return NOT_LOGGED_IN
            self.sys.mpdbh.update_leaderboard(i[0], i[1], username)
        return SUCCESS

    def _update_user_ranking(self, unused_data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        try:
            rank, points = self.sys.mpc.userranking()
        except mpclient.NotConnectedError:
            return NO_CONNECTION
        except mpclient.CouldNotLoginError:
            return NOT_LOGGED_IN
        self.sys.mpdbh.update_user_ranking(rank, points)
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
            if not self.sys.mpc.submit_daydeal_score(draw, dayoffset, result):
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
            if not self.sys.mpc.start_challenge(userid, rounds):
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
        if result[0] == -2.0:  # Ensure a result is saved locally
            self.sys.mpdbh.update_challenge_round(challenge_id, roundno,
                                                  resuser=result)
        try:
            if not self.sys.mpc.ping_pong or not self.sys.mpc \
                  .submit_round_result(challenge_id, roundno, result):
                return FAILURE
        except mpclient.NotConnectedError:
            return NO_CONNECTION
        except mpclient.CouldNotLoginError:
            return NOT_LOGGED_IN
        self.sys.mpdbh.update_challenge_round(challenge_id, roundno,
                                              resuser=result, result_sent=True)
        return SUCCESS

    def _friend_request(self, data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        username = data.decode('utf8')
        if self.sys.mpc.friend_request(username):
            return SUCCESS
        return FAILURE

    def _challenge_stats(self, data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        try:
            otherid = int(data.decode('utf8'))
        except ValueError:
            return WRONG_FORMAT
        res = self.sys.mpc.challenge_stats(otherid)
        if sum(res) < 0:
            return FAILURE
        if self.sys.mpdbh.update_user(otherid, stats=res):
            return SUCCESS
        return FAILURE

    def _update_single_user(self, data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        try:
            otherid = int(data.decode('utf8'))
        except ValueError:
            return WRONG_FORMAT
        username = self.sys.mpc.get_username(otherid)
        draw_count_preference = self.sys.mpc.get_draw_count_pref(otherid)
        logger.debug(f'user {otherid} {draw_count_preference}')
        rank, points = self.sys.mpc.userranking(otherid)
        res = self.sys.mpc.challenge_stats(otherid)
        if sum(res) < 0:
            return FAILURE
        if self.sys.mpdbh \
            .update_user(otherid, username=username,
                         draw_count_preference=draw_count_preference, rank=rank,
                         points=points, stats=res):
            return SUCCESS
        return FAILURE

    def _reject_challenge(self, data: bytes) -> bytes:
        if not self._check_login():
            return NOT_LOGGED_IN
        try:
            challenge_id = int(data.decode('utf8'))
        except ValueError:
            return WRONG_FORMAT
        if self.sys.mpc.accept_challenge(challenge_id, False) == 1:
            if not self.sys.mpdbh.reject_challenge(challenge_id):
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
        roundno = self.sys.mpdbh.roundno(challenge_id)
        if roundno == 0:
            seed = self.sys.mpc.accept_challenge(challenge_id, True, gamet)
        else:
            seed = self.sys.mpc.new_round(challenge_id, gamet)
        if seed > 0:
            roundno += 1
            if not self.sys.mpdbh.update_challenge_round(challenge_id, roundno,
                                                         draw, score, seed):
                logger.error('Something went wrong during add_challenge_round')
            return SUCCESS
        return FAILURE

    # Helper

    def _check_login(self) -> bool:
        if self.data.login and self.sys.mpc.connected:
            return True
        try:
            res = self.sys.mpc.login()
        except (mpclient.NotConnectedError, mpclient.CouldNotLoginError):
            res = False
        self.data.login = res
        return res

    # DB Sync

    def _sync_local_database(self) -> bytes:
        timestamp = 0 if self.data.first_sync else self.sys.mpdbh.timestamp
        timestamp = max(timestamp - 60, 0)
        self.data.first_sync = False
        now = util.timestamp() - 60
        ret = SUCCESS
        try:
            reqs = self.sys.mpc.pending(timestamp)
        except mpclient.NotConnectedError:
            return NO_CONNECTION
        except mpclient.CouldNotLoginError:
            return NOT_LOGGED_IN
        if ret == SUCCESS and sum([i in reqs for i in (3, 4, 5, 14, 15)]) > 0:
            self._prune_user()
            if not self._update_user(timestamp, reqs):
                ret = FAILURE
        if ret == SUCCESS and 129 in reqs or 130 in reqs or 136 in reqs:
            self._prune_challenge()
            if not self._update_challenges(timestamp, reqs):
                ret = FAILURE
        try:
            pref = self.sys.mpc.get_draw_count_pref()
        except mpclient.NotConnectedError:
            ret = NO_CONNECTION
        except mpclient.CouldNotLoginError:
            ret = NOT_LOGGED_IN
        if ret == SUCCESS:
            self.sys.mpdbh.update_draw_count_pref(pref)
            self.sys.mpdbh.update_timestamp(now)
        return ret

    def _update_user(self, timestamp, reqs: List[int]) -> bool:
        check = {3: (0, self.sys.mpc.pending_sent_friend_request),
                 15: (1, self.sys.mpc.pending_recv_friend_request),
                 4: (2, self.sys.mpc.get_friend_list),
                 5: (3, self.sys.mpc.get_blocked_list)}
        skip = []
        for req in reqs:
            if req in check:
                rtype, meth = check[req]
            else:
                continue
            try:
                res = meth(timestamp)
            except (mpclient.NotConnectedError, mpclient.CouldNotLoginError):
                return False
            for i in res:
                logger.debug(f'Updating user with id {i} rtype {rtype}')
                try:
                    username = self.sys.mpc.get_username(i)
                    draw_count_preference = self.sys.mpc.get_draw_count_pref(i)
                    rank, points = self.sys.mpc.userranking(i)
                except (mpclient.NotConnectedError,
                        mpclient.CouldNotLoginError):
                    return False
                self.sys.mpdbh.update_user(i, username, rtype,
                                           draw_count_preference, rank, points)
        if 14 in reqs:
            for i in self.sys.mpdbh.userids:
                if i in skip:
                    continue
                try:
                    username = self.sys.mpc.get_username(i)
                    dpref = self.sys.mpc.get_draw_count_pref(i)
                    rank, points = self.sys.mpc.userranking(i)
                except (mpclient.NotConnectedError,
                        mpclient.CouldNotLoginError):
                    return False
                self.sys.mpdbh \
                    .update_user(i, username, draw_count_preference=dpref,
                                 rank=rank, points=points)
        return True

    def _prune_user(self) -> None:
        now = time.time()
        if now - self.data.relupdate < WAIT:
            return
        self.data.relupdate = now
        for i in self.sys.mpdbh.userids:
            if not self.sys.mpc.active_relation(i):
                logger.debug(f'Relation became inactive {i}')
                if not self.sys.mpdbh.delete_user(i):
                    logger.warning(f'Unable to delete inactive user {i}')

    def _update_challenges(self, timestamp, reqs: List[int]) -> bool:
        check = {136: (0, self.sys.mpc.pending_challenge_req_out),
                 129: (1, self.sys.mpc.pending_challenge_req_in),
                 130: (2, self.sys.mpc.active_challenges)}
        challenge_ids = []
        for req in reqs:
            if req in check:
                status, meth = check[req]
            else:
                continue
            logger.debug(f'Checking challenges with status {status}')
            try:
                res = meth(timestamp)
            except (mpclient.NotConnectedError, mpclient.CouldNotLoginError):
                return False
            for i in res:
                if status < 2:
                    rounds, challenge_id, otherid = i
                    roundno = 0
                    userturn = status == 1
                else:
                    challenge_id = i.challenge_id
                    roundno = i.roundno
                    rounds = i.rounds
                    otherid = i.userid
                    userturn = i.waiting
                challenge_ids.append(challenge_id)
                self.sys.mpdbh.update_challenge(challenge_id, otherid, rounds,
                                                status, True, userturn)
                if roundno == rounds:
                    roundno -= 1
                if not self._update_challenge_rounds(challenge_id, roundno):
                    return False
        logger.debug(f'Updated challenges {repr(challenge_ids)}')
        return True

    def _update_challenge_rounds(self, challenge_id: int, roundno: int) -> bool:
        for i in range(roundno + 1):
            if self.sys.mpdbh.round_complete(challenge_id, i + 1):
                continue
            try:
                res = self.sys.mpc.challenge_round(challenge_id, i + 1)
            except (mpclient.NotConnectedError, mpclient.CouldNotLoginError):
                return False
            if res is None:
                logger.debug(f'No entry for challenge {challenge_id} round '
                             f'{i + 1}')
                continue
            try:
                seed = self.sys.mpc.get_round_seed(challenge_id, i + 1)
            except (mpclient.NotConnectedError, mpclient.CouldNotLoginError):
                return False
            gametype, resuser, resother = res
            logger.debug(f'Updating round with data {repr(res)}')
            self.sys.mpdbh.update_challenge_round(challenge_id, i + 1,
                                                  gametype.draw, gametype.score,
                                                  seed, resuser, resother,
                                                  resuser[0] != -1.0)
        return True

    def _prune_challenge(self) -> None:
        now = time.time()
        if now - self.data.chupdate > WAIT:
            res = [i[0] for i in self.sys.mpdbh.chwaiting]
            self.data.chupdate = now
            logger.debug('Pruning challenges full')
        else:
            res = [i[0] for i in self.sys.mpdbh.chwaiting_last_round]
            logger.debug('Pruning challenges only last round')
        for i in res:
            if self.sys.mpc.challenge_active(i):
                continue
            logger.debug(f'Challenge {i} marked as inactive')
            if not self.sys.mpdbh.challenge_complete(i):
                self._update_challenge_rounds(
                    i, self.sys.mpdbh.num_rounds(i) - 1)
            self.sys.mpdbh.inactive_challenge(i)

    def _send_unsent_results(self) -> None:
        if not self._check_login():
            return
        for challenge_id, roundno in self.sys.mpdbh.unsent_results:
            seed, draw, _ = self.sys.mpdbh.get_round_info(challenge_id, roundno)
            result = self.sys.mpdbh.round_result(challenge_id, roundno)
            if result[0] != -2.0:
                try:
                    duration, moves, points, _ = self.sys.stats \
                        .result(seed, draw, True, challenge=challenge_id)
                except TypeError:
                    continue
                result = duration, points, moves
            try:
                if not self.sys.mpc.ping_pong or not self.sys.mpc \
                    .submit_round_result(challenge_id, roundno, result):
                    return
            except (mpclient.NotConnectedError, mpclient.CouldNotLoginError):
                return
            self.sys.mpdbh.update_challenge_round(challenge_id, roundno,
                                                  resuser=result,
                                                  result_sent=True)

@logger.catch
def main(cfg: str):
    """Main entry point."""
    Multiplayer(cfg).start()


if __name__ == '__main__':
    logger.remove()
    try:
        import android  # pylint: disable=unused-import
        CFG = '../.foolysh/foolysh.ini'
        logger.add(sys.stderr, level='INFO')
    except ImportError:
        CFG = '.foolysh/foolysh.ini'
        logger.add(sys.stderr, level='DEBUG')
    main(CFG)
