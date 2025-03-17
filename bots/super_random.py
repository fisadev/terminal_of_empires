import random


class BotLogic:
    """
    Bot logic for the Rando bot.
    """
    def turn(self, map_size, my_resources, world):
        """
        Rando bot just tries random actions. Maye we try to do stuff we can't (like placing a fort
        in neutral terrain). Who knows! We don't care :p
        """
        action_type = random.choice(["conquer", "harvest", "fort", "farm", "castle"])
        if action_type == "harvest":
            action_position = None
        else:
            action_position = (
                random.randint(0, map_size[0] - 1),
                random.randint(0, map_size[1] - 1),
            )
        return action_type, action_position
