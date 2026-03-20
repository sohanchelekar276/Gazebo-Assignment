import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python import get_package_share_directory
import xacro


def generate_launch_description():

    # Dynamically find the path to the rover_gazebosim package
    pkg_share = get_package_share_directory('rover_gazebosim')

    # Load robot description from URDF file
    robot_description = xacro.process_file(
        os.path.join(pkg_share, 'urdf/rover.urdf')
    ).toxml()

    # Load configuration for parameter bridge
    config_file = os.path.join(get_package_share_directory('rover_gazebosim'), 'config', 'parameter_bridge.yaml')

    return LaunchDescription([
        # Launch arguments for GUI and initial position
        DeclareLaunchArgument('gui', default_value='true', description='Enable/Disable GUI'),
        DeclareLaunchArgument('x', default_value='2', description='Initial x position of the rover'),
        DeclareLaunchArgument('y', default_value='2', description='Initial y position of the rover'),
        DeclareLaunchArgument('z', default_value='1', description='Initial z position of the rover'),

        # Set environment variables for resource paths
        SetEnvironmentVariable(
            name='IGN_GAZEBO_RESOURCE_PATH',
            value=os.path.dirname(get_package_share_directory('rover_gazebosim'))
        ),

        # Launch Ignition Gazebo with a specific world file
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(get_package_share_directory("ros_gz_sim"), "launch", "gz_sim.launch.py")
            ),
            launch_arguments={
                "gz_args": os.path.join(pkg_share, 'worlds', 'ign_rect_world.sdf')
            }.items(),
        ),

        # Robot State Publisher for publishing the robot's URDF to the parameter server
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            output='screen',
            parameters=[{"robot_description": robot_description}]
        ),

        # Joint State Publisher for publishing joint states
        Node(
            package='joint_state_publisher',
            executable='joint_state_publisher',
            name='joint_state_publisher',
            parameters=[{'use_gui': LaunchConfiguration('gui')}]
        ),

        # Spawn the rover in Ignition Gazebo
        Node(
            package="ros_gz_sim",
            executable="create",
            output="screen",
            name="rover_spawn",
            arguments=[
                "-string", robot_description,
                "-name", "rover",
                "-x", LaunchConfiguration("x"),
                "-y", LaunchConfiguration("y"),
                "-z", LaunchConfiguration("z"),
            ],
        ),

        # ROS-Gazebo Bridge for parameter communication
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            parameters=[{'config_file': config_file}]
        ),
    ])