def read_map(image):

    color_map = {
        #### any color not in the dict -> floor block
        (  0,   0,   0): 4,  # black -> wall block
        (127, 127, 127): 5,  # black -> wall block
        (195, 195, 195): 3, # light gray -> castle block
        # (255, 201,  14): 2,  # gold -> mistery block
        # (136,   0,  21): 3,  # dark red -> brick block
        # (255, 127,  39): 4,  # orange -> block block
        # (181, 230,  29): 5,  # light green -> base pipe block, 6 for top,10 top face
        # (  0, 255,   0): 10,  # pure green -> horizontal pipe block
        # (195, 195, 195): 8, # light gray -> castle block
        
        # (255, 255, 255):-1, # white -> cloud block
        # (255, 242,   0):-2, # yellow -> grow mushroom
        # ( 34, 177,  76):-3, # dark green -> life mushroom
        # (239, 228, 176):-4, # light yellow -> hidden mistery block
        # (  0, 162, 232):-5, # blue -> star
        # ( 63,  72, 204):-6, # indigo blue -> enter pipe
        # (112, 146, 190):-7, # gray blue -> exit pipe
        # (200, 191, 231):-20,# light purple -> hidden coin x10 
    }

    entity_map = {
        (237,  28,  36): 0, # red -> robot
        (34, 177,  76): 1,  # light green -> tree
        # (255, 174, 201): 2, # pink -> koopa
        # (163,  73, 164): 8, # purple -> flag pole
        # (153, 217, 234): 9, # blue -> coin
    }

    # Convert the image to a 2D list of integers using the color map
    map_data = []
    entity_data = []
    height = image.get_height()
    for x in range(image.get_width()):
        map_data.append([])
        for y in range(height):
            pixel_color = image.get_at((x, y))
            block_type = color_map.get((pixel_color.r, pixel_color.g, pixel_color.b), 0)

            map_data[x].append(block_type)
            entity_type = entity_map.get((pixel_color.r, pixel_color.g, pixel_color.b), -1)
            if entity_type >= 0:
                entity_data.append([entity_type, x + 0.5, y+0.5, 0, 0, x%2, 0, 5])# type, x, y, direction, distance, status, cooldown, health
                if entity_type == 1:
                    map_data[x][-1] = -1
    
    return map_data, entity_data