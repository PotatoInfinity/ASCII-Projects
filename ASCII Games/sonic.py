import curses 
import random 
import time 
import common 

def draw_instructions (stdscr ,rows ,cols ):
    inst ="Controls: [RIGHT] Accelerate  |  [LEFT] Brake  |  [SPACE] Jump  |  [Q] Quit"
    try :
        stdscr .addstr (rows -2 ,(cols -len (inst ))//2 ,inst ,curses .color_pair (2 )|curses .A_DIM )
    except curses .error :
        pass 

def run_game (stdscr ):
    curses .curs_set (0 )
    stdscr .keypad (True )
    stdscr .timeout (30 )

    common .init_colors ()

    width ,height =70 ,15 
    if not common .check_terminal_size (stdscr ,min_rows =height +6 ,min_cols =width +10 ):
        stdscr .timeout (-1 )
        return 

    rows ,cols =stdscr .getmaxyx ()
    start_x =(cols -width )//2 
    start_y =(rows -height )//2 -1 

    score =0.0 
    best_score =common .load_high_score ("sonic")


    sonic_y =float (height -3 )
    sonic_dy =0.0 
    gravity =0.25 
    jump_strength =-1.6 

    rings =0 
    speed =0.5 
    max_speed =3.0 



    objects =[]

    game_over =False 

    tick =0 

    while not game_over :
        tick +=1 


        key =stdscr .getch ()

        if key in (ord ('q'),ord ('Q'),27 ):
            break 


        if key ==curses .KEY_RIGHT :
            speed =min (max_speed ,speed +0.1 )
        elif key ==curses .KEY_LEFT :
            speed =max (0.2 ,speed -0.2 )
        else :

            speed =max (0.5 ,speed -0.02 )


        if key ==ord (' ')and sonic_y >=height -3 :
            sonic_dy =jump_strength 



        sonic_dy +=gravity 
        sonic_y +=sonic_dy 

        if sonic_y >=height -3 :
            sonic_y =float (height -3 )
            sonic_dy =0.0 


        if random .random ()<(0.05 *speed ):

            obj_type ='A'if random .random ()<0.4 else 'o'

            obj_y =float (height -3 )if obj_type =='A'else float (height -random .randint (3 ,6 ))
            objects .append ({"type":obj_type ,"x":float (width ),"y":obj_y })


        for obj in objects :
            obj ["x"]-=speed 


        sonic_x =15 
        sy =int (sonic_y )
        for obj in objects [:]:
            ox ,oy =int (obj ["x"]),int (obj ["y"])
            if ox ==sonic_x and abs (sy -oy )<=1 :
                if obj ["type"]=='o':
                    rings +=1 
                    score +=10 *speed 
                    try :curses .flash ();curses .flushinp ()
                    except :pass 
                    objects .remove (obj )
                elif obj ["type"]=='A':
                    if rings >0 :
                        rings =0 
                        speed =0.5 
                        objects .remove (obj )
                        try :
                            for _ in range (2 ):curses .flash ()
                            curses .flushinp ()
                        except :pass 
                    else :
                        game_over =True 
                        break 


        objects =[o for o in objects if o ["x"]>-1 ]


        score +=speed *0.2 


        stdscr .clear ()

        header_str =f" SCORE: {int (score )}   |   BEST: {best_score }   |   RINGS: {rings }   |   SPEED: {'#'*int (speed *5 )}"
        title_str =" &  ASCII THE HEDGEHOG  & "
        try :
            stdscr .addstr (start_y -3 ,(cols -len (title_str ))//2 ,title_str ,curses .color_pair (4 )|curses .A_BOLD )
            stdscr .addstr (start_y -2 ,(cols -len (header_str ))//2 ,header_str ,curses .color_pair (5 )|curses .A_BOLD )
        except curses .error :
            pass 


        try :

            offset =int (tick *speed )%2 
            g1 ="▓▒"*(width //2 )
            g2 ="▒▓"*(width //2 )
            stdscr .addstr (start_y +height -2 ,start_x ,g1 if offset ==0 else g2 ,curses .color_pair (2 ))
            stdscr .addstr (start_y +height -1 ,start_x ,g2 if offset ==0 else g1 ,curses .color_pair (3 ))
        except curses .error :pass 


        for obj in objects :
            char =obj ["type"]
            color =curses .color_pair (1 )|curses .A_BOLD if char =='A'else curses .color_pair (5 )|curses .A_BOLD 
            try :stdscr .addstr (start_y +int (obj ["y"]),start_x +int (obj ["x"]),char ,color )
            except curses .error :pass 


        try :

            char ='&'if speed <1.5 or int (tick )%2 ==0 else '@'
            stdscr .addstr (start_y +int (sonic_y ),start_x +sonic_x ,char ,curses .color_pair (4 )|curses .A_BOLD )
        except curses .error :pass 

        draw_instructions (stdscr ,rows ,cols )
        stdscr .refresh ()

    stdscr .timeout (-1 )

    if game_over :
        final_score =int (score )
        common .save_high_score ("sonic",final_score )

        try :curses .flash ()
        except Exception :pass 
        time .sleep (0.5 )
        curses .flushinp ()

        stdscr .clear ()
        border_box ="========================================"
        g_over_msg ="* * *  G A M E   O V E R  * * *"
        result_msg =f"Final Score: {final_score }"
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
