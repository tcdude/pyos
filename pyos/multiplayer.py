"""
Service that handles communication with the pyosserver and the app thread.
"""

import datetime
import os
import socket
import sys
from typing import Callable, Dict, List, Tuple

from foolysh.tools import config

import common
import mpclient
import mpdb
import util

SEP = chr(0) * 3
SUCCESS = chr(0).encode('utf8')
FAILURE = chr(1).encode('utf8')
ILLEGAL_REQUEST = chr(2).encode('utf8')
WRONG_FORMAT = chr(3).encode('utf8')
NO_CONNECTION = chr(4).encode('utf8')
NOT_LOGGED_IN = chr(5).encode('utf8')


class Multiplayer:
    """Multiplayer service."""
    def __init__(self, cfg_file: str) -> None:
        self.cfg = config.Config(cfg_file)
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.mpc = mpclient.MultiplayerClient(cfg_file)
        self.mpdbh = mpdb.MPDBHandler(common.MPDATAFILE)
        self._login = False
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
            15: self._submit_challenge_round_result}

    def start(self):
        """Start listening."""
        uds = self.cfg.get('mp', 'uds')
        try:
            os.unlink(uds)
        except OSError:
            if os.path.exists(uds):
                raise
        self.sock.bind(uds)
        self.sock.listen()
        while True:
            conn, _ = self.sock.accept()
            if not self.handle(conn):
                break
            conn.close()
        self.sock.close()
        try:
            os.unlink(uds)
        except OSError:
            pass
        sys.exit(0)

    def handle(self, conn) -> bool:
        """Handle a request and return whether to keep listening."""
        data = conn.recv(self.cfg.getint('mp', 'bufsize', fallback=4096))
        if data[0] == 255:      # Stop Service
            conn.sendall(SUCCESS)
            return False
        if data[0] in self._handler_methods:
            if not self.mpc.connected and not self.mpc.connect():
                conn.sendall(NO_CONNECTION)
            else:
                conn.sendall(self._handler_methods[data[0]](data[1:]))
        else:
            conn.sendall(ILLEGAL_REQUEST)
        return True

    def _new_account(self, data: bytes) -> bytes:
        try:
            username, password = data.decode('utf8').split(SEP, 1)
        except ValueError:
            return WRONG_FORMAT
        if self.mpc.new_user(username, password):
            return SUCCESS
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
            userid, decision = int(userid), ord(decision) > 0
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

    def _check_login(self) -> bool:
        if self._login and self.mpc.connected:
            return True
        try:
            res = self.mpc.login()
        except (mpclient.NotConnectedError, mpclient.CouldNotLoginError):
            res = False
        self._login = res
        return res

    def _sync_local_database(self) -> bytes:
        timestamp = self.mpdbh.timestamp
        now = util.timestamp()
        ret = SUCCESS
        try:
            reqs = self.mpc.pending(timestamp)
        except mpclient.NotConnectedError:
            ret = NO_CONNECTION
        except mpclient.CouldNotLoginError:
            ret = NOT_LOGGED_IN
        if ret == SUCCESS and sum([i in reqs for i in (3, 4, 5, 14, 15)]) > 0:
            if not self._update_user(timestamp):
                ret = FAILURE
        if ret == SUCCESS and 129 in reqs or 130 in reqs:
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
        return ret

    def _update_user(self, timestamp) -> bool:
        check = ((0, self.mpc.pending_sent_friend_request),
                 (1, self.mpc.pending_recv_friend_request),
                 (2, self.mpc.get_friend_list), (3, self.mpc.get_blocked_list))
        for rtype, meth in check:
            try:
                res = meth(timestamp)
            except (mpclient.NotConnectedError, mpclient.CouldNotLoginError):
                return False
            for i in res:
                username = self.mpc.get_username(i)
                try:
                    draw_count_preference = self.mpc.get_draw_count_pref(i)
                except (mpclient.NotConnectedError,
                        mpclient.CouldNotLoginError):
                    return False
                self.mpdbh.update_user(i, username, rtype,
                                       draw_count_preference)
        return True

    def _update_challenges(self, timestamp) -> bool:
        check = ((0, self.mpc.pending_challenge_req_out),
                 (1, self.mpc.pending_challenge_req_in),
                 (2, self.mpc.active_challenges))
        challenge_ids = []
        for status, meth in check:
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


if __name__ == '__main__':
    try:
        import android  # pylint: disable=unused-import
        CFG = 'com.tizilogic.pyos/files/.foolysh/foolysh.ini'
    except ImportError:
        CFG = '.foolysh/foolysh.ini'
