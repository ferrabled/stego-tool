# Importing all necessary libraries
import cv2
import os
import argparse

parser = argparse.ArgumentParser(description="Simple Python script to get all frames from a video")
parser.add_argument("video", help="The video path")
args = parser.parse_args()
  
# Read the video from specified path
cam = cv2.VideoCapture(args.video)
  
try:
      
    # creating a folder named data
    if not os.path.exists('data'):
        os.makedirs('data')
  
# if not created then raise error
except OSError:
    print ('Error: Creating directory of data')
  
# frame
currentframe = 0
  
#while(True):
      
# reading from frame
ret,frame = cam.read()

if ret:
    # if video is still left continue creating images
    name = './data/frame' + str(currentframe) + '.png'
    print ('Creating...' + name)

    # converting the image from BGR to RGB
    newRGBimage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # writing the extracted images
    cv2.imwrite(name, newRGBimage)

    # increasing counter so that it will
    # show how many frames are created
    currentframe += 1
#else:
#    break
  
# Release all space and windows once done
cam.release()
cv2.destroyAllWindows()