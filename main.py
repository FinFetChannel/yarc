import asyncio
import pygame as pg
import pygame.surfarray
import math
import random
import numpy as np

import src.maps as maps

async def main():
    pg.init()
    screen_scale = 2
    screen_size = [int(192*screen_scale), 4*int(27*screen_scale)]
    fov = 75
    mod = fov/screen_size[0]
    screen = pg.display.set_mode(screen_size, pg.SCALED)
    
    clock = pg.time.Clock()
    font = pg.font.SysFont(None, 20, 1)

    pg.mouse.set_visible(False)
    
    mapa, entity_data = maps.read_map(pg.image.load('map0.png'))
    print(entity_data)

    x_pos = y_pos = 1.533
    rot = rot_v = 0
    
    # entities = []
    # for entitity in entity_data:
    #     entities.append()
    
    pg.event.set_grab(1)
    wall = pg.image.load('wall.jpg').convert()
    floor = pg.surfarray.array3d(pg.image.load('floor.jpg').convert())
    floor_color = np.mean(floor[0]), np.mean(floor[1]), np.mean(floor[2]),
    # floor = pg.surfarray.array3d(pg.transform.smoothscale(pg.transform.smoothscale(pg.image.load('floor.jpg'), (20,20)), (100,100)))
    sky = pg.transform.smoothscale(pg.image.load('skybox.png').convert(), (12*screen_size[0]*60/fov, 3*screen_size[1]))
    
    robot_sheet = pg.image.load('robot.png').convert()
    robot_sheet.set_colorkey((255,255,255))
    robot = []
    for j in range(3):
        robot.append([])
        for i in range(4):
            robot[-1].append(pg.Surface.subsurface(robot_sheet, [i*100, j*200, 100, 200]))
    floor_points = np.random.uniform(-10, len(mapa)+10, (100, 2))
    tree = pg.image.load('tree.png').convert()
    tree.set_colorkey((255,255,255))
    # subpoints = 3
    # for i in range(subpoints*len(mapa)-subpoints):
    #     for j in range(subpoints*len(mapa)-subpoints):
    #         # position = [i/subpoints+0.5, j/subpoints+0.5]
    #         position = [random.uniform(1, len(mapa)-1), random.uniform(1, len(mapa)-1)]
    #         if mapa[int(position[0])][int(position[1])] == 0:
    #             floor_points.append(position)

    
    sprites = [robot, tree]
    floor_scale = 2
    hres = int(screen_size[0]/floor_scale)
    halfvres = int(screen_size[1]/(2*floor_scale))
    frame = np.zeros([hres, halfvres*2, 3])    

    vertical_pos = 0
    vertical_vel = 0
    graphics_low = 0
    indoor = 1
    bullet_time = 0
    total_time = 0
    animation_time = 0
    running = 1
    while running:

        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                running = 0
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

        floor_points = floor_points + np.random.uniform(-1, 1, (100, 2))*elapsed_time
        x_pos, y_pos, rot, rot_v = movement(x_pos, y_pos, rot, rot_v, mapa, 2*elapsed_time)
        
        vertical_pos = max(0, vertical_pos+vertical_vel*elapsed_time)
        vertical_vel = max(-2, vertical_vel - elapsed_time*10)
        offset = (rot_v + vertical_pos)*screen_size[1]
        
        if graphics_low:
            pg.draw.rect(screen, floor_color, [0,screen_size[1]/2+offset,screen_size[0], screen_size[1]/2-offset])
        
        elif offset < screen_size[1]/2:
            floorcasting(x_pos, y_pos, rot, fov, mod, screen, frame, floor, floor_scale, offset)

        sub_sky = pg.Surface.subsurface(sky, (math.degrees(rot%(2*math.pi)*screen_size[0]/fov), screen_size[1]-offset, screen_size[0], screen_size[1]/2+offset))
        screen.blit(sub_sky, (0, 0))    
        for i in range(len(floor_points)):
            draw_point(screen, x_pos, y_pos, rot, fov, floor_points[i], offset, indoor, (55,55,0))
            
        
        raycast_walls(screen, mod, fov, mapa, x_pos, y_pos, rot, offset, wall)
        for i, entity in enumerate(entity_data):
            if entity[0] in [0] and entity[5] == 0:
                move_sprite(entity, 0.5, mapa, elapsed_time)
            draw_sprite(screen, x_pos, y_pos, rot, fov, mapa, entity, sprites, offset, animation_time)
            if i > 0 and entity[4] > entity_data[i-1][4]:
                entity_data[i-1], entity_data[i] = entity_data[i], entity_data[i-1]
            
        screen.blit(font.render(str(fps), 1, [255, 255, 255]), [5,5])
        
        pg.display.update()

        await asyncio.sleep(0)  # very important, and keep it 0
        if not running:
            pg.quit()
            return

def movement(x_pos, y_pos, rot, rot_v, mapa, elapsed_time):
    
    if pg.mouse.get_focused():
        p_mouse = pg.mouse.get_rel()
        if abs(p_mouse[0]) > 1:
            rot = rot + min(max((p_mouse[0])/200, -0.2), .2)
        if abs(p_mouse[1]) > 1:
            rot_v = rot_v - min(max((p_mouse[1])/200, -0.2), .2)
            rot_v = min(0.5, max(-0.5, rot_v))
    
    sizeX = len(mapa) - 1
    sizeY = len(mapa[0]) - 1
    pressed_keys = pg.key.get_pressed()
    x, y = x_pos, y_pos
    
    forward = (pressed_keys[pg.K_UP] or pressed_keys[ord('w')]) - (pressed_keys[pg.K_DOWN] or pressed_keys[ord('s')])
    sideways = (pressed_keys[pg.K_LEFT] or pressed_keys[ord('a')]) - (pressed_keys[pg.K_RIGHT] or pressed_keys[ord('d')])

    if forward*sideways != 0: # limit speed moving diagonally
        forward, sideways = forward*0.7, sideways*0.7

    x += elapsed_time*(forward*math.cos(rot) + sideways*math.sin(rot))
    y += elapsed_time*(forward*math.sin(rot) - sideways*math.cos(rot))

    delta_player = 0.1

    x = np.clip(x, delta_player, sizeX-delta_player)
    y = np.clip(y, delta_player, sizeY-delta_player)

    if (mapa[int(x-delta_player)][int(y-delta_player)] == 0 
        and mapa[int(x+delta_player)][int(y+delta_player)] == 0 
        and mapa[int(x+delta_player)][int(y-delta_player)] == 0 
        and mapa[int(x-delta_player)][int(y+delta_player)] == 0):
        return x, y, rot, rot_v
    
    elif (mapa[int(x_pos-delta_player)][int(y-delta_player)] == 0 
        and mapa[int(x_pos+delta_player)][int(y+delta_player)] == 0 
        and mapa[int(x_pos+delta_player)][int(y-delta_player)] == 0 
        and mapa[int(x_pos-delta_player)][int(y+delta_player)] == 0):
        return x_pos, y, rot, rot_v
    
    elif (mapa[int(x-delta_player)][int(y_pos-delta_player)] == 0 
        and mapa[int(x+delta_player)][int(y_pos+delta_player)] == 0 
        and mapa[int(x+delta_player)][int(y_pos-delta_player)] == 0 
        and mapa[int(x-delta_player)][int(y_pos+delta_player)] == 0):
        return x, y_pos, rot, rot_v
    
    return x_pos, y_pos, rot, rot_v
        
def move_sprite(entity, velocity, mapa, elapsed_time):
    sizeX = len(mapa) - 1
    sizeY = len(mapa[0]) - 1
    x = entity[1] + elapsed_time*math.cos(entity[3])*velocity
    y = entity[2] + elapsed_time*math.sin(entity[3])*velocity

    if x > 0 and y > 0 and x < sizeX and y < sizeY and mapa[int(x)][int(y)] == 0:
        entity[1], entity[2] = x, y
    else:
        entity[3] = random.uniform(0, 2*math.pi)

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

    for i in range(15):
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
        dist = dist - deltaDistY
    else:
        dist = dist - deltaDistX
        
    x = x + rayDirX*dist - 0.0001*cos
    y = y + rayDirY*dist - 0.0001*sin
    
    return x, y, dist

def raycast_walls(screen, mod, fov, mapa, x_pos, y_pos, rot, offset, wall):
    horizontal_res, vertical_res = screen.get_size()
    for i in range(horizontal_res): #vision loop
        rot_i = rot + math.radians(i*mod - fov*0.5)
        x, y, dist = lodev_DDA(x_pos, y_pos, rot_i, mapa)
        
        scale = int(vertical_res/max(0.1, dist*math.cos(math.radians(i*mod-fov*0.5))))
        text_coord = x%1
        if text_coord < 0.001 or text_coord > 0.999:
            text_coord = y%1
        subsurface = pg.Surface.subsurface(wall, (99*text_coord, 0, 1, 99))
        resized = pg.transform.scale(subsurface, (1,scale))
        screen.blit(resized, (i, (vertical_res-scale)*0.5+offset))

def draw_sprite(screen, x_pos, y_pos, rot, fov, mapa, entity, sprites, offset, total_time):
    entity_pos = entity[1], entity[2]
    in_fov, angle, angle2, angle2degree = vision(x_pos, y_pos, rot, fov, entity_pos)

    if in_fov:
        x, y, dist = lodev_DDA(x_pos, y_pos, angle, mapa)
        dist2player = math.sqrt((x_pos-entity[1])**2+(y_pos-entity[2])**2)
        entity[4] = dist2player
        if dist2player-0.2 < dist:
            horizontal_res, vertical_res = screen.get_size()
            screen_scale = vertical_res*0.003
            if type(sprites[entity[0]]) == list:
                facing_angle = int(((entity[3] - angle -3*math.pi/4)%(2*math.pi))/(math.pi/2))
                if type(sprites[entity[0]][0]) == list:
                    if entity[5] == 0:
                        selected_sprite = sprites[entity[0]][1+int(total_time*3)%2][facing_angle]
                    elif entity[5] == 1:
                        selected_sprite = sprites[entity[0]][0][facing_angle]
                else:
                    selected_sprite = sprites[entity[0]][facing_angle]
            else:
                selected_sprite = sprites[entity[0]]

            old_size = selected_sprite.get_size()

            scale =  min(4, 1/(dist2player*math.cos(angle2)))
            new_size = screen_scale*old_size[0]*scale, screen_scale*old_size[1]*scale
            hor_coord = (fov*0.5-angle2degree)*horizontal_res/fov - new_size[0]*0.5
            ground_coord = (1+scale)*vertical_res*0.5 + offset
            
            scaled_sprite = pg.transform.scale(selected_sprite, new_size)
            screen.blit(scaled_sprite, (hor_coord, ground_coord - new_size[1]))   

def draw_point(screen, x_pos, y_pos, rot, fov, point_pos, offset, indoor, color):
    in_fov, angle, angle2, angle2degree = vision(x_pos, y_pos, rot, fov, point_pos)
    if in_fov:
        horizontal_res, vertical_res = screen.get_size()
        dist2player = math.sqrt((x_pos-point_pos[0])**2+(y_pos-point_pos[1])**2)
        scale =  min(4, 1/(dist2player*math.cos(angle2)))
        hor_coord = int((fov*0.5-angle2degree)*horizontal_res/fov)
        ground_coord = int((vertical_res+scale*vertical_res)*0.5 + offset)
        pg.draw.circle(screen, color, (hor_coord, ground_coord), scale*5)
        if indoor:
            pg.draw.circle(screen, (255,255,255), (hor_coord, ground_coord-2*scale*vertical_res), scale*5)

def vision(x_pos, y_pos, rot, fov, point_pos):
    angle = math.atan2(point_pos[1]-y_pos, point_pos[0]-x_pos) # absolute angle
    if abs(point_pos[1]-y_pos + math.sin(angle)) < abs(point_pos[1]-y_pos):
        angle -= math.pi # wrong direction
    angle2 = (rot-angle)%(2*math.pi) # relative angle
    angle2degree = math.degrees(angle2)
    if angle2degree > 180:
        angle2degree = angle2degree - 360
    in_fov = angle2degree > -fov/2 and angle2degree < fov/2

    return in_fov, angle, angle2, angle2degree

def floorcasting(x_pos, y_pos, rot, fov, mod, screen, frame, floor, floor_scale, offset):
    screen_size = screen.get_size()
    halfvres = int(screen_size[1]/(2*floor_scale))
    hres = int(screen_size[0]/floor_scale)
    n_pixels = int(halfvres - offset/floor_scale)
    ns = halfvres/((halfvres - offset/floor_scale +0.1-np.linspace(0, halfvres- offset/floor_scale, n_pixels)))# depth
    # shade = 0.5 + 0.5*(np.linspace(0, n_pixels, n_pixels)/halfvres)
    # shade = np.dstack((shade, shade, shade))
    for i in range(hres):
        rot_i = rot + math.radians(i*mod*floor_scale - fov*0.5)
        sin, cos, cos2 = np.sin(rot_i), np.cos(rot_i), np.cos(rot_i-rot)
        xs, ys = x_pos+ns*cos/cos2, y_pos+ns*sin/cos2
        xxs, yys = (xs%1*99).astype('int'), (ys%1*99).astype('int')
        frame[i][2*halfvres-n_pixels:] = floor[np.flip(xxs),np.flip(yys)]#* shade 
        # frame[i][2*halfvres-n_pixels:2*halfvres-int(2*n_pixels/3)] = floor2[np.flip(xxs[int(2*n_pixels/3):]),np.flip(yys[int(2*n_pixels/3):])]
        # frame[i][2*halfvres-int(2*n_pixels/3):] = floor[np.flip(xxs[:int(2*n_pixels/3)]),np.flip(yys[:int(2*n_pixels/3)])]#* shade 

    surf = pg.surfarray.make_surface(frame)
    screen.blit(pg.transform.smoothscale(surf, screen_size), (0,0))

if __name__ == '__main__':
    asyncio.run( main() )



