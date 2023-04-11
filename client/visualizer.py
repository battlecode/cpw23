import curses
from curses.textpad import rectangle
import time


# Style constants
HEALTH_CELL_WIDTH = 2


# Color pair constants
HEALTH_FILLED = 1
HEALTH_EMPTY = 2


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
        rectangle(self.scr, 5, 5, 10, 10)
        for i in range(10):
            self._draw_health((5, 5), (3, 5))
            time.sleep(0.5)
            self.scr.refresh()

    def _draw_health(self, pos, health):
        """
        Render a health bar

        Args:
            screen: curses screen context
            pos (tuple(int, int)): x and y pos of left side of rendered bar
            health (tuple(int, int)): cur, max health
        """
        filled = health[0] * HEALTH_CELL_WIDTH
        self.scr.addstr(
            pos[1], pos[0],
            " " * filled,
            curses.color_pair(HEALTH_FILLED)
        )

        empty = health[1] - health[0]
        self.scr.addstr(
            pos[1], pos[0] + filled,
            " " * empty * HEALTH_CELL_WIDTH,
            curses.color_pair(HEALTH_EMPTY)
        )

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
            vis.render_game(None)
            pass

    vis.run(execute)
