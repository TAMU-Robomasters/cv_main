import numpy as np
import cv2
import math
from toolbox.globals import PARAMETERS,print


def visualizeDepthFrame(depth_frame_array):
    depth_colormap = cv2.applyColorMap(cv2.convertScaleAbs(depth_frame_array, alpha = 0.04), cv2.COLORMAP_JET)# this puts a color efffect on the depth frame
    images = depth_colormap                              # use this for individual streams
    # cv2.namedWindow('Align Example', cv2.WINDOW_NORMAL)   # names and shows the streams
    cv2.imwrite('depthmap.jpg', images)
    # # if you press escape or q you can cancel the process
    # key = cv2.waitKey(1)
    # print("press escape to cancel")
    # if key & 0xFF == ord('q') or key == 27:
    #     cv2.destroyAllWindows()
    
def getDistFromArray(depth_frame_array, bbox):
    gridSize = PARAMETERS['aiming']['grid_size']

    try:
        xTopLeft = bbox[0] 
        yTopLeft = bbox[1]
        width = bbox[2]
        height = bbox[3]
        # this is used to add to the currentX and currentY so that we can get the different points in the 9x9 grid
        x_interval = width/gridSize
        y_interval = height/gridSize
        # stores the x and y of the last point in the grid we got the distance from
        currX = 0
        currY = 0
        distances = np.array([])
        # double for loop to go through 2D array of 9x9 grid
        for i in range(gridSize):
            currX += x_interval # add the interval you calculated to traverse through the 9x9 grid
            # print(currX)
            if (xTopLeft+currX >= len(depth_frame_array[0])):
                break
            for j in range(gridSize):
                currY += y_interval # add the interval you calculated to traverse through the 9x9 grid
                # gets the distance of the point from the depth frame on the grid and appends to the array
                # print(currY)
                if (yTopLeft+currY >= len(depth_frame_array)):
                    break
                distances = np.append(distances, depth_frame_array[int(yTopLeft+currY)][int(xTopLeft+currX)]/1000)
            currY = 0
        
        distances = distances[distances!=0.0]   # removes all occurances of 0.0 (areas where there is not enough data return 0.0 as depth)
        median = np.median(distances)           # gets the median from the array
        std = np.std(distances)                 # gets the standard deviation from the array
        modifiedDistances = []                  # initializes a new array for removing outlier numbers
        # goes through distances array and adds any values that are less than X*standard deviations and ignores the rest
        for i in range(np.size(distances)):
            if abs(distances[i] - median) < 1.5 * std: # tune the standard deviation range for better results
                modifiedDistances = np.append(modifiedDistances,distances[i])

        distance = (np.mean(modifiedDistances)+np.median(modifiedDistances))/2
        return distance if (distance and distance>0 and distance<10) else 1
    except:
        return 1


# bbox[x coordinate of the top left of the bounding box, y coordinate of the top left of the bounding box, width of box, height of box]
# def WorldCoordinate(depth_frame, bbox):
#     depth_intrin = depth_frame.profile.as_video_stream_profile().intrinsics
#     depth_value = DistanceInBox(bbox)
#     # depth_pixel = [depth_intrin.ppx, depth_intrin.ppy]
#     depth_pixel = [bbox[0] + .5 * bbox[2], bbox[1] + .5 * bbox[3]]
#     depth_point =   rs.rs2_deproject_pixel_to_point(depth_intrin, depth_pixel, depth_value)
#     return depth_point
#     if not depth_frame:                     # if there is no aligned_depth_frame or color_frame then leave the loop
#         return None

# def getBulletDropPixels(depth_image,best_bounding_box):
#     z0 = getDistFromArray(depth_image,best_bounding_box)
#     print("Target Distance from Robot:",z0)
#     bulletHorizontalVelocity = PARAMETERS['aiming']['bullet_horizontal_velocity']
#     predictedTimeTaken = z0/bulletHorizontalVelocity
#     bulletDropMeters = .5 * 9.8 * (predictedTimeTaken**2)
#     bulletDropPixels = bulletDropMeters * 3779.5275
#     print("Bullet Drop Amount",bulletDropPixels)
#     return bulletDropPixels

# not that cool bullet drop
# def getBulletDropPixels(depth_image, best_bounding_box):
#     d = getDistFromArray(depth_image, best_bounding_box) #distance to bbox
#     t = d/30 # replace withe shooter velocity constant
#     worldCoords = WorldCoordinate(depth_image, best_bounding_box) # bbox coords in meters
#     worldCoords[1] -= (0.5)(9.8)(t)**2 # adjust the y coord by subtracting the dist in y that the bullet drops in the given depth
#     depth_intrin = depth_image.profile.as_video_stream_profile().intrinsics
#     pixelCoordsWithAdj = rs.rs2_project_point_to_pixel(depth_intrin, worldCoords) # y convert adjusted world coordinates to pixels

#     y = best_bounding_box[1] - pixelCoordsWithAdj[1] # get the difference of the original bbox y coord and the adjusted bbox y coord
#     return y # return the offset of the y coord in pixels

def bulletDropCompensation(depth_image, best_bounding_box, phee):
    # Calculated Variables
    depth = getDistFromArray(depth_image, best_bounding_box) #  meters
    diffC = 240 - 320 # pixels
    theta = math.degrees(math.atan((diffC/((diffC/abs(diffC)) * 240)) * math.tan(math.radians( (diffC/abs(diffC)) * 27.5))))   # in degrees
    # print("theta", theta)

    diffC = depth * math.tan(math.radians(theta)) # convert diffP to meters
    # print("diffC", diffC)

    # phee = -30

    # Constants
    lengthBarrel = 0.15
    cameraGap = 0.01
    v = 30
    depthFromPivot = lengthBarrel + depth
    diffP = diffC + cameraGap
    print("diffP", diffP)
    rho = math.degrees(math.atan(diffP/depthFromPivot))
    print("rho", rho) 
    phi = phee + rho

    # phi = -30
    # print("phi", phi)

    rangeP = depthFromPivot/math.cos(math.radians(rho))
    # print("rangeP", rangeP)
    # # rangeP = 2
    i = rangeP * math.cos(math.radians(phi))
    j = rangeP * math.sin(math.radians(phi))
    t = rangeP/v
    phiF = math.degrees(math.asin((j+4.9*t**2) / (v*t) ))
    # print("phiF", phiF)
    changeP = ((diffC/abs(diffC)) * 240) / math.tan(math.radians((diffC/abs(diffC)) * 27.5)) * math.tan(math.radians( (diffC/abs(diffC)) * phiF))
    
    return best_bounding_box[1]+0.5*best_bounding_box[3]-changeP