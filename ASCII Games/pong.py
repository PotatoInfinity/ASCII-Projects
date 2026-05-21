import curses 
import random 
import time 
import common 

def draw_instructions (stdscr ,rows ,cols ):
    """Draws player instructions at the bottom of the screen."""
    inst ="Controls: [W / S] or [↑ / ↓] to Move  |  [Q] to Quit"
    try :
        stdscr .addstr (rows -2 ,(cols -len (inst ))//2 ,inst ,curses .color_pair (2 )|curses .A_DIM )
    except curses .error :
        pass 

def run_game (stdscr ):

    curses .curs_set (0 )
    stdscr .keypad (True )
    stdscr .timeout (33 )


    common .init_colors ()


    width ,height =60 ,20 


    if not common .check_terminal_size (stdscr ,min_rows =height +6 ,min_cols =width +10 ):
        stdscr .timeout (-1 )
        return 

    rows ,cols =stdscr .getmaxyx ()

    start_x =(cols -width )//2 
    start_y =(rows -height )//2 -1 


    player_score =0 
    cpu_score =0 
    max_score =5 


    paddle_height =3 
    player_y =height //2 -paddle_height //2 
    cpu_y =height //2 -paddle_height //2 


    ball_x =float (width //2 )
    ball_y =float (height //2 )

    def reset_ball (direction =None ):
        nonlocal ball_x ,ball_y ,ball_dx ,ball_dy 
        ball_x =float (width //2 )
        ball_y =float (height //2 )


        if direction is None :
            ball_dx =0.6 if random .choice ([True ,False ])else -0.6 
        else :
            ball_dx =direction 


        ball_dy =random .uniform (-0.4 ,0.4 )

    ball_dx =0.0 
    ball_dy =0.0 
    reset_ball ()


    cpu_speed =0.35 

    game_over =False 
    winner =""

    while not game_over :

        key =stdscr .getch ()

        if key in (ord ('q'),ord ('Q'),27 ):
            break 


        if key in (ord ('w'),ord ('W'),curses .KEY_UP ):
            player_y =max (1 ,player_y -1 )
        elif key in (ord ('s'),ord ('S'),curses .KEY_DOWN ):
            player_y =min (height -paddle_height -1 ,player_y +1 )

        prev_ball_x =ball_x 

        ball_x +=ball_dx 
        ball_y +=ball_dy 



        cpu_center =cpu_y +(paddle_height /2 )
        if abs (ball_y -cpu_center )>0.5 :
            if ball_y >cpu_center :
                cpu_y =min (float (height -paddle_height -1 ),cpu_y +cpu_speed )
            else :
                cpu_y =max (1.0 ,cpu_y -cpu_speed )


        if ball_y <=1 :
            ball_y =1.0 
            ball_dy =-ball_dy 
        elif ball_y >=height -2 :
            ball_y =float (height -2 )
            ball_dy =-ball_dy 



        if ball_dx <0 and ball_x <=2.2 and prev_ball_x >=1.8 :
            if player_y -0.5 <=ball_y <=player_y +paddle_height +0.5 :

                ball_x =2.3 
                ball_dx =-ball_dx 

                ball_dx *=1.1 

                paddle_center =player_y +(paddle_height /2 )
                hit_offset =ball_y -paddle_center 
                ball_dy =hit_offset *0.5 


        if ball_dx >0 and ball_x >=width -3.2 and prev_ball_x <=width -2.8 :
            if cpu_y -0.5 <=ball_y <=cpu_y +paddle_height +0.5 :

                ball_x =float (width -3.3 )
                ball_dx =-ball_dx 
                ball_dx *=1.1 

                paddle_center =cpu_y +(paddle_height /2 )
                hit_offset =ball_y -paddle_center 
                ball_dy =hit_offset *0.5 


        if ball_x <0 :
            cpu_score +=1 
            if cpu_score >=max_score :
                game_over =True 
                winner ="CPU"
            else :
                reset_ball (direction =0.5 )
        elif ball_x >width :
            player_score +=1 
            if player_score >=max_score :
                game_over =True 
                winner ="PLAYER"

                current_wins =common .load_high_score ("pong_wins")
                common .save_high_score ("pong_wins",current_wins +1 )
            else :
                reset_ball (direction =-0.5 )


        stdscr .clear ()


        wins =common .load_high_score ("pong_wins")
        score_str =f" PLAYER: {player_score }   |   CPU: {cpu_score }   |   BEST WINS: {wins } "
        title_str =" [o]  PONG ARCADE  [o] "
        try :
            stdscr .addstr (start_y -3 ,(cols -len (title_str ))//2 ,title_str ,curses .color_pair (5 )|curses .A_BOLD )
            stdscr .addstr (start_y -2 ,(cols -len (score_str ))//2 ,score_str ,curses .color_pair (4 )|curses .A_BOLD )
        except curses .error :
            pass 


        try :

            stdscr .addstr (start_y ,start_x ,"┏"+"━"*(width -2 )+"┓",curses .color_pair (2 ))

            for y in range (1 ,height -1 ):
                stdscr .addstr (start_y +y ,start_x ,"┃",curses .color_pair (2 ))

                if y %2 ==1 :
                    stdscr .addstr (start_y +y ,start_x +(width //2 ),":",curses .color_pair (7 )|curses .A_DIM )
                stdscr .addstr (start_y +y ,start_x +width -1 ,"┃",curses .color_pair (2 ))

            stdscr .addstr (start_y +height -1 ,start_x ,"┗"+"━"*(width -2 )+"┛",curses .color_pair (2 ))
        except curses .error :
            pass 


        for y in range (paddle_height ):
            try :
                stdscr .addstr (start_y +int (player_y )+y ,start_x +2 ,"█",curses .color_pair (1 )|curses .A_BOLD )
            except curses .error :
                pass 


        for y in range (paddle_height ):
            try :
                stdscr .addstr (start_y +int (cpu_y )+y ,start_x +width -3 ,"█",curses .color_pair (3 )|curses .A_BOLD )
            except curses .error :
                pass 


        try :
            stdscr .addstr (start_y +int (ball_y ),start_x +int (ball_x ),"o",curses .color_pair (4 )|curses .A_BOLD )
        except curses .error :
            pass 

        draw_instructions (stdscr ,rows ,cols )
        stdscr .refresh ()


    if game_over :
        stdscr .timeout (-1 )
        stdscr .clear ()


        border_box ="========================================"
        g_over_msg ="* * *  G A M E   O V E R  * * *"

        if winner =="PLAYER":
            result_msg ="VICTORY! You defeated the CPU!"
            color =curses .color_pair (1 )
        else :
            result_msg ="DEFEAT! The CPU wins this round."
            color =curses .color_pair (3 )

        any_key ="Press any key to return to main menu..."

        try :
            stdscr .addstr (rows //2 -4 ,(cols -len (border_box ))//2 ,border_box ,curses .color_pair (2 ))
            stdscr .addstr (rows //2 -2 ,(cols -len (g_over_msg ))//2 ,g_over_msg ,color |curses .A_BOLD )
            stdscr .addstr (rows //2 ,(cols -len (result_msg ))//2 ,result_msg ,color |curses .A_BOLD )
            stdscr .addstr (rows //2 +2 ,(cols -len (any_key ))//2 ,any_key ,curses .color_pair (7 )|curses .A_DIM )
            stdscr .addstr (rows //2 +4 ,(cols -len (border_box ))//2 ,border_box ,curses .color_pair (2 ))
        except curses .error :
            pass 

        stdscr .refresh ()
        stdscr .getch ()

    stdscr .timeout (-1 )
