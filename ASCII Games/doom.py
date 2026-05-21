import curses
import math
import time
import random
import common

MAP = [
    "############################",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#.####.#####.##.#####.####.#",
    "#..........................#",
    "#.####.##.########.##.####.#",
    "#......##....##....##......#",
    "######.#####.##.#####.######",
    "     #.##              ##.# ",
    "     #.##  ###B####   ##.#  ",
    "######.##  #      #   ##.###",
    "#......    #  E   #      ..#",
    "#.####.##  #      #   ##.###",
    "#.####.##  ########   ##.#  ",
    "#......##              ##.# ",
    "######.#####.##.#####.######",
    "#......##....##....##......#",
    "#.####.##.########.##.####.#",
    "#..........................#",
    "#.####.#####.##.#####.####.#",
    "#............##............#",
    "############################",
]

# Use strictly solid blocks for walls so they never blend with floor/ceiling
SHADE_CHARS = ['█', '▓', '▒', '░']

def get_doomguy_face(health, is_shooting, is_hit, frame_count):
    if health <= 0:
        return "[  X_X  ]"
    if is_hit:
        return "[  O_#  ]"
    if is_shooting:
        return "[  ▄_▄  ]"
    
    if health > 75:
        face = "O_O"
    elif health > 40:
        face = "o_o"
    else:
        face = "._."
    
    if frame_count % 30 < 10:
        return f"[  {face}  ]"
    elif frame_count % 30 < 20:
        return f"[  <{face}  ]"
    else:
        return f"[  {face}>  ]"

def run_game(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)
    stdscr.timeout(33)

    common.init_colors()

    scr_w = 100
    scr_h = 36
    hud_h = 5

    if not common.check_terminal_size(stdscr, min_rows=scr_h + hud_h + 3, min_cols=scr_w + 4):
        stdscr.timeout(-1)
        return

    rows, cols = stdscr.getmaxyx()
    start_x = (cols - scr_w) // 2
    start_y = 2

    MAP_MUTABLE = [list(row) for row in MAP]
    map_w = len(MAP[0])
    map_h = len(MAP)

    fov = math.pi / 2.5
    max_depth = 20.0
    move_speed = 0.14
    turn_speed = 0.08

    # Player state
    px, py = 1.5, 1.5
    pa = 0.0
    health = 100
    armor = 0
    ammo = 40
    score = 0
    kills = 0
    has_key = False
    weapons_owned = [True, True, False]  # Fist, Pistol, Shotgun
    current_weapon = 1  # Start with Pistol
    player_shoot_cd = 0

    # Enemies
    def make_enemy(x, y, etype):
        hp = 20 if etype == 'zombieman' else (45 if etype == 'imp' else 80)
        return {
            'x': x, 'y': y, 'alive': True, 'hp': hp, 'max_hp': hp,
            'type': etype, 'flash': 0, 'dist': 0,
            'angle': 0.0, 'shoot_cd': random.randint(15, 45)
        }

    enemies = [
        make_enemy(5.5, 5.5, 'zombieman'),
        make_enemy(10.5, 3.5, 'zombieman'),
        make_enemy(20.5, 5.5, 'imp'),
        make_enemy(2.5, 15.5, 'imp'),
        make_enemy(15.5, 12.5, 'pinky'),
        make_enemy(25.5, 15.5, 'pinky'),
        make_enemy(13.5, 8.5, 'imp'),
    ]

    # Collectible items on map
    items = [
        {'x': 13.5, 'y': 13.5, 'type': 'shotgun', 'alive': True},
        {'x': 25.5, 'y': 2.5, 'type': 'key', 'alive': True},
        {'x': 2.5, 'y': 19.5, 'type': 'medikit', 'alive': True},
        {'x': 25.5, 'y': 19.5, 'type': 'medikit', 'alive': True},
        {'x': 13.5, 'y': 18.5, 'type': 'medikit', 'alive': True},
        {'x': 20.5, 'y': 10.5, 'type': 'armor', 'alive': True},
        {'x': 7.5, 'y': 12.5, 'type': 'armor', 'alive': True},
        {'x': 10.5, 'y': 19.5, 'type': 'ammo', 'alive': True},
        {'x': 18.5, 'y': 19.5, 'type': 'ammo', 'alive': True},
        {'x': 5.5, 'y': 2.5, 'type': 'ammo', 'alive': True},
    ]

    projectiles = []
    shoot_flash = 0
    hit_flash = 0
    game_over = False
    win = False
    minimap_on = False
    frame_count = 0
    hud_message = "WELCOME TO CLASSIC ASCII DOOM!"
    hud_message_timer = 60

    def map_blocked(x, y):
        ix, iy = int(x), int(y)
        if ix < 0 or ix >= map_w or iy < 0 or iy >= map_h:
            return True
        c = MAP_MUTABLE[iy][ix]
        return c == '#' or c == ' ' or c == 'B'

    def cast_ray(angle):
        ray_cos = math.cos(angle)
        ray_sin = math.sin(angle)
        dist = 0.0
        hit = False
        step = 0.05
        while not hit and dist < max_depth:
            dist += step
            tx = int(px + ray_cos * dist)
            ty = int(py + ray_sin * dist)
            if tx < 0 or tx >= map_w or ty < 0 or ty >= map_h:
                hit = True
                dist = max_depth
            else:
                c = MAP_MUTABLE[ty][tx]
                if c == '#' or c == ' ' or c == 'B':
                    hit = True
        return dist

    while not game_over and not win:
        frame_count += 1
        key = stdscr.getch()

        if key in (27,):  # ESC key
            break

        # Weapon switching
        if key == ord('1'):
            current_weapon = 0
            hud_message = "WEAPON: FIST"
            hud_message_timer = 30
        elif key == ord('2') and weapons_owned[1]:
            current_weapon = 1
            hud_message = "WEAPON: PISTOL"
            hud_message_timer = 30
        elif key == ord('3') and weapons_owned[2]:
            current_weapon = 2
            hud_message = "WEAPON: SHOTGUN"
            hud_message_timer = 30
        elif key in (ord('m'), ord('M')):
            minimap_on = not minimap_on

        # Movement and strafe keys with sliding collision buffers
        buf = 0.22
        if key in (curses.KEY_LEFT, ord('a'), ord('A')):
            pa -= turn_speed
        elif key in (curses.KEY_RIGHT, ord('d'), ord('D')):
            pa += turn_speed
        elif key in (ord('w'), ord('W'), curses.KEY_UP):
            dx = math.cos(pa) * move_speed
            dy = math.sin(pa) * move_speed
            nx = px + dx
            sign_x = 1 if dx > 0 else -1
            if not map_blocked(nx + sign_x * buf, py): px = nx
            ny = py + dy
            sign_y = 1 if dy > 0 else -1
            if not map_blocked(px, ny + sign_y * buf): py = ny
        elif key in (ord('s'), ord('S'), curses.KEY_DOWN):
            dx = -math.cos(pa) * move_speed
            dy = -math.sin(pa) * move_speed
            nx = px + dx
            sign_x = 1 if dx > 0 else -1
            if not map_blocked(nx + sign_x * buf, py): px = nx
            ny = py + dy
            sign_y = 1 if dy > 0 else -1
            if not map_blocked(px, ny + sign_y * buf): py = ny
        elif key in (ord('q'), ord('Q')):
            # Strafe Left
            dx = -math.sin(pa) * move_speed
            dy = math.cos(pa) * move_speed
            nx = px + dx
            sign_x = 1 if dx > 0 else -1
            if not map_blocked(nx + sign_x * buf, py): px = nx
            ny = py + dy
            sign_y = 1 if dy > 0 else -1
            if not map_blocked(px, ny + sign_y * buf): py = ny
        elif key in (ord('e'), ord('E')):
            # Strafe Right
            dx = math.sin(pa) * move_speed
            dy = -math.cos(pa) * move_speed
            nx = px + dx
            sign_x = 1 if dx > 0 else -1
            if not map_blocked(nx + sign_x * buf, py): px = nx
            ny = py + dy
            sign_y = 1 if dy > 0 else -1
            if not map_blocked(px, ny + sign_y * buf): py = ny

        # Combat firing logic
        if player_shoot_cd > 0:
            player_shoot_cd -= 1

        if key == ord(' ') and player_shoot_cd == 0:
            # Check ammo
            has_ammo = True
            if current_weapon == 1:  # Pistol uses 1 ammo
                if ammo >= 1:
                    ammo -= 1
                else:
                    has_ammo = False
            elif current_weapon == 2:  # Shotgun uses 2 ammo
                if ammo >= 2:
                    ammo -= 2
                else:
                    has_ammo = False

            if not has_ammo:
                hud_message = "OUT OF AMMO!"
                hud_message_timer = 30
            else:
                shoot_flash = 3
                # Set weapon cooldowns
                if current_weapon == 0:
                    player_shoot_cd = 7
                elif current_weapon == 1:
                    player_shoot_cd = 12
                elif current_weapon == 2:
                    player_shoot_cd = 28

                # Firing combat resolution
                if current_weapon == 0:  # FIST
                    closest_e = None
                    min_dist = 1.3
                    for e in enemies:
                        if not e['alive']:
                            continue
                        dx = e['x'] - px
                        dy = e['y'] - py
                        dist_e = math.sqrt(dx*dx + dy*dy)
                        if dist_e < min_dist:
                            # Line of sight check
                            step = 0.1
                            d = 0.0
                            blocked = False
                            angle_to = math.atan2(dy, dx)
                            while d < dist_e:
                                d += step
                                if map_blocked(px + math.cos(angle_to)*d, py + math.sin(angle_to)*d):
                                    blocked = True
                                    break
                            if not blocked:
                                closest_e = e
                                min_dist = dist_e
                    if closest_e:
                        dmg = random.randint(15, 30)
                        closest_e['hp'] -= dmg
                        closest_e['flash'] = 3
                        score += 15
                        hud_message = f"PUNCHED {closest_e['type'].upper()} FOR {dmg} DMG!"
                        hud_message_timer = 20
                        if closest_e['hp'] <= 0:
                            closest_e['alive'] = False
                            kills += 1
                            score += 100
                            hud_message = f"KILLED A {closest_e['type'].upper()}!"
                            hud_message_timer = 30

                elif current_weapon == 1:  # PISTOL
                    closest_e = None
                    min_dist = max_depth
                    aim_tolerance = fov / (scr_w / 6)
                    for e in enemies:
                        if not e['alive']:
                            continue
                        dx = e['x'] - px
                        dy = e['y'] - py
                        dist_e = math.sqrt(dx*dx + dy*dy)
                        if dist_e < min_dist:
                            angle_to = math.atan2(dy, dx)
                            diff = (angle_to - pa + math.pi) % (2*math.pi) - math.pi
                            if abs(diff) < aim_tolerance:
                                # Line of sight check
                                step = 0.1
                                d = 0.0
                                blocked = False
                                while d < dist_e:
                                    d += step
                                    if map_blocked(px + math.cos(angle_to)*d, py + math.sin(angle_to)*d):
                                        blocked = True
                                        break
                                if not blocked:
                                    closest_e = e
                                    min_dist = dist_e
                    if closest_e:
                        dmg = random.randint(10, 22)
                        closest_e['hp'] -= dmg
                        closest_e['flash'] = 3
                        score += 10
                        if closest_e['hp'] <= 0:
                            closest_e['alive'] = False
                            kills += 1
                            score += 100
                            hud_message = f"KILLED A {closest_e['type'].upper()}!"
                            hud_message_timer = 30

                elif current_weapon == 2:  # SHOTGUN
                    shot_hit_any = False
                    aim_tolerance_shotgun = fov / 4.0  # wider spread cone
                    for e in enemies:
                        if not e['alive']:
                            continue
                        dx = e['x'] - px
                        dy = e['y'] - py
                        dist_e = math.sqrt(dx*dx + dy*dy)
                        if dist_e < 11.0:
                            angle_to = math.atan2(dy, dx)
                            diff = (angle_to - pa + math.pi) % (2*math.pi) - math.pi
                            if abs(diff) < aim_tolerance_shotgun:
                                # Line of sight check
                                step = 0.1
                                d = 0.0
                                blocked = False
                                while d < dist_e:
                                    d += step
                                    if map_blocked(px + math.cos(angle_to)*d, py + math.sin(angle_to)*d):
                                        blocked = True
                                        break
                                if not blocked:
                                    # Pellet count depends on how centered the aim is
                                    pellets = random.randint(4, 7) - int(abs(diff) / aim_tolerance_shotgun * 3)
                                    pellets = max(1, pellets)
                                    dmg = pellets * random.randint(6, 12)
                                    e['hp'] -= dmg
                                    e['flash'] = 3
                                    score += 15
                                    shot_hit_any = True
                                    if e['hp'] <= 0:
                                        e['alive'] = False
                                        kills += 1
                                        score += 100
                                        hud_message = f"KILLED A {e['type'].upper()}!"
                                        hud_message_timer = 30
                    if shot_hit_any and not hud_message_timer:
                        hud_message = "SHOTGUN BLAST HITS!"
                        hud_message_timer = 20

        # Automatic Locked Door Unlock
        if has_key:
            dx = px - 14.5
            dy = py - 9.5
            dist_to_door = math.sqrt(dx*dx + dy*dy)
            if dist_to_door < 1.8:
                if MAP_MUTABLE[9][14] == 'B':
                    MAP_MUTABLE[9][14] = '.'
                    hud_message = "BLUE DOOR UNLOCKED & OPENED!"
                    hud_message_timer = 60

        # Level Exit check
        ix, iy = int(px), int(py)
        if MAP_MUTABLE[iy][ix] == 'E':
            win = True

        # Flashes cooldown
        if shoot_flash > 0:
            shoot_flash -= 1
        if hit_flash > 0:
            hit_flash -= 1

        # Projectiles updates
        for p in projectiles:
            if p['active']:
                nx = p['x'] + p['vx']
                ny = p['y'] + p['vy']
                if map_blocked(nx, ny):
                    p['active'] = False
                    continue
                dx = nx - px
                dy = ny - py
                dist_p = math.sqrt(dx*dx + dy*dy)
                if dist_p < 0.6:
                    p['active'] = False
                    damage = random.randint(10, 20)
                    if armor > 0:
                        absorb = damage // 2
                        armor = max(0, armor - absorb)
                        health -= (damage - absorb)
                    else:
                        health -= damage
                    hit_flash = 4
                    continue
                p['x'] = nx
                p['y'] = ny

        # Enemy updates & AI
        alive_enemies = [e for e in enemies if e['alive']]

        for e in alive_enemies:
            dx = px - e['x']
            dy = py - e['y']
            dist_e = math.sqrt(dx*dx + dy*dy)
            e['dist'] = dist_e

            if e['flash'] > 0:
                e['flash'] -= 1
            if e['shoot_cd'] > 0:
                e['shoot_cd'] -= 1

            if dist_e < 12.0:
                # Movement per type
                if e['type'] == 'pinky':
                    # Pinky rushes the player fast
                    spd = 0.055
                elif e['type'] == 'imp':
                    spd = 0.032
                else:
                    spd = 0.02
                
                if dist_e > 1.1:
                    angle_to = math.atan2(dy, dx)
                    nx = e['x'] + math.cos(angle_to) * spd
                    ny = e['y'] + math.sin(angle_to) * spd
                    if not map_blocked(nx, e['y']): e['x'] = nx
                    if not map_blocked(e['x'], ny): e['y'] = ny

                # Enemy Attack Resolution (with robust Line-Of-Sight wall checks!)
                if e['type'] == 'pinky':
                    if dist_e < 1.2 and e['shoot_cd'] == 0:
                        e['shoot_cd'] = random.randint(15, 30)
                        damage = random.randint(12, 25)
                        if armor > 0:
                            absorb = damage // 2
                            armor = max(0, armor - absorb)
                            health -= (damage - absorb)
                        else:
                            health -= damage
                        hit_flash = 4
                elif e['type'] == 'imp':
                    if dist_e < 10.0 and e['shoot_cd'] == 0:
                        e['shoot_cd'] = random.randint(45, 80)
                        # Imp Line-Of-Sight Check
                        step = 0.1
                        d = 0.0
                        blocked = False
                        angle_to = math.atan2(dy, dx)
                        while d < dist_e:
                            d += step
                            if map_blocked(e['x'] + math.cos(angle_to)*d, e['y'] + math.sin(angle_to)*d):
                                blocked = True
                                break
                        if not blocked:
                            # Spawn fireball projectile
                            ang = math.atan2(dy, dx)
                            vx = math.cos(ang) * 0.16
                            vy = math.sin(ang) * 0.16
                            projectiles.append({'x': e['x'], 'y': e['y'], 'vx': vx, 'vy': vy, 'active': True})
                else:  # zombieman (hitscan pistol)
                    if dist_e < 8.0 and e['shoot_cd'] == 0:
                        e['shoot_cd'] = random.randint(50, 90)
                        # Zombieman Line-Of-Sight Check (Prevents shooting through walls!)
                        step = 0.1
                        d = 0.0
                        blocked = False
                        angle_to = math.atan2(dy, dx)
                        while d < dist_e:
                            d += step
                            if map_blocked(e['x'] + math.cos(angle_to)*d, e['y'] + math.sin(angle_to)*d):
                                blocked = True
                                break
                        if not blocked:
                            hit_chance = max(0.15, 0.7 - dist_e * 0.07)
                            if random.random() < hit_chance:
                                damage = random.randint(4, 9)
                                if armor > 0:
                                    absorb = damage // 2
                                    armor = max(0, armor - absorb)
                                    health -= (damage - absorb)
                                else:
                                    health -= damage
                                hit_flash = 4
            else:
                # Idle drift patrol
                if random.random() < 0.01:
                    angle_rand = random.uniform(-0.3, 0.3)
                    nx = e['x'] + math.cos(angle_rand) * 0.5
                    ny = e['y'] + math.sin(angle_rand) * 0.5
                    if not map_blocked(nx, e['y']): e['x'] = nx
                    if not map_blocked(e['x'], ny): e['y'] = ny

        if health <= 0:
            health = 0
            game_over = True

        # Player item pickups check
        for item in items:
            if item['alive']:
                dx = px - item['x']
                dy = py - item['y']
                dist_p = math.sqrt(dx*dx + dy*dy)
                if dist_p < 0.8:
                    item['alive'] = False
                    if item['type'] == 'medikit':
                        health = min(100, health + 25)
                        hud_message = "PICKED UP MEDIKIT! (+25 HP)"
                        hud_message_timer = 45
                    elif item['type'] == 'armor':
                        armor = min(100, armor + 50)
                        hud_message = "PICKED UP ARMOR! (+50 ARMOR)"
                        hud_message_timer = 45
                    elif item['type'] == 'ammo':
                        ammo = min(99, ammo + 15)
                        hud_message = "PICKED UP AMMO! (+15 AMMO)"
                        hud_message_timer = 45
                    elif item['type'] == 'shotgun':
                        weapons_owned[2] = True
                        current_weapon = 2
                        ammo = min(99, ammo + 8)
                        hud_message = "YOU GOT THE SHOTGUN!"
                        hud_message_timer = 45
                    elif item['type'] == 'key':
                        has_key = True
                        hud_message = "GOT BLUE KEY! FIND THE LOCKED BLUE DOOR!"
                        hud_message_timer = 60

        # ── RENDER ──
        stdscr.clear()

        # Raycasting 3D walls
        z_buf = [0.0] * scr_w

        for col in range(scr_w):
            ray_angle = (pa - fov / 2.0) + (col / scr_w) * fov
            dist = cast_ray(ray_angle)
            corrected = dist * math.cos(ray_angle - pa)
            corrected = max(0.05, corrected)
            z_buf[col] = corrected

            # Compressed wall rendering to correct for standard terminal aspect ratio!
            wall_height_scale = 0.55
            ceiling = int(scr_h / 2.0 - (scr_h * wall_height_scale) / corrected)
            floor_row = scr_h - ceiling

            for row in range(scr_h):
                draw_y = start_y + row
                draw_x = start_x + col
                char = ' '
                color = curses.color_pair(7)

                if row < ceiling:
                    # Solid clean black sky - absolutely zero visual noise!
                    char = ' '
                    color = curses.color_pair(7) | curses.A_DIM
                elif row <= floor_row:
                    # Cohesive modern Ice Blue Walls - ALWAYS solid block characters!
                    shade_idx = min(3, int(corrected / max_depth * 4))
                    char = SHADE_CHARS[shade_idx]
                    if shade_idx == 0:
                        color = curses.color_pair(2) | curses.A_BOLD  # Bright Cyan
                    elif shade_idx == 1:
                        color = curses.color_pair(2)                  # Normal Cyan
                    elif shade_idx == 2:
                        color = curses.color_pair(7)                  # Normal White
                    else:
                        color = curses.color_pair(7) | curses.A_DIM    # Dim Gray/White
                else:
                    # Clean light-textured floor in Dim Gray (easy to distinguish from solid walls!)
                    b = (row - scr_h / 2.0) / (scr_h / 2.0)
                    if b < 0.3:
                        char = '.'
                    elif b < 0.6:
                        char = ','
                    else:
                        char = '_'
                    color = curses.color_pair(7) | curses.A_DIM

                if hit_flash > 0:
                    color = curses.color_pair(3) | curses.A_BOLD

                try:
                    stdscr.addstr(draw_y, draw_x, char, color)
                except curses.error:
                    pass

        # 3D Sprites sorting & drawing (Enemies, Pickups, Projectiles)
        sprites_to_draw = []
        for e in enemies:
            dx = e['x'] - px
            dy = e['y'] - py
            dist = math.sqrt(dx*dx + dy*dy)
            e['dist'] = dist
            sprites_to_draw.append({
                'x': e['x'], 'y': e['y'], 'dist': dist, 'type': 'enemy', 'obj': e
            })
        
        for item in items:
            if not item['alive']:
                continue
            dx = item['x'] - px
            dy = item['y'] - py
            dist = math.sqrt(dx*dx + dy*dy)
            item['dist'] = dist
            sprites_to_draw.append({
                'x': item['x'], 'y': item['y'], 'dist': dist, 'type': 'item', 'obj': item
            })
            
        for p in projectiles:
            if not p['active']:
                continue
            dx = p['x'] - px
            dy = p['y'] - py
            dist = math.sqrt(dx*dx + dy*dy)
            p['dist'] = dist
            sprites_to_draw.append({
                'x': p['x'], 'y': p['y'], 'dist': dist, 'type': 'projectile', 'obj': p
            })

        sprites_to_draw.sort(key=lambda s: s['dist'], reverse=True)

        for s in sprites_to_draw:
            dist_s = s['dist']
            if dist_s < 0.4:
                continue

            dx = s['x'] - px
            dy = s['y'] - py
            angle_to = math.atan2(dy, dx)
            diff = (angle_to - pa + math.pi) % (2*math.pi) - math.pi
            if abs(diff) > fov * 0.75:
                continue

            screen_col = int((diff / fov + 0.5) * scr_w)
            sprite_h = min(scr_h, int(scr_h / dist_s * wall_height_scale * 2.0))
            sprite_w = max(1, sprite_h // 2)
            top = scr_h // 2 - sprite_h // 2
            start_col = screen_col - sprite_w // 2

            for sc in range(sprite_w):
                col = start_col + sc
                if col < 0 or col >= scr_w:
                    continue
                if dist_s >= z_buf[col]:
                    continue
                for sr in range(sprite_h):
                    row = top + sr
                    if row < 0 or row >= scr_h:
                        continue
                    col_frac = sc / max(1, sprite_w - 1)
                    row_frac = sr / max(1, sprite_h - 1)

                    if s['type'] == 'enemy':
                        e = s['obj']
                        if e['alive']:
                            if e['type'] == 'zombieman':
                                h_char, b_char = 'o', 'Z'
                                body_color = curses.color_pair(1) | curses.A_BOLD
                            elif e['type'] == 'imp':
                                h_char, b_char = 'o', 'I'
                                body_color = curses.color_pair(3) | curses.A_BOLD
                            else:
                                h_char, b_char = 'W', 'D'
                                body_color = curses.color_pair(5) | curses.A_BOLD

                            if 0.15 < col_frac < 0.85 and row_frac < 0.25:
                                ch = h_char
                                color = curses.color_pair(7) | curses.A_BOLD
                            elif 0.1 < col_frac < 0.9 and 0.25 <= row_frac < 0.65:
                                ch = b_char
                                color = body_color
                                if e['flash'] > 0:
                                    ch = 'X'
                                    color = curses.color_pair(5) | curses.A_BOLD
                            elif 0.15 < col_frac < 0.45 and row_frac >= 0.65:
                                ch = '|'
                                color = curses.color_pair(7)
                            elif 0.55 < col_frac < 0.85 and row_frac >= 0.65:
                                ch = '|'
                                color = curses.color_pair(7)
                            else:
                                continue
                        else:
                            if row_frac > 0.75:
                                ch = '-'
                                color = curses.color_pair(3) | curses.A_DIM
                            else:
                                continue

                    elif s['type'] == 'item':
                        item = s['obj']
                        if item['type'] == 'medikit':
                            if 0.3 < col_frac < 0.7 and 0.2 < row_frac < 0.8:
                                ch = '+'
                                color = curses.color_pair(1) | curses.A_BOLD
                            else:
                                continue
                        elif item['type'] == 'armor':
                            if 0.2 < col_frac < 0.8 and 0.3 < row_frac < 0.9:
                                ch = 'A'
                                color = curses.color_pair(2) | curses.A_BOLD
                            else:
                                continue
                        elif item['type'] == 'ammo':
                            if 0.2 < col_frac < 0.8 and 0.4 < row_frac < 0.8:
                                ch = 'M'
                                color = curses.color_pair(4) | curses.A_BOLD
                            else:
                                continue
                        elif item['type'] == 'shotgun':
                            if 0.1 < col_frac < 0.9 and 0.5 < row_frac < 0.7:
                                ch = 'S'
                                color = curses.color_pair(6) | curses.A_BOLD
                            else:
                                continue
                        elif item['type'] == 'key':
                            if 0.3 < col_frac < 0.7 and 0.3 < row_frac < 0.7:
                                ch = 'K'
                                color = curses.color_pair(2) | curses.A_BOLD
                            else:
                                continue
                        else:
                            continue

                    elif s['type'] == 'projectile':
                        if 0.3 < col_frac < 0.7 and 0.3 < row_frac < 0.7:
                            ch = '*'
                            color = curses.color_pair(3) | curses.A_BOLD
                        else:
                            continue

                    try:
                        stdscr.addstr(start_y + row, start_x + col, ch, color)
                    except curses.error:
                        pass

        # Draw HUD center weapon
        gun_cx = start_x + scr_w // 2
        gun_y = start_y + scr_h - 1
        
        if current_weapon == 0:
            gun_lines = [
                "  .---.  ",
                " /  |  \\ ",
                " |  |  | ",
                " \\_____/ ",
            ]
            gun_col = curses.color_pair(1) | curses.A_BOLD if shoot_flash > 0 else curses.color_pair(7)
        elif current_weapon == 1:
            gun_lines = [
                "   ||    ",
                "   ||    ",
                "  _||_   ",
                " [____]  ",
            ]
            gun_col = curses.color_pair(4) | curses.A_BOLD if shoot_flash > 0 else curses.color_pair(7) | curses.A_BOLD
        else:
            gun_lines = [
                "  || ||  ",
                "  || ||  ",
                "  || ||  ",
                " /=====  ",
                "[______] ",
            ]
            gun_col = curses.color_pair(5) | curses.A_BOLD if shoot_flash > 0 else curses.color_pair(7) | curses.A_BOLD

        for gi, gl in enumerate(gun_lines):
            try:
                stdscr.addstr(gun_y - (len(gun_lines) - 1 - gi),
                              gun_cx - len(gl) // 2, gl, gun_col)
            except curses.error:
                pass
        
        if shoot_flash > 0:
            try:
                if current_weapon == 1:
                    stdscr.addstr(gun_y - len(gun_lines), gun_cx - 1, " * ",
                                  curses.color_pair(4) | curses.A_BOLD)
                elif current_weapon == 2:
                    stdscr.addstr(gun_y - len(gun_lines), gun_cx - 2, "***",
                                  curses.color_pair(4) | curses.A_BOLD)
                    stdscr.addstr(gun_y - len(gun_lines) - 1, gun_cx - 1, "*",
                                  curses.color_pair(4) | curses.A_BOLD)
            except curses.error:
                pass

        # Overlay minimap (automap) if enabled
        if minimap_on:
            m_start_x = start_x + scr_w - map_w - 4
            m_start_y = start_y + 1
            
            try:
                border_color = curses.color_pair(2) | curses.A_DIM
                stdscr.addstr(m_start_y - 1, m_start_x - 1, "┌" + "─" * map_w + "┐", border_color)
                for my in range(map_h):
                    stdscr.addstr(m_start_y + my, m_start_x - 1, "│", border_color)
                    stdscr.addstr(m_start_y + my, m_start_x + map_w, "│", border_color)
                stdscr.addstr(m_start_y + map_h, m_start_x - 1, "└" + "─" * map_w + "┘", border_color)
                stdscr.addstr(m_start_y - 1, m_start_x + (map_w - 9) // 2, " AUTOMAP ", curses.color_pair(2) | curses.A_BOLD)
            except curses.error:
                pass

            for my in range(map_h):
                for mx in range(map_w):
                    ch = ' '
                    color = curses.color_pair(7) | curses.A_DIM
                    
                    if int(px) == mx and int(py) == my:
                        norm_pa = pa % (2 * math.pi)
                        if norm_pa < math.pi / 4 or norm_pa >= 7 * math.pi / 4:
                            ch = '>'
                        elif norm_pa < 3 * math.pi / 4:
                            ch = 'v'
                        elif norm_pa < 5 * math.pi / 4:
                            ch = '<'
                        else:
                            ch = '^'
                        color = curses.color_pair(2) | curses.A_BOLD
                    else:
                        tile = MAP_MUTABLE[my][mx]
                        if tile == '#':
                            ch = '█'
                            color = curses.color_pair(7) | curses.A_DIM
                        elif tile == 'B':
                            ch = 'B'
                            color = curses.color_pair(2) | curses.A_BOLD
                        elif tile == 'E':
                            ch = 'E'
                            color = curses.color_pair(1) | curses.A_BOLD
                        elif tile == ' ':
                            ch = ' '
                        else:
                            ch = '·'
                            
                        # Overlay elements
                        for e in enemies:
                            if e['alive'] and int(e['x']) == mx and int(e['y']) == my:
                                if e['type'] == 'zombieman':
                                    ch = 'z'
                                    color = curses.color_pair(1) | curses.A_BOLD
                                elif e['type'] == 'imp':
                                    ch = 'i'
                                    color = curses.color_pair(3) | curses.A_BOLD
                                else:
                                    ch = 'd'
                                    color = curses.color_pair(5) | curses.A_BOLD
                        
                        for item in items:
                            if item['alive'] and int(item['x']) == mx and int(item['y']) == my:
                                if item['type'] == 'medikit':
                                    ch = '+'
                                    color = curses.color_pair(1) | curses.A_BOLD
                                elif item['type'] == 'armor':
                                    ch = 'a'
                                    color = curses.color_pair(2) | curses.A_BOLD
                                elif item['type'] == 'ammo':
                                    ch = 'm'
                                    color = curses.color_pair(4) | curses.A_BOLD
                                elif item['type'] == 'shotgun':
                                    ch = 's'
                                    color = curses.color_pair(6) | curses.A_BOLD
                                elif item['type'] == 'key':
                                    ch = 'k'
                                    color = curses.color_pair(2) | curses.A_BOLD
                    
                    try:
                        stdscr.addstr(m_start_y + my, m_start_x + mx, ch, color)
                    except curses.error:
                        pass

        # ── STATUS HUD BAR ──
        hud_y = start_y + scr_h + 1
        
        is_hit = hit_flash > 0
        is_shooting_action = shoot_flash > 0
        face_str = get_doomguy_face(health, is_shooting_action, is_hit, frame_count)

        # Health bar
        hp_bar_len = 10
        hp_filled = int((health / 100) * hp_bar_len)
        hp_bar = "█" * max(0, hp_filled) + "░" * max(0, hp_bar_len - hp_filled)
        
        # Armor bar
        armor_bar_len = 10
        armor_filled = int((armor / 100) * armor_bar_len)
        armor_bar = "█" * max(0, armor_filled) + "░" * max(0, armor_bar_len - armor_filled)

        weapons_str = " ".join([str(i+1) if weapons_owned[i] else "_" for i in range(3)])
        key_str = "[BLUE KEY]" if has_key else "[NO KEY]"
        key_color = curses.color_pair(2) | curses.A_BOLD if has_key else curses.color_pair(7) | curses.A_DIM

        hud_line1 = f"  ♥ HP: [{hp_bar}] {health:3d}%    🛡 ARMOR: [{armor_bar}] {armor:3d}%    🔫 AMMO: {ammo:2d}/99    👤 FACE: {face_str}"
        hud_line2 = f"  🎯 SCORE: {score:05d}   💀 KILLS: {kills}/{len(enemies)}   🔑 KEY: {key_str}   🎒 WEAPONS: {weapons_str}"
        
        if hud_message_timer > 0:
            hud_line3 = f"  »» {hud_message} ««"
            hud_line3_color = curses.color_pair(4) | curses.A_BOLD
            hud_message_timer -= 1
        else:
            hud_line3 = "  ⚙ AUTOMAP: [M]   STRAFE: [Q/E]   WEAPONS: [1/2/3]   SHOOT: [SPACE]   QUIT: [ESC]"
            hud_line3_color = curses.color_pair(7) | curses.A_DIM

        frame_top = "═" * scr_w
        try:
            stdscr.addstr(hud_y - 1, start_x, frame_top, curses.color_pair(2))
            stdscr.addstr(hud_y, start_x, hud_line1[:scr_w], curses.color_pair(7))
            stdscr.addstr(hud_y + 1, start_x, hud_line2[:scr_w], curses.color_pair(7))
            stdscr.addstr(hud_y + 2, start_x, hud_line3[:scr_w], hud_line3_color)
        except curses.error:
            pass

        title = " █▓▒░  ASCII DOOM CLASSIC  ░▒▓█ "
        try:
            stdscr.addstr(0, (cols - len(title)) // 2, title,
                          curses.color_pair(3) | curses.A_BOLD)
        except curses.error:
            pass

        stdscr.refresh()

    # Game over / win screen
    stdscr.timeout(-1)
    stdscr.clear()
    try:
        if win:
            msg = f"  *** VICTORY! You opened the Blue Door and exited! Score: {score} ***  "
            clr = curses.color_pair(1) | curses.A_BOLD
        elif game_over:
            msg = f"  *** YOU DIED! Score: {score}  Kills: {kills}/{len(enemies)} ***  "
            clr = curses.color_pair(3) | curses.A_BOLD
        else:
            return
        any_key = "Press any key to return to arcade menu..."
        stdscr.addstr(rows // 2 - 1, (cols - len(msg)) // 2, msg, clr)
        stdscr.addstr(rows // 2 + 1, (cols - len(any_key)) // 2, any_key,
                      curses.color_pair(7) | curses.A_DIM)
    except curses.error:
        pass
    stdscr.refresh()
    stdscr.getch()
