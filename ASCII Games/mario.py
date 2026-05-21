import curses 
import random 
import time 
import common 

def draw_instructions (stdscr ,rows ,cols ):
    inst ="Controls: [SPACE / UP] Jump  |  [Q] Quit"
    try :
        stdscr .addstr (rows -2 ,(cols -len (inst ))//2 ,inst ,curses .color_pair (2 )|curses .A_DIM )
    except curses .error :
        pass 

def run_game (stdscr ):
    curses .curs_set (0 )
    stdscr .keypad (True )
    stdscr .timeout (40 )

    common .init_colors ()

    width ,height =60 ,18 
    if not common .check_terminal_size (stdscr ,min_rows =height +6 ,min_cols =width +10 ):
        stdscr .timeout (-1 )
        return 

    rows ,cols =stdscr .getmaxyx ()
    start_x =(cols -width )//2 
    start_y =(rows -height )//2 -1 

    score =0 
    best_score =common .load_high_score ("mario")

    ground_y =height -4 


    mario_x =10 
    mario_y =float (ground_y -1 )
    mario_dy =0.0 
    gravity =0.12 
    jump_power =-1.2 


    terrain =["="for _ in range (width )]
    enemies =[]

    game_over =False 


    pit_cooldown =0 
    enemy_cooldown =0 

    speed_timer =0 

    while not game_over :
        speed_timer +=1 
        base_speed =max (1 ,int (4 -(score /500 )))


        key =stdscr .getch ()

        if key in (ord ('q'),ord ('Q'),27 ):
            break 


        if key in (ord (' '),curses .KEY_UP ):

            is_on_ground =(int (mario_y )==ground_y -1 )and terrain [mario_x ]=="="
            if is_on_ground :
                mario_dy =jump_power 



        mario_dy +=gravity 
        mario_y +=mario_dy 


        if int (mario_y )>=ground_y -1 :
            if terrain [mario_x ]=="=":
                mario_y =float (ground_y -1 )
                mario_dy =0.0 
            elif int (mario_y )>height :

                game_over =True 


        if speed_timer >=base_speed :
            speed_timer =0 
            score +=1 


            terrain .pop (0 )


            for i in range (len (enemies )):
                enemies [i ]-=1.0 
            enemies =[e for e in enemies if e >0 ]


            if pit_cooldown >0 :
                terrain .append (" ")
                pit_cooldown -=1 
                enemy_cooldown =5 
            else :
                terrain .append ("=")
                if random .random ()<0.05 and score >50 :
                    pit_cooldown =random .randint (2 ,5 )


                if pit_cooldown ==0 and enemy_cooldown >0 :
                    enemy_cooldown -=1 
                elif pit_cooldown ==0 and random .random ()<0.08 :
                    enemies .append (float (width -1 ))
                    enemy_cooldown =10 


        my =int (mario_y )
        mx =mario_x 
        for e in enemies [:]:
            ex =int (e )
            if ex ==mx or ex ==mx +1 :
                if my ==ground_y -2 and mario_dy >0 :

                    score +=50 
                    mario_dy =-0.8 
                    enemies .remove (e )
                    try :
                        curses .flash ()
                    except :pass 
                elif my >=ground_y -1 :

                    game_over =True 


        stdscr .clear ()

        header_str =f" SCORE: {score }   |   BEST: {best_score } "
        title_str =" M  SUPER ASCII BROS  M "
        try :
            stdscr .addstr (start_y -3 ,(cols -len (title_str ))//2 ,title_str ,curses .color_pair (5 )|curses .A_BOLD )
            stdscr .addstr (start_y -2 ,(cols -len (header_str ))//2 ,header_str ,curses .color_pair (4 )|curses .A_BOLD )
        except curses .error :
            pass 


        try :
            stdscr .addstr (start_y ,start_x ,"┏"+"━"*(width -2 )+"┓",curses .color_pair (6 ))
            for y in range (1 ,height -1 ):
                stdscr .addstr (start_y +y ,start_x ,"┃",curses .color_pair (6 ))
                stdscr .addstr (start_y +y ,start_x +width -1 ,"┃",curses .color_pair (6 ))
            stdscr .addstr (start_y +height -1 ,start_x ,"┗"+"━"*(width -2 )+"┛",curses .color_pair (6 ))
        except curses .error :
            pass 


        for x ,char in enumerate (terrain ):
            if char =="=":
                try :
                    stdscr .addstr (start_y +ground_y ,start_x +x ,"=",curses .color_pair (2 )|curses .A_BOLD )
                    stdscr .addstr (start_y +ground_y +1 ,start_x +x ,"▓",curses .color_pair (3 ))
                    stdscr .addstr (start_y +ground_y +2 ,start_x +x ,"▒",curses .color_pair (3 ))
                except curses .error :
                    pass 


        for e in enemies :
            try :
                ex =int (e )
                if 0 <ex <width -1 :
                    stdscr .addstr (start_y +ground_y -1 ,start_x +ex ,"n",curses .color_pair (1 )|curses .A_BOLD )
            except curses .error :
                pass 


        try :
            my =int (mario_y )
            if 0 <my <height -1 :

                stdscr .addstr (start_y +my ,start_x +mario_x ,"M",curses .color_pair (4 )|curses .A_BOLD )
        except curses .error :
            pass 

        draw_instructions (stdscr ,rows ,cols )
        stdscr .refresh ()

    stdscr .timeout (-1 )

    if game_over :
        common .save_high_score ("mario",score )

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
            stdscr .addstr (rows //2 -4 ,(cols -len (border_box ))//2 ,border_box ,curses .color_pair (1 ))
            stdscr .addstr (rows //2 -2 ,(cols -len (g_over_msg ))//2 ,g_over_msg ,curses .color_pair (3 )|curses .A_BOLD )
            stdscr .addstr (rows //2 ,(cols -len (result_msg ))//2 ,result_msg ,curses .color_pair (4 )|curses .A_BOLD )
            stdscr .addstr (rows //2 +2 ,(cols -len (any_key ))//2 ,any_key ,curses .color_pair (7 )|curses .A_DIM )
            stdscr .addstr (rows //2 +4 ,(cols -len (border_box ))//2 ,border_box ,curses .color_pair (1 ))
        except curses .error :
            pass 

        stdscr .refresh ()
        stdscr .getch ()
