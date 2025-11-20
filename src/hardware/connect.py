from lerobot.robots.so101_follower import SO101FollowerConfig, SO101Follower
from lerobot.teleoperators.so101_leader import SO101LeaderConfig, SO101Leader
from . import _features
from ..config.ports_and_cameras import (
    FOLLOWER_PORT,
    LEADER_PORT,
    camera_config,
    ROBOT_ID,
    LEADER_ID,
)


def make_robot():
    robot_config = SO101FollowerConfig(
        port=FOLLOWER_PORT,
        id=ROBOT_ID,
        cameras=camera_config,
    )
    return SO101Follower(robot_config)


def make_teleop():
    teleop_config = SO101LeaderConfig(
        port=LEADER_PORT,
        id=LEADER_ID,
    )
    return SO101Leader(teleop_config)


def connect_both():
    robot = make_robot()
    teleop_device = make_teleop()
    robot.connect()
    teleop_device.connect()
    return robot, teleop_device


def disconnect_both(robot, teleop_device):
    teleop_device.disconnect()
    robot.disconnect()


def dataset_features_for(robot):
    return _features.features_from(robot)