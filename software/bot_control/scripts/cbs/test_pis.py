#!/usr/bin/env python

import rospy
import time
import numpy as np
from bot_control.msg import Poses
from bot_control.msg import StartGoal
from geometry_msgs.msg import Point
# from drdo_exploration.msg import teleopData
class pose_publisher:
    def __init__(self):
        self.n_agents=1
        self.current_pose=np.zeros([self.n_agents,3])+1
        self.poses=Poses()
        self.initialize_pose()
        self.pub_poses=rospy.Publisher('/poses',Poses,queue_size=1)
        self.current_pose=[[128.0,213.57,0]]
        self.poses.posei[0].x=self.current_pose[0][0]
        self.poses.posei[0].y=self.current_pose[0][1]
        self.poses.posei[0].z=self.current_pose[0][2]
        # print(self.data)
        while not rospy.is_shutdown(): 
            self.pub_poses.publish(self.poses)
            print("publihsed to estimate")
            time.sleep(2)

    def initialize_pose(self):
        temp_poses=[]
        for i in range(self.n_agents):
            temp_poses.append(Point())
        self.poses.posei=temp_poses

if __name__ == '__main__':
    rospy.init_node('pose_estimator')
    rospy.loginfo('reading from camera')
    pose_pub_obj=pose_publisher()
    #to keep the function running in loop
    rospy.spin()



#         self.pub_test=rospy.Publisher('/goal_point',Point,queue_size=1)
#         self.data=Point()
#         self.data.x=26.0
#         self.data.y=450.0
#         self.data.z=0
#         # self.data.start_y=[6,7,5,0]
#         # self.data.goal_x=[2,0,5,0]
#         # self.data.goal_y=[4,2,2,7]
#         # self.data.bot_num=[0,1,2,3]
#         print(self.data)
#         while not rospy.is_shutdown(): 
#             # time.sleep(10) 
#             self.pub_test.publish(self.data)


# if __name__ == '__main__':
#     rospy.init_node('test_node')
#     # rospy.loginfo('reading from camera')
#     pose_pub_obj=pose_publisher()
#     #to keep the function running in loop
#     rospy.spin()