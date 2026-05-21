import curses 
import random 
import time 
import common 

def draw_instructions (stdscr ,rows ,cols ):
    inst ="Controls: [<- / ->] Change Lane  |  [Q] Quit"
    legend ="TNT(#) is GREEN  |  Wumpas(*) are PURPLE"
    try :
        stdscr .addstr (rows -3 ,(cols -len (legend ))//2 ,legend ,curses .color_pair (5 )|curses .A_BOLD )
        stdscr .addstr (rows -2 ,(cols -len (inst ))//2 ,inst ,curses .color_pair (2 )|curses .A_DIM )
    except curses .error :
        pass 

def run_game (stdscr ):
    curses .curs_set (0 )
    stdscr .keypad (True )
    stdscr .timeout (50 )

    common .init_colors ()

    width ,height =60 ,20 
    if not common .check_terminal_size (stdscr ,min_rows =height +6 ,min_cols =width +10 ):
        stdscr .timeout (-1 )
        return 

    rows ,cols =stdscr .getmaxyx ()
    start_x =(cols -width )//2 
    start_y =(rows -height )//2 -1 

    score =0 
    wumpas =0 
    best_score =common .load_high_score ("crash")


    horizon_y =5 
    ground_y =height -2 
    center_x =width //2 
    max_lane_spread =20 

    def get_lane_x (lane ,y ):

        if y <horizon_y :return center_x 
        progress =float (y -horizon_y )/float (ground_y -horizon_y )
        spread =int (max_lane_spread *progress )
        return center_x +(lane *spread )


    crash_lane =0 



    objects =[]

    game_over =False 
    speed =0.4 
    tick =0 

    while not game_over :
        tick +=1 
        speed =min (1.0 ,0.4 +(score /1000.0 ))


        key =stdscr .getch ()

        if key in (ord ('q'),ord ('Q'),27 ):
            break 

        if key ==curses .KEY_LEFT :
            crash_lane =max (-1 ,crash_lane -1 )
        elif key ==curses .KEY_RIGHT :
            crash_lane =min (1 ,crash_lane +1 )



        if random .random ()<(0.1 *speed ):
            lane =random .choice ([-1 ,0 ,1 ])
            r =random .random ()
            if r <0.2 :o_type ='#'
            elif r <0.5 :o_type ='?'
            else :o_type ='*'
            objects .append ({"lane":lane ,"y":float (horizon_y ),"type":o_type })


        for obj in objects :

            progress =float (obj ["y"]-horizon_y )/float (ground_y -horizon_y )
            obj_speed =speed *(0.5 +progress *2.0 )
            obj ["y"]+=obj_speed 


        for obj in objects [:]:
            if obj ["y"]>=ground_y :
                if obj ["lane"]==crash_lane :
                    if obj ["type"]=='#':
                        game_over =True 
                        try :
                            for _ in range (3 ):curses .flash ()
                        except :pass 
                    elif obj ["type"]=='?':
                        score +=50 
                        try :curses .flash ()
                        except :pass 
                    elif obj ["type"]=='*':
                        wumpas +=1 
                        score +=10 
                    objects .remove (obj )
                elif obj ["y"]>ground_y +2 :
                    objects .remove (obj )

        score +=int (speed *2 )


        stdscr .clear ()

        header_str =f" SCORE: {score }   |   BEST: {best_score }   |   WUMPAS: {wumpas } "
        title_str =" X  BANDICOOT RUN  X "
        try :
            stdscr .addstr (start_y -3 ,(cols -len (title_str ))//2 ,title_str ,curses .color_pair (4 )|curses .A_BOLD )
            stdscr .addstr (start_y -2 ,(cols -len (header_str ))//2 ,header_str ,curses .color_pair (2 )|curses .A_BOLD )
        except curses .error :
            pass 


        try :
            stdscr .addstr (start_y +horizon_y ,start_x ,"-"*width ,curses .color_pair (7 )|curses .A_DIM )
        except curses .error :pass 


        for y in range (horizon_y +1 ,ground_y +2 ):
            lx =get_lane_x (-1 ,y )-(int (10 *float (y -horizon_y )/float (ground_y -horizon_y )))
            rx =get_lane_x (1 ,y )+(int (10 *float (y -horizon_y )/float (ground_y -horizon_y )))


            color =curses .color_pair (3 )if (y +int (tick *speed *2 ))%4 <2 else curses .color_pair (2 )

            try :
                stdscr .addstr (start_y +y ,start_x +lx ,"/",color |curses .A_BOLD )
                stdscr .addstr (start_y +y ,start_x +rx ,"\\",color |curses .A_BOLD )
            except curses .error :pass 


        objects .sort (key =lambda o :o ["y"])
        for obj in objects :
            y =int (obj ["y"])
            if horizon_y <y <=ground_y +1 :
                x =get_lane_x (obj ["lane"],y )
                char =obj ["type"]

                color =curses .color_pair (7 )
                if char =='#':color =curses .color_pair (1 )|curses .A_BOLD 
                elif char =='?':color =curses .color_pair (4 )|curses .A_BOLD 
                elif char =='*':color =curses .color_pair (5 )|curses .A_BOLD 

                try :

                    if y >ground_y -4 :
                        stdscr .addstr (start_y +y -1 ,start_x +x -1 ,char *3 ,color )
                        stdscr .addstr (start_y +y ,start_x +x -1 ,char *3 ,color )
                    else :
                        stdscr .addstr (start_y +y ,start_x +x ,char ,color )
                except curses .error :pass 


        cx =get_lane_x (crash_lane ,ground_y )
        try :
            stdscr .addstr (start_y +ground_y -1 ,start_x +cx -1 ,"\\O/",curses .color_pair (4 )|curses .A_BOLD )
            stdscr .addstr (start_y +ground_y ,start_x +cx -1 ," | ",curses .color_pair (4 )|curses .A_BOLD )
            stdscr .addstr (start_y +ground_y +1 ,start_x +cx -1 ,"/ \\",curses .color_pair (4 )|curses .A_BOLD )
        except curses .error :pass 

        draw_instructions (stdscr ,rows ,cols )
        stdscr .refresh ()

    stdscr .timeout (-1 )

    if game_over :
        common .save_high_score ("crash",score )

        time .sleep (0.5 )
        curses .flushinp ()

        stdscr .clear ()
        border_box ="========================================"
        g_over_msg ="* * *  W O A H !  * * *"
        result_msg =f"Final Score: {score }"
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
