"""
Small program to launch builds on `build_server.py`.
"""

import socket
import struct
import time

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

UDS = '/tmp/pyosbs.sock'


def _sel_arch() -> int:
    while True:
        arch = input('Arch (0=64, 1=32, 2=Both) [0]: ')
        if not arch.strip():
            arch = 0
            break
        if arch.strip() in ('0', '1', '2'):
            arch = int(arch)
            break
        print(f'Unknown input {arch}. Try again...')
    return arch


def _sel_release() -> bool:
    while True:
        release = input('Build Type (0=Debug, 1=Release) [0]: ')
        if not release.strip():
            release = False
            break
        if release.strip() in ('0', '1'):
            release = int(release) > 0
            break
        print(f'Unknown input {release}. Try again...')
    return release


def _sel_clean() -> int:
    while True:
        clean = input('Clean Build Env before building (0=Clean Minimal, '
                      '1=Clean Full, 2=Don\'t clean) [0]: ')
        if not clean.strip():
            clean = 0
            break
        if clean.strip() in ('0', '1', '2'):
            clean = int(clean)
            break
        print(f'Unknown input {clean}. Try again...')
    return clean


def main():
    """Main entry point."""
    arch = _sel_arch()
    release = _sel_release()
    clean = _sel_clean()

    if arch == 2:
        jobs = [(True, release, clean), (False, release, clean)]
    elif arch == 1:
        jobs = [(False, release, clean)]
    else:
        jobs = [(True, release, clean)]

    for arm64, rel, cln in jobs:
        cmd = 0 if cln == 2 else 1
        if cln == 1:
            cmd = cmd | 2
        if arm64:
            cmd = cmd | 4
        if rel:
            cmd = cmd | 8
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(UDS)
        sock.sendall(struct.pack('<B', cmd))
        envid = sock.recv(4096).decode('utf8')
        envname = f'[{envid}]'
        arch = 'arm64-v8a' if arm64 else 'armeabi-v7a'
        print(f'Log output for {arch} build displayed in "{envname} {arch}"')
        time.sleep(0.5)

if __name__ == '__main__':
    main()
