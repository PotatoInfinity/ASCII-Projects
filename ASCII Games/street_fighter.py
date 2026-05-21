import curses 
import random 
import time 
import common 

def draw_instructions (stdscr ,rows ,cols ):
    inst ="Controls: [<- / ->] Move  |  [A] Punch  |  [S] Kick  |  [D] Block  |  [F] Fireball"
    try :
        stdscr .addstr (rows -2 ,(cols -len (inst ))//2 ,inst ,curses .color_pair (2 )|curses .A_DIM )
    except curses .error :
        pass 

def run_game (stdscr ):
    curses .curs_set (0 )
    stdscr .keypad (True )
    stdscr .timeout (50 )

    common .init_colors ()

    width ,height =60 ,16 
    if not common .check_terminal_size (stdscr ,min_rows =height +6 ,min_cols =width +10 ):
        stdscr .timeout (-1 )
        return 

    rows ,cols =stdscr .getmaxyx ()
    start_x =(cols -width )//2 
    start_y =(rows -height )//2 -1 

    score =0 
    best_score =common .load_high_score ("street_fighter")

    ground_y =height -2 


    p1_hp ,p1_max =100 ,100 
    p2_hp ,p2_max =100 ,100 

    p1_x =10.0 
    p2_x =50.0 

    p1_state ="IDLE"
    p1_timer =0 
    p1_fireball_cooldown =0 

    p2_state ="IDLE"
    p2_timer =0 

    fireballs =[]

    game_over =False 
    game_won =False 

    def apply_damage (target ,amount ):
        nonlocal p1_hp ,p2_hp ,p1_state ,p2_state ,p1_timer ,p2_timer 
        if target =="P1":
            if p1_state =="BLOCK":
                p1_hp -=max (1 ,amount //4 )
            else :
                p1_hp -=amount 
                p1_state ="HURT"
                p1_timer =5 
        else :
            if p2_state =="BLOCK":
                p2_hp -=max (1 ,amount //4 )
            else :
                p2_hp -=amount 
                p2_state ="HURT"
                p2_timer =5 

    tick =0 

    while not (game_over or game_won ):
        tick +=1 


        if p1_timer >0 :
            p1_timer -=1 
            if p1_timer <=0 :p1_state ="IDLE"

        if p2_timer >0 :
            p2_timer -=1 
            if p2_timer <=0 :p2_state ="IDLE"

        if p1_fireball_cooldown >0 :
            p1_fireball_cooldown -=1 


        key =stdscr .getch ()

        if key in (ord ('q'),ord ('Q'),27 ):
            break 

        if p1_state =="IDLE":
            if key ==curses .KEY_LEFT :
                p1_x =max (2.0 ,p1_x -1.5 )
            elif key ==curses .KEY_RIGHT :
                p1_x =min (p2_x -3.0 ,p1_x +1.5 )
            elif key in (ord ('a'),ord ('A')):
                p1_state ="PUNCH"
                p1_timer =4 
                if p2_x -p1_x <=5.0 :
                    apply_damage ("P2",8 )
            elif key in (ord ('s'),ord ('S')):
                p1_state ="KICK"
                p1_timer =6 
                if p2_x -p1_x <=6.5 :
                    apply_damage ("P2",12 )
            elif key in (ord ('d'),ord ('D')):
                p1_state ="BLOCK"
                p1_timer =8 
            elif key in (ord ('f'),ord ('F'))and p1_fireball_cooldown <=0 :
                p1_state ="PUNCH"
                p1_timer =6 
                p1_fireball_cooldown =30 
                fireballs .append ({"x":p1_x +2 ,"y":float (ground_y -2 ),"dx":2.0 ,"owner":"P1"})


        if p2_state =="IDLE"and tick %5 ==0 :
            dist =p2_x -p1_x 
            if dist >8.0 :

                if random .random ()<0.2 :
                    p2_state ="PUNCH"
                    p2_timer =6 
                    fireballs .append ({"x":p2_x -2 ,"y":float (ground_y -2 ),"dx":-2.0 ,"owner":"P2"})
                else :
                    p2_x -=1.0 
            else :

                r =random .random ()
                if r <0.3 :
                    p2_state ="PUNCH"
                    p2_timer =4 
                    if dist <=5.0 :apply_damage ("P1",8 )
                elif r <0.6 :
                    p2_state ="KICK"
                    p2_timer =6 
                    if dist <=6.5 :apply_damage ("P1",12 )
                elif r <0.8 :
                    p2_state ="BLOCK"
                    p2_timer =10 
                else :
                    p2_x =min (float (width -4 ),p2_x +1.5 )


        for f in fireballs :
            f ["x"]+=f ["dx"]

            if f ["owner"]=="P1"and f ["x"]>=p2_x -1 :
                apply_damage ("P2",10 )
                f ["x"]=width +10 
            elif f ["owner"]=="P2"and f ["x"]<=p1_x +1 :
                apply_damage ("P1",10 )
                f ["x"]=-10 

        fireballs =[f for f in fireballs if 0 <f ["x"]<width ]


        if p1_hp <=0 :game_over =True 
        if p2_hp <=0 :game_won =True 


        stdscr .clear ()

        header_str =f" SCORE: {score }   |   BEST: {best_score } "
        title_str =" X  STREET FIGHTER II  X "
        try :
            stdscr .addstr (start_y -3 ,(cols -len (title_str ))//2 ,title_str ,curses .color_pair (5 )|curses .A_BOLD )
            stdscr .addstr (start_y -2 ,(cols -len (header_str ))//2 ,header_str ,curses .color_pair (4 )|curses .A_BOLD )
        except curses .error :
            pass 


        p1_bar ="█"*(p1_hp //5 )
        p2_bar ="█"*(p2_hp //5 )
        try :
            stdscr .addstr (start_y ,start_x +2 ,f"P1: [{p1_bar :<20}]",curses .color_pair (2 )|curses .A_BOLD )
            stdscr .addstr (start_y ,start_x +width -26 ,f"[{p2_bar :>20}] :CPU",curses .color_pair (3 )|curses .A_BOLD )
        except curses .error :pass 


        try :
            stdscr .addstr (start_y +ground_y ,start_x ,"="*width ,curses .color_pair (7 )|curses .A_DIM )
        except curses .error :pass 


        def draw_sprite (x ,state ,is_p1 ):
            color =curses .color_pair (2 )if is_p1 else curses .color_pair (3 )
            ix =int (x )

            if state =="HURT":
                head ="x"
                body ="/"if is_p1 else "\\"
                legs ="<"if is_p1 else ">"
            elif state =="BLOCK":
                head ="o"
                body ="["if is_p1 else "]"
                legs ="|"
            elif state =="PUNCH":
                head ="o"
                body ="---"if is_p1 else "---"
                legs ="|"
                ix =ix if is_p1 else ix -2 
            elif state =="KICK":
                head ="o"
                body ="|"
                legs ="\\_"if is_p1 else "_/"
                ix =ix if is_p1 else ix -1 
            else :

                head ="o"
                body ="|"
                legs ="^"

            try :
                stdscr .addstr (start_y +ground_y -3 ,start_x +ix ,head ,color |curses .A_BOLD )
                stdscr .addstr (start_y +ground_y -2 ,start_x +ix ,body ,color |curses .A_BOLD )
                stdscr .addstr (start_y +ground_y -1 ,start_x +ix ,legs ,color |curses .A_BOLD )
            except curses .error :pass 


        for f in fireballs :
            char ="O"if f ["owner"]=="P1"else "*"
            color =curses .color_pair (1 )|curses .A_BOLD if f ["owner"]=="P1"else curses .color_pair (5 )|curses .A_BOLD 
            try :stdscr .addstr (start_y +int (f ["y"]),start_x +int (f ["x"]),char ,color )
            except curses .error :pass 


        draw_sprite (p1_x ,p1_state ,True )
        draw_sprite (p2_x ,p2_state ,False )

        draw_instructions (stdscr ,rows ,cols )
        stdscr .refresh ()

    stdscr .timeout (-1 )

    if game_over or game_won :
        if game_won :score +=max (0 ,p1_hp )*10 
        common .save_high_score ("street_fighter",score )

        try :curses .flash ()
        except Exception :pass 
        time .sleep (0.5 )
        curses .flushinp ()

        stdscr .clear ()
        border_box ="========================================"
        if game_won :
            g_over_msg ="* * *  K . O .  * * *"
            result_msg =f"You win! Final Score: {score }"
            color =curses .color_pair (2 )
        else :
            g_over_msg ="* * *  Y O U   L O S E  * * *"
            result_msg =f"Defeated. Final Score: {score }"
            color =curses .color_pair (3 )

        any_key ="Press any key to return to main menu..."

        try :
            stdscr .addstr (rows //2 -4 ,(cols -len (border_box ))//2 ,border_box ,color )
            stdscr .addstr (rows //2 -2 ,(cols -len (g_over_msg ))//2 ,g_over_msg ,color |curses .A_BOLD )
            stdscr .addstr (rows //2 ,(cols -len (result_msg ))//2 ,result_msg ,curses .color_pair (4 )|curses .A_BOLD )
            stdscr .addstr (rows //2 +2 ,(cols -len (any_key ))//2 ,any_key ,curses .color_pair (7 )|curses .A_DIM )
            stdscr .addstr (rows //2 +4 ,(cols -len (border_box ))//2 ,border_box ,color )
        except curses .error :
            pass 

        stdscr .refresh ()
        stdscr .getch ()
