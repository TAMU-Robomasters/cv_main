
import cv2
import numpy as np
import filter.py as filter


class Box():
    def __init__(self, x, y, height, width):
        self.x = x
        self.y = y
        self.height = height
        self.width = width


def main():
    box = Box(300, 150, 50, 100)
    # print(box.x)

    blck_backgrnd = np.zeros((480, 848,1), dtype= "uint8")


    # make kalman filter object

    # run while loop (true) exits on escape key
    while (True):
        cv2.rectangle(blck_backgrnd, (box.x, box.y) , (box.x + box.width, box.y + box.height), (255,255,50), 2)
        cv2.imshow('Single Channel Window', blck_backgrnd)
        if cv2.waitKey(0):
            cv2.destroyAllWindows()
            break


main()
