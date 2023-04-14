import curses
from curses.textpad import rectangle
import time
from controller import Controller
import threading
import asyncio
import traceback
from datetime import datetime

# Delay between automatic updates in seconds
AUTORUN_DELAY = 0.5

# Style constants
BAR_CELL_WIDTH = 2
BOT_SPACING = 7

# Color pair constants
HEALTH_FILLED = 1
HEALTH_EMPTY = 2
LOG_TEXT = 3
SHIELD_FILLED = 4
SHIELD_EMPTY = 5
NAME_TEXT = 6
AMMO_TEXT = 7
ERROR_TEXT = 8

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
        self.autorun = True
        self.last_autorun = datetime.now()

        threading.Thread(target=self.loop.run_forever).start()
        self._update()

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
        self._submit_command(lambda: self.scr.clear(), "clear")

    def render_game(self, state, tag):
        self._submit_command(lambda: self._render_game_internal(state), tag)

    def render_error(self, error):
        self._submit_command(lambda: self._render_error_internal(error), "error")

    def _render_game_internal(self, state):
        """
        Renders a current game state

        Args:
            state: Game state as defined in server/server.py
        """
        self.scr.clear()

        if(state["type"] == 'begin_game'):
            self._draw_log(
                (5, 15), 
                "NEW GAME",
                curses.A_BOLD
            )
        elif(state["type"] == 'game_update'):
            self._draw_team(
                (5, 10),
                state["bots"],
                state["actions"],
                state["op_actions"],
                state["name"]
            )
            self._draw_team(
                (5, 25),
                state["op_bots"],
                state["op_actions"],
                state["actions"],
                state["op_name"]
            )
            self._draw_log(
                (5, 30), 
                str(state),
                curses.color_pair(LOG_TEXT) | curses.A_BOLD
            )
            if state["exceptions"] != "":
                self._draw_log(
                    (5, 42),
                    state["exceptions"],
                    curses.color_pair(ERROR_TEXT) | curses.A_BOLD
                )
        elif(state["type"] == 'game_over'):
            self._draw_log(
                (5, 15), 
                "GAME OVER. WINNER = " + state["winner"]
                if state["winner"] is not None else "GAME OVER. TIE",
                curses.A_BOLD
            )
        self._draw_info((60, 0))
        self.scr.refresh()

    def _render_error_internal(self, message):
        self.scr.clear()
        self._draw_log(
            (5, 5), 
            message,
            curses.color_pair(ERROR_TEXT) | curses.A_BOLD
        )
        self.scr.refresh()

    def _seek(self, tag, amount, forwards):
        if amount == 0:
            return

        def check():
            nonlocal amount
            if self.commands[self.command_idx][0] == tag:
                amount -= 1
            if amount == 0:
                return True
            return False

        og_idx = self.command_idx
        if forwards:
            while self.command_idx < len(self.commands) - 1:
                self.command_idx += 1
                if check():
                    return
        else:
            while self.command_idx > 0:
                self.command_idx -= 1
                if check():
                    return

        # Reset if no tag was found
        self.command_idx = og_idx

    def _update(self):
        if self.scr:
            input = self.scr.getch()

            if self.command_idx > 0 and input == 97:  # a
                self.command_idx -= 1
            elif self.command_idx < len(self.commands) - 1 and input == 100:  # d
                self.command_idx += 1
            elif input == 32:  # space
                self.autorun = not self.autorun
            elif input == 115 and self.commands:  # s
                # Seek to start of game which means 1 start tag if we are in the middle
                # or zero if we are at the start
                self._seek(
                    "begin",
                    0 if self.commands[self.command_idx][0] == "begin" else 1,
                    False
                )
            elif input == 101 and self.commands:  # e
                # Seek to end of game which means 1 end tag if we are in the middle
                # or zero if we are at the end
                self._seek(
                    "end",
                    0 if self.commands[self.command_idx][0] == "end" else 1,
                    True
                )
            elif input == 110:  # n
                self._seek("begin", 1, True)
            elif input == 112 and self.commands:  # p
                # Seek back to previous game, which means passing over 2 begin tags
                # if we are in the middle of a game or 1 if we are exactly at the
                # start
                self._seek(
                    "begin",
                    1 if self.commands[self.command_idx][0] == "begin" else 2,
                    False
                )

            if (self.autorun and
                (datetime.now() - self.last_autorun).seconds >= AUTORUN_DELAY and
                self.command_idx < len(self.commands) - 1):
                self.command_idx += 1

            if self.commands:
                self.commands[self.command_idx][1]()
            else:
                self.scr.clear()
                self._draw_info((0, 0))
                self.scr.refresh()

        self._run_task(self._update)

    def _submit_command(self, cmd, tag):
        def add():
            self.commands.append((tag, cmd))
        self._run_task(add)

    def _run_task(self, task, delay=False, *args):
        async def run_coro():
            if delay:
                await asyncio.sleep(AUTORUN_DELAY)
            try:
                task(*args)
            except Exception as e:
                print("Error running task!")
                print(traceback.format_exc())
                
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

    def _draw_team(self, pos, bots, actions, opp_actions, name):
        start_x = pos[0]
        for i, (bot, action) in enumerate(zip(bots, actions)):
            is_alive = bot[0] > 0

            # Health bar
            end_x = self._draw_bar(
                (start_x, pos[1]),
                bot[0], Controller.INITIAL_HEALTH,
                HEALTH_FILLED, HEALTH_EMPTY
            )

            middle = start_x + (end_x - start_x) // 2
            bot_x = middle - ASCII_BOT_SIZE[0] // 2
            bot_y = pos[1] - ASCII_BOT_SIZE[1] - 2

            # Shield bar
            shield_health = self._get_shield_health(
                actions, opp_actions, i
            )
            if shield_health is not None:
                start = middle - (Controller.SHIELD_HEALTH * BAR_CELL_WIDTH) // 2
                self._draw_bar(
                    (start, pos[1] + 2),
                    shield_health, Controller.SHIELD_HEALTH,
                    SHIELD_FILLED, SHIELD_EMPTY
                )

            # Render bot
            if is_alive:
                self._draw_multiline_text((bot_x, bot_y), ASCII_BOTS[i % len(ASCII_BOTS)])

            # Bot actions
            if action["type"] == "load":
                action_text = f"\nLoading\n"
            elif action["type"] == "launch":
                action_text = f"Launching at\n{action['target']} w/ {action['strength']} ammo\n"
            elif action["type"] == "shield":
                action_text = "\nShielding\n"
            else:
                action_text = "\nNone\n"
            action_x = middle - max([len(text) for text in action_text.split('\n')]) // 2
            action_y = bot_y - 3
            if is_alive:
                self._draw_multiline_text((action_x, action_y), action_text)

            # Bot ammo
            ammo_text = f"Bot Ammo: {bot[1]}"
            ammo_x = middle - len(ammo_text)//2
            ammo_y = bot_y - 1
            if is_alive:
                self._draw_multiline_text(
                    (ammo_x, ammo_y),
                    ammo_text,
                    curses.color_pair(AMMO_TEXT)
                )

            start_x = end_x + BOT_SPACING

        # Username
        middle = pos[0] + (end_x - pos[0]) // 2
        cleaned = name.strip().replace("\n", "")
        name_x = middle - len(cleaned) // 2
        name_y = action_y - 2
        self._draw_multiline_text(
            (name_x, name_y),
            cleaned,
            curses.color_pair(NAME_TEXT) | curses.A_BOLD
        )

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

    def _draw_info(self, pos):
        info_text = f"""
    Autorun: {'on' if self.autorun else 'off'}
    Space - Toggle autorun
      A   - Previous turn
      D   - Next turn
      P   - Seek to previous game
      N   - Seek to next game
      S   - Seek to start of current game
      E   - Seek to end of current game
        """
        self._draw_multiline_text(pos, info_text)

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
        curses.init_pair(HEALTH_FILLED, -1, curses.COLOR_RED)
        curses.init_pair(HEALTH_EMPTY, -1, curses.COLOR_WHITE)
        curses.init_pair(LOG_TEXT, curses.COLOR_WHITE, -1)
        curses.init_pair(SHIELD_FILLED, -1, curses.COLOR_BLUE)
        curses.init_pair(SHIELD_EMPTY, -1, curses.COLOR_WHITE)
        curses.init_pair(NAME_TEXT, curses.COLOR_CYAN, -1)
        curses.init_pair(AMMO_TEXT, curses.COLOR_YELLOW, -1)
        curses.init_pair(ERROR_TEXT, curses.COLOR_RED, -1)

    def _curses_main(self, scr, callback):
        """
        Main init function passed to curses wrapper
        """
        curses.curs_set(0)
        self.scr = scr
        curses.halfdelay(4)
        self._init_colors()
        self.scr.clear()

        try:
            callback()
        except:
            pass

        self.cleanup()

if __name__ == "__main__":
    vis = Visualizer()

    def execute():
        while True:
            state = {
                "bots": [[2, 1], [3, 2], [4, 3]],
                "op_bots": [[5, 4], [0, 5], [2, 6]],
                "actions": [{"type": "load", "target": 0, "strength": 1},
                            {"type": "launch", "target": 1, "strength": 3},
                            {"type": "shield", "target": 2, "strength": 1}],
                "op_actions": [{"type": "load", "target": 0, "strength": 1},
                               {"type": "launch", "target": 2, "strength": 1},
                               {"type": "shield", "target": 2, "strength": 1}],
            }
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
