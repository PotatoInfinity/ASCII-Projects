import json 
import os 
import curses 

HIGH_SCORE_FILE =".high_scores.json"

def init_colors ():
    """Initialize curses color pairs, handles errors gracefully if colors not supported."""
    if not curses .has_colors ():
        return False 
    try :
        curses .start_color ()
        try :
            curses .use_default_colors ()
            bg =-1 
        except Exception :
            bg =curses .COLOR_BLACK 

        curses .init_pair (1 ,curses .COLOR_GREEN ,bg )
        curses .init_pair (2 ,curses .COLOR_CYAN ,bg )
        curses .init_pair (3 ,curses .COLOR_RED ,bg )
        curses .init_pair (4 ,curses .COLOR_YELLOW ,bg )
        curses .init_pair (5 ,curses .COLOR_MAGENTA ,bg )
        curses .init_pair (6 ,curses .COLOR_BLUE ,bg )
        curses .init_pair (7 ,curses .COLOR_WHITE ,bg )
        return True 
    except Exception :
        return False 

def check_terminal_size (stdscr ,min_rows =24 ,min_cols =80 ):
    """
    Checks if the terminal meets the minimum size requirements.
    If not, renders a warning message and returns False.
    """
    rows ,cols =stdscr .getmaxyx ()
    if rows <min_rows or cols <min_cols :
        stdscr .clear ()
        msg =f"Terminal too small! Required: {min_cols }x{min_rows }"
        current =f"Current: {cols }x{rows }"
        instruction ="Please resize your terminal and press any key to try again, or Q to quit."

        try :
            stdscr .addstr (rows //2 -2 ,max (0 ,(cols -len (msg ))//2 ),msg ,curses .color_pair (3 )|curses .A_BOLD )
            stdscr .addstr (rows //2 -1 ,max (0 ,(cols -len (current ))//2 ),current ,curses .color_pair (7 ))
            stdscr .addstr (rows //2 +1 ,max (0 ,(cols -len (instruction ))//2 ),instruction ,curses .color_pair (2 ))
        except curses .error :
            pass 

        stdscr .refresh ()
        return False 
    return True 

def load_high_score (game_name ):
    """Loads high score for a specific game from a persistent local JSON file."""
    if not os .path .exists (HIGH_SCORE_FILE ):
        return 0 
    try :
        with open (HIGH_SCORE_FILE ,"r")as f :
            data =json .load (f )
            return data .get (game_name ,0 )
    except Exception :
        return 0 

def save_high_score (game_name ,score ):
    """Saves high score for a specific game to a persistent local JSON file if it is a new record."""
    data ={}
    if os .path .exists (HIGH_SCORE_FILE ):
        try :
            with open (HIGH_SCORE_FILE ,"r")as f :
                data =json .load (f )
        except Exception :
            pass 

    current_high =data .get (game_name ,0 )
    if score >current_high :
        data [game_name ]=score 
        try :
            with open (HIGH_SCORE_FILE ,"w")as f :
                json .dump (data ,f )
            return True 
        except Exception :
            return False 
    return False 

