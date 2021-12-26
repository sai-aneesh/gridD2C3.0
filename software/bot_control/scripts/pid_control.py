#! /usr/bin/env python2.7

import rospy
from tf.transformations import euler_from_quaternion
from geometry_msgs.msg import Pose, PoseArray, Point,PointStamped
from std_msgs.msg import Bool, UInt8
from math import sqrt, pi, atan, ceil,sin,cos
import numpy as np

class PID:
    def __init__(self):
        self.n_agents=4
        self.control_rate=rospy.Rate(10)

        # defining tunable params        
        self.kp_lin_x= 1
        self.kd_lin_x= 0
        self.ki_lin_x= 0

        self.kp_soft_lin_x= 1
        self.kd_soft_lin_x= 0
        self.ki_soft_lin_x= 0

        self.kp_lin_y= 1
        self.kd_lin_y= 0
        self.ki_lin_y= 0

        self.kp_soft_lin_y= 1
        self.kd_soft_lin_y= 0
        self.ki_soft_lin_y= 0

        self.kp_angle= 1
        self.kd_angle= 0
        self.ki_angle= 0

        self.kp_soft_angle= 1
        self.kd_soft_angle= 0
        self.ki_soft_angle= 0

        self.max_vel_lin=30.0/60.0
        self.max_vel_ang=1.1

        self.intergral_windup_yaw=20
        self.intergral_windup_lin_x=15
        self.intergral_windup_lin_y=15

        self.lin_x_threshold = 5
        self.lin_x_smalldiff = 10

        self.lin_y_threshold = 5
        self.lin_y_smalldiff = 10

        self.angle_threshold = 0.1
        self.angle_smalldiff = 0.3

        self.halt_time=20  #1 unit here is one time step which is 1/frequncy (control rate)
        # error varibales
        self.lastError_dist_x = np.zeros(self.n_agents)
        self.lastError_dist_y = np.zeros(self.n_agents)
        self.lastError_angle = np.zeros(self.n_agents)

        self.sumError_dist_x = np.zeros(self.n_agents)
        self.sumError_dist_y = np.zeros(self.n_agents)
        self.sumError_angle = np.zeros(self.n_agents)

        #other valribales from here     
        self.current_pose=np.zeros([self.n_agents,3]) #[bot_num][0 for x | 1 for y | 2 for yaw]
        self.goal_pose=np.zeros([self.n_agents,3])
        self.v_x_output=np.zeros(self.n_agents)   #vx and vy are in global coordinate system
        self.v_y_output=np.zeros(self.n_agents)
        self.w_output=np.zeros(self.n_agents)
        self.initialize_current_pose()
        self.halt_count=np.zeros(self.n_agents)
        self.need_new_plan = np.zeros(self.n_agents) +1 #in PID sense of a new plan is a next waypoint

        # bot specs (see daig in documentation)
        self.l1=0.07
        self.l2=0.07
        self.l3=0.07

        # publishers
        self.control_input_pub = rospy.Publisher('/cmd_vel', PoseArray, queue_size=10)
        self.cmd_vel_msg=PoseArray() # here we use only poistion of Poses msg. x will have vx, y will be vy and z will be omega in position object 
        self.wheel_speed_pub=rospy.Publisher('/wheel_speed',PoseArray, queue_size=10)
        self.wheel_vel_msg=PoseArray() # here we use only poistion of Poses msg. x will have w1, y will be w1 and z will be w3 in position object
        self.initialize_cmd_vel_msg()        
        self.flag_pid_pub = rospy.Publisher('/flag_id',UInt8,queue_size=10)

        # subscribers
        self.current_state_sub=rospy.Subscriber('/poses', PoseArray,self.current_state_callback,queue_size=10)
        self.goal_pose_sub=rospy.Subscriber('/goal_point', PointStamped,self.goal_pose_callback,queue_size=10)

    def initialize_current_pose(self):
        for i in range(self.n_agents):
            if(i<int(ceil(self.n_agents/2.0))):
                self.current_pose[i][0]=(4-i)*6+3
                
                if(i==0):
                    self.current_pose[i][1]=3
                    self.current_pose[i][2]=pi/2
                else :
                    self.current_pose[i][1]=9
                    self.current_pose[i][2]=0
            else :
                self.current_pose[i][0]=(9 + i - ceil(self.n_agents/2.0))*6 + 3
                
                if(i==ceil(self.n_agents/2.0)):
                    self.current_pose[i][1]=3
                    self.current_pose[i][2]=pi/2
                else :
                    self.current_pose[i][1]=9
                    self.current_pose[i][2]=pi

        for i in range(self.n_agents):
            if(i<int(ceil(self.n_agents/2.0))):
                self.goal_pose[i][0]=(4-i)*6+3
                
                if(i==0):
                    self.goal_pose[i][1]=3
                    self.goal_pose[i][2]=pi/2
                else :
                    self.goal_pose[i][1]=9
                    self.goal_pose[i][2]=0
            else :
                self.goal_pose[i][0]=(9 + i - ceil(self.n_agents/2.0))*6 + 3
                
                if(i==ceil(self.n_agents/2.0)):
                    self.goal_pose[i][1]=3
                    self.goal_pose[i][2]=pi/2
                else :
                    self.goal_pose[i][1]=9
                    self.goal_pose[i][2]=pi

    def initialize_cmd_vel_msg(self):
        temp_poses=[]
        temp_poses2=[]
        for i in range(self.n_agents):
            temp_poses.append(Pose())
            temp_poses2.append(Pose())
        self.cmd_vel_msg.poses=temp_poses
        self.wheel_vel_msg.poses=temp_poses2

    def current_state_callback(self,msg):
        for i in range(self.n_agents):
            self.current_pose[i][0]=msg.poses[i].position.x
            self.current_pose[i][1]=msg.poses[i].position.y
            self.current_pose[i][2]=msg.poses[i].position.z

    def goal_pose_callback(self,msg):
        self.goal_pose[msg.header.seq][0]=msg.point.x
        self.goal_pose[msg.header.seq][1]=msg.point.y
        if (msg.point.z != 100):
            self.goal_pose[msg.header.seq][2]=msg.point.z
        self.need_new_plan[msg.header.seq]=0
        # print(self.goal_pose)

    def twist_msg(self):
        for i in range(self.n_agents):            
            if abs(self.v_x_output[i])>self.max_vel_lin :
                self.cmd_vel_msg.poses[i].position.x = self.max_vel_lin*abs(self.v_x_output[i])/self.v_x_output[i]
                self.v_x_output[i]=self.max_vel_lin*abs(self.v_x_output[i])/self.v_x_output[i]    
            else :
               self.cmd_vel_msg.poses[i].position.x = self.v_x_output[i]

            if abs(self.v_y_output[i])>self.max_vel_lin :
                self.cmd_vel_msg.poses[i].position.y = self.max_vel_lin*abs(self.v_y_output[i])/self.v_y_output[i]    
                self.v_y_output[i] = self.max_vel_lin*abs(self.v_y_output[i])/self.v_y_output[i]
            else :
               self.cmd_vel_msg.poses[i].position.y = self.v_y_output[i]

            if(abs(self.w_output[i])>self.max_vel_ang):
                self.cmd_vel_msg.poses[i].position.z = self.max_vel_ang*abs(self.w_output[i])/self.w_output[i]
                self.w_output[i] = self.max_vel_ang*abs(self.w_output[i])/self.w_output[i]
            else :
                self.cmd_vel_msg.poses[i].position.z = self.w_output[i]  

        # computing the wheel speeds
        self.inverse_tranform()

        self.control_input_pub.publish(self.cmd_vel_msg)
        self.wheel_speed_pub.publish(self.wheel_vel_msg)

    def inverse_tranform(self):
        for i in range(self.n_agents):
            a=self.current_pose[i][2]
            inverse_kinematics_transform=np.array([[sin(a),-cos(a),-self.l1],[cos(pi/4+a),sin(pi/4+a),-self.l2],[-cos(pi/4-a),sin(pi/4-a),-self.l3]])
            req_vel=np.array([[self.v_x_output[i]],[self.v_y_output[i]],[self.w_output[i]]])
            wheel_speed=np.matmul(inverse_kinematics_transform,req_vel)
            # print(wheel_speed)
            self.wheel_vel_msg.poses[i].position.x=wheel_speed[0][0]
            self.wheel_vel_msg.poses[i].position.y=wheel_speed[1][0]
            self.wheel_vel_msg.poses[i].position.z=wheel_speed[2][0]

    def resetValues(self,i):
        self.lastError_dist_x[i] = 0
        self.lastError_dist_y[i] = 0
        self.lastError_angle[i] = 0
        
        self.sumError_dist_x[i] = 0
        self.sumError_dist_y[i] = 0
        self.sumError_angle[i] = 0        

    def correct_diff_yaw(self, diff_yaw):
        if diff_yaw < -1*pi:
            return self.correct_diff_yaw(diff_yaw+2*pi)
        if diff_yaw > pi:
            return self.correct_diff_yaw(diff_yaw-2*pi)
        return diff_yaw

    def pid(self):
        while not rospy.is_shutdown():
            for i in range(self.n_agents):
                if(self.need_new_plan[i] == 0): 
                    diff_yaw=self.correct_diff_yaw(self.goal_pose[i][2]-self.current_pose[i][2])
                    distance_x= self.goal_pose[i][0] - self.current_pose[i][0]
                    distance_y= self.goal_pose[i][1] - self.current_pose[i][1]
                    #PID along x
                    if (abs(distance_x) > self.lin_x_smalldiff):
                        self.v_x_output[i] = self.kp_lin_x*(distance_x) + self.kd_lin_x*(distance_x-self.lastError_dist_x[i])+self.ki_lin_x*self.sumError_dist_x[i]
                        self.lastError_dist_x[i]= distance_x
                        if(abs(self.sumError_dist_x[i] + distance_x)<self.intergral_windup_lin_x):
                            self.sumError_dist_x[i] = self.sumError_dist_x[i] + distance_x

                    elif (abs(distance_x) <= self.lin_x_smalldiff and abs(distance_x) > self.lin_x_threshold):
                        self.v_x_output[i] = self.kp_soft_lin_x*(distance_x) + self.kd_soft_lin_x*(distance_x-self.lastError_dist_x[i])+self.ki_soft_lin_x*self.sumError_dist_x[i]
                        self.lastError_dist_x[i]= distance_x
                        if(abs(self.sumError_dist_x[i] + distance_x)<self.intergral_windup_lin_x):
                            self.sumError_dist_x[i] = self.sumError_dist_x[i] + distance_x

                    else:
                        self.v_x_output[i]=0
                    #PID along y
                    if (abs(distance_y) > self.lin_y_smalldiff):
                        self.v_y_output[i] = self.kp_lin_y*(distance_y) + self.kd_lin_y*(distance_y-self.lastError_dist_y[i])+self.ki_lin_y*self.sumError_dist_y[i]
                        self.lastError_dist_y[i]= distance_y
                        if(abs(self.sumError_dist_y[i] + distance_y)<self.intergral_windup_lin_y):
                            self.sumError_dist_y[i] = self.sumError_dist_y[i] + distance_y

                    elif (abs(distance_y) <= self.lin_y_smalldiff and abs(distance_y) > self.lin_y_threshold):
                        self.v_y_output[i] = self.kp_soft_lin_y*(distance_y) + self.kd_soft_lin_y*(distance_y-self.lastError_dist_y[i])+self.ki_soft_lin_y*self.sumError_dist_y[i]
                        self.lastError_dist_y[i]= distance_y
                        if(abs(self.sumError_dist_y[i] + distance_y)<self.intergral_windup_lin_y):
                            self.sumError_dist_y[i] = self.sumError_dist_y[i] + distance_y

                    else:
                        self.v_y_output[i]=0

                    #PID angular
                    if (abs(diff_yaw) > self.angle_smalldiff):
                        self.w_output= self.kp_angle*(diff_yaw) + self.kd_angle*(diff_yaw-self.lastError_angle[i]) + self.ki_angle*(self.sumError_angle[i])
                        self.lastError_angle[i] = diff_yaw
                        if(abs(self.sumError_angle[i]+diff_yaw)<self.intergral_windup_yaw):
                            self.sumError_angle[i]=self.sumError_angle[i]+diff_yaw
                    elif (abs(diff_yaw) <= self.angle_smalldiff and abs(diff_yaw)>self.angle_threshold):
                        self.w_output= self.kp_angle_soft*(diff_yaw) + self.kd_angle_soft*(diff_yaw-self.lastError_angle[i]) + self.ki_angle_soft*(self.sumError_angle[i])
                        self.lastError_angle[i] = diff_yaw
                        if(abs(self.sumError_angle[i]+diff_yaw)<self.intergral_windup_yaw):
                            self.sumError_angle[i]=self.sumError_angle[i]+diff_yaw
                    else:
                        self.w_output=0

                    # might have to tweak in case of overshoot or very high time
                    if(abs(diff_yaw) <= self.angle_threshold and abs(distance_y) < self.lin_y_threshold and abs(distance_x) < self.lin_x_threshold):
                        self.need_new_plan[i]=1
                        self.resetValues(i)


                    # for halt we appned -100,-100 to goal_pose hence the below thing for the same
                    if (self.goal_pose[i][0]==-100 and self.goal_pose[i][0]==-100):
                        if(self.halt_count[i] < self.halt_time):
                            self.halt_count[i]=self.halt_count[i]+1
                        else :
                            self.need_new_plan[i]=1
                            self.halt_count[i]=0
                        self.v_x_output[i]=0.0
                        self.v_y_output[i]=0.0
                        self.w_output[i]=0.0
                if(self.need_new_plan[i] == 1):
                    pub_msgs=UInt8()
                    pub_msgs.data=i
                    self.flag_pid_pub.publish(pub_msgs)
                    self.need_new_plan[i]=2
                                
            self.twist_msg()
            # print('hey there')
            self.control_rate.sleep() 

    
if __name__ == '__main__':

    rospy.init_node('controller_node')
    rospy.loginfo("controller_node for bot1 created")
    pid_controller=PID()
    pid_controller.pid()
    # spin() simply keeps python from exiting until this node is stopped
    # rospy.spin()