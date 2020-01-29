# -*- coding: utf-8 -*-
"""
Created on Tue Jan 28 19:43:04 2020

@author: xyf11
"""

import yolo_video
#import model
if __name__ == '__main__':
    inputpath = "test.avi"
    output = "output.avi"
    yolo = "./v3t1k/"
    confidence = 0.5
    threshold = 0.3
    yolo_video.modeling(inputpath,output,yolo,confidence,threshold)
    #print(result)