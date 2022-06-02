from pynput.keyboard import Listener as PynputListener
import inspect
import ctypes
import os
import time
import signal






#### !!! VERY UGLY CODE !!! IGNORE UNDER ALL CIRCUMSTANCES !!! ####
def dirty_print(
    emul_inst,
    key="",
):

    os.system("cls")
    output = ""
    output_side = ""

    print(f"LAST_KEY: [{key}]")
    print("")
    print("")
    print(f"CLIPBOARD: '{emul_inst.clipboard}'")
    print(f"{emul_inst.temp_cursor} | {emul_inst.cursor} {emul_inst.sel_start}")
    print("\n")

    if emul_inst.cursor < emul_inst.sel_start:
        temp = f"{emul_inst.input[:emul_inst.sel_start]}¦{emul_inst.input[emul_inst.sel_start:]}"
        output = f"{temp[:emul_inst.cursor]}|{temp[emul_inst.cursor:]}"
        output_side = (
            " " * (emul_inst.cursor) + "|" + "·" * (emul_inst.sel_start - emul_inst.cursor) + "¦"
        )

    elif emul_inst.sel_start < emul_inst.cursor:
        temp = f"{emul_inst.input[:emul_inst.cursor]}|{emul_inst.input[emul_inst.cursor:]}"
        output = f"{temp[:emul_inst.sel_start]}¦{temp[emul_inst.sel_start:]}"
        output_side = (
            " " * (emul_inst.sel_start) + "¦" + "·" * (emul_inst.cursor - emul_inst.sel_start) + "|"
        )

    else:
        output = f"{emul_inst.input[:emul_inst.cursor]}|{emul_inst.input[emul_inst.cursor:]}"
        output_side = " " * (emul_inst.cursor) + "|"

    print(output_side)
    print(output)
    print(output_side)

####################################################################################







class ChatEmulator:
    def __init__(self, pynp_inst):
        self.pynp = pynp_inst

        self.cursor = self.sel_start = 0
        self.temp_cursor = -1
        self.input = self.clipboard = ""

    def clear(self):
        self.cursor = self.sel_start = 0
        self.input = ""



    def get_input(self, key):

        # type-able key only
        if len(key) == 1:
            if self.pynp.caps_lock:
                if self.pynp.shift:
                    key = key.lower()
                else:
                    key = key.upper()

            self.__delete_selected()
            self.__insert(key, self.cursor)

            self.temp_cursor = -1
            print(self.input)
            return self.input


        # the rest
        match key:
            case "enter":
                self.input = 0
                self.cursor = self.sel_start = 0

            case "delete":
                if self.__selection():
                    self.__delete_selected()
                elif self.cursor < len(self.input):
                    self.__delete(self.cursor, self.cursor + 1)

            case "backspace":
                if self.__selection():
                    self.__delete_selected()
                elif self.cursor:
                    if self.pynp.ctrl:
                        if self.input[self.cursor - 1] != "🬲":
                            self.__delete(self.cursor - 1, self.cursor)
                            self.cursor -= 1
                            self.sel_start = self.cursor
                            self.__insert("🬲", self.cursor)
                    else:
                        self.__delete(self.cursor - 1, self.cursor)
                        self.cursor -= 1
                        self.sel_start = self.cursor

            case "left":
                if self.temp_cursor != -1:
                    if self.pynp.shift or self.pynp.ctrl:
                        self.cursor = self.temp_cursor
                if self.cursor:
                    if self.pynp.shift or not self.__selection():
                        self.cursor -= 1
                    elif not self.pynp.ctrl:
                        if self.sel_start < self.cursor:
                            self.cursor = self.sel_start
                    if not self.pynp.shift:
                        self.sel_start = self.cursor
                    if self.pynp.ctrl:
                        self.__word_warp(key)
                elif not self.pynp.shift:
                    self.cursor = self.sel_start

            case "right":
                if self.temp_cursor != -1:
                    if self.pynp.shift or self.pynp.ctrl:
                        self.cursor = self.temp_cursor
                if self.cursor < len(self.input):
                    if self.pynp.shift or not self.__selection():
                        self.cursor += 1
                    elif not self.pynp.ctrl:
                        if self.sel_start > self.cursor:
                            self.cursor = self.sel_start
                    if not self.pynp.shift:
                        self.sel_start = self.cursor
                    if self.pynp.ctrl:
                        self.__word_warp(key)

                elif not self.pynp.shift:
                    self.sel_start = self.cursor

            case "home":
                self.cursor = self.sel_start = 0

            case "end":
                self.cursor = self.sel_start = len(self.input)

            # CTRL + A
            case "\\x01" if self.temp_cursor == -1:
                self.temp_cursor = self.cursor

                self.sel_start = 0
                self.cursor = len(self.input)

            # CTRL + C
            case "\\x03":
                self.__copy_selection()

            # CTRL + X
            case "\\x18":
                self.__copy_selection()
                self.__delete_selected()

            # CTRL + V
            case "\\x16":
                if self.pynp.ctrl:
                    self.__delete_selected()

                self.__insert(self.clipboard, self.cursor)

        if key not in {"enter", "ctrl", "shift", "\\x01", "\\x03", "\\x18", "\\x16"}:
            self.temp_cursor = -1

        return self.input

    def __word_warp(self, direction):
        if direction == "left":
            sliced = self.input[: self.cursor][::-1]
        else:
            sliced = self.input[self.cursor :]

        while sliced.startswith(" "):
            sliced = sliced[1:]

            if direction == "left":
                self.cursor -= 1
            else:
                self.cursor += 1

        char_list = list(sliced)

        for char in char_list:
            if char == " ":
                break
            elif direction == "left":
                self.cursor -= 1
            else:
                self.cursor += 1

        if not self.pynp.shift:
            self.sel_start = self.cursor

    def __copy_selection(self):
        if self.__selection():
            if self.cursor < self.sel_start:
                self.clipboard = self.input[self.cursor : self.sel_start]
            elif self.sel_start < self.cursor:
                self.clipboard = self.input[self.sel_start : self.cursor]

    def __selection(self):
        return self.cursor != self.sel_start

    def __insert(self, text, pos):
        self.input = self.input[:pos] + text + self.input[pos:]
        self.cursor += len(text)
        self.sel_start = self.cursor

    def __delete(self, start, end):
        self.input = self.input[:start] + self.input[end:]

    def __delete_selected(self):
        if self.cursor < self.sel_start:
            self.input = self.input[: self.cursor] + self.input[self.sel_start :]
            self.sel_start = self.cursor
        elif self.sel_start < self.cursor:
            self.input = self.input[: self.sel_start] + self.input[self.cursor :]
            self.cursor = self.sel_start



class PynPlus:
    def __init__(self):
        self.Listener = PynputListener

        self.ctrl = self.shift = self.alt = False
        self.caps_lock = self.__get_caps_lock()

    def format(self, key):

        keystate = inspect.stack()[1].function

        key = self.__parse_numpad(self.__special(self.__unquote(str(key))))

        if key == "ctrl":
            self.ctrl = keystate == "on_press"

        elif key == "shift":
            self.shift = keystate == "on_press"
        elif key == "alt":
            self.alt = keystate == "on_press"

        self.caps_lock = self.__get_caps_lock()

        return key

    def __get_caps_lock(self):
        hllDll = ctypes.WinDLL("User32.dll")
        VK_CAPITAL = 0x14

        out = hllDll.GetKeyState(VK_CAPITAL)

        if out == 65408:
            out = 0
        elif out == 65409:
            out = 1

        return out

    def __special(self, key):
        if key == "[~]":
            key = "~"
        elif key == "\\\\":
            key = "\\"

        if key.startswith("Key."):
            key = key[4:]

            match key:
                case "ctrl_l" | "ctrl_r":
                    key = "ctrl"
                case "alt_l" | "alt_gr":
                    key = "alt"
                case "shift" | "shift_r":
                    key = "shift"
                case "space":
                    key = " "

        return key

    def __parse_numpad(self, key):
        if key.startswith("<") and key.endswith(">"):
            key = str(int(key[1:-1]) - 96)

        return key

    def __unquote(self, key):
        if key.startswith('"'):
            return key.replace('"', "")
        else:
            return key.replace("'", "")


def on_press(key):
    try:
        key = pynp.format(key)

        # we like em dirty codez >:D
        whatevero = emul.get_input(key)
        dirty_print(emul, key)

    except KeyboardInterrupt:
        pass


def on_release(key):
    key = pynp.format(key)

    if key == 'esc':
        os.system('cls')
        print('Stopped the app!')
        # return False # exit


def handler(signum, frame):
    pass

if __name__ == "__main__":

    pynp = PynPlus()
    emul = ChatEmulator(pynp)

    listener = pynp.Listener(on_press=on_press, on_release=on_release)
    listener.start()

    os.system('cls')
    print('Started the app!')

    signal.signal(signal.SIGINT, handler)

    # only to keep the process alive
    while True:
        time.sleep(6)

