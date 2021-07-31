import rospy
from time import sleep
from tf.transformations import euler_from_quaternion, quaternion_from_euler , euler_matrix
from geometry_msgs.msg import Point,Twist
from geometry_msgs.msg import PoseStamped
from math import atan2, cos, sin, ceil
from std_msgs.msg import Int16, Float64
from arm_rrt.msg import config_point
import numpy as np
import random
import time
from sensor_msgs.msg import JointState , LaserScan
from tf2_msgs.msg import TFMessage
import matplotlib.pyplot as plt

class position
    def __init__(self,X,Y):
        self.x=X
        self.y=Y
class bot: 
    def __init__(self,point,parent):
        self.position=np.array(point,dtype=float)
        self.parent_node=parent

class path_planner:
    def __init__(self):
        self.rate_move=rospy.Rate(0.5)
        self.point_to_reach=[]
        self.pub_joint2=rospy.Publisher('/me604/joint2_position_controller/command',Float64,queue_size=10)
        self.pub_joint1=rospy.Publisher('/me604/joint1_position_controller/command',Float64,queue_size=10)
        self.sub_laser_data=rospy.Subscriber("/me604/laser/scan1",LaserScan, self.Laserscan_callback, queue_size=1)

    def plan(self):
        # introduced a delay to allow varaibles to get assigned using call backs
        time.sleep(5)
        for i in range(30):
            self.points_sampled_x.append(lower_angle_limit_config +i/30.0*upper_angle_limit_config)
            self.points_sampled_y.append(lower_angle_limit_config +i/30.0*upper_angle_limit_config)
        for i in range(30):
            for j in range(30):
                if(self.collision_free([self.points_sampled_x[i],self.points_sampled_y[j]])):
                    plt.scatter(self.points_sampled_x[i],self.points_sampled_y[j], color= "green", s=10)
                else :
                    plt.scatter(self.points_sampled_x[i],self.points_sampled_y[j], color= "red", s=10)
        plt.show()


if __name__ == '__main__':
    rospy.init_node('rrt_node')
    rospy.loginfo("rrt_node created")
    try:
        while (rospy.get_time()==0):
          pass
        rospy.loginfo("starting to acccept end goal to generate path")
        path_planner_obj=path_planner()
        path_planner_obj.plan()

    except rospy.ROSInterruptException:
        pass