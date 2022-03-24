from toolbox.globals import path_to, config, print

def aim(bounding_boxes):
    # this should be nearly the same as aiming_main
    # BUT should just have additional debugging/print statements
    # however:
    # FIXME: this aiming doesn't actually do anything
    """
    @bounding_boxes - this is a list of boxes
                      each box (should) corrispond to an armor-plate on an enemy vehicle
                      the box itself is a list containing 4 things (in this order)
                      - integer: the x-coordinate of the top left corner of the box (measured in pixels)
                      - integer: the y-coordinate of the top left corner of the box (measured in pixels)
                      - integer: the width of the box (measured in pixels)
                      - integer: the height of the box (measured in pixels)
    @@returns:
        a list (or tuple) with two elements
        - the x-coordinate of where to aim the barrel
        - the y-coordinate of where to aim the barrel
        
        note: in the future this function might return more data, like the depth/distance to the target
    """
    
    x = 100
    y = 100
    
    return x, y


# if running the test file directly
if __name__ == "__main__":
    test_data = [
        #  # fake inputs                 # expected outputs (dead center of box)
        #  #  x,  y, width, height       #  x    y   
        (  [ 50, 50,  200, 200 ],        ( 150, 150 )  ),
        (  [ 50, 50,  200, 200 ],        ( 150, 150 )  ),
        # TODO: add some better data
        (  [ 50, 50,  200, 200 ],        ( 150, 150 )  ),
        (  [ 50, 50,  200, 200 ],        ( 150, 150 )  ),
        (  [ 50, 50,  200, 200 ],        ( 150, 150 )  ),
        (  [ 50, 50,  200, 200 ],        ( 150, 150 )  ),
        (  [ 50, 50,  200, 200 ],        ( 150, 150 )  ),
        (  [ 50, 50,  200, 200 ],        ( 150, 150 )  ),
    ]
    
    # test all those inputs
    for each_input, each_expeacted_output in test_data:
        actual_output = aim(each_input) 
        if actual_output != each_expeacted_output:
            raise Exception(f'The aiming function failed a test:\ninput: {each_input}\nexpected_output:{each_expeacted_output}\nactual output:{actual_output}')
