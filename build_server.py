"""
Provides a small server that runs build environments in subprocesses.
"""

from multiprocessing import Process, Queue
import os
import selectors
import socket
import struct
from subprocess import Popen, PIPE, STDOUT
import sys
import time
from typing import Callable, Dict

from loguru import logger

import buildlog

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

BASE = os.path.abspath(os.path.split(__file__)[0])
if os.getcwd() != BASE:
    os.chdir(BASE)
P4A = 'https://github.com/kivy/python-for-android/archive/develop.zip'
UDS = '/tmp/pyosbs.sock'
UDSENVS = './buildenv.sock'
BE_ARGS = (1000, 'p4a-py3-api28ndk21', '.', P4A, 'master')
ENVCMD = f'p4aspaces cmd p4a-py3-api28ndk21 --map-to-user tc ' \
    f' --workspace {BASE} ' \
    f'--p4a https://github.com/kivy/python-for-android/archive/develop.zip ' \
    f'--buildozer master "python3 /home/userhome/workspace/buildenv.py ' \
    f'-eid --ENVID--"'


class EnvData:
    """Holds data related to a unique build env."""
    def __init__(self, bitness: int, proc: Process, title: str) -> None:
        self._bitness = bitness
        self._proc = proc
        self._conn: socket.socket = None
        self._title: str = title

    def kill(self) -> None:
        """Sends the kill signal to the underlying process."""
        self._proc.kill()

    @property
    def title(self) -> str:
        """Returns the title of the env."""
        return self._title

    @property
    def bitness(self) -> int:
        """Returns the bitness of the env."""
        return self._bitness

    @property
    def proc(self) -> Process:
        """Returns the Process instance of the env."""
        return self._proc

    @property
    def conn(self) -> socket.socket:
        """
        Returns the socket instance or None if not set.
        """
        return self._conn

    @conn.setter
    def conn(self, value: socket.socket) -> None:
        self._conn = value

    @property
    def alive(self) -> bool:
        """
        Returns `True` if the underlying process is still alive, otherwise
        `False`.
        """
        return self._proc.is_alive()


def _env_thread(cmd: str, title: str, cmdq: Queue) -> None:
    proc = Popen(cmd, stdout=PIPE, stderr=STDOUT, shell=True,
                 universal_newlines=True)
    cmdq.put(('ADD', title, None))
    for line in proc.stdout:
        cmdq.put(('LOG', title, line))


class EnvManager:
    """
    Spawns build envs on demand and make them available to the BuildServer.
    Cleans up unused build envs, keeping only one alive for each arch.
    """
    def __init__(self, sel: selectors.DefaultSelector, cmdq: Queue) -> None:
        self._envid = 0
        self._envs: Dict[int, EnvData] = {}
        self._free = []
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._jobs = {}
        self._pending = {}
        self._sel = sel
        self._cmdq = cmdq
        self._start_listen()

    def new_env(self, bitness: int) -> int:
        """
        Returns the envid of a free build env.

        Args:
            bitness: 32/64 bit arch to be used for the env.
        """
        ret = -1
        drop = []
        for i, envid in enumerate(self._free):
            env = self._envs[envid]
            if env.bitness == bitness and env.alive:
                ret = i
                break
            if not env.alive:
                self._envs.pop(envid)
                drop.append(i)
        for i in reversed(drop):
            self._free.pop(i)
        if ret > -1:
            return self._free.pop(ret)
        title = f'[{self._envid}] '
        title += f'{"arm64-v8a" if bitness == 64 else "armeabi-v7a"}'
        cmd = ENVCMD.replace('--ENVID--', str(self._envid))
        logger.debug(cmd)
        proc = Process(target=_env_thread, args=(cmd, title, self._cmdq),
                       daemon=True)
        proc.start()
        # proc = Popen(cmd, stdout=PIPE, stderr=STDOUT, shell=True,
        #              universal_newlines=True)
        logger.debug(f'Started Build Env with pid {proc.pid}')
        # self._cmdq.put(('ADD', title, None))
        self._envs[self._envid] = EnvData(bitness, proc, title)
        self._envid += 1
        return self._envid - 1

    def start_job(self, envid: int, callback: Callable[[bool], None], cmd: int
                  ) -> None:
        """
        Start a build job. Raises a ValueError when an unknown `envid` is
        passed. Upon completion of the job, the provided callback is called with
        the result of the build job.

        Args:
            envid: The build env to execute the job in.
            logfile: The logfile to use to capture the build stdout/stderr.
            callback: Callable with signature `bool`, `int`.
            cmd: Command to execute.
        """
        if envid not in self._envs:
            raise ValueError(f'Unknown or faulty envid {envid}')
        if not self.ready(envid):
            logger.debug('Env not ready, put job into pending')
            self._pending[envid] = callback, cmd
            return
        logger.debug('Env is ready, scheduling send')
        self._jobs[self._envs[envid].conn] = cmd, callback, envid
        self._sel.register(self._envs[envid].conn, selectors.EVENT_WRITE,
                           self._send_job)

    def release_env(self, envid: int) -> None:
        """Release a previously used build env."""
        keep = True
        for i in self._free:
            if self._envs[i].bitness == self._envs[envid].bitness:
                keep = False
                break
        if keep:
            logger.debug('Keeping released env alive')
            self._free.append(envid)
            return
        self._sel.unregister(self._envs[envid].conn)
        logger.debug(f'Sending stop signal to envid {envid}')
        self._envs[envid].conn.sendall(struct.pack('<B', 255))
        while self._envs[envid].alive:
            pass
        self._cmdq.put(('REMOVE', self._envs[envid].title, None))
        self._envs.pop(envid)

    def ready(self, envid: int) -> bool:
        """Whether an env is ready to receive a job."""
        if envid not in self._envs:
            raise ValueError('Invalid envid')
        return self._envs[envid].conn is not None \
            and self._envs[envid].conn not in self._jobs

    def stop(self):
        """Stop all build envs and close server."""
        for k in self._envs:
            if self._envs[k].alive and self._envs[k].conn is not None:
                self._envs[k].conn.sendall(struct.pack('<B', 255))
        wait = time.time() + 5
        while time.time() < wait:
            if not self._cleanup():
                break
        for k in self._envs:
            if self._envs[k].alive:
                self._envs[k].kill()
        self._cmdq.put((None, 'QUIT', None))

    def _send_job(self, conn, unused_mask) -> None:
        cmd, _, envid = self._jobs[conn]
        logger.debug(f'Sending cmd {cmd} to envid {envid}')
        conn.sendall(struct.pack('<B', cmd))
        self._sel.modify(conn, selectors.EVENT_READ, self._job_done)

    def _job_done(self, conn, unused_mask) -> None:
        callback, envid = self._jobs[conn][-2:]
        data = conn.recv(4096)
        if not data or len(data) != 1:
            self._sel.unregister(conn)
            conn.close()
            logger.error(f'Got an invalid response from the build env '
                         f'{repr(data)}')
            return
        callback(data[0] == 0, envid)
        self._jobs.pop(conn)
        try:
            self._sel.unregister(conn)
        except KeyError:
            pass

    def _start_listen(self) -> None:
        try:
            os.unlink(UDSENVS)
        except OSError:
            pass
        self._sock.setblocking(False)
        self._sock.bind(UDSENVS)
        self._sock.listen()
        self._sel.register(self._sock, selectors.EVENT_READ, self._accept)

    def _accept(self, unused_conn, unused_mask) -> None:
        logger.debug('New env connection')
        conn, _ = self._sock.accept()
        conn.setblocking(False)
        self._sel.register(conn, selectors.EVENT_READ, self._register_env)
        logger.debug('Waiting for env to announce its ID')

    def _register_env(self, conn, unused_mask) -> None:
        logger.debug('Build Env register')
        data = conn.recv(4096)
        if len(data) == 4:
            try:
                envid, = struct.unpack('<I', data)
            except struct.error as err:
                logger.error(f'Unable to unpack data: {err}')
            else:
                if envid not in self._envs:
                    logger.error(f'Unknown envid {envid}')
                else:
                    logger.debug(f'Build Env {envid} successfully registered')
                    self._envs[envid].conn = conn
                    self._sel.unregister(conn)
                    if envid in self._pending:
                        self.start_job(envid, *self._pending.pop(envid))
                    return
        else:
            logger.error('Invalid data received')
        self._sel.unregister(conn)
        conn.close()

    def _cleanup(self) -> bool:
        cleaned = False
        drop = []
        for k in self._envs:
            if not self._envs[k].alive:
                drop.append(k)
                cleaned = True
        for k in drop:
            self._envs.pop(k)
        return cleaned


class BuildServer:
    """Server listening on a UDS for build commands."""
    def __init__(self, sel: selectors.DefaultSelector, cmdq: Queue) -> None:
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._conn = {}
        self._envmgr = EnvManager(sel, cmdq)
        self._sel = sel

    def start(self) -> None:
        """Start to listen"""
        try:
            os.unlink(UDS)
        except OSError:
            pass
        self._sock.bind(UDS)
        self._sock.listen(100)
        self._sock.setblocking(False)
        self._sel.register(self._sock, 3, self._accept)
        logger.debug('Waiting for connections')

    def stop(self) -> None:
        """Stop listening and cleanup running processes."""
        logger.debug('Stopping')
        self._envmgr.stop()
        self._sel.unregister(self._sock)
        self._sock.close()

    def _accept(self, unused_conn, unused_mask) -> None:
        logger.debug('New connection')
        conn, _ = self._sock.accept()
        conn.setblocking(False)
        self._sel.register(conn, selectors.EVENT_READ, self._handle_build)

    def _handle_build(self, conn, unused_mask) -> None:
        logger.debug('Receive build command')
        data = conn.recv(4096)
        if len(data) != 1:
            logger.debug('Got wrong request size.')
            self._sel.unregister(conn)
            conn.close()
            return
        cmd = data[0]
        os.makedirs('logs', exist_ok=True)
        if cmd & 4 > 0:
            envid = self._envmgr.new_env(64)
        else:
            envid = self._envmgr.new_env(32)
        logger.debug(f'Starting new build job cmd={cmd} in env={envid}')
        self._envmgr.start_job(envid, self._release_env, cmd)
        self._conn[conn] = envid
        self._sel.modify(conn, selectors.EVENT_WRITE, self._reply_client)

    def _reply_client(self, conn, unused_mask) -> None:
        conn.sendall(f'{self._conn[conn]}'.encode('utf8'))
        self._sel.unregister(conn)
        conn.close()

    def _release_env(self, result: bool, envid: int) -> None:
        if result:
            logger.debug(f'[{envid}] Job finished successfully')
        else:
            logger.warning(f'[{envid}] Job failed')
        self._envmgr.release_env(envid)


def main() -> None:
    """Main entry point."""
    sel = selectors.DefaultSelector()
    logger.debug('Start Build Server')
    cmdq = Queue()
    thread = Process(target=buildlog.log_thread,
                     args=('Build Server Log', cmdq))
    thread.start()
    srv = BuildServer(sel, cmdq)
    srv.start()
    try:
        while True:
            _ = Popen('stty sane', stdout=sys.stdout, stderr=sys.stderr,
                      shell=True)
            events = sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)
    finally:
        srv.stop()
        sel.close()


if __name__ == '__main__':
    main()
