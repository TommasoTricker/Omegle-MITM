from PIL import Image, ImageTk
import requests
import threading
import time
import tkinter as tk
import tkinter.scrolledtext as scrolledtext
from typing import List

from stranger import Stranger

NO_MESSAGES_TIMEOUT = 20
STATUS_COLOURS = {"disconnected": "red", "searching": "blue", "chatting": "green"}


def main() -> None:
    def add_text_and_colour(text: str, colour: str, coloured_characters: int) -> None:
        if scrolled_text.yview()[1] == 1.0:
            scroll = True
        else:
            scroll = False

        start = scrolled_text.index(tk.END + "-1c")
        scrolled_text.config(state="normal")
        scrolled_text.insert(tk.END, text + "\n")
        scrolled_text.config(state="disabled")
        if coloured_characters:
            scrolled_text.tag_add(colour, start, scrolled_text.index(start + f"+{coloured_characters}c"))

        if scroll:
            scrolled_text.see(tk.END)

    def view_message(stranger: Stranger, message: str) -> None:
        text = f"Stranger {stranger.id}: {message}"
        print(text)
        add_text_and_colour(text, stranger.colour, text.index(":"))

    def view_status_update(stranger: Stranger, status_update: str) -> None:
        text = f"Stranger {stranger.id} {status_update}"
        print(text)
        add_text_and_colour(text, stranger.colour, len(text))

    def new_and_view(stranger: Stranger) -> None:
        if stranger.status == "chatting":
            view_status_update(stranger, "disconnected")
        stranger.new()
        stranger.status = "disconnected"

    def new_and_view_both() -> None:
        if stranger1.status == "chatting":
            view_status_update(stranger1, "disconnected")
        stranger1.status = "chatting"
        stranger1.new()

        if stranger2.status == "chatting":
            view_status_update(stranger2, "disconnected")
        stranger2.status = "chatting"
        stranger2.new()

        stranger1.status = "disconnected"
        stranger2.status = "disconnected"
        

    def thread_target() -> None:
        def handle_messages(from_stranger: Stranger, to_stranger: Stranger) -> None:
            for message in from_stranger.send_messages(to_stranger.get_new_messages()):
                view_message(to_stranger, message)

        def handle_status_update(stranger: Stranger, canvas: tk.Canvas) -> None:
            previous = stranger.status

            stranger.status = stranger.check_status()

            if previous != stranger.status:
                canvas.itemconfig(oval1, fill=STATUS_COLOURS[stranger.status], outline=STATUS_COLOURS[stranger.status])
                if (previous == "disconnected" or previous == "searching") and stranger.status == "chatting":
                    interests = stranger.get_common_interests()

                    if interests:
                        view_status_update(stranger, f"found ({interests})")
                    else:
                        view_status_update(stranger, f"found")

                elif previous == "chatting" and (stranger.status == "disconnected" or stranger.status == "searching"):
                    view_status_update(stranger, "disconnected")

        start_time = time.time()
        previous_message_count_1 = 0
        previous_message_count_2 = 0

        while run.is_set():
            handle_status_update(stranger1, canvas1)
            handle_status_update(stranger2, canvas2)

            if stranger1.status == "chatting" and stranger2.status == "chatting":
                handle_messages(stranger1, stranger2)
                handle_messages(stranger2, stranger1)

            if auto_both_disconnect.get() and (stranger1.status == "disconnected" or stranger2.status == "disconnected"):
                new_and_view_both()

            if auto_both_inactivity.get() and stranger1.status == "chatting" and stranger2.status == "chatting":
                if stranger1.message_count > previous_message_count_1 or stranger2.message_count > previous_message_count_2:
                    start_time = time.time()
                    previous_message_count_1 = stranger1.message_count
                    previous_message_count_2 = stranger2.message_count
                elif time.time() - start_time >= NO_MESSAGES_TIMEOUT:
                    new_and_view_both()
            else:
                start_time = time.time()
                previous_message_count_1 = 0
                previous_message_count_2 = 0

        thread_done.set()

    stranger1 = Stranger(1, "red")
    stranger1.interests = ["English"]

    stranger2 = Stranger(2, "blue")
    stranger2.interests = ["English"]

    root = tk.Tk()
    root.title("Omegle Man in the Middle: Mess with Strangers!")
    root.iconphoto(False, ImageTk.PhotoImage(Image.open(requests.get(
        "https://www.omegle.com/static/favicon.png", stream=True).raw)))

    auto_both_disconnect = tk.BooleanVar()
    auto_both_inactivity = tk.BooleanVar()

    scrolled_text = scrolledtext.ScrolledText(root)
    scrolled_text.config(state="disabled")
    scrolled_text.tag_config("red", foreground="red")
    scrolled_text.tag_config("blue", foreground="blue")
    scrolled_text.grid(row=0, column=0, sticky=tk.NSEW)

    controls = tk.Frame(root)
    controls.grid(row=1, column=0, sticky=tk.NSEW)

    def send_and_view_messages(stranger: Stranger, messages: List[str]) -> None:
        for message in stranger.send_messages(messages):
            view_message(stranger, message)

    # Intervene
    intervene_column = 0

    intervene = tk.LabelFrame(controls, text="Intervene")
    intervene.grid(row=0, column=intervene_column, sticky=tk.EW)

    canvas1 = tk.Canvas(intervene, width=20, height=20)
    oval1 = canvas1.create_oval(
        5, 5, 15, 15, fill=STATUS_COLOURS[stranger1.status], outline=STATUS_COLOURS[stranger1.status])
    canvas1.grid(row=0, column=0)

    tk.Label(intervene, text="Stranger 1").grid(row=0, column=1)

    stranger1_message = tk.Entry(intervene)
    stranger1_message.grid(row=0, column=2, sticky=tk.EW)

    tk.Button(intervene, text="Send", command=lambda: send_and_view_messages(
        stranger1, [stranger1_message.get()])).grid(row=0, column=3)

    tk.Button(intervene, text="Disconnect", command=lambda: stranger1.disconnect()).grid(row=0, column=4)

    tk.Button(intervene, text="New", command=lambda: new_and_view(stranger1)).grid(row=0, column=5)

    canvas2 = tk.Canvas(intervene, width=20, height=20)
    oval2 = canvas2.create_oval(
        5, 5, 15, 15, fill=STATUS_COLOURS[stranger2.status], outline=STATUS_COLOURS[stranger2.status])
    canvas2.grid(row=1, column=0)

    tk.Label(intervene, text="Stranger 2").grid(row=1, column=1)

    stranger2_message = tk.Entry(intervene)
    stranger2_message.grid(row=1, column=2, sticky=tk.EW)

    tk.Button(intervene, text="Send", command=lambda: send_and_view_messages(
        stranger2, [stranger2_message.get()])).grid(row=1, column=3)

    tk.Button(intervene, text="Disconnect", command=lambda: stranger2.disconnect()).grid(row=1, column=4)

    tk.Button(intervene, text="New", command=lambda: new_and_view(stranger2)).grid(row=1, column=5)

    tk.Label(intervene, text="(Stranger X won't see you sent a message as them)").grid(
        row=2, column=1, columnspan=5, sticky=tk.W)

    tk.Button(intervene, text="New both", command=new_and_view_both).grid(row=3, column=1)

    tk.Button(intervene, text="Disconnect both", command=lambda: [
              stranger1.disconnect(), stranger2.disconnect()]).grid(row=4, column=1)

    def change_interests(stranger: Stranger, interests: str) -> None:
        stranger.interests = [s.strip() for s in interests.split(",") if s]

    # Interests
    interests_column = 1

    interests = tk.LabelFrame(controls, text="Interests")
    interests.grid(row=0, column=interests_column, sticky=tk.EW)

    tk.Label(interests, text="Stranger 1").grid(row=0, column=0)

    stranger1_interests = tk.Entry(interests)
    stranger1_interests.insert(0, "English")
    stranger1_interests.grid(row=0, column=1, sticky=tk.EW)

    tk.Label(interests, text="Stranger 2").grid(row=1, column=0)

    stranger2_interests = tk.Entry(interests)
    stranger2_interests.insert(0, "English")
    stranger2_interests.grid(row=1, column=1, sticky=tk.EW)

    tk.Button(interests, text="Set", command=lambda: [change_interests(stranger1, stranger1_interests.get(
    )), change_interests(stranger2, stranger2_interests.get())]).grid(row=2, column=1, columnspan=2)

    tk.Label(interests, text="Separate interests with a comma (,)").grid(row=3, column=0, columnspan=3, sticky=tk.W)

    tk.Label(interests, text="(Interests will apply on the next chat)").grid(
        row=4, column=0, columnspan=3, sticky=tk.W)

    # Settings
    settings_column = 2

    settings = tk.LabelFrame(controls, text="Settings")
    settings.grid(row=0, column=settings_column, sticky=tk.NSEW)

    tk.Checkbutton(settings, text="Automatically start new chat for both if one disconnects",
                   variable=auto_both_disconnect).grid(row=0, column=0, sticky=tk.NW)
    tk.Checkbutton(settings, text=f"Automatically start new chat for both if {NO_MESSAGES_TIMEOUT} seconds pass without messages",
                   variable=auto_both_inactivity).grid(row=1, column=0, sticky=tk.NW)

    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)

    controls.columnconfigure(intervene_column, weight=3)
    controls.columnconfigure(interests_column, weight=1)

    intervene.columnconfigure(2, weight=1)

    interests.columnconfigure(1, weight=1)

    run = threading.Event()
    run.set()

    thread_done = threading.Event()

    threading.Thread(target=thread_target).start()

    def on_closing() -> None:
        add_text_and_colour("Closing... (Might take a sec)", "", 0)
        run.clear()
        while not thread_done.is_set():
            root.update()
        stranger1.driver.quit()
        stranger2.driver.quit()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
