import asyncio
import pygame as pg
import math

pg.init()
screen = pg.display.set_mode((800,600))
clock = pg.time.Clock()
font = pg.font.SysFont("Arial", 20, 1)
pg.mouse.set_visible(False)

async def main():
    running = 1
    size = 6
    mapa = [[1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 1],
            [1, 0, 1, 0, 1, 1],
            [1, 0, 1, 0, 1, 1],
            [1, 0, 0, 0, 0, 1],
            [1, 1, 1, 1, 1, 1]]
    posx = posy = rot = 1.5
    horizontal_res = 200
    vertical_res = int(horizontal_res*0.75)
    frame = pg.Surface([horizontal_res, vertical_res])
    mod = 60/horizontal_res
    pg.event.set_grab(1)
    wall = pg.image.load('wall.jpg').convert()
    sky = pg.transform.smoothscale(pg.image.load('skybox.jpg').convert(), (12*horizontal_res, vertical_res))
    

    while True:
        elapsed_time = clock.tick()/1000
        posx, posy, rot = movement(posx, posy, rot, mapa, 2*elapsed_time)

        fps = str(round(clock.get_fps(),1))
        # frame.fill([0,0,0])
        frame.blit(sky, (-math.degrees(rot%(2*math.pi)*horizontal_res/60), 0))
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                running = 0

        for i in range(horizontal_res): #vision loop
            rot_i = rot + math.radians(i*mod - 30)
            x, y = (posx, posy)
            sin, cos = (0.02*math.sin(rot_i), 0.02*math.cos(rot_i))
            n = 0
            while True: # ray loop
                x, y = (x + cos, y + sin)
                n = n+1
                if mapa[int(x)][int(y)] != 0:
                    h = vertical_res*(1/(0.02 * n*math.cos(math.radians(i*mod-30))))
                    xx = x%1
                    if xx < 0.05 or xx > 0.95:
                        xx = y%1
                    resized = pg.transform.scale(wall, (h,h))
                    subsurface = pg.Surface.subsurface(resized, (min(int(h)-1, int(xx*h)), 0, 1, int(h)))
                    frame.blit(subsurface, (i, (vertical_res-h)*0.5))
                    break 

        upscaled = pg.transform.scale(frame, [800,600])
        
        upscaled.blit(font.render(fps, 1, [255, 255, 255]), [0,0])
        screen.blit(upscaled, (0,0))

        

        pg.display.update()

        await asyncio.sleep(0)  # very important, and keep it 0
        if not running:
            pg.quit()
            return

def movement(posx, posy, rot, mapa, elapsed_time):
    
    if pg.mouse.get_focused():
        p_mouse = pg.mouse.get_rel()
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

asyncio.run( main() )

# do not add anything from here
# asyncio.run is non block on pg-wasm

