from lerobot.datasets.utils import hw_to_dataset_features

def features_from(robot):
    action_features = hw_to_dataset_features(robot.action_features, "action")
    obs_features = hw_to_dataset_features(robot.observation_features, "observation")
    return {**action_features, **obs_features}