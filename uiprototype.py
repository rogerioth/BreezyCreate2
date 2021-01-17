import sys
import time
import curses
from curses import wrapper
import subprocess

def execute(cmd, parameters):
    result = subprocess.run([cmd, parameters], capture_output=True, text=True).stdout
    return result

def panel(stdscr, x, y, title, w, h):
    c1 = '┌'
    c2 = '┐'
    c3 = '└'
    c4 = '┘'
    ch = '─'
    cv = '│'
    sp = ' '
    titleStart = '['
    titleEnd = ']'
    fullTitle = titleStart + title + titleEnd
    titleLen = len(fullTitle)
    vTopBar = "".join(map(lambda x: x*(w - titleLen - 1), ch)) + c2
    stdscr.addstr(y, x, c1 + ch + fullTitle + vTopBar)

    for i in range(1, h):
        filling = "".join(map(lambda x: x*(w), sp))
        stdscr.addstr(y + i, x, cv + filling + cv)

    stdscr.addstr(y + h, x, c3 + "".join(map(lambda x: x*(w), ch)) + c4)

def progress(stdscr, count, total, row, status=''):
    bar_len = 50
    filled_len = int(round(bar_len * count / float(total)))

    percents = round(100.0 * count / float(total), 1)
    bar = '=' * filled_len + '-' * (bar_len - filled_len)

    content = '[%s] %s%s ...%s\r' % (bar, percents, '%', status)
    stdscr.addstr(row, 4, content)
    # needs to re-add right border again

def main(stdscr):
    ipconfig = '0.0.0.0'
    stdscr = curses.initscr()
    stdscr.clear()

    height,width = stdscr.getmaxyx()

    panel(stdscr, 1,1, 'Dashboard', width - 4, height - 4)

    stdscr.addstr(height - 4, 5, '' + ipconfig, curses.A_REVERSE)
    stdscr.refresh()

    total = 1000
    i = 0
    while i < total:
        progress(stdscr, i, total, 4, status='Doing very long job')
        progress(stdscr, i, total, 5, status='Second bar')
        time.sleep(0.01)  # emulating long-playing job
        i += 1
        stdscr.refresh()

    curses.echo()
    stdscr.refresh()

    curses.endwin()

wrapper(main)
