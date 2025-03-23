import requests
from serialization_helpers import serialize_world, deserialize_action


class RemoteBotLogic:
    """
    A proxy for a bot running in another machine.
    When a turn is requested, it calls the bot server in the specified ip for the action.
    """
    def __init__(self, bot_server):
        self.bot_server = bot_server

    def turn(self, map_size, my_resources, world):
        """
        Call the bot server to get the action.
        """
        response = requests.post(f'{self.bot_server}/turn', json={
            'map_size': map_size,
            'resources': my_resources,
            'world': serialize_world(world),
        })
        return deserialize_action(response.json()["action"])
