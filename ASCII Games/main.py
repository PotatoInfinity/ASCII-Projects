import curses
import sys
import common
import pong
import flappy_bird
import pacman
import snake
import space_invaders
import tetris
import mario
import doom
import donkey_kong
import street_fighter
import sonic
import crash

LOGO = [
    "  █████╗  ███████╗ ██████╗██╗██╗          ██████╗  █████╗ ███╗   ███╗███████╗███████╗",
    " ██╔══██╗ ██╔════╝██╔════╝██║██║         ██╔════╝ ██╔══██╗████╗ ████║██╔════╝██╔════╝",
    " ███████║ ███████╗██║     ██║██║         ██║  ███╗███████║██╔████╔██║█████╗  ███████╗ ",
    " ██╔══██║ ╚════██║██║     ██║██║         ██║   ██║██╔══██║██║╚██╔╝██║██╔══╝  ╚════██║ ",
    " ██║  ██║ ███████║╚██████╗██║██║         ╚██████╔╝██║  ██║██║ ╚═╝ ██║███████╗███████║ ",
    " ╚═╝  ╚═╝ ╚══════╝ ╚═════╝╚═╝╚═╝         ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚══════╝",
]

MENU_ITEMS = [
    ("[o]  PONG",           "Defeat the AI in a fast-paced classic table tennis match."),
    ("v>   FLAPPY BIRD",    "Flap your wings and navigate safely through a series of pipes."),
    ("C.   PACMAN",         "Navigate the maze, eat all the dots, and dodge the hungry ghosts."),
    ("~O   SNAKE",          "Slither around, eat apples to grow, and avoid biting your own tail."),
    ("=^=  SPACE INVADERS", "Defend Earth from descending waves of alien invaders."),
    ("[]   TETRIS",         "Rotate and drop blocks to clear lines in this classic puzzle game."),
    ("M    SUPER ASCII BROS","Endless platforming! Jump over pits and stomp Goombas."),
    ("█▓▒░ DOOM",           "3D ASCII Raycasting — explore the maze, find enemies, and shoot!"),
    ("DK   DONKEY KONG",    "Climb ladders and jump over rolling barrels to reach the top."),
    ("X    STREET FIGHTER II","1v1 side-scrolling fighting. Throw fireballs and block attacks!"),
    ("&    ASCII THE HEDGEHOG","Run at extreme speeds, dodge spikes, and collect rings!"),
    ("X    BANDICOOT RUN",  "Pseudo-3D forward running! Dodge TNTs and collect Wumpas!"),
    ("[X]  EXIT GAME",      "Safely return to your terminal shell."),
]

def draw_menu(stdscr, selected_idx):
    stdscr.clear()

    if not common.check_terminal_size(stdscr, min_rows=30, min_cols=90):
        return

    rows, cols = stdscr.getmaxyx()

    try:
        stdscr.addstr(0, 0, "═" * cols, curses.color_pair(2))
        stdscr.addstr(rows - 1, 0, "═" * cols, curses.color_pair(2))
    except curses.error:
        pass

    logo_y = 1
    for i, line in enumerate(LOGO):
        logo_x = max(0, (cols - len(line)) // 2)
        try:
            color = curses.color_pair(5) if i % 2 == 0 else curses.color_pair(2)
            stdscr.addstr(logo_y + i, logo_x, line, color | curses.A_BOLD)
        except curses.error:
            pass

    subtitle = "─── CHOOSE YOUR ARCADE CHALLENGE ───"
    try:
        stdscr.addstr(logo_y + len(LOGO) + 1, (cols - len(subtitle)) // 2, subtitle,
                      curses.color_pair(4) | curses.A_DIM)
    except curses.error:
        pass

    menu_y = logo_y + len(LOGO) + 2

    box_margin = 4
    box_width = cols - (box_margin * 2)
    box_x = box_margin

    num_items = len(MENU_ITEMS)

    try:
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(menu_y - 1, box_x, "┏" + "━" * (box_width - 2) + "┓")
        for i in range(num_items + 3):
            stdscr.addstr(menu_y + i, box_x, "┃")
            stdscr.addstr(menu_y + i, box_x + box_width - 1, "┃")
        stdscr.addstr(menu_y + num_items + 3, box_x, "┗" + "━" * (box_width - 2) + "┛")
        stdscr.attroff(curses.color_pair(2))
    except curses.error:
        pass

    for idx, (name, description) in enumerate(MENU_ITEMS):
        item_y = menu_y + idx
        if idx == selected_idx:
            selector_text = f" ➔  {name}"
            pad = box_width - 6 - len(selector_text)
            selector_text += " " * max(0, pad)
            try:
                stdscr.addstr(item_y, box_x + 3, selector_text, curses.color_pair(1) | curses.A_BOLD)
                stdscr.addstr(menu_y + num_items + 1, box_x + 3, "─" * (box_width - 6), curses.color_pair(2))
                stdscr.addstr(menu_y + num_items + 2, box_x + 3, f"» {description}"[:box_width - 6],
                              curses.color_pair(1) | curses.A_DIM)
            except curses.error:
                pass
        else:
            selector_text = f"    {name}"
            try:
                stdscr.addstr(item_y, box_x + 3, selector_text, curses.color_pair(7))
            except curses.error:
                pass

    footer = "Navigate: [↑/↓]  |  Select: [ENTER]  |  Quit: [Q / ESC]"
    try:
        stdscr.addstr(rows - 3, (cols - len(footer)) // 2, footer, curses.color_pair(2) | curses.A_BOLD)
    except curses.error:
        pass

    stdscr.refresh()

def main(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)
    stdscr.nodelay(False)

    common.init_colors()

    selected_idx = 0
    num_items = len(MENU_ITEMS)

    while True:
        draw_menu(stdscr, selected_idx)
        key = stdscr.getch()

        if key in (curses.KEY_UP, ord('k'), ord('K')):
            selected_idx = (selected_idx - 1) % num_items
        elif key in (curses.KEY_DOWN, ord('j'), ord('J')):
            selected_idx = (selected_idx + 1) % num_items
        elif key in (10, 13, curses.KEY_ENTER):
            if selected_idx == 0:  pong.run_game(stdscr)
            elif selected_idx == 1: flappy_bird.run_game(stdscr)
            elif selected_idx == 2: pacman.run_game(stdscr)
            elif selected_idx == 3: snake.run_game(stdscr)
            elif selected_idx == 4: space_invaders.run_game(stdscr)
            elif selected_idx == 5: tetris.run_game(stdscr)
            elif selected_idx == 6: mario.run_game(stdscr)
            elif selected_idx == 7: doom.run_game(stdscr)
            elif selected_idx == 8: donkey_kong.run_game(stdscr)
            elif selected_idx == 9: street_fighter.run_game(stdscr)
            elif selected_idx == 10: sonic.run_game(stdscr)
            elif selected_idx == 11: crash.run_game(stdscr)
            elif selected_idx == 12: break

            curses.curs_set(0)
            stdscr.keypad(True)
            stdscr.nodelay(False)
        elif key in (ord('q'), ord('Q'), 27):
            break

if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
    print("\nThanks for playing ASCII Games! See you soon!\n")
