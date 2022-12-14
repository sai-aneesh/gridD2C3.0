function pose_callback(~,msg)
global n_agents;
global current_pose;
global img;
global bot_marker;

 for i=1:n_agents
 	current_pose(i,1)=msg.Poses(i).Position.X*9;
 	current_pose(i,2)=msg.Poses(i).Position.Y*9;
 	current_pose(i,3)=msg.Poses(i).Position.Z*180/pi;
 end
 img1=img;
  %image update logic
 for i=1:n_agents
     x=floor(current_pose(i,1) + 0*0.1);
     y=floor(current_pose(i,2) + 0*0.1);
     yaw=current_pose(i,3) + 0*0.1;
     aruco_rot=imrotate(reshape(bot_marker(i,:,:),[44,44]),yaw);
     aruco_rot=aruco_rot(1:44,1:44);
     x=(x-ceil(size(aruco_rot,1)/2) + 1):(x+floor(size(aruco_rot,1)/2));
     y=(y-ceil(size(aruco_rot,1)/2) + 1):(y+floor(size(aruco_rot,1)/2));
     img1(x,y)=aruco_rot;
 end
 imshow(img1)
end
