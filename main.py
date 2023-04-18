import asyncio
import pygame as pg
import math
import random

async def main():
    pg.init()
    screen_scale = 3.7
    screen_size = [int(192*screen_scale), int(108*screen_scale)]
    fov = 75
    mod = fov/screen_size[0]
    screen = pg.display.set_mode(screen_size, pg.SCALED)
    
    clock = pg.time.Clock()
    font = pg.font.SysFont(None, 20, 1)

    pg.mouse.set_visible(False)
    
    mapa = [[1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 1],
            [1, 0, 1, 0, 1, 1],
            [1, 0, 1, 0, 1, 1],
            [1, 0, 0, 0, 0, 1],
            [1, 1, 1, 1, 1, 1]]
    
    x_pos = y_pos = 1.533
    rot = rot_v = 0
    
    pg.event.set_grab(1)
    wall = pg.image.load('wall.jpg').convert()
    sky = pg.transform.smoothscale(pg.image.load('skybox.png').convert(), (12*screen_size[0]*60/fov, 3*screen_size[1]))
    floor_points = []
    subpoints = 3
    for i in range(subpoints*len(mapa)-subpoints):
        for j in range(subpoints*len(mapa)-subpoints):
            position = [i/subpoints+0.5, j/subpoints+0.5]
            if mapa[int(position[0])][int(position[1])] == 0:
                floor_points.append(position)

    robot_sheet = pg.image.load('robot.png').convert()
    robot_sheet.set_colorkey((255,255,255))
    robot = []
    for i in range(4):
        robot.append(pg.Surface.subsurface(robot_sheet, [i*100, 0, 100, 200]))
    robot_pos = [2.54, 1.5, 0] # x, y, dir
    
    indoor = 0
    bullet_time = 0
    total_time = 0
    running = 1
    while running:

        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                running = 0
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    if bullet_time + 5 < total_time:
                        bullet_time = total_time + 5

        elapsed_time = clock.tick()*0.001
        total_time += elapsed_time
        fps = int(clock.get_fps())

        if bullet_time > total_time:
            elapsed_time *= 0.1

        x_pos, y_pos, rot, rot_v = movement(x_pos, y_pos, rot, rot_v, mapa, 2*elapsed_time)
        robot_pos = move_sprite(robot_pos, 0.5, mapa, elapsed_time)

        offset = rot_v*screen_size[1]
        if indoor:
            screen.fill((70,70,79))
            pg.draw.rect(screen, (230,230,200), [0,0,screen_size[0], screen_size[1]/2+offset])
        else:
            sub_sky = pg.Surface.subsurface(sky, (math.degrees(rot%(2*math.pi)*screen_size[0]/fov), screen_size[1]-offset, screen_size[0], screen_size[1]))
            screen.blit(sub_sky, (0, 0))
        
        for i in range(len(floor_points)):
            draw_points(screen, x_pos, y_pos, rot, fov, floor_points[i], offset, indoor)

        raycast_walls(screen, mod, fov, mapa, x_pos, y_pos, rot, offset, wall)
        draw_sprite(screen, x_pos, y_pos, rot, fov, mapa, robot_pos, robot, offset)
        
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
            rot_v = min(1, max(-1, rot_v))
    
    size = len(mapa)
    pressed_keys = pg.key.get_pressed()
    x, y = x_pos, y_pos
    
    forward = (pressed_keys[pg.K_UP] or pressed_keys[ord('w')]) - (pressed_keys[pg.K_DOWN] or pressed_keys[ord('s')])
    sideways = (pressed_keys[pg.K_LEFT] or pressed_keys[ord('a')]) - (pressed_keys[pg.K_RIGHT] or pressed_keys[ord('d')])

    if forward*sideways != 0: # limit speed moving diagonally
        forward, sideways = forward*0.7, sideways*0.7

    x += elapsed_time*(forward*math.cos(rot) + sideways*math.sin(rot))
    y += elapsed_time*(forward*math.sin(rot) - sideways*math.cos(rot))

    x = max(0, min(size-1, x))
    y = max(0, min(size-1, y))

    if (mapa[int(x-0.3)][int(y-0.3)] == 0 
        and mapa[int(x+0.3)][int(y+0.3)] == 0 
        and mapa[int(x+0.3)][int(y-0.3)] == 0 
        and mapa[int(x-0.3)][int(y+0.3)] == 0):
        return x, y, rot, rot_v
    elif (mapa[int(x_pos-0.3)][int(y-0.3)] == 0 
        and mapa[int(x_pos+0.3)][int(y+0.3)] == 0 
        and mapa[int(x_pos+0.3)][int(y-0.3)] == 0 
        and mapa[int(x_pos-0.3)][int(y+0.3)] == 0):
        return x_pos, y, rot, rot_v
    elif (mapa[int(x-0.3)][int(y_pos-0.3)] == 0 
        and mapa[int(x+0.3)][int(y_pos+0.3)] == 0 
        and mapa[int(x+0.3)][int(y_pos-0.3)] == 0 
        and mapa[int(x-0.3)][int(y_pos+0.3)] == 0):
        return x, y_pos, rot, rot_v
    
    return x_pos, y_pos, rot, rot_v

def move_sprite(position, velocity, mapa, elapsed_time):
    size = len(mapa)
    x = position[0] + elapsed_time*math.cos(position[2])*velocity
    y = position[1] + elapsed_time*math.sin(position[2])*velocity

    if x > 0 and y > 0 and x < size -1 and y < size-1 and mapa[int(x)][int(y)] == 0:
        return [x, y, position[2]]
    else:
        direction = random.uniform(0, 2*math.pi)
        return [position[0], position[1], direction]

### Digital Differential Analysis Algorithm by Lode V., source:
### https://lodev.org/cgtutor/raycasting.html
def lodev_DDA(x, y, rot_i, mapa):
    size = len(mapa)
    found_wall = False
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

    while 1:
        if (sideDistX < sideDistY):
            sideDistX += deltaDistX
            mapX += stepX
            dist = sideDistX
            side = 0
            if mapX < 0 or mapX > size-1:
                break
        else:
            sideDistY += deltaDistY
            mapY += stepY
            dist = sideDistY
            side = 1
            if mapY < 0 or mapY > size-1:
                break
        if mapa[mapX][mapY] != 0:
            found_wall = True
            break
            
    if side:
        dist = dist - deltaDistY
    else:
        dist = dist - deltaDistX
        
    x = x + rayDirX*dist - 0.0001*cos
    y = y + rayDirY*dist - 0.0001*sin
    
    return x, y, dist, found_wall

def raycast_walls(screen, mod, fov, mapa, x_pos, y_pos, rot, offset, wall):
    horizontal_res, vertical_res = screen.get_size()
    for i in range(horizontal_res): #vision loop
        rot_i = rot + math.radians(i*mod - fov*0.5)
        x, y, dist, found_wall = lodev_DDA(x_pos, y_pos, rot_i, mapa)
        
        if found_wall:
            scale = vertical_res*(min(4, (1/(dist*math.cos(math.radians(i*mod-fov*0.5))))))
            text_coord = x%1
            if text_coord < 0.05 or text_coord > 0.95:
                text_coord = y%1

            subsurface = pg.Surface.subsurface(wall, (int(100*text_coord), 0, 1, 99))
            resized = pg.transform.scale(subsurface, (1,scale))
            screen.blit(resized, (i, (vertical_res-scale)*0.5+offset))

def draw_sprite(screen, x_pos, y_pos, rot, fov, mapa, sprite_pos, sprite, offset):
    
    in_fov, angle, angle2, angle2degree = vision(x_pos, y_pos, rot, fov, sprite_pos)

    if in_fov:
        x, y, dist, found_wall = lodev_DDA(x_pos, y_pos, angle, mapa)
        dist2player = math.sqrt((x_pos-sprite_pos[0])**2+(y_pos-sprite_pos[1])**2)
        if dist2player-0.2 < dist:
            horizontal_res, vertical_res = screen.get_size()
            screen_scale = vertical_res*0.003
            old_size = sprite[0].get_size()
            scale =  min(4, 1/(dist2player*math.cos(angle2)))
            new_size = screen_scale*old_size[0]*scale, screen_scale*old_size[1]*scale
            hor_coord = (fov*0.5-angle2degree)*horizontal_res/fov - new_size[0]*0.5
            ground_coord = (1+scale)*vertical_res*0.5 + offset
            facing_angle = int(((sprite_pos[2] - angle -3*math.pi/4)%(2*math.pi))/(math.pi/2))
            scaled_sprite = pg.transform.scale(sprite[facing_angle], new_size)
            screen.blit(scaled_sprite, (hor_coord, ground_coord - new_size[1]))   

def draw_points(screen, x_pos, y_pos, rot, fov, point_pos, offset, indoor):
    
    in_fov, angle, angle2, angle2degree = vision(x_pos, y_pos, rot, fov, point_pos)
    if in_fov:
        horizontal_res, vertical_res = screen.get_size()
        dist2player = math.sqrt((x_pos-point_pos[0])**2+(y_pos-point_pos[1])**2)
        scale =  min(4, 1/(dist2player*math.cos(angle2)))
        hor_coord = int((fov*0.5-angle2degree)*horizontal_res/fov)
        ground_coord = int((vertical_res+scale*vertical_res)*0.5 + offset)
        pg.draw.circle(screen, (105,105,105), (hor_coord, ground_coord), scale*5)
        if indoor:
            pg.draw.circle(screen, (255,255,255), (hor_coord, ground_coord-scale*vertical_res), scale*5)

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

if __name__ == '__main__':
    asyncio.run( main() )



