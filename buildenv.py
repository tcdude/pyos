"""
Provides a small server that runs build environments in subprocesses.
"""

import argparse
import selectors
import socket
import struct
from subprocess import Popen
import sys
from typing import Union

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

UDSENVS = './buildenv.sock'


def _cleanup(full: bool) -> bool:
    if full:
        proc = Popen(['p4a', 'clean_all'])
        if proc.wait():
            return False
        return True
    proc = Popen(['p4a', 'clean_recipe_build', 'foolysh'])
    if proc.wait():
        return False
    proc = Popen(['p4a', 'clean_download_cache', 'foolysh'])
    if proc.wait():
        return False
    return True


def _build(arch: int, release: bool) -> Union[Popen, None]:
    if arch == 32:
        barch = 'armeabi-v7a'
    else:
        barch = 'arm64-v8a'
    cmd = ['python3', 'setup.py', 'apk', '--arch', barch,
           '--service=solver:service/solver.py',
           '--service=multiplayer:multiplayer.py']
    if release:
        cmd.append('--release')
    return Popen(cmd, stdout=sys.stdout, stderr=sys.stderr,
                 universal_newlines=True)


class BuildEnv:
    """
    Runs a build worker inside a clean p4aspaces environment to launch build
    processes.

    Args:
        envid: The envid received through cmd line args, used to identify the
            client with the EnvManager.
        sel: The global DefaultSelector used in this process.
    """
    def __init__(self, envid: int) -> None:
        self._envid = envid
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._fresh = True
        self._proc: Popen = None
        self._sel: selectors.DefaultSelector = selectors.DefaultSelector()
        self._success = False

    def start(self) -> None:
        """Start the build env."""
        print('Connecting to server...')
        self._sock.connect(UDSENVS)
        self._sock.setblocking(False)
        self._sel.register(self._sock, selectors.EVENT_WRITE, self._login)
        print('Starting main loop')
        while True:
            for key, _ in self._sel.select(timeout=0.1):
                callback = key.data
                callback()

            if self._proc is not None:
                poll = self._proc.poll()
                if poll is None:
                    continue
                self._sel.register(self._sock, selectors.EVENT_WRITE,
                                   self._job_done)
                self._success = poll == 0
                self._proc = None

    def _login(self) -> None:
        print('Announce env to build server')
        self._sock.sendall(struct.pack('<I', self._envid))
        self._sel.modify(self._sock, selectors.EVENT_READ, self._recv)

    def _recv(self) -> None:
        data = self._sock.recv(4096)
        if not data or data[0] == 255:
            print('Received stop')
            self._sock.close()
            sys.exit(0)
        print(f'Received command {data[0]}')
        self.handle_cmd(data)
        self._sel.unregister(self._sock)

    def _job_done(self) -> None:
        print(f'Sending job finished result {self._success}')
        self._sock.sendall(struct.pack('<B', 0 if self._success else 1))
        self._sel.modify(self._sock, selectors.EVENT_READ, self._recv)

    def handle_cmd(self, data: bytes) -> None:
        """Handles a build command."""
        cmd = data[0]
        if self._fresh:
            clean = False
            full = False
        else:
            clean = cmd & 1 > 0
            full = cmd & 2 > 0
        arch = 64 if (cmd & 4 > 0) else 32
        release = cmd & 8 > 0
        res = True
        if clean:
            print(f'Cleaning env full={full}')
            res = _cleanup(full)
            if self._fresh and res:
                self._fresh = False
        if res:
            print('Starting build')
            self._proc = _build(arch, release)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Buildenv using p4aspaces')
    parser.add_argument('-eid', dest='envid', type=int, default=-1,
                        help='This is an automated process. Do not call')
    args = parser.parse_args()
    if args.envid == -1:
        raise RuntimeError('Expected -eid argument.')
    srv = BuildEnv(args.envid)
    srv.start()


if __name__ == '__main__':
    main()
