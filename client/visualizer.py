import curses
from curses.textpad import rectangle
import time
from controller import Controller
import threading
import asyncio
import sys
import traceback

AUTORUN_DELAY = 0.5


# Style constants
BAR_CELL_WIDTH = 2
BOT_SPACING = 5

# Color pair constants
HEALTH_FILLED = 1
HEALTH_EMPTY = 2
LOG_TEXT = 3

ASCII_BOT_SIZE = (6, 3)
ASCII_BOTS = ["""
 [@@]
/|__|\\
 d  b
    """, """
 [oo]
/|##|\\
 d  b
    """, """
 [**]
/|--|\\
 d  b
    """]


class Visualizer:
    def __init__(self):
        self.scr = None  # Screen
        self.loop = asyncio.new_event_loop()
        self.commands = []
        self.command_idx = 0

        threading.Thread(target=self.loop.run_forever).start()
        threading.Thread(target=self._listen_for_input).start()

    def cleanup(self):
        self.loop.call_soon_threadsafe(self.loop.stop)

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
        self._submit_command(lambda: self.scr.clear())

    def render_game_temp(self, state):
        self._submit_command(lambda: self.render_game(state))

    def render_game(self, state):
        """
        Renders a current game state

        Args:
            state: Game state as defined in server/server.py
        """
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
        self._draw_log(
            (5, 25), 
            str(state),
            curses.color_pair(LOG_TEXT) | curses.A_BOLD
        )

        self.scr.refresh()

    def _handle_input(self, input):
        if self.command_idx > 0 and input == 97:  # a
            self.command_idx -= 1
        if self.command_idx < len(self.commands) - 1 and input == 100:  # d
            self.command_idx += 1

        if self.commands:
            self.commands[self.command_idx]()
            print(self.command_idx)

    def _listen_for_input(self):
        while True:
            if not self.scr:
                continue
            input = self.scr.getch()
            if input != -1:
                self._run_task(lambda i: self._handle_input(i), False, input)

    def _submit_command(self, cmd):
        def add():
            self.commands.append(cmd)
            print("added " + len(self.commands))
        self._run_task(add)

    def _run_task(self, task, delay=False, *args):
        async def run_coro():
            if delay:
                await asyncio.sleep(AUTORUN_DELAY)
            task(*args)
        asyncio.run_coroutine_threadsafe(run_coro(), self.loop)

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
        try:
            for i, line in enumerate(text.split('\n')):
                if line:
                    self.scr.addstr(pos[1] + i, pos[0], line, args)
        except curses.error:
            pass

    def _draw_team(self, pos, bots):  #, actions, opp_actions):
        start_x = pos[0]
        for i, bot in enumerate(bots):
            # Health bar
            end_x = self._draw_bar(
                (start_x, pos[1]), bot[0], Controller.INITIAL_HEALTH, HEALTH_FILLED, HEALTH_EMPTY) + BOT_SPACING

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
            self._draw_multiline_text((middle - ASCII_BOT_SIZE[0] + 1, pos[1] - ASCII_BOT_SIZE[1] - 2),
                                      ASCII_BOTS[i % len(ASCII_BOTS)])

            start_x = end_x

    def _draw_log(self, pos, text, args=0):
        # get console width curses
        width = min(curses.COLS - 2 * pos[0] - 2, 100)
        textLines = []
        for i in range(0, len(text), width):
            textLines.append(text[i:i + width])
        height = max(3, len(textLines))
        # draw a box around the log
        try:
            rectangle(self.scr, pos[1] - 1, pos[0] - 1, pos[1] + 1 + height, pos[0] + width + 1)
        except curses.error:
            pass
        # draw the text in the rectangle
        for i, line in enumerate(textLines):
            try:
                self.scr.addstr(pos[1] + i, pos[0], line, args)
            except curses.error:
                pass

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
        empty = max - cur
        try:
            self.scr.addstr(pos[1], pos[0], " " * filled, curses.color_pair(color_filled))
            self.scr.addstr(pos[1], pos[0] + filled, " " * empty * BAR_CELL_WIDTH, curses.color_pair(color_empty))
        except curses.error:
            pass
        return pos[0] + filled + empty * BAR_CELL_WIDTH

    def _init_colors(self):
        """
        Initialize predefined terminal colors
        """
        curses.use_default_colors()
        curses.init_pair(HEALTH_FILLED, curses.COLOR_WHITE, curses.COLOR_RED)
        curses.init_pair(HEALTH_EMPTY, curses.COLOR_WHITE, curses.COLOR_WHITE)
        curses.init_pair(LOG_TEXT, curses.COLOR_RED, -1)

    def _curses_main(self, scr, callback):
        """
        Main init function passed to curses wrapper
        """
        curses.curs_set(0)
        self.scr = scr
        self.scr.nodelay(True)
        self._init_colors()
        self.clear()

        callback()


if __name__ == "__main__":
    vis = Visualizer()

    def execute():
        while True:
            state = {"bots": [[2], [3], [4]], "op_bots": [[5], [0], [2]]}
            vis.render_game(state)
            time.sleep(0.5)
            pass

    try:
        vis.run(execute)
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print("\nError launching visualizer!!!\n")
        print(traceback.format_exc())
