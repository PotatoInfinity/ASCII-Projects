import curses 
import random 
import time 
import common 


MAP =[
"                                                            ",
"                                                            ",
"        &                                                   ",
"   ===H======                                               ",
"   D  H                                                     ",
"   ===H==============================================       ",
"                                                    H       ",
"                                                    H       ",
"        ============================================H====   ",
"        H                                                   ",
"        H                                                   ",
"  ======H==============================================     ",
"                                                      H     ",
"                                                      H     ",
"         =============================================H==   ",
"         H                                                  ",
"         H                                                  ",
"  =======H================================================= ",
"  M                                                         ",
"============================================================"
]

def draw_instructions (stdscr ,rows ,cols ):
    inst ="Controls: [<- / ->] Move  |  [UP / DOWN] Climb  |  [SPACE] Jump  |  [Q] Quit"
    try :
        stdscr .addstr (rows -2 ,(cols -len (inst ))//2 ,inst ,curses .color_pair (2 )|curses .A_DIM )
    except curses .error :
        pass 

def run_game (stdscr ):
    curses .curs_set (0 )
    stdscr .keypad (True )
    stdscr .timeout (50 )

    common .init_colors ()

    map_h =len (MAP )
    map_w =len (MAP [0 ])

    if not common .check_terminal_size (stdscr ,min_rows =map_h +6 ,min_cols =map_w +10 ):
        stdscr .timeout (-1 )
        return 

    rows ,cols =stdscr .getmaxyx ()
    start_x =(cols -map_w )//2 
    start_y =(rows -map_h )//2 -1 

    score =0 
    best_score =common .load_high_score ("donkey_kong")
    lives =3 
    level =1 


    terrain =[]
    p_spawn =(18 ,2 )
    dk_pos =(4 ,3 )
    princess_pos =(2 ,8 )

    for y ,line in enumerate (MAP ):
        row =list (line )
        for x ,char in enumerate (row ):
            if char =='M':
                p_spawn =(y ,x )
                row [x ]=' '
            elif char =='D':
                dk_pos =(y ,x )
                row [x ]=' '
            elif char =='&':
                princess_pos =(y ,x )
                row [x ]=' '
        terrain .append (row )


    px ,py =float (p_spawn [1 ]),float (p_spawn [0 ])
    p_dy =0.0 
    is_jumping =False 
    is_climbing =False 

    gravity =0.2 
    jump_strength =-1.2 

    barrels =[]
    barrel_timer =0 

    game_over =False 
    game_won =False 

    def reset_level ():
        nonlocal px ,py ,p_dy ,is_jumping ,is_climbing ,barrels 
        px ,py =float (p_spawn [1 ]),float (p_spawn [0 ])
        p_dy =0.0 
        is_jumping =False 
        is_climbing =False 
        barrels .clear ()

    def spawn_barrel ():
        barrels .append ({
        "x":float (dk_pos [1 ]+2 ),
        "y":float (dk_pos [0 ]),
        "dir":1 ,
        "falling":False 
        })

    while not (game_over or game_won ):
        barrel_speed =max (10 ,40 -(level *5 ))
        barrel_timer +=1 
        if barrel_timer >=barrel_speed :
            spawn_barrel ()
            barrel_timer =0 


        key =stdscr .getch ()

        if key in (ord ('q'),ord ('Q'),27 ):
            break 

        ipx ,ipy =int (px ),int (py )


        on_ground =(ipy +1 <map_h and terrain [ipy +1 ][ipx ]=='=')or (ipy +1 <map_h and terrain [ipy +1 ][ipx ]=='H'and not is_climbing )
        on_ladder =(terrain [ipy ][ipx ]=='H')or (ipy +1 <map_h and terrain [ipy +1 ][ipx ]=='H')

        if key ==curses .KEY_LEFT :
            if not is_climbing :
                px =max (1.0 ,px -1.0 )
        elif key ==curses .KEY_RIGHT :
            if not is_climbing :
                px =min (float (map_w -2 ),px +1.0 )
        elif key ==curses .KEY_UP :
            if on_ladder :
                is_climbing =True 
                py =max (1.0 ,py -1.0 )

                px =float (ipx )
        elif key ==curses .KEY_DOWN :
            if on_ladder and not on_ground :
                is_climbing =True 
                py =min (float (map_h -2 ),py +1.0 )
                px =float (ipx )
        elif key ==ord (' '):
            if on_ground and not is_climbing :
                is_jumping =True 
                p_dy =jump_strength 




        if not is_climbing :

            ipx ,ipy =int (px ),int (py )
            on_ground =False 
            if ipy +1 <map_h :
                if terrain [ipy +1 ][ipx ]in ['=','H']:
                    on_ground =True 

            if not on_ground or p_dy <0 :
                p_dy +=gravity 
                py +=p_dy 
                is_jumping =True 
            else :
                p_dy =0.0 
                is_jumping =False 

                py =float (ipy )


            if p_dy <0 and ipy -1 >=0 and terrain [ipy -1 ][ipx ]=='=':
                p_dy =0 
        else :
            p_dy =0.0 


        ipx ,ipy =int (px ),int (py )
        if is_climbing and terrain [ipy ][ipx ]!='H'and (ipy +1 >=map_h or terrain [ipy +1 ][ipx ]!='H'):
            is_climbing =False 


        for b in barrels :
            bx ,by =int (b ["x"]),int (b ["y"])

            if not b ["falling"]:

                b ["x"]+=float (b ["dir"])*0.8 
                nbx =int (b ["x"])

                if by +1 <map_h and terrain [by +1 ][nbx ]==' ':
                    b ["falling"]=True 
                    b ["x"]=float (nbx )
            else :

                b ["y"]+=0.8 
                nby =int (b ["y"])
                if nby +1 <map_h and terrain [nby +1 ][bx ]in ['=','H']:
                    b ["falling"]=False 
                    b ["y"]=float (nby )
                    b ["dir"]*=-1 


            if b ["y"]>=map_h -2 :
                if b in barrels :
                    barrels .remove (b )


        ipx ,ipy =int (px ),int (py )
        hit =False 
        for b in barrels :
            bx ,by =int (b ["x"]),int (b ["y"])
            if bx ==ipx and by ==ipy :
                hit =True 
                break 

            if bx ==ipx and by ==ipy +1 and is_jumping and p_dy <0.5 :
                score +=10 

        if hit :
            lives -=1 
            try :curses .flash ()
            except Exception :pass 
            time .sleep (0.5 )
            curses .flushinp ()
            if lives <=0 :
                game_over =True 
            else :
                reset_level ()


        if ipx ==princess_pos [1 ]and ipy ==princess_pos [0 ]:
            level +=1 
            score +=1000 
            try :curses .flash ()
            except Exception :pass 
            time .sleep (0.5 )
            curses .flushinp ()
            reset_level ()

        if game_over :
            break 


        stdscr .clear ()

        header_str =f" SCORE: {score }   |   BEST: {best_score }   |   LEVEL: {level }   |   LIVES: {'M '*lives }"
        title_str =" DK  DONKEY KONG  DK "
        try :
            stdscr .addstr (start_y -3 ,(cols -len (title_str ))//2 ,title_str ,curses .color_pair (5 )|curses .A_BOLD )
            stdscr .addstr (start_y -2 ,(cols -len (header_str ))//2 ,header_str ,curses .color_pair (4 )|curses .A_BOLD )
        except curses .error :
            pass 


        for y ,row in enumerate (terrain ):
            for x ,char in enumerate (row ):
                if char !=' ':
                    color =curses .color_pair (3 )if char =='H'else curses .color_pair (1 )
                    try :stdscr .addstr (start_y +y ,start_x +x ,char ,color |curses .A_BOLD )
                    except curses .error :pass 


        try :
            stdscr .addstr (start_y +dk_pos [0 ],start_x +dk_pos [1 ],"DK",curses .color_pair (1 )|curses .A_BOLD )
            stdscr .addstr (start_y +princess_pos [0 ],start_x +princess_pos [1 ],"&",curses .color_pair (5 )|curses .A_BLINK )
        except curses .error :pass 


        for b in barrels :
            try :stdscr .addstr (start_y +int (b ["y"]),start_x +int (b ["x"]),"o",curses .color_pair (4 )|curses .A_BOLD )
            except curses .error :pass 


        try :
            stdscr .addstr (start_y +int (py ),start_x +int (px ),"M",curses .color_pair (2 )|curses .A_BOLD )
        except curses .error :pass 

        draw_instructions (stdscr ,rows ,cols )
        stdscr .refresh ()

    stdscr .timeout (-1 )

    if game_over :
        common .save_high_score ("donkey_kong",score )

        try :curses .flash ()
        except Exception :pass 
        time .sleep (0.5 )
        curses .flushinp ()

        stdscr .clear ()
        border_box ="========================================"
        g_over_msg ="* * *  G A M E   O V E R  * * *"
        result_msg =f"Final Score: {score }  |  Level Reached: {level }"
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
