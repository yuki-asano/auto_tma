#!/bin/bash

set -e

# set same environment with .bashrc
export ROS_WS=$HOME/auto_tma_ws

# ROS
source /opt/ros/noetic/setup.bash
source $ROS_WS/devel/setup.bash

# for nextage
export PYTHONPATH=$PYTHONPATH:/usr/local/lib/python3.8/site-packages  # for omniORBpy
export PYTHONPATH=$PYTHONPATH:$ROS_WS/src/robot_control/robots/nextage/nextage_nxa_interface/api/NxApiSdk/python/lib
export PYTHONPATH=$PYTHONPATH:$ROS_WS/src/robot_control/robots/nextage/nextage_nxa_interface/api/NxApiSdk/python/lib/NxApiLib/idl_NxApi


roslaunch auto_tma auto_tma.launch
