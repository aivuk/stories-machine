import curses

window = curses.initscr()
window.nodelay(1)

while True:
    ch = window.getch()
    if ch >= 0:
        break


