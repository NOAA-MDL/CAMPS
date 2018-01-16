#!/usr/bin/env python
import sys
import os
relative_path = os.path.abspath(
            os.path.dirname(os.path.realpath(__file__)) + "/..")
sys.path.insert(0, relative_path)
import getpass
import curses
import time
import registry.util as util

clipboard = ""
STARTY = 6
print "LOADING NETCDF.YML"
netcdf = util.read_nc_config()


def center(str_len):
    lines = curses.LINES - 1
    cols = curses.COLS - 1
    return int(cols / 2) - int(str_len / 2) - 1


def print_options(stdscr):
    #stdscr.addstr(6,0,'e - enter variable editing')
    stdscr.addstr(7, 0, 's - search variables')
    stdscr.addstr(8, 0, 'h - help')
    stdscr.addstr(9, 0, 'q - quit this program')


def clear(stdscr, y=5):
    stdscr.move(y, 0)
    stdscr.clrtobot()
    stdscr.refresh()


def var_editing(stdscr):
    nc_vars = netcdf.variables
    START_EDIT = STARTY + 7
    clear(stdscr)
    intro_str = "Editing: "
    stdscr.addstr(STARTY, 0, "Editing: ")
    stdscr.addstr(STARTY, len(intro_str), clipboard, curses.color_pair(4))
    stdscr.addstr(STARTY + 1, 0, "OPTIONS: ")
    stdscr.addstr(STARTY + 2, 0, "t - Add Time Bounds")
    stdscr.addstr(STARTY + 3, 0, "p - Add Plev Bounds")
    stdscr.addstr(STARTY + 4, 0, "e - Add Elev Bounds")
    stdscr.addstr(STARTY + 5, 0, "q - quit ")

    stdscr.addstr(START_EDIT, 0, "Variable metadata:")
    if clipboard in nc_vars:
        for i, (key, value) in enumerate(nc_vars[clipboard]['attribute'].iteritems()):
            stdscr.addstr(START_EDIT + 1 + i, 0, key)
            stdscr.addstr(START_EDIT + 1 + i, 25, str(value))
    else:  # If a new variable
        stdscr.addstr(
            STARTY + 1, 0, "You're creating a new variable!", curses.color_pair(3))
    stdscr.refresh()
    while True:  # enter or carriage return exits
        try:
            char = stdscr.getch()
        except:
            break
        # enter or carriage return exits
        if char == 10 or char == 13 or char == ord('q'):
            break
        # elif char == 127 or char == 8 or char == 263: #backspace
        elif char == curses.KEY_DOWN:
            pass
        elif char == curses.KEY_UP:
            pass
        else:
            ascii_char = unichr(char)
    clear(stdscr)


def display_help(stdscr):
    clear(stdscr)
    stdscr.addstr(STARTY, 0, "Search for variables using the search tool")
    stdscr.addstr(STARTY + 1, 0, "and edit them using the editor!")
    stdscr.addstr(
        STARTY + 2, 0, "highlighted variables will be copied to the clipboard.")
    stdscr.addstr(STARTY + 4, 0, "Developed by Riley")
    stdscr.refresh()
    num_seconds = 5
    for i in range(num_seconds):
        stdscr.addstr(STARTY + 6, 0, "Returning home in " +
                      str(num_seconds - i) + " seconds")
        stdscr.refresh()
        time.sleep(1)
    clear(stdscr)


def search_nc(all_vars, subset):
    possible_matches = []
    for name, metadata in all_vars.iteritems():
        if subset in name:
            possible_matches.append(name)
            continue
        if 'standard_name' in metadata['attribute']:
            if subset in metadata['attribute']['standard_name']:
                possible_matches.append(name)
        if 'long_name' in metadata['attribute']:
            if subset in metadata['attribute']['long_name']:
                possible_matches.append(name)
        if 'units' in metadata['attribute']:
            if subset in metadata['attribute']['units']:
                possible_matches.append(name)
    return possible_matches


def loading(stdscr):
    clear(stdscr)
    stdscr.addstr(STARTY, 0, "   Loading... ", curses.A_STANDOUT)
    stdscr.refresh()


def search(stdscr):
    loading(stdscr)
    all_vars = netcdf.variables
    clear(stdscr)
    searchX = 6
    stdscr.addstr(
        STARTY, 0, "Start typing a search term to narrow down variables")
    stdscr.addstr(
        STARTY + 1, 0, "Pressing Enter will exit. Arrow up/down to select variable.")
    stdscr.addstr(STARTY + 2, 0, "var : _________________")
    stdscr.refresh()
    selection = -1
    s = ""
    char = ""
    possible_matches = []
    while True:  # enter or carriage return exits
        stdscr.move(STARTY + 2, searchX)
        char = stdscr.getch()

        # stdscr.addstr(str(char))
        # stdscr.refresh()
        # time.sleep(4)
        if char == 10 or char == 13:  # enter or carriage return exits
            break
        elif char == 127 or char == 8 or char == 263:  # backspace
            if s == "":
                continue
            stdscr.move(STARTY + 2, searchX - 1)
            stdscr.addstr('_')
            stdscr.move(STARTY + 2, searchX - 1)
            searchX -= 1
            s = s[0:-1]
            possible_matches = search_nc(all_vars, s)
        elif char == curses.KEY_DOWN:
            if selection >= curses.LINES - 1 or selection > len(possible_matches) - 2:
                selection = -1
            selection += 1
        elif char == curses.KEY_UP:
            if selection <= 0:
                selection = len(possible_matches)
            selection -= 1
        else:
            ascii_char = unichr(char)
            stdscr.addstr(ascii_char)
            s += ascii_char
            # stdscr.addstr(str(char))
            searchX += 1
            possible_matches = search_nc(all_vars, s)
        if selection >= 0 and selection <= len(possible_matches) - 1:
            set_clipboard(possible_matches[selection])
        elif len(possible_matches) == 1:
            selection = 0
            set_clipboard(possible_matches[selection])
        else:
            set_clipboard(s)
        display_matches(stdscr, possible_matches, selection)
        display_clipboard(stdscr)
    clear(stdscr)
    var_editing(stdscr)

    # time.sleep(1)


def set_clipboard(val):
    global clipboard
    clipboard = val


def display_clipboard(stdscr):
    stdscr.move(STARTY + 2, 25)
    stdscr.clrtoeol()
    if clipboard == "":
        return
    stdscr.addstr(STARTY + 2, 25, " " + clipboard + " ", curses.color_pair(4))
    stdscr.refresh()


def display_matches(stdscr, matches, selection):
    clear(stdscr, STARTY + 4)
    stdscr.addstr(STARTY + 4, 0, "Possible Matches:")
    for i, match in enumerate(matches):
        if selection == i:
            stdscr.addstr(STARTY + 5 + i, 0, match, curses.color_pair(3))
        else:
            stdscr.addstr(STARTY + 5 + i, 0, match)
        if STARTY + 5 + i == curses.LINES - 1:
            return


if __name__ == "__main__":
    username = getpass.getuser()
    
    stdscr = curses.initscr()
    curses.start_color()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)
    lines = curses.LINES - 1
    cols = curses.COLS - 1
    #center = lambda str_len : int(cols/2) - int(str_len/2) - 1
    curses.curs_set(False)
    
    # Init Color Pairs
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_WHITE)
    curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_YELLOW)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_RED)
    curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_GREEN)
    
    s = "Hello " + username + "!"
    stdscr.addstr(1, center(len(s)), s, curses.color_pair(1))
    s = "Welcome to the interactive netcdf variable editor!"
    stdscr.addstr(2, center(len(s)), s)
    s = '-' * cols
    stdscr.addstr(4, 0, s, curses.color_pair(2))
    stdscr.refresh()
    
    ans = 0
    while ans != ord('q'):
        print_options(stdscr)
        ans = stdscr.getch()
        if ans == ord('e'):
            var_editing(stdscr)
        elif ans == ord('s'):
            search(stdscr)
        elif ans == ord('h'):
            display_help(stdscr)
    
    # Terminate curses
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()
