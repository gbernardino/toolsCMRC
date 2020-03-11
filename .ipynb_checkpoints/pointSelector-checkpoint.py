import numpy as np

from skimage.transform import hough_line, hough_line_peaks
from skimage.feature import canny
from skimage import data
import PIL
from PIL import Image
import matplotlib.pyplot as plt
import cv2
import argparse

def click_and_select(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        # record the ending (x, y) coordinates and indicate that
        # the cropping operation is finished
        param['points'].append((x, y))
        # draw a rectangle around the region of interest
        cv2.circle(image, (x, y), 10, (0, 255, 0), -1 )
        cv2.imshow("image", image)
        print(x, y, param)
        
parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('imagePath')
parser.add_argument('resultPath')
parser.add_argument('--nPoints',  default=4, type = int)

args = parser.parse_args()

# load the image, clone it, and setup the mouse callback function
image = cv2.imread(args.imagePath)
clone = image.copy()
cv2.namedWindow("image", cv2.WND_PROP_FULLSCREEN)          
#cv2.setWindowProperty("image", cv2.WND_PROP_FULLSCREEN, cv2.cv.CV_WINDOW_FULLSCREEN)
params = {'points' : [], 'circles' : []}
cv2.setMouseCallback("image", click_and_select, params)
# keep looping until the 'q' key is pressed
while len(params['points']) < args.nPoints:
    # display the image and wait for a keypress
    cv2.imshow("image", image)
    key = cv2.waitKey(1) & 0xFF
    # if the 'r' key is pressed, reset the cropping region
    if key == ord("r") and params['points']:
        del params['points'][-1]
        image  = clone.copy()
        for p in params['points']: 
            cv2.circle(image, p, 10, (0, 0, 255), -1 )
    # if the 'c' key is pressed, break from the loop
    elif key == ord("c"):
        break
np.savetxt(args.resultPath, np.array(params['points']))