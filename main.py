import asyncio
import pygame as pg
import math
import random

async def main():
    pg.init()
    horizontal_res = 192*4
    vertical_res = 108*4
    fov = 60
    mod = fov/horizontal_res
    step = 0.005
    screen = pg.display.set_mode((horizontal_res,vertical_res))#, pg.SCALED)
    clock = pg.time.Clock()
    font = pg.font.SysFont("Arial", 20, 1)
    pg.mouse.set_visible(False)
    running = 1
    mapa = [[1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 1],
            [1, 0, 1, 0, 1, 1],
            [1, 0, 1, 0, 1, 1],
            [1, 0, 0, 0, 0, 1],
            [1, 1, 1, 1, 1, 1]]
    posx = posy = rot = 1.5
    
    frame = pg.Surface([horizontal_res, vertical_res])
    
    pg.event.set_grab(1)
    wall = pg.image.load('wall.jpg').convert()
    sky = pg.transform.smoothscale(pg.image.load('skybox.jpg').convert(), (12*horizontal_res, vertical_res))

    while True:
        elapsed_time = clock.tick()/1000
        posx, posy, rot = movement(posx, posy, rot, mapa, 2*elapsed_time)

        fps = str(round(clock.get_fps(),1))
        frame.blit(sky, (-math.degrees(rot%(2*math.pi)*horizontal_res/fov), 0))
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                running = 0

        for i in range(horizontal_res): #vision loop
            rot_i = rot + math.radians(i*mod - fov*0.5)
            x, y, dist = lodev(posx, posy, rot_i, mapa)
            
            scale = vertical_res*(min(4, (1/(dist*math.cos(math.radians(i*mod-fov*0.5))))))
            text_coord = x%1
            if text_coord < 0.05 or text_coord > 0.95:
                text_coord = y%1

            subsurface = pg.Surface.subsurface(wall, (int(100*text_coord), 0, 1, 99))
            resized = pg.transform.scale(subsurface, (1,scale))
            frame.blit(resized, (i, (vertical_res-scale)*0.5))

        screen.blit(frame, (0,0))
        screen.blit(font.render(fps, 1, [255, 255, 255]), [0,0])
        
        pg.display.update()

        await asyncio.sleep(0)  # very important, and keep it 0
        if not running:
            pg.quit()
            return

def movement(posx, posy, rot, mapa, elapsed_time):
    
    if pg.mouse.get_focused():
        p_mouse = pg.mouse.get_rel()
        if abs(p_mouse[0]) > 1:
            rot = rot + min(max((p_mouse[0])/200, -0.2), .2)
    
    pressed_keys = pg.key.get_pressed()
    x, y = posx, posy
    
    forward = (pressed_keys[pg.K_UP] or pressed_keys[ord('w')]) - (pressed_keys[pg.K_DOWN] or pressed_keys[ord('s')])
    sideways = (pressed_keys[pg.K_LEFT] or pressed_keys[ord('a')]) - (pressed_keys[pg.K_RIGHT] or pressed_keys[ord('d')])

    if forward*sideways != 0: # limit speed moving diagonally
        forward, sideways = forward*0.7, sideways*0.7

    x += elapsed_time*(forward*math.cos(rot) + sideways*math.sin(rot))
    y += elapsed_time*(forward*math.sin(rot) - sideways*math.cos(rot))

    if (mapa[int(x-0.3)][int(y-0.3)] == 0 
        and mapa[int(x+0.3)][int(y+0.3)] == 0 
        and mapa[int(x+0.3)][int(y-0.3)] == 0 
        and mapa[int(x-0.3)][int(y+0.3)] == 0):
        return x, y, rot
    elif (mapa[int(posx-0.3)][int(y-0.3)] == 0 
        and mapa[int(posx+0.3)][int(y+0.3)] == 0 
        and mapa[int(posx+0.3)][int(y-0.3)] == 0 
        and mapa[int(posx-0.3)][int(y+0.3)] == 0):
        return posx, y, rot
    elif (mapa[int(x-0.3)][int(posy-0.3)] == 0 
        and mapa[int(x+0.3)][int(posy+0.3)] == 0 
        and mapa[int(x+0.3)][int(posy-0.3)] == 0 
        and mapa[int(x-0.3)][int(posy+0.3)] == 0):
        return x, posy, rot
    else:
        return posx, posy, rot

def lodev(x, y, rot_i, mapa):
    size = len(mapa)
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
            if mapX < 1 or mapX > size-1:
                break
        else:
            sideDistY += deltaDistY
            mapY += stepY
            dist = sideDistY
            side = 1
            if mapY < 1 or mapY > size-1:
                break
        if mapa[mapX][mapY] != 0:
            break
            
    if side:
        dist = dist - deltaDistY
    else:
        dist = dist - deltaDistX
        
    x = x + rayDirX*dist - 0.001*cos
    y = y + rayDirY*dist - 0.001*sin
    
    return x, y, dist

asyncio.run( main() )

# do not add anything from here
# asyncio.run is non block on pg-wasm

