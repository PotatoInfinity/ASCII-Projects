import curses 
import random 
import time 
import common 

def draw_instructions (stdscr ,rows ,cols ):
    """Draws player controls at the bottom of the screen."""
    inst ="Controls: [SPACE] or [↑] to Flap  |  [Q] to Quit"
    try :
        stdscr .addstr (rows -2 ,(cols -len (inst ))//2 ,inst ,curses .color_pair (1 )|curses .A_DIM )
    except curses .error :
        pass 

def run_game (stdscr ):

    curses .curs_set (0 )
    stdscr .keypad (True )
    stdscr .timeout (33 )


    common .init_colors ()


    width ,height =50 ,20 


    if not common .check_terminal_size (stdscr ,min_rows =height +6 ,min_cols =width +10 ):
        stdscr .timeout (-1 )
        return 

    rows ,cols =stdscr .getmaxyx ()

    start_x =(cols -width )//2 
    start_y =(rows -height )//2 -1 


    bird_x =12 
    bird_y =float (height //2 )
    bird_velocity =0.0 
    gravity =0.08 
    jump_strength =-0.9 


    gap_height =6 
    pipes =[]

    def spawn_pipe ():

        gap_y =random .randint (2 ,height -gap_height -2 )
        pipes .append ({"x":float (width -2 ),"gap_y":gap_y ,"passed":False })


    spawn_pipe ()


    score =0 
    high_score =common .load_high_score ("flappy_bird")
    game_over =False 

    while not game_over :

        key =stdscr .getch ()

        if key in (ord ('q'),ord ('Q'),27 ):
            break 


        if key in (ord (' '),curses .KEY_UP ):
            bird_velocity =jump_strength 



        bird_velocity =min (0.8 ,bird_velocity +gravity )
        bird_y +=bird_velocity 


        if bird_y <1 :
            bird_y =1.0 
            bird_velocity =0.0 
        elif bird_y >=height -2 :

            game_over =True 


        pipe_speed =0.35 
        for pipe in pipes :
            pipe ["x"]-=pipe_speed 


        pipes =[p for p in pipes if p ["x"]>1 ]


        if len (pipes )>0 :
            last_pipe_x =pipes [-1 ]["x"]
            if last_pipe_x <width -18 :
                spawn_pipe ()
        else :
            spawn_pipe ()


        for pipe in pipes :
            px =int (pipe ["x"])


            if not pipe ["passed"]and px <bird_x :
                score +=1 
                pipe ["passed"]=True 


            if px ==bird_x or px ==bird_x -1 :
                by =int (bird_y )

                if by <pipe ["gap_y"]or by >=pipe ["gap_y"]+gap_height :
                    game_over =True 


        stdscr .clear ()


        score_str =f" SCORE: {score }   |   BEST: {high_score } "
        title_str =" v>  FLAPPY BIRD  v> "
        try :
            stdscr .addstr (start_y -3 ,(cols -len (title_str ))//2 ,title_str ,curses .color_pair (5 )|curses .A_BOLD )
            stdscr .addstr (start_y -2 ,(cols -len (score_str ))//2 ,score_str ,curses .color_pair (4 )|curses .A_BOLD )
        except curses .error :
            pass 


        try :

            stdscr .addstr (start_y ,start_x ,"┏"+"━"*(width -2 )+"┓",curses .color_pair (1 ))

            for y in range (1 ,height -1 ):
                stdscr .addstr (start_y +y ,start_x ,"┃",curses .color_pair (1 ))
                stdscr .addstr (start_y +y ,start_x +width -1 ,"┃",curses .color_pair (1 ))

            stdscr .addstr (start_y +height -1 ,start_x ,"┗"+"━"*(width -2 )+"┛",curses .color_pair (1 ))
        except curses .error :
            pass 


        for pipe in pipes :
            px =int (pipe ["x"])
            if 1 <px <width -1 :

                for y in range (1 ,pipe ["gap_y"]):
                    try :
                        stdscr .addstr (start_y +y ,start_x +px ,"█",curses .color_pair (3 ))
                    except curses .error :
                        pass 

                for y in range (pipe ["gap_y"]+gap_height ,height -1 ):
                    try :
                        stdscr .addstr (start_y +y ,start_x +px ,"█",curses .color_pair (3 ))
                    except curses .error :
                        pass 


        try :

            bird_char =">"if bird_velocity >=0 else "^"
            stdscr .addstr (start_y +int (bird_y ),start_x +bird_x ,bird_char ,curses .color_pair (4 )|curses .A_BOLD )
        except curses .error :
            pass 

        draw_instructions (stdscr ,rows ,cols )
        stdscr .refresh ()


    if game_over :

        common .save_high_score ("flappy_bird",score )

        try :
            curses .flash ()
        except Exception :
            pass 

        stdscr .timeout (-1 )
        stdscr .clear ()


        border_box ="========================================"
        g_over_msg ="* * *  C R A S H E D  * * *"
        result_msg =f"Final Score: {score } Pipes Cleared"
        any_key ="Press any key to return to main menu..."

        try :
            stdscr .addstr (rows //2 -4 ,(cols -len (border_box ))//2 ,border_box ,curses .color_pair (1 ))
            stdscr .addstr (rows //2 -2 ,(cols -len (g_over_msg ))//2 ,g_over_msg ,curses .color_pair (3 )|curses .A_BOLD )
            stdscr .addstr (rows //2 ,(cols -len (result_msg ))//2 ,result_msg ,curses .color_pair (4 )|curses .A_BOLD )
            stdscr .addstr (rows //2 +2 ,(cols -len (any_key ))//2 ,any_key ,curses .color_pair (7 )|curses .A_DIM )
            stdscr .addstr (rows //2 +4 ,(cols -len (border_box ))//2 ,border_box ,curses .color_pair (1 ))
        except curses .error :
            pass 

        stdscr .refresh ()
        stdscr .getch ()

    stdscr .timeout (-1 )
