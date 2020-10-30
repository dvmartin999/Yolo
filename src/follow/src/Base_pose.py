#!/usr/bin/env python3

import rospy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
from tf import TransformBroadcaster
import math

class Base_pose():
    def __init__(self):
        rospy.init_node('Base_position', anonymous=True)
        self.base_pub = rospy.Publisher('/odometry/filtered_map', Odometry, queue_size=1)

        self.br = TransformBroadcaster()
        trans = (0,0,0)
        rot   = (0,0,0,1)
        stamp = rospy.Time.now()
        self.br.sendTransform(trans, rot, stamp,"base_link","map")

        self.Current_goal = []
        self.Movedir = [0,0,0]
        self.VPose = Odometry()
        self.VPose.header.stamp = rospy.Time.now()
        self.VPose.header.frame_id = "map"
        self.VPose.pose.pose.position.x    = float(0)
        self.VPose.pose.pose.position.y    = float(0)
        self.VPose.pose.pose.position.z    = float(0)
        self.VPose.pose.pose.orientation.x = float(0)
        self.VPose.pose.pose.orientation.y = float(0)
        self.VPose.pose.pose.orientation.z = float(0)
        self.VPose.pose.pose.orientation.w = float(1)

        rate = rospy.Rate(20) # 10hz

        while not rospy.is_shutdown():
            rospy.Subscriber("/move_base_simple/goal", PoseStamped, self.Find_goal, queue_size=1)
            if self.Current_goal == []:
                self.Movedir = [0,0,0]
            else:
                Movex = self.Current_goal.pose.position.x-self.VPose.pose.pose.position.x
                Movey = self.Current_goal.pose.position.y-self.VPose.pose.pose.position.y
                Movez = self.Current_goal.pose.position.z-self.VPose.pose.pose.position.z
                Movemag = math.sqrt((Movex)**2+(Movey)**2)
                self.Movedir = [Movex, Movey, 0]
                print(self.Movedir)
                #self.Movedir = [1,0,0]
            self.VPose.header.stamp = rospy.Time.now()
            self.VPose.pose.pose.position.x += self.Movedir[0]
            self.VPose.pose.pose.position.y += self.Movedir[1]
            self.VPose.pose.pose.position.z += self.Movedir[2]
            self.br = TransformBroadcaster()
            trans = (self.VPose.pose.pose.position.x, self.VPose.pose.pose.position.y, self.VPose.pose.pose.position.z)
            rot   = (self.VPose.pose.pose.orientation.x, self.VPose.pose.pose.orientation.y, self.VPose.pose.pose.orientation.z, self.VPose.pose.pose.orientation.w)
            self.br.sendTransform(trans, rot, self.VPose.header.stamp,"base_link","map") #Pose.header.stamp,"base","map")
            self.base_pub.publish(self.VPose)
            rate.sleep()

    def Find_goal(self,Pose):
        if Pose == []:
            pass
            #self.Current_goal = []
        else:
            self.Current_goal = Pose

if __name__ == '__main__':
    try:
        Base_pose()
    except rospy.ROSInterruptException:
        pass