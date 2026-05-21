import curses 
import random 
import time 
import common 

def draw_instructions (stdscr ,rows ,cols ):
    inst ="Controls: [<- / ->] Move  |  [SPACE] Shoot  |  [Q] Quit"
    try :
        stdscr .addstr (rows -2 ,(cols -len (inst ))//2 ,inst ,curses .color_pair (2 )|curses .A_DIM )
    except curses .error :
        pass 

def run_game (stdscr ):
    curses .curs_set (0 )
    stdscr .keypad (True )
    stdscr .timeout (40 )

    common .init_colors ()

    width ,height =60 ,25 
    if not common .check_terminal_size (stdscr ,min_rows =height +6 ,min_cols =width +10 ):
        stdscr .timeout (-1 )
        return 

    rows ,cols =stdscr .getmaxyx ()
    start_x =(cols -width )//2 
    start_y =(rows -height )//2 -1 


    score =0 
    best_score =common .load_high_score ("space_invaders")
    lives =3 
    wave =1 

    player_x =float (width //2 )
    player_y =height -2 
    player_ship ="=^="

    player_lasers =[]
    alien_lasers =[]

    aliens =[]
    alien_direction =1 
    alien_move_timer =0 
    alien_speed =20 

    bunkers =[]

    def init_wave ():
        nonlocal alien_speed ,alien_direction ,alien_move_timer 
        aliens .clear ()
        player_lasers .clear ()
        alien_lasers .clear ()


        for row in range (5 ):
            for col in range (11 ):
                aliens .append ({
                "x":float (5 +col *4 ),
                "y":float (2 +row *2 ),
                "type":row %2 
                })
        alien_direction =1 
        alien_speed =max (2 ,20 -(wave *2 ))
        alien_move_timer =0 

    def init_bunkers ():
        bunkers .clear ()
        for bx in [10 ,25 ,40 ,55 ]:

            for by in range (height -6 ,height -4 ):
                for cx in range (bx -2 ,bx +3 ):
                    bunkers .append ({"x":cx ,"y":by ,"hp":3 })

    init_bunkers ()
    init_wave ()

    game_over =False 
    game_won =False 

    tick =0 

    while not (game_over or game_won ):
        tick +=1 

        key =stdscr .getch ()

        if key in (ord ('q'),ord ('Q'),27 ):
            break 

        if key ==curses .KEY_LEFT :
            player_x =max (1.0 ,player_x -1.5 )
        elif key ==curses .KEY_RIGHT :
            player_x =min (float (width -4 ),player_x +1.5 )
        elif key ==ord (' '):

            if len (player_lasers )<3 :
                player_lasers .append ({"x":player_x +1 ,"y":float (player_y -1 )})



        for laser in player_lasers :
            laser ["y"]-=0.8 
        player_lasers =[l for l in player_lasers if l ["y"]>0 ]


        for laser in alien_lasers :
            laser ["y"]+=0.4 
        alien_lasers =[l for l in alien_lasers if l ["y"]<height ]


        alien_move_timer +=1 
        if alien_move_timer >=alien_speed :
            alien_move_timer =0 


            hit_edge =False 
            for a in aliens :
                if (alien_direction ==1 and a ["x"]>=width -3 )or (alien_direction ==-1 and a ["x"]<=1 ):
                    hit_edge =True 
                    break 

            if hit_edge :
                alien_direction *=-1 
                for a in aliens :
                    a ["y"]+=1 
            else :
                for a in aliens :
                    a ["x"]+=alien_direction *1.0 


        if aliens and random .random ()<0.03 +(wave *0.01 ):
            shooter =random .choice (aliens )
            alien_lasers .append ({"x":shooter ["x"],"y":shooter ["y"]+1 })



        for laser in player_lasers [:]:
            lx ,ly =int (laser ["x"]),int (laser ["y"])
            hit =False 
            for a in aliens [:]:
                ax ,ay =int (a ["x"]),int (a ["y"])
                if ay ==ly and ax <=lx <=ax +2 :
                    aliens .remove (a )
                    if laser in player_lasers :
                        player_lasers .remove (laser )
                    score +=10 
                    hit =True 

                    alien_speed =max (1 ,alien_speed -0.2 )
                    break 
            if hit :
                continue 


            for b in bunkers [:]:
                if b ["x"]==lx and b ["y"]==ly :
                    b ["hp"]-=1 
                    if b ["hp"]<=0 :
                        bunkers .remove (b )
                    if laser in player_lasers :
                        player_lasers .remove (laser )
                    break 


        for laser in alien_lasers [:]:
            lx ,ly =int (laser ["x"]),int (laser ["y"])
            if ly ==player_y and int (player_x )<=lx <=int (player_x )+2 :
                lives -=1 
                alien_lasers .remove (laser )
                try :
                    curses .flash ()
                except Exception :
                    pass 
                time .sleep (0.5 )
                curses .flushinp ()
                player_lasers .clear ()
                alien_lasers .clear ()
                if lives <=0 :
                    game_over =True 
                break 

            for b in bunkers [:]:
                if b ["x"]==lx and b ["y"]==ly :
                    b ["hp"]-=1 
                    if b ["hp"]<=0 :
                        bunkers .remove (b )
                    if laser in alien_lasers :
                        alien_lasers .remove (laser )
                    break 


        for a in aliens :
            if a ["y"]>=height -4 :
                game_over =True 
                break 


        if len (aliens )==0 :
            wave +=1 
            score +=100 
            init_wave ()

        if game_over :
            break 


        stdscr .clear ()

        header_str =f" SCORE: {score }   |   WAVE: {wave }   |   LIVES: {'A '*lives }"
        title_str =" =^=  SPACE INVADERS  =^= "
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


        for b in bunkers :
            char ="#"if b ["hp"]==3 else ("+"if b ["hp"]==2 else ".")
            try :
                stdscr .addstr (start_y +b ["y"],start_x +b ["x"],char ,curses .color_pair (1 )|curses .A_BOLD )
            except curses .error :
                pass 


        for a in aliens :
            char ="M"if tick %20 <10 else "W"
            if a ["type"]==1 :
                char ="X"if tick %20 <10 else "H"
            try :
                stdscr .addstr (start_y +int (a ["y"]),start_x +int (a ["x"]),char ,curses .color_pair (3 )|curses .A_BOLD )
            except curses .error :
                pass 


        for l in player_lasers :
            try :
                stdscr .addstr (start_y +int (l ["y"]),start_x +int (l ["x"]),"|",curses .color_pair (2 )|curses .A_BOLD )
            except curses .error :
                pass 
        for l in alien_lasers :
            try :
                stdscr .addstr (start_y +int (l ["y"]),start_x +int (l ["x"]),"!",curses .color_pair (4 )|curses .A_BOLD )
            except curses .error :
                pass 


        try :
            stdscr .addstr (start_y +player_y ,start_x +int (player_x ),player_ship ,curses .color_pair (1 )|curses .A_BOLD )
        except curses .error :
            pass 

        draw_instructions (stdscr ,rows ,cols )
        stdscr .refresh ()

    stdscr .timeout (-1 )

    if game_over :
        common .save_high_score ("space_invaders",score )

        try :
            curses .flash ()
        except Exception :
            pass 
        time .sleep (0.5 )
        curses .flushinp ()

        stdscr .clear ()
        border_box ="========================================"
        g_over_msg ="* * *  G A M E   O V E R  * * *"
        result_msg =f"Wave {wave } reached. Final Score: {score }"
        any_key ="Press any key to return to main menu..."

        try :
            stdscr .addstr (rows //2 -4 ,(cols -len (border_box ))//2 ,border_box ,curses .color_pair (3 ))
            stdscr .addstr (rows //2 -2 ,(cols -len (g_over_msg ))//2 ,g_over_msg ,curses .color_pair (3 )|curses .A_BOLD )
            stdscr .addstr (rows //2 ,(cols -len (result_msg ))//2 ,result_msg ,curses .color_pair (4 )|curses .A_BOLD )
            stdscr .addstr (rows //2 +2 ,(cols -len (any_key ))//2 ,any_key ,curses .color_pair (7 )|curses .A_DIM )
            stdscr .addstr (rows //2 +4 ,(cols -len (border_box ))//2 ,border_box ,curses .color_pair (3 ))
        except curses .error :
            pass 

        stdscr .refresh ()
        stdscr .getch ()
