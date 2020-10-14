# IPs
- Klein
```
10.122.12.69
```
- Jakob
```
10.122.12.25
```

- ubuntu and password
```
10.122.12.159
raspberry
```
- tank and password
```
10.122.12.106
thomas
```
# Access to "tank"
```
ssh tank@10.122.12.106
```
Pass: thomas
```
export ROS_MASTER_URI=http://10.122.12.106:11311
export ROS_IP=10.122.12.106
```
- Start Zed2 
```
cd tank_ws
source devel/setup.bash
roslaunch zed_wrapper zed2.launch
```
# Record ROSBAG with multiple nodes
- Open terminal and ssh to tank
```
cd tank_ws/bagfiles
rosbag record -O name node1 node2 node3
```

# Yolo

## To start Vision.py from webcam
- First open a terminal
```
source /opt/ros/noetic/setup.bash
roslaunch usb_cam usb_cam-test.launch
```
- Open another terminal
```
cd yolo_ws
source devel/setup.bash
rosrun visionv2 Vision.py
```
## To start Vision.py from zed2
- First open a terminal and follow **Access to "tank"**
- Open another terminal
```
cd yolo_ws
source devel/setup.bash
export ROS_MASTER_URI=http://10.122.12.106:11311
export ROS_IP=12.122.12.??
rosrun visionv2 Vision.py
```
