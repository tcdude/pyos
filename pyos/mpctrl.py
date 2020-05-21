"""
Provides the control interface for the multiplayer service.
"""

from dataclasses import dataclass, field
import os
import selectors
import socket
import struct
import threading
import time
from typing import Callable, Dict, Union

from foolysh.tools import config
from loguru import logger
try:
    import android  # pylint: disable=unused-import
    from jnius import autoclass
except ImportError:
    import subprocess

from common import Result
from multiplayer import (SEP, SUCCESS, FAILURE, ILLEGAL_REQUEST, WRONG_FORMAT,
                         NO_CONNECTION, NOT_LOGGED_IN)
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

RESMAP = {SUCCESS: 0, FAILURE: 1, ILLEGAL_REQUEST: 2, WRONG_FORMAT: 3,
          NO_CONNECTION: 4, NOT_LOGGED_IN: 5}
RESTXT = {0: 'Success', 1: 'Request Failed', 2: 'Illegal request',
          3: 'Wrong Format', 4: 'No Connection', 5: 'Not Logged In',
          6: 'Socket file not present'}
REQ = [struct.pack('<B', i) for i in range(256)]
STOP = REQ[255]
SEL = selectors.DefaultSelector()


@dataclass
class Request:
    """Handles a single request."""
    reqid: int
    port: int
    req: bytes
    res_dict: Dict[int, int]
    sock: socket.socket = field(init=False)
    retry: int = 3

    def __post_init__(self) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(('', self.port))
        if self.req is None:  # Service alive check
            self.sock.close()
            self.res_dict[self.reqid] = 0
            return
        SEL.register(self.sock, selectors.EVENT_WRITE, self.send)

    def send(self, sock: socket.socket) -> None:
        """Sends the request when writable."""
        sock.sendall(self.req)
        SEL.modify(sock, selectors.EVENT_READ, self.recv)

    def recv(self, sock: socket.socket) -> None:
        """Reads the request as soons as the socket becomes readable."""
        data = sock.recv(1024)
        if not data and self.retry > 0:
            self.retry -= 1
            return
        if data[:1] in RESMAP:
            self.res_dict[self.reqid] = RESMAP[data]
        else:
            self.res_dict[self.reqid] = RESMAP[FAILURE]
        SEL.unregister(sock)
        sock.close()

    def cancel(self) -> None:
        """Cancels the event"""
        try:
            SEL.unregister(self.sock)
        except (KeyError, ValueError):
            pass
        self.sock.close()


@dataclass
class CtrlData:
    """Holds the dicts for MPControl."""
    # pylint: disable=too-many-instance-attributes
    pending: Dict[int, Union[Request, bytes]] = field(default_factory=dict)
    retry: Dict[int, int] = field(default_factory=dict)
    results: Dict[int, int] = field(default_factory=dict)
    callbacks: Dict[int, Callable[[int], None]] = field(default_factory=dict)
    reload_cfg: Dict[int, int] = field(default_factory=dict)
    start_thread: threading.Thread = None
    active: bool = False
    lock: threading.Lock = threading.Lock()


class MPControl:
    """
    Control interface for the multiplayer service.

    .. note::
        Methods that start a request to the multiplayer service running in the
        background return either the request id to query the result later or -1
        if something went wrong upon creating the Request.
    """
    # pylint: disable=too-many-public-methods
    def __init__(self, cfg: config.Config) -> None:
        self.cfg = cfg
        self._reqid = 0
        self._data = CtrlData()
        self._proc = None
        self._port = 0
        if 'autoclass' in globals():
            self._service = autoclass('com.tizilogic.pyos.ServiceMultiplayer')
        else:
            self._service = None

    # Requests

    def create_new_account(self, username: str, password: str) -> int:
        """Start a "Create a new account" request."""
        reqid = self._request(
            REQ[0] + f'{username}{SEP}{password}'.encode('utf8'))
        self._data.reload_cfg[reqid] = 0
        return reqid

    def change_username(self, username: str) -> int:
        """Start a "Change username" request."""
        reqid = self._request(REQ[1] + f'{username}'.encode('utf8'))
        self._data.reload_cfg[reqid] = 0
        return reqid

    def change_password(self, password: str) -> int:
        """Start a "Change password" request."""
        reqid = self._request(REQ[2] + f'{password}'.encode('utf8'))
        self._data.reload_cfg[reqid] = 0
        return reqid

    def friend_request(self, username: str) -> int:
        """Start a "Friend Request" request."""
        return self._request(REQ[16] + username.encode('utf8'))

    def sync_relationships(self) -> int:
        """Start a "Synchronize Relationships" request."""
        return self._request(REQ[3])

    def reply_friend_request(self, userid: int, decision: bool) -> int:
        """Start a "Reply Friend Request" request."""
        val = 1 if decision else 0
        return self._request(REQ[4] + f'{userid}{SEP}{val}'.encode('utf8'))

    def unblock_user(self, userid: int, decision: bool) -> int:
        """Start a "Unblock User" request."""
        val = chr(1 if decision else 0)
        return self._request(REQ[5] + f'{userid}{SEP}{val}'.encode('utf8'))

    def block_user(self, userid: int) -> int:
        """Start a "Block User" request."""
        return self._request(REQ[6] + f'{userid}'.encode('utf8'))

    def remove_friend(self, userid: int) -> int:
        """Start a "Remove Friend" request."""
        return self._request(REQ[7] + f'{userid}'.encode('utf8'))

    def set_draw_count_pref(self, pref: int) -> int:
        """Start a "Set Draw Count Preference" request."""
        return self._request(REQ[8] + f'{pref}'.encode('utf8'))

    def update_dd_scores(self) -> int:
        """Start a "Update Daily Deal Best Scores" request."""
        return self._request(REQ[9])

    def update_leaderboard(self, start: int, end: int) -> int:
        """Start a "Update Challenge Leaderboard" request."""
        return self._request(REQ[10] + f'{start}{SEP}{end}'.encode('utf8'))

    def update_user_ranking(self) -> int:
        """Start a "Update User Ranking" request."""
        return self._request(REQ[11])

    def submit_dd_score(self, draw: int, dayoffset: int, result: Result) -> int:
        """Start a "Submit Day Deal Score" request."""
        res = util.encode_result(result)
        return self._request(
            REQ[12] + f'{draw}{SEP}{dayoffset}'.encode('utf8') + res)

    def start_challenge(self, userid: int, rounds: int) -> int:
        """Start a "Start Challenge" request."""
        return self._request(REQ[13] + f'{userid}{SEP}{rounds}'.encode('utf8'))

    def sync_challenges(self) -> int:
        """Start a "Synchronize Challenges" request."""
        return self._request(REQ[14])

    def submit_challenge_round_result(self, challenge_id: int, roundno: int,
                                      result: Result) -> int:
        """Start a "Submit Challenge Round Result" request."""
        res = util.encode_result(result)
        return self._request(
            REQ[15] + f'{challenge_id}{SEP}{roundno}'.encode('utf8') + res)

    def challenge_stats(self, otherid: int) -> int:
        """Request update of challenge stats."""
        return self._request(REQ[17] + str(otherid).encode('utf8'))

    def update_other_user(self, otherid: int) -> int:
        """Update specific user completely."""
        return self._request(REQ[18] + str(otherid).encode('utf8'))

    def reject_challenge(self, challenge_id: int) -> int:
        """Reject a challenge."""
        return self._request(REQ[19] + str(challenge_id).encode('utf8'))

    def accept_challenge(self, challenge_id: int, draw: int, score: int) -> int:
        """Accept a challenge."""
        return self._request(
            REQ[20] + f'{challenge_id}{SEP}{draw}{SEP}{score}'.encode('utf8'))

    def nop(self) -> int:
        """
        No Operation request that always returns SUCCESS if service is running.
        """
        return self._request(REQ[254])

    # Other

    def register_callback(self, reqid: int, callback: Callable[[int], None],
                          *args, **kwargs) -> bool:
        """
        Register a result callback.

        Args:
            reqid: A valid request id.
            callback: A callable that accepts at least one positional argument
                for the result code of the request.
            *args: Additional positional arguments to pass to the callback.
            **kwargs: Keyword arguments to pass to the callback.

        Returns:
            Success as boolean.
        """
        if reqid in self._data.pending or reqid in self._data.results:
            self._data.callbacks[reqid] = callback, args, kwargs
            return True
        return False

    def update(self):
        """
        Method to call regularly to process pending jobs and execute registered
        callbacks.
        """
        if not self._data.active:
            logger.debug('Update called before the service has come online')
            return
        events = SEL.select(timeout=-1)
        for key, _ in events:
            callback = key.data
            callback(key.fileobj)

        self._data.lock.acquire()

        need_req = []
        for k in self._data.pending:
            if isinstance(self._data.pending[k], (bytes, type(None))):
                need_req.append(k)
                self._data.retry[k] -= 1
        for k in need_req:
            req = self._data.pending[k]
            if self._data.retry:
                self._data.pending[k] = Request(k, self._port, req,
                                                self._data.results)
            else:
                if req:
                    logger.warning(f'Request [{req[0]}] reached max retries')
                else:
                    logger.warning('Empty Request reached max retries')
                self._data.pending.pop(k)
                self._data.retry.pop(k)
                self._data.results[k] = RESMAP[FAILURE]
        drop = []
        for k in self._data.results:
            if k in self._data.pending:
                if k in self._data.reload_cfg:
                    if self._data.results[k] == self._data.reload_cfg[k]:
                        logger.debug('Reloading configuration')
                        self.cfg.reload()
                    self._data.reload_cfg.pop(k)
                self._data.pending.pop(k)
            if k in self._data.callbacks:
                callback, args, kwargs = self._data.callbacks.pop(k)
                callback(self._data.results[k], *args, **kwargs)
                drop.append(k)
        for k in drop:
            self._data.results.pop(k)

        self._data.lock.release()

    def result(self, reqid: int) -> int:
        """
        Returns:
            The result code if available, `-1` if the result is not yet ready or
            -2 for an unknown `reqid`.
        """
        if reqid in self._data.results:
            return self._data.results.pop(reqid)
        if reqid in self._data.pending:
            return -1
        return -2

    def start_service(self) -> None:
        """Start the multiplayer service."""
        if self._proc is not None and self._proc.poll() is None:
            return
        if self._data.active:
            return
        if 'autoclass' in globals():
            logger.info('Starting Android Service multiplayer')
            # pylint: disable=invalid-name
            mActivity = autoclass('org.kivy.android.PythonActivity').mActivity
            # pylint: enable=invalid-name
            self._service.start(mActivity, '')
        elif 'autoclass' not in globals():
            logger.info('Starting multiplayer subprocess')
            self._proc = subprocess.Popen(['python', 'multiplayer.py'])
        cnt = 0
        while not os.path.exists(self.cfg.get('mp', 'uds')) and cnt < 100:
            cnt += 1
            time.sleep(0.01)
        if os.path.exists(self.cfg.get('mp', 'uds')):
            with open(self.cfg.get('mp', 'uds'), 'r') as fhandler:
                self._port = int(fhandler.read())
            self._data.lock.acquire()
            for _ in range(10):
                reqid = self._start_request(force=True)
                if reqid > -1:
                    _ = self.result(reqid)
                    self._data.active = True
                    break
                time.sleep(0.3)
            self._data.lock.release()
        self._data.start_thread = None  # Clean up after itself

    def stop(self):
        """Stop the service, if it is currently running."""
        if not self._data.active:
            return
        logger.debug('Cancel pending requests')
        for k in self._data.pending:
            self._data.pending[k].cancel()
        logger.debug('Stopping Multiplayer Service')
        reqid = self._request(STOP)
        stop = time.time() + 5
        while self.result(reqid) == -1 and time.time() < stop:
            time.sleep(0.001)
            self.update()
        if self._proc is not None:
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()

    def _request(self, req: bytes = None) -> int:
        if not self._data.active:
            if self._data.start_thread is None \
                  or not self._data.start_thread.is_alive():
                self._data.start_thread = threading \
                    .Thread(target=self.start_service)
                self._data.start_thread.start()
        return self._start_request(req)

    def _start_request(self, req: bytes = None, force: bool = False) -> int:
        try:
            self._data.pending[self._reqid] = Request(self._reqid, self._port,
                                                      req, self._data.results)
        except (NameError, FileNotFoundError, ConnectionRefusedError):
            if force:
                return -1
            self._data.pending[self._reqid] = req
            self._data.retry[self._reqid] = 5
            self._data.active = False
        return self._inc_reqid()

    def _inc_reqid(self) -> int:
        self._reqid += 1
        return self._reqid - 1

    @property
    def active(self) -> bool:
        """Whether the service is running."""
        return self._data.active

    @property
    def noaccount(self) -> bool:
        """Whether account setup is necessary."""
        self.cfg.reload()
        if self.cfg.get('mp', 'user', fallback=''):
            return False
        return True
