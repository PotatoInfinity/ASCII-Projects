import curses 
import random 
import time 
import common 

def draw_instructions (stdscr ,rows ,cols ):
    inst ="Controls: [ARROW KEYS] to Move  |  [Q] to Quit"
    try :
        stdscr .addstr (rows -2 ,(cols -len (inst ))//2 ,inst ,curses .color_pair (1 )|curses .A_DIM )
    except curses .error :
        pass 

def run_game (stdscr ):
    curses .curs_set (0 )
    stdscr .keypad (True )

    common .init_colors ()

    width ,height =40 ,20 
    if not common .check_terminal_size (stdscr ,min_rows =height +6 ,min_cols =width +10 ):
        stdscr .timeout (-1 )
        return 

    rows ,cols =stdscr .getmaxyx ()
    start_x =(cols -width )//2 
    start_y =(rows -height )//2 -1 

    score =0 
    best_score =common .load_high_score ("snake")


    snake =[(height //2 ,width //2 )]

    dy ,dx =0 ,1 
    next_dy ,next_dx =0 ,1 

    food =None 

    def spawn_food ():
        while True :
            fy =random .randint (1 ,height -2 )
            fx =random .randint (1 ,width -2 )
            if (fy ,fx )not in snake :
                return (fy ,fx )

    food =spawn_food ()

    game_over =False 


    base_timeout =150 

    while not game_over :

        current_timeout =max (50 ,base_timeout -(score *2 ))
        if dx !=0 :
            current_timeout =int (current_timeout *0.6 )
        stdscr .timeout (current_timeout )


        key =stdscr .getch ()

        if key in (ord ('q'),ord ('Q'),27 ):
            break 

        if key ==curses .KEY_UP and dy !=1 :
            next_dy ,next_dx =-1 ,0 
        elif key ==curses .KEY_DOWN and dy !=-1 :
            next_dy ,next_dx =1 ,0 
        elif key ==curses .KEY_LEFT and dx !=1 :
            next_dy ,next_dx =0 ,-1 
        elif key ==curses .KEY_RIGHT and dx !=-1 :
            next_dy ,next_dx =0 ,1 


        dy ,dx =next_dy ,next_dx 


        head_y ,head_x =snake [0 ]
        new_y =head_y +dy 
        new_x =head_x +dx 


        if new_y <=0 or new_y >=height -1 or new_x <=0 or new_x >=width -1 :
            game_over =True 
            continue 


        if (new_y ,new_x )in snake :
            game_over =True 
            continue 

        snake .insert (0 ,(new_y ,new_x ))


        if (new_y ,new_x )==food :
            score +=10 
            food =spawn_food ()
        else :
            snake .pop ()


        stdscr .clear ()

        header_str =f" SCORE: {score }   |   BEST: {best_score } "
        title_str =" ~O  SNAKE ARCADE  O~ "
        try :
            stdscr .addstr (start_y -3 ,(cols -len (title_str ))//2 ,title_str ,curses .color_pair (1 )|curses .A_BOLD )
            stdscr .addstr (start_y -2 ,(cols -len (header_str ))//2 ,header_str ,curses .color_pair (4 )|curses .A_BOLD )
        except curses .error :
            pass 


        try :
            stdscr .addstr (start_y ,start_x ,"┏"+"━"*(width -2 )+"┓",curses .color_pair (2 ))
            for y in range (1 ,height -1 ):
                stdscr .addstr (start_y +y ,start_x ,"┃",curses .color_pair (2 ))
                stdscr .addstr (start_y +y ,start_x +width -1 ,"┃",curses .color_pair (2 ))
            stdscr .addstr (start_y +height -1 ,start_x ,"┗"+"━"*(width -2 )+"┛",curses .color_pair (2 ))
        except curses .error :
            pass 


        try :
            stdscr .addstr (start_y +food [0 ],start_x +food [1 ],"*",curses .color_pair (3 )|curses .A_BOLD )
        except curses .error :
            pass 


        for i ,(sy ,sx )in enumerate (snake ):
            char ="@"if i ==0 else "o"
            color =curses .color_pair (4 )if i ==0 else curses .color_pair (1 )
            try :
                stdscr .addstr (start_y +sy ,start_x +sx ,char ,color )
            except curses .error :
                pass 

        draw_instructions (stdscr ,rows ,cols )
        stdscr .refresh ()

    stdscr .timeout (-1 )

    if game_over :
        common .save_high_score ("snake",score )
        try :
            curses .flash ()
        except Exception :
            pass 

        time .sleep (0.5 )
        curses .flushinp ()

        stdscr .clear ()
        border_box ="========================================"
        g_over_msg ="* * *  G A M E   O V E R  * * *"
        result_msg =f"Final Score: {score }"
        any_key ="Press any key to return to main menu..."

        try :
            stdscr .addstr (rows //2 -4 ,(cols -len (border_box ))//2 ,border_box ,curses .color_pair (2 ))
            stdscr .addstr (rows //2 -2 ,(cols -len (g_over_msg ))//2 ,g_over_msg ,curses .color_pair (3 )|curses .A_BOLD )
            stdscr .addstr (rows //2 ,(cols -len (result_msg ))//2 ,result_msg ,curses .color_pair (4 )|curses .A_BOLD )
            stdscr .addstr (rows //2 +2 ,(cols -len (any_key ))//2 ,any_key ,curses .color_pair (7 )|curses .A_DIM )
            stdscr .addstr (rows //2 +4 ,(cols -len (border_box ))//2 ,border_box ,curses .color_pair (2 ))
        except curses .error :
            pass 

        stdscr .refresh ()
        stdscr .getch ()

    stdscr .timeout (-1 )
