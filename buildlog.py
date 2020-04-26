"""
Handles the log output to a tcl window.
"""

from multiprocessing import Queue
from queue import Empty
import re
import sys
import tkinter
import tkinter.scrolledtext
import tkinter.ttk

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


def escape_ansi(line):
    """Remove ANSI escape sequences from a string."""
    ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
    return ansi_escape.sub('', line)


class LogWindow:
    """The window to display the output."""
    def __init__(self, root, cmdq: Queue):
        self.root = root
        self.cmdq = cmdq
        self.notebook = tkinter.ttk.Notebook(root)
        self.notebook.pack(expand=1, fill='both')
        self.text = {}
        self.root.after(10, self.log)

    def add_tab(self, title):
        """Add a new logging tab."""
        if title in self.text:
            raise ValueError('A tab with that name already exists.')
        frame = tkinter.ttk.Frame(self.notebook)
        self.notebook.add(frame, text=title)
        text = tkinter.scrolledtext.ScrolledText(frame, state='disabled',
                                                 bg='Black', fg='LightGray')
        text.configure(font='TkFixedFont')
        text.pack(expand=1, fill='both')
        self.text[title] = text

    def remove_tab(self, title):
        """Removes a logging tab."""
        if title not in self.text:
            raise ValueError(f'Unknown tab "{title}".')
        self.text[title].pack_forget()
        for i in range(self.notebook.index('end')):
            if self.notebook.tab(i)['text'] == title:
                self.notebook.forget(i)
                return
        raise RuntimeError('Unable to find the correct tab.')

    def log(self):
        """Called every 100ms."""
        while True:
            try:
                action, title, content = self.cmdq.get(block=False)
            except Empty:
                break
            else:
                if title == 'QUIT':
                    self.quit()
                if action == 'ADD':
                    self.add_tab(title)
                elif action == 'LOG':
                    self._update_text(title, content)
                else:
                    self.remove_tab(title)
        self.root.after(10, self.log)

    def quit(self):
        """Close the main loop."""
        self.root.destroy()
        sys.exit(0)

    def _update_text(self, title, text):
        text = escape_ansi(text)
        if '- Download ' in text:
            return
        self.text[title].configure(state='normal')
        self.text[title].insert(tkinter.END, text)
        self.text[title].configure(state='disabled')
        # Autoscroll to the bottom
        self.text[title].yview(tkinter.END)


def log_thread(title, cmdq):
    """Start a new log window."""
    root = tkinter.Tk()
    root.title(title)
    root.geometry('1080x600+6200+0')
    _ = LogWindow(root, cmdq)
    root.mainloop()
