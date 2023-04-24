import asyncio
import pygame as pg
import pygame.surfarray
import math
import random
import numpy as np

import src.maps as maps

TALLNESS = 2
FOV =75

async def main():
    pg.init()
    screen_scale = 2
    screen_size = [int(192*screen_scale), 4*int(27*screen_scale)]
    mod = FOV/screen_size[0]
    screen = pg.display.set_mode(screen_size, pg.SCALED)
    
    clock = pg.time.Clock()
    font = pg.font.SysFont(None, 20, 1)

    pg.mouse.set_visible(False)
    
    mapa, entity_data = maps.read_map(pg.image.load('map0.png'))

    x_pos = y_pos = 1.533
    rot = rot_v = 0
    
    pg.event.set_grab(1)
    textures = []
    for i in '01234':
        textures.append(pg.image.load('textures/wall'+i+'.jpg').convert())
    for i in '0':
        textures.append(pg.image.load('textures/door'+i+'.jpg').convert())
    fence = pg.image.load('textures/fence.png').convert()
    fence.set_colorkey((0,0,0))
    floor = pg.surfarray.array3d(pg.image.load('textures/floor2.jpg').convert())
    floor_color = np.mean(floor[0]), np.mean(floor[1]), np.mean(floor[2]),
    ceiling_color = (200,200,200)
    # floor = pg.surfarray.array3d(pg.transform.smoothscale(pg.transform.smoothscale(pg.image.load('floor.jpg'), (20,20)), (100,100)))
    sky = pg.transform.smoothscale(pg.image.load('textures/skybox.png').convert(), (12*screen_size[0]*60/FOV, 3*screen_size[1]))
    robot_sheet = pg.image.load('sprites/robot.png').convert()
    robot_sheet.set_colorkey((255,255,255))
    robot = []
    for j in range(3):
        robot.append([])
        for i in range(4):
            robot[-1].append(pg.Surface.subsurface(robot_sheet, [i*100, j*200, 100, 200]))
    bug_points = np.random.uniform(-10, len(mapa)+10, (100, 2))
    tree = pg.image.load('sprites/tree.png').convert()
    tree.set_colorkey((255,255,255))

    player_shots = []
    enemy_shots = []
    light_points = []
    floor_points = []
    subpoints = 1
    for i in range(int(subpoints*len(mapa)-1)):
        for j in range(int(subpoints*len(mapa[0])-1)):
            position = [i/subpoints+0.5, j/subpoints+0.5]
            if mapa[int(position[0])][int(position[1])] < 1:
                light_points.append(position)
            for k in range(3):
                position = [random.uniform(1, len(mapa)-1), random.uniform(1, len(mapa)-1)]
                if mapa[int(position[0])][int(position[1])] < 1:
                    floor_points.append(position)

    sprites = [robot, tree]
    floor_scale = 2
    hres = int(screen_size[0]/floor_scale)
    halfvres = int(screen_size[1]/(2*floor_scale))
    frame = np.zeros([hres, halfvres*2, 3])    

    vertical_pos = 0
    vertical_vel = 0
    graphics_low = 0
    health = 20
    indoor = 1
    bullet_time = 0
    total_time = 0
    animation_time = 0
    running = 1
    p_mouse_target = list(pg.mouse.get_rel())
    while running:

        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                running = 0
            if event.type == pg.MOUSEBUTTONDOWN:
                player_shots.append([0.4, x_pos+0.5*math.cos(rot), y_pos+0.5*math.sin(rot), rot, rot_v])
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE and vertical_pos == 0:
                    vertical_vel = 3
                if event.key == pg.K_f and bullet_time + 5 < total_time:
                    bullet_time = total_time + 5

        elapsed_time = clock.tick()*0.001
        total_time += elapsed_time
        fps = int(clock.get_fps())
        
        if bullet_time > total_time:
            elapsed_time *= 0.1
        animation_time += elapsed_time

        bug_points = bug_points + np.random.uniform(-1, 1, (100, 2))*elapsed_time
        x_pos, y_pos, rot, rot_v = movement(x_pos, y_pos, rot, rot_v, mapa, 2*elapsed_time, p_mouse_target)
        
        vertical_pos = max(0, vertical_pos+vertical_vel*elapsed_time)
        vertical_vel = max(-2, vertical_vel - elapsed_time*10)
        offset = (rot_v + vertical_pos)*screen_size[1]
        
        if graphics_low:
            pg.draw.rect(screen, floor_color, [0,screen_size[1]/2+offset,screen_size[0], screen_size[1]/2-offset])
            for i in range(len(floor_points)):
                draw_point(screen, x_pos, y_pos, rot, FOV, floor_points[i], offset, 0, (60,66,55), 3)
        
        elif offset < screen_size[1]/2:
            floorcasting(x_pos, y_pos, rot, FOV, mod, screen, frame, floor, floor_scale, offset)

        
        if indoor:
            pg.draw.rect(screen, ceiling_color, [0,0, screen_size[0], screen_size[1]/2+offset])
            for i in range(len(light_points)):
                draw_point(screen, x_pos, y_pos, rot, FOV, light_points[i], offset, 1.05, (220,220,200), 12)
                draw_point(screen, x_pos, y_pos, rot, FOV, light_points[i], offset, 1.05, (255,255,255))
        else:
            sub_sky = pg.Surface.subsurface(sky, (math.degrees(rot%(2*math.pi)*screen_size[0]/FOV), screen_size[1]-offset, screen_size[0], screen_size[1]/2+offset))
            screen.blit(sub_sky, (0, 0))

        raycast_walls(screen, mod, FOV, mapa, x_pos, y_pos, rot, offset, textures)

        for i, entity in enumerate(entity_data): # type, x, y, direction, distance, status, cooldown
            if entity[0] in [0]:
                if entity[5]:
                    move_entity(entity, 0.5, mapa, elapsed_time)
                elif entity[0] == 0:
                    in_FOV, angle, angle2, angle2degree = vision(entity[1], entity[2], entity[3], FOV, [x_pos, y_pos])
                    entity[3] =  angle + random.uniform(-0.1, 0.1)
                    if in_FOV and total_time - entity[6] > 0:
                        entity[6] = total_time + .5
                        enemy_shots.append([0.38, entity[1]+0.1*math.cos(entity[3]), entity[2]+0.1*math.sin(entity[3]), entity[3], 0.1])
                        
            
            draw_sprite(screen, x_pos, y_pos, rot, FOV, mapa, entity, sprites, offset, animation_time)
            
            if entity[7] <= 0:
                entity_data.remove(entity)
            elif i > 0 and entity[4] > entity_data[i-1][4]:
                entity_data[i-1], entity_data[i] = entity_data[i], entity_data[i-1]

        for shot in player_shots:
            shot[0] += math.sin(shot[4])*elapsed_time*3  
            if move_entity(shot, 5, mapa, elapsed_time) or shot[0]<0 or collision_entities(shot, entity_data):
                draw_point(screen, x_pos, y_pos, rot, FOV, shot[1:3], offset, shot[0], (255,255,255), 10)
                player_shots.remove(shot)
            else:
                draw_point(screen, x_pos, y_pos, rot, FOV, shot[1:3], offset, shot[0], (55,255,255), 3)
        
        for shot in enemy_shots:
            shot[0] += math.sin(shot[4])*elapsed_time*3
            dist2player = math.sqrt((x_pos-shot[1])**2+(y_pos-shot[1])**2)
            if move_entity(shot, 5, mapa, elapsed_time) or shot[0] < 0 or dist2player < 0.1:
                draw_point(screen, x_pos, y_pos, rot, FOV, shot[1:3], offset, shot[0], (255,255,255), 10)
                enemy_shots.remove(shot)
                health -= dist2player < 0.1
                print(health)
            else:
                draw_point(screen, x_pos, y_pos, rot, FOV, shot[1:3], offset, shot[0], (255,55,55), 3)
            

        screen.blit(font.render(str(fps), 1, [255, 255, 255]), [5,5])
        pg.display.update()

        await asyncio.sleep(0)  # very important, and keep it 0

def collision_entities(shot, entity_data):
    for entity in entity_data:
        if math.sqrt((shot[1]-entity[1])**2 + (shot[2]-entity[2])**2) < 0.1:
            entity[7] -= 1
            return 1
    return 0

def movement(x_pos, y_pos, rot, rot_v, mapa, elapsed_time, p_mouse_target):
    
    if pg.mouse.get_focused():
        p_mouse = pg.mouse.get_rel()
        p_mouse_target[0] += p_mouse[0]
        p_mouse_target[1] += p_mouse[1]
        if abs(p_mouse_target[0]) > 1:
            rot = rot + min(max((p_mouse_target[0]/2)/200, -0.2), .2)
            p_mouse_target[0] /= 2
        if abs(p_mouse_target[1]) > 1:
            rot_v = rot_v - min(max((p_mouse_target[1]/2)/200, -0.2), .2)
            rot_v = min(1, max(-0.5, rot_v))
            p_mouse_target[1] /= 2
    
    pressed_keys = pg.key.get_pressed()
    
    forward = (pressed_keys[pg.K_UP] or pressed_keys[ord('w')]) - (pressed_keys[pg.K_DOWN] or pressed_keys[ord('s')])
    sideways = (pressed_keys[pg.K_LEFT] or pressed_keys[ord('a')]) - (pressed_keys[pg.K_RIGHT] or pressed_keys[ord('d')])

    if forward*sideways != 0: # limit speed moving diagonally
        forward, sideways = forward*0.7, sideways*0.7

    x_pos, y_pos = check_wall_collisions(x_pos, y_pos, rot, forward, sideways, elapsed_time, 0.1, mapa)
    
    return x_pos, y_pos, rot, rot_v

def check_wall_collisions(x_pos, y_pos, rot, forward, sideways, elapsed_time, delta_player, mapa):
    
    x = x_pos + math.sqrt(TALLNESS)*elapsed_time*(forward*math.cos(rot) + sideways*math.sin(rot))
    y = y_pos + math.sqrt(TALLNESS)*elapsed_time*(forward*math.sin(rot) - sideways*math.cos(rot))

    x_delta = x + delta_player*(forward*math.cos(rot) + sideways*math.sin(rot))
    y_delta = y + delta_player*(forward*math.sin(rot) - sideways*math.cos(rot))

    if mapa[int(x_delta)][int(y_delta)] < 0 and np.sqrt((0.5-x%1)**2 + (0.5-y%1)**2) > 0.25:
            return x, y

    if mapa[int(x_delta)][int(y_delta)] == 0:
        return x, y
    
    if mapa[int(x_pos + delta_player*(forward*math.cos(rot) + sideways*math.sin(rot)))][int(y_delta)] == 0:
        return x_pos, y
    
    if mapa[int(x_delta)][int(y_pos + delta_player*(forward*math.sin(rot) - sideways*math.cos(rot)))] == 0:
        return x, y_pos
    
    return x_pos, y_pos
        
def move_entity(entity, velocity, mapa, elapsed_time):
    x = entity[1] + elapsed_time*math.cos(entity[3])*velocity
    y = entity[2] + elapsed_time*math.sin(entity[3])*velocity

    if x < 0 or y < 0 or x > len(mapa)-1 or y> len(mapa[0])-1:
        entity[3] = random.uniform(0, 2*math.pi)
        return 1

    x, y = check_wall_collisions(entity[1], entity[2], entity[3], velocity, 0, elapsed_time, 0.1, mapa)

    if x == entity[1] or y == entity[2]:
        entity[3] = random.uniform(0, 2*math.pi)
        return 1
        
    else:
        entity[1], entity[2] = x, y
        return 0

### Digital Differential Analysis Algorithm by Lode V., source:
### https://lodev.org/cgtutor/raycasting.html
def lodev_DDA(x, y, rot_i, mapa):
    sizeX = len(mapa) - 1
    sizeY = len(mapa[0]) - 1
    sin, cos = math.sin(rot_i), math.cos(rot_i)
    norm = math.sqrt(cos**2 + sin**2)
    rayDirX, rayDirY = cos/norm + 1e-16, sin/norm + 1e-16
    
    mapX, mapY = int(x), int(y)

    deltaDistX, deltaDistY = abs(1/rayDirX), abs(1/rayDirY)

    if rayDirX < 0:
        stepX, sideDistX = -1, (x - mapX) * deltaDistX
    else:
        stepX, sideDistX = 1, (mapX + 1.0 - x) * deltaDistX
        
    if rayDirY < 0:
        stepY, sideDistY = -1, (y - mapY) * deltaDistY
    else:
        stepY, sideDistY = 1, (mapY + 1 - y) * deltaDistY

    for i in range(20):
        if (sideDistX < sideDistY):
            sideDistX += deltaDistX
            mapX += stepX
            dist = sideDistX
            side = 0
            if mapX < 0 or mapX > sizeX:
                return 0, 0, 400
        else:
            sideDistY += deltaDistY
            mapY += stepY
            dist = sideDistY
            side = 1
            if mapY < 0 or mapY > sizeY:
                return 0, 0, 400
        if mapa[mapX][mapY] > 0:
            break
            
    if side:
        dist = dist - deltaDistY + 0.0001
    else:
        dist = dist - deltaDistX + 0.0001
        
    x = x + rayDirX*dist
    y = y + rayDirY*dist
    
    return x, y, dist

def raycast_walls(screen, mod, FOV, mapa, x_pos, y_pos, rot, offset, textures):
    horizontal_res, vertical_res = screen.get_size()
    # blit_list = []
    for i in range(horizontal_res): #vision loop
        rot_i = rot + math.radians(i*mod - FOV*0.5)
        x, y, dist = lodev_DDA(x_pos, y_pos, rot_i, mapa)
        texture = mapa[int(x)][int(y)]
        texture_size = textures[texture].get_size()
        scale = int(TALLNESS*vertical_res/max(0.1, dist*math.cos(math.radians(i*mod-FOV*0.5))))
        text_coord = x%1
        if text_coord < 0.001 or text_coord > 0.999:
            text_coord = y%1
        subsurface = pg.Surface.subsurface(textures[texture], (texture_size[0]*text_coord, 0, 1, texture_size[1]))
        resized = pg.transform.scale(subsurface, (1,scale))
        screen.blit(resized, (i, (vertical_res-scale)*0.5+offset))
    #     blit_list.append((resized, (i, (vertical_res-scale)*0.5+offset)))
    # screen.fblits(blit_list)

def draw_sprite(screen, x_pos, y_pos, rot, FOV, mapa, entity, sprites, offset, total_time):
    entity_pos = entity[1], entity[2]
    in_FOV, angle, angle2, angle2degree = vision(x_pos, y_pos, rot, FOV, entity_pos)

    if in_FOV:
        x, y, dist = lodev_DDA(x_pos, y_pos, angle, mapa)
        dist2player = math.sqrt((x_pos-entity[1])**2+(y_pos-entity[2])**2)
        entity[4] = dist2player
        if dist2player-0.2 < dist:
            horizontal_res, vertical_res = screen.get_size()
            screen_scale = vertical_res*0.003
            if type(sprites[entity[0]]) == list:
                facing_angle = int(((entity[3] - angle -3*math.pi/4)%(2*math.pi))/(math.pi/2))
                if type(sprites[entity[0]][0]) == list:
                    if entity[5] == 1: # animated
                        selected_sprite = sprites[entity[0]][1+int(total_time*3)%2][facing_angle]
                    else: #not animated/moving
                        selected_sprite = sprites[entity[0]][0][facing_angle]
                else:
                    selected_sprite = sprites[entity[0]][facing_angle]
            else:
                selected_sprite = sprites[entity[0]]

            old_size = selected_sprite.get_size()

            scale =  min(4, TALLNESS/(dist2player*math.cos(angle2)))
            new_size = screen_scale*old_size[0]*scale, screen_scale*old_size[1]*scale
            hor_coord = (FOV*0.5-angle2degree)*horizontal_res/FOV - new_size[0]*0.5
            ground_coord = (1+scale)*vertical_res*0.5 + offset
            
            scaled_sprite = pg.transform.scale(selected_sprite, new_size)
            screen.blit(scaled_sprite, (hor_coord, ground_coord - new_size[1]))   

def draw_point(screen, x_pos, y_pos, rot, FOV, point_pos, offset, height, color, diameter=5):
    in_FOV, angle, angle2, angle2degree = vision(x_pos, y_pos, rot, FOV, point_pos)
    if in_FOV:
        horizontal_res, vertical_res = screen.get_size()
        dist2player = math.sqrt((x_pos-point_pos[0])**2+(y_pos-point_pos[1])**2)
        scale =  min(4, TALLNESS/(dist2player*math.cos(angle2)))
        hor_coord = (FOV*0.5-angle2degree)*horizontal_res/FOV
        ground_coord = (vertical_res+scale*vertical_res)*0.5 + offset
        if scale*diameter < 1:
            screen.set_at((int(hor_coord), int(ground_coord-height*scale*vertical_res)), color)
        else:
            pg.draw.circle(screen, color, (hor_coord, ground_coord-height*scale*vertical_res), max(1,scale*diameter))

def vision(x_pos, y_pos, rot, FOV, point_pos):
    angle = math.atan2(point_pos[1]-y_pos, point_pos[0]-x_pos) # absolute angle
    if abs(point_pos[1]-y_pos + math.sin(angle)) < abs(point_pos[1]-y_pos):
        angle -= math.pi # wrong direction
    angle2 = (rot-angle)%(2*math.pi) # relative angle
    angle2degree = math.degrees(angle2)
    if angle2degree > 180:
        angle2degree = angle2degree - 360
    in_FOV = angle2degree > -FOV/2 and angle2degree < FOV/2

    return in_FOV, angle, angle2, angle2degree

def floorcasting(x_pos, y_pos, rot, FOV, mod, screen, frame, floor, floor_scale, offset):
    size = floor.shape
    screen_size = screen.get_size()
    halfvres = int(screen_size[1]/(2*floor_scale))
    hres = int(screen_size[0]/floor_scale)
    n_pixels = int(halfvres - offset/floor_scale)
    ns = TALLNESS*halfvres/((halfvres - offset/floor_scale +0.1-np.linspace(0, halfvres- offset/floor_scale, n_pixels)))# depth
    # shade = 0.5 + 0.5*(np.linspace(0, n_pixels, n_pixels)/halfvres)
    # shade = np.dstack((shade, shade, shade))
    for i in range(hres):
        rot_i = rot + math.radians(i*mod*floor_scale - FOV*0.5)
        sin, cos, cos2 = np.sin(rot_i), np.cos(rot_i), np.cos(rot_i-rot)
        xs, ys = x_pos+ns*cos/cos2, y_pos+ns*sin/cos2
        xxs, yys = ((50*xs)%size[0]).astype('int'), ((50*ys)%size[1]).astype('int')
        frame[i][2*halfvres-n_pixels:] = floor[np.flip(xxs),np.flip(yys)]#* shade 
        # frame[i][2*halfvres-n_pixels:2*halfvres-int(2*n_pixels/3)] = floor2[np.flip(xxs[int(2*n_pixels/3):]),np.flip(yys[int(2*n_pixels/3):])]
        # frame[i][2*halfvres-int(2*n_pixels/3):] = floor[np.flip(xxs[:int(2*n_pixels/3)]),np.flip(yys[:int(2*n_pixels/3)])]#* shade 

    surf = pg.surfarray.make_surface(frame)
    screen.blit(pg.transform.smoothscale(surf, screen_size), (0,0))

if __name__ == '__main__':
    asyncio.run( main() )



