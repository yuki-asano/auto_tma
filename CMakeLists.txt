cmake_minimum_required(VERSION 2.8.0)
project(auto_tma)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  actionlib
  actionlib_msgs
  message_generation
  #
  mitsutoyo_instrument  # MitsutoyoMicrometer.msg
)

catkin_python_setup()

#add_action_files(
#  DIRECTORY action
#)

generate_messages(
  DEPENDENCIES
  std_msgs
  actionlib_msgs
)

catkin_package(
  CATKIN_DEPENDS rospy std_msgs actionlib actionlib_msgs message_runtime
  #
  netzsch_instrument
  mitsutoyo_instrument
  )

include_directories(
  ${catkin_INCLUDE_DIRS}
)
