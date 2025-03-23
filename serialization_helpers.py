from game import Position, Terrain


def deserialize_world(raw_world):
    """
    Deserialize jsonified world data.
    """
    return {
        Position(*raw_position): Terrain(*raw_terrain)
        for raw_position, raw_terrain in raw_world.items()
    }


def deserialize_action(raw_action):
    """
    Deserialize jsonified action data.
    """
    action_type, action_param = raw_action

    if action_param is not None:
        action_param = Position(*action_param)

    return action_type, action_param


def deserialize_map_size(raw_map_size):
    """
    Deserialize jsonified map size data.
    """
    return Position(*raw_map_size)
