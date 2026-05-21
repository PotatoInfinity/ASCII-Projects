import curses 
import random 
import time 
import common 

def draw_instructions (stdscr ,rows ,cols ):
    inst ="Controls: [<- / ->] Move  |  [UP] Rotate  |  [DOWN] Soft Drop  |  [SPACE] Hard Drop"
    try :
        stdscr .addstr (rows -2 ,(cols -len (inst ))//2 ,inst ,curses .color_pair (2 )|curses .A_DIM )
    except curses .error :
        pass 


SHAPES =[
[(0 ,-1 ),(0 ,0 ),(0 ,1 ),(0 ,2 )],
[(-1 ,-1 ),(0 ,-1 ),(0 ,0 ),(0 ,1 )],
[(1 ,-1 ),(0 ,-1 ),(0 ,0 ),(0 ,1 )],
[(0 ,0 ),(0 ,1 ),(1 ,0 ),(1 ,1 )],
[(1 ,0 ),(1 ,1 ),(0 ,1 ),(0 ,2 )],
[(0 ,-1 ),(0 ,0 ),(0 ,1 ),(-1 ,0 )],
[(-1 ,0 ),(-1 ,1 ),(0 ,1 ),(0 ,2 )]
]

COLORS =[2 ,6 ,7 ,4 ,1 ,5 ,3 ]

def rotate_shape (shape_idx ,piece ):
    if shape_idx ==3 :
        return piece 
    return [(x ,-y )for y ,x in piece ]

def run_game (stdscr ):
    curses .curs_set (0 )
    stdscr .keypad (True )
    stdscr .timeout (40 )

    common .init_colors ()


    grid_w ,grid_h =10 ,20 
    render_w =grid_w *2 

    if not common .check_terminal_size (stdscr ,min_rows =grid_h +6 ,min_cols =render_w +30 ):
        stdscr .timeout (-1 )
        return 

    rows ,cols =stdscr .getmaxyx ()
    start_x =(cols -render_w )//2 
    start_y =(rows -grid_h )//2 -1 

    score =0 
    best_score =common .load_high_score ("tetris")
    lines_cleared =0 
    level =1 


    grid =[[0 for _ in range (grid_w )]for _ in range (grid_h )]

    game_over =False 

    current_piece =None 
    current_idx =0 
    cx ,cy =0 ,0 

    fall_timer =0 

    def spawn_piece ():
        nonlocal current_piece ,current_idx ,cx ,cy 
        current_idx =random .randint (0 ,6 )
        current_piece =list (SHAPES [current_idx ])
        cy =1 
        cx =grid_w //2 -1 

        if not check_valid (cy ,cx ,current_piece ):
            return False 
        return True 

    def check_valid (test_y ,test_x ,test_piece ):
        for y ,x in test_piece :
            ny ,nx =test_y +y ,test_x +x 
            if nx <0 or nx >=grid_w or ny <0 or ny >=grid_h :
                return False 
            if grid [ny ][nx ]!=0 :
                return False 
        return True 

    def lock_piece ():
        nonlocal score ,lines_cleared ,level 
        for y ,x in current_piece :
            if 0 <=cy +y <grid_h and 0 <=cx +x <grid_w :
                grid [cy +y ][cx +x ]=COLORS [current_idx ]


        lines_to_clear =[]
        for r in range (grid_h ):
            if all (cell !=0 for cell in grid [r ]):
                lines_to_clear .append (r )

        if lines_to_clear :
            num =len (lines_to_clear )

            for r in lines_to_clear :
                del grid [r ]

            for _ in range (num ):
                grid .insert (0 ,[0 for _ in range (grid_w )])


            multipliers =[40 ,100 ,300 ,1200 ]
            score +=multipliers [num -1 ]*level 
            lines_cleared +=num 
            level =(lines_cleared //10 )+1 

    if not spawn_piece ():
        game_over =True 

    while not game_over :
        fall_speed =max (2 ,20 -(level *2 ))


        key =stdscr .getch ()

        if key in (ord ('q'),ord ('Q'),27 ):
            break 

        if key ==curses .KEY_LEFT :
            if check_valid (cy ,cx -1 ,current_piece ):
                cx -=1 
        elif key ==curses .KEY_RIGHT :
            if check_valid (cy ,cx +1 ,current_piece ):
                cx +=1 
        elif key ==curses .KEY_UP :
            rotated =rotate_shape (current_idx ,current_piece )
            if check_valid (cy ,cx ,rotated ):
                current_piece =rotated 
        elif key ==curses .KEY_DOWN :
            if check_valid (cy +1 ,cx ,current_piece ):
                cy +=1 
                score +=1 
        elif key ==ord (' '):

            while check_valid (cy +1 ,cx ,current_piece ):
                cy +=1 
                score +=2 
            lock_piece ()
            if not spawn_piece ():
                game_over =True 
            fall_timer =0 
            continue 


        fall_timer +=1 
        if fall_timer >=fall_speed :
            fall_timer =0 
            if check_valid (cy +1 ,cx ,current_piece ):
                cy +=1 
            else :
                lock_piece ()
                if not spawn_piece ():
                    game_over =True 


        stdscr .clear ()

        header_str =f" SCORE: {score }   |   BEST: {best_score }   |   LEVEL: {level } "
        title_str =" []  TETRIS ARCADE  [] "
        try :
            stdscr .addstr (start_y -3 ,(cols -len (title_str ))//2 ,title_str ,curses .color_pair (5 )|curses .A_BOLD )
            stdscr .addstr (start_y -2 ,(cols -len (header_str ))//2 ,header_str ,curses .color_pair (4 )|curses .A_BOLD )
        except curses .error :
            pass 


        try :
            stdscr .addstr (start_y ,start_x -1 ,"┏"+"━"*render_w +"┓",curses .color_pair (7 ))
            for r in range (grid_h ):
                stdscr .addstr (start_y +r +1 ,start_x -1 ,"┃",curses .color_pair (7 ))
                stdscr .addstr (start_y +r +1 ,start_x +render_w ,"┃",curses .color_pair (7 ))
            stdscr .addstr (start_y +grid_h +1 ,start_x -1 ,"┗"+"━"*render_w +"┛",curses .color_pair (7 ))
        except curses .error :
            pass 


        for r in range (grid_h ):
            for c in range (grid_w ):
                if grid [r ][c ]!=0 :
                    try :
                        stdscr .addstr (start_y +r +1 ,start_x +(c *2 ),"[]",curses .color_pair (grid [r ][c ]))
                    except curses .error :
                        pass 


        if current_piece :
            for y ,x in current_piece :
                if 0 <=cy +y <grid_h and 0 <=cx +x <grid_w :
                    try :
                        stdscr .addstr (start_y +(cy +y )+1 ,start_x +((cx +x )*2 ),"[]",curses .color_pair (COLORS [current_idx ])|curses .A_BOLD )
                    except curses .error :
                        pass 

        draw_instructions (stdscr ,rows ,cols )
        stdscr .refresh ()

    stdscr .timeout (-1 )

    if game_over :
        common .save_high_score ("tetris",score )

        try :
            curses .flash ()
        except Exception :
            pass 
        time .sleep (0.5 )
        curses .flushinp ()

        stdscr .clear ()
        border_box ="========================================"
        g_over_msg ="* * *  G A M E   O V E R  * * *"
        result_msg =f"Final Score: {score }  |  Level: {level }"
        any_key ="Press any key to return to main menu..."

        try :
            stdscr .addstr (rows //2 -4 ,(cols -len (border_box ))//2 ,border_box ,curses .color_pair (7 ))
            stdscr .addstr (rows //2 -2 ,(cols -len (g_over_msg ))//2 ,g_over_msg ,curses .color_pair (3 )|curses .A_BOLD )
            stdscr .addstr (rows //2 ,(cols -len (result_msg ))//2 ,result_msg ,curses .color_pair (4 )|curses .A_BOLD )
            stdscr .addstr (rows //2 +2 ,(cols -len (any_key ))//2 ,any_key ,curses .color_pair (7 )|curses .A_DIM )
            stdscr .addstr (rows //2 +4 ,(cols -len (border_box ))//2 ,border_box ,curses .color_pair (7 ))
        except curses .error :
            pass 

        stdscr .refresh ()
        stdscr .getch ()
