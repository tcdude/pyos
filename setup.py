"""
Copyright (c) 2019 Tiziano Bettio

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

from distutils.core import setup
from distutils.core import Extension
from setuptools import find_packages

__author__ = 'Tiziano Bettio'
__copyright__ = 'Copyright (C) 2019 Tiziano Bettio'
__license__ = 'MIT'
__version__ = '0.2'


options = {'apk': {'debug': None,
                   'bootstrap': 'sdl2',
                   'requirements': 'libffi,sdl2,sdl2_image,sdl2_ttf,python3,'
                                   'pysdl2,Pillow,plyer',
                   'package': 'com.tizilogic.pyos',
                   'android-api': 28,
                   'arch': 'arm64-v8a',  # switch for builds
                   'dist-name': 'pyos-beta',
                   'icon': 'pyos/assets/app-images/icon192.png',
                   'presplash': 'pyos/assets/app-images/splash.png',
                   'presplash-color': '#224422',
                   }}

setup(
    name='Simple Solitaire',
    version='0.2.5',
    description='An ad free, simple solitaire game',
    author='tcdude',
    author_email='tizilogic@gmail.com',
    packages=find_packages(),
    options=options,
    package_data={'pyos': [
        '*.py',
        'ui/*.py',
        'engine/*.py',
        'assets/images/*.png',
        'assets/fonts/*.ttf'
    ]},
    install_requires=[
        'plyer',
        'Pillow',
        'pytest',
        'Cython',
        'git+https://github.com/tcdude/foolysh.git'
    ],
)
