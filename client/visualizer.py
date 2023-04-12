import curses
from curses.textpad import rectangle
import time
from controller import Controller


# Style constants
BAR_CELL_WIDTH = 2
BOT_SPACING = 5


# Color pair constants
HEALTH_FILLED = 1
HEALTH_EMPTY = 2


ASCII_BOT_SIZE = (6, 3)
ASCII_BOTS = [
    """
 [@@]
/|__|\\
 d  b
    """,
    """
 [oo]
/|##|\\
 d  b
    """,
    """
 [**]
/|--|\\
 d  b
    """
]


class Visualizer:
    def __init__(self):
        self.scr = None  # Screen

    def run(self, callback):
        """
        Starts the terminal visualizer and encapsulates functionality in the
        specified callback.

        The visualizer context only lives as long as the callback function.

        Args: callback (callable): The function to call after initialization
        """
        curses.wrapper(lambda scr: self._curses_main(scr, callback))

    def clear(self):
        """
        Clear the terminal screen
        """
        self.scr.clear()

    def render_game(self, state):
        """
        Renders a current game state

        Args:
            state: Game state as defined in server/server.py
        """
        # rectangle(self.scr, 5, 5, 10, 10)
        self._draw_team(
            (5, 5),
            state["bots"],
            #state["actions"],
            #state["op_actions"]
        )
        self._draw_team(
            (5, 20),
            state["op_bots"],
            #state["op_actions"],
            #state["actions"]
        )

        self.scr.refresh()

    def _get_shield_health(self, actions, opp_actions, bot_idx):
        # Ensure bot actually shielded
        if actions[bot_idx]["type"] != "shield":
            return None

        # If so, determine health of shield
        health = Controller.SHIELD_HEALTH
        for action in opp_actions:
            if action["type"] == "launch" and action["target"] == bot_idx:
                health -= action["strength"]

        return max(health, 0)

    def _draw_multiline_text(self, pos, text, args=0):
        for i, line in enumerate(text.split('\n')):
            if line:
                self.scr.addstr(pos[1] + i, pos[0], line, args)

    def _draw_team(self, pos, bots): #, actions, opp_actions):
        start_x = pos[0]
        for i, bot in enumerate(bots):
            # Health bar
            end_x = self._draw_bar(
                (start_x, pos[1]),
                bot[0], Controller.INITIAL_HEALTH,
                HEALTH_FILLED, HEALTH_EMPTY
            ) + BOT_SPACING

            # Shield bar
            """
            shield_health = self._get_shield_health(
                actions, opp_actions, i
            )
            if shield_health is not None:
                pass
            """

            # Render bot
            middle = start_x + (end_x - start_x) // 2
            self._draw_multiline_text(
                (
                    middle - ASCII_BOT_SIZE[0] + 1,
                    pos[1] - ASCII_BOT_SIZE[1] - 2
                ),
                ASCII_BOTS[i % len(ASCII_BOTS)]
            )

            start_x = end_x

    def _draw_bar(self, pos, cur, max, color_filled, color_empty):
        """
        Render a progress bar

        Args:
            screen: Curses screen context
            pos (tuple(int, int)): x and y pos of left side of rendered bar
            cur (int): Current value
            max (int): Maximum value
            color_filled (int): Color pair to use for the filled portion
            color_empty (int): Color pair to use for the empty portion

        Returns (int):
            x coordinate directly after the end of the bar
        """
        filled = cur * BAR_CELL_WIDTH
        self.scr.addstr(
            pos[1], pos[0],
            " " * filled,
            curses.color_pair(color_filled)
        )

        empty = max - cur
        self.scr.addstr(
            pos[1], pos[0] + filled,
            " " * empty * BAR_CELL_WIDTH,
            curses.color_pair(color_empty)
        )

        return pos[0] + filled + empty * BAR_CELL_WIDTH

    def _init_colors(self):
        """
        Initialize predefined terminal colors
        """
        curses.use_default_colors()
        curses.init_pair(HEALTH_FILLED, curses.COLOR_WHITE, curses.COLOR_RED)
        curses.init_pair(HEALTH_EMPTY, curses.COLOR_WHITE, curses.COLOR_WHITE)

    def _curses_main(self, scr, callback):
        """
        Main init function passed to curses wrapper
        """
        curses.curs_set(0)
        self.scr = scr
        self._init_colors()
        self.clear()

        callback()


if __name__ == "__main__":
    vis = Visualizer()

    def execute():
        while True:
            state = {
                "bots": [[2], [3], [4]],
                "op_bots": [[5], [0], [2]]
            }
            vis.render_game(state)
            time.sleep(0.5)
            pass

    vis.run(execute)
