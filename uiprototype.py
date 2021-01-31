import sys
import time
import curses
from curses import wrapper
import subprocess

class Panel:
    c1 = '┌'
    c2 = '┐'
    c3 = '└'
    c4 = '┘'
    ch = '─'
    cv = '│'
    sp = ' '
    titleStart = '['
    titleEnd = ']'

    def __init__(self, stdscr, x, y, title, w, h):
        self.stdscr = stdscr
        self.x = x
        self.y = y
        self.title = title
        self.w = w
        self.h = h
    
    def render(self):
        fullTitle = self.titleStart + self.title + self.titleEnd
        titleLen = len(fullTitle)
        vTopBar = "".join(map(lambda x: x*(self.w - titleLen - 1), self.ch)) + self.c2
        self.stdscr.addstr(self.y, self.x, self.c1 + self.ch + fullTitle + vTopBar)

        for i in range(1, self.h):
            filling = "".join(map(lambda x: x*(self.w), self.sp))
            self.stdscr.addstr(self.y + i, self.x, self.cv + filling + self.cv)

        self.stdscr.addstr(self.y + self.h, self.x, self.c3 + "".join(map(lambda x: x*(self.w), self.ch)) + self.c4)

    def renderStatusBar(self, content, x):
        self.stdscr.addstr(self.y + self.h, self.x + x, content, curses.A_REVERSE)
        self.stdscr.refresh()

class ProgressBar:
    # x                  x+w
    # [========-----------]
    # 74.5% Status

    def __init__(self, stdscr, x, y, title, w=50):
        self.stdscr = stdscr
        self.x = x
        self.y = y
        self.title = title
        self.w = w

    def render(self, max, progress, status=''):
        bar_len = self.w - 2
        filled_len = int(round(bar_len * progress / float(max)))

        percents = round(100.0 * progress / float(max), 1)
        bar = '=' * filled_len + '-' * (bar_len - filled_len)
        self.stdscr.addstr(self.y, self.x, '[' + bar + ']')

        statusLabel = '%s%s %s\r' % (percents, '%', status)
        self.stdscr.addstr(self.y + 1, self.x, statusLabel)

def execute(cmd, parameters):
    result = subprocess.run([cmd, parameters], capture_output=True, text=True).stdout
    return result

def main(stdscr):
    ipconfig = '0.0.0.0'
    stdscr = curses.initscr()
    stdscr.clear()

    height,width = stdscr.getmaxyx()
    usableWindowWidth = width - 4

    mainPanel = Panel(stdscr, 1, 1, 'Dashboard', usableWindowWidth, height - 4)
    mainPanel.render()
    mainPanel.renderStatusBar(ipconfig, 3)

    p1 = ProgressBar(stdscr, 3, 4, 'Job 1', usableWindowWidth - 4)
    p2 = ProgressBar(stdscr, 3, 7, 'Job 2', usableWindowWidth - 4)

    total = 1000
    i = 0
    while i < total:
        p1.render(1000, i, 'axis')
        p2.render(1000, i, 'axis')
        time.sleep(0.001)  # emulating long-playing job
        i += 1
        stdscr.refresh()

    curses.echo()
    stdscr.refresh()

    curses.endwin()

wrapper(main)
