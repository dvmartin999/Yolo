#!/usr/bin/env python3
import sys
import os
import rospy
import numpy as np

from sensor_msgs.msg import Image, CompressedImage, TimeReference
#from sensor_msgs.msg import CompressedImage
from std_msgs.msg import Time
from vision_msgs.msg import Detection2DArray, Detection2D, ObjectHypothesisWithPose
from cv_bridge import CvBridge, CvBridgeError
import message_filters

dir_to_Tracker=os.path.dirname(os.path.dirname(os.path.dirname( __file__ )))
dir_to_Scripts = os.path.join(dir_to_Tracker,"Scripts") 
sys.path.append(dir_to_Scripts)

from yolov3.utils import detect_image, Load_Yolo_model
from yolov3.configs import *
from yolov3.yolov3 import *

os.environ['CUDA_VISIBLE_DEVICES'] = '0'

class object_detector:
    def __init__(self):
        print("[INFO] Initializing ROS...")
        rospy.init_node('Detection')

        print("[INFO] Loading modules...")
        self.yolo = Load_Yolo_model()
        self.bridge = CvBridge()

        print("[INFO] Loading config...")
        self.timer = TimeReference()

        print("[INFO] Initialize ROS publishers...")
        self.boxes_pub = rospy.Publisher("/Tracker/Detection/Boxes",Detection2DArray, queue_size=1)
        self.timer_pub = rospy.Publisher("/Tracker/Timer",TimeReference, queue_size=1)

        print("[INFO] Initialize ROS Subscribers...")
        self.processing_image = False # Need to mark when callback is active, so we're only processing one image at a time
        rospy.Subscriber("/zed2/zed_node/left/image_rect_color",Image,self.callback_raw_image,queue_size=1)
        self.class_name_list = read_class_names(YOLO_COCO_CLASSES)

        print("[INFO] Loading complete")
        self.init_time_delay = 0
        
        # Recursion doesn't work great in Python, which limits the recursion depth
        #self.callback()


    def callback(self):
        image = rospy.wait_for_message("/zed2/zed_node/left/image_rect_color/compressed",CompressedImage)
        time1 = rospy.Time.now().to_sec()
        self.timer.header = image.header
        self.timer.header.frame_id = "zed2_left_camera_frame"
        self.timer.time_ref = rospy.Time.now() 
        self.timer_pub.publish(self.timer)
        cv_image = self.bridge.compressed_imgmsg_to_cv2(image, "bgr8")
        _ , bboxes=detect_image(self.yolo, cv_image, "", input_size=YOLO_INPUT_SIZE, show=False,CLASSES=TRAIN_CLASSES,score_threshold=0.3, iou_threshold=0.1, rectangle_colors=(255,0,0))
        detect = Detection2DArray()
        detect.header = image.header

        for Object in bboxes:
            detection = Detection2D()
            hypo = ObjectHypothesisWithPose()
            #Start x
            x1 = Object[0]
            #End x
            x2 = Object[2]
            #Start y
            y1 = Object[1]
            #end y
            y2 = Object[3]

            #Size x
            Sx = x2-x1
            #Size y
            Sy = y2-y1
            #Center x
            Cx = x1+Sx/2
            #Center y
            Cy = y1+Sy/2

            detection.bbox.center.x = Cx
            detection.bbox.center.y = Cy
            detection.bbox.size_x   = Sx
            detection.bbox.size_y   = Sy

            hypo.id = int(Object[5])
            hypo.score = Object[4]

            detection.results = [hypo,]
            detection.is_tracking = False
            detect.detections.append(detection)
        self.boxes_pub.publish(detect)

        self.callback()   

    def callback_raw_image(self, image):
        if self.processing_image:
            return
        self.processing_image = True
        rospy.loginfo("Received image with size: %d x %d", image.height, image.width)
        time1 = rospy.Time.now().to_sec()
        self.timer.header = image.header
        self.timer.header.frame_id = "zed2_left_camera_frame"
        self.timer.time_ref = rospy.Time.now() 
        self.timer_pub.publish(self.timer)
        cv_image = np.frombuffer(image.data, dtype=np.uint8).reshape(image.height, image.width, 4)
        _ , bboxes=detect_image(self.yolo, cv_image, "", input_size=YOLO_INPUT_SIZE, show=False,CLASSES=YOLO_COCO_CLASSES,score_threshold=0.3, iou_threshold=0.1, rectangle_colors=(255,0,0))
        detect = Detection2DArray()
        detect.header = image.header

        for Object in bboxes:
            detection = Detection2D()
            hypo = ObjectHypothesisWithPose()
            #Start x
            x1 = Object[0]
            #End x
            x2 = Object[2]
            #Start y
            y1 = Object[1]
            #end y
            y2 = Object[3]

            #Size x
            Sx = x2-x1
            #Size y
            Sy = y2-y1
            #Center x
            Cx = x1+Sx/2
            #Center y
            Cy = y1+Sy/2

            detection.bbox.center.x = Cx
            detection.bbox.center.y = Cy
            detection.bbox.size_x   = Sx
            detection.bbox.size_y   = Sy

            hypo.id = int(Object[5])
            hypo.score = Object[4]
            rospy.loginfo("Object %s found at (%d, %d)->(%d, %d)", self.class_name_list[hypo.id], x1, y1, x2, y2)

            detection.results = [hypo,]
            detection.is_tracking = False
            detect.detections.append(detection)
        self.boxes_pub.publish(detect)
        self.processing_image = False


def main(args):
    try:
        yolo = object_detector()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
        
if __name__ =='__main__':
	main(sys.argv)
