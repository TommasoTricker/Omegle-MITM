from dataclasses import dataclass, field
import requests
import threading
import time
import tkinter as tk
import tkinter.scrolledtext as scrolledtext
from typing import List

from PIL import Image, ImageTk
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options


class Status:
    SEARCHING = "searching"
    CHATTING = "chatting"
    DISCONNECTED = "disconnected"


NO_MESSAGES_TIMEOUT = 20
SHOW_BROWSER = False
STARTING_INTERESTS = ["English"]
STATUS_COLOURS = {Status.DISCONNECTED: "red",
                  Status.SEARCHING: "blue", 
                  Status.CHATTING: "green"}


@dataclass
class Stranger:
    id: int
    colour: str
    interests: List[str]
    old_interests: List[str] = field(default_factory=list)
    driver: webdriver.Firefox = None
    message_count: int = 0
    status: Status = Status.SEARCHING
    canvas: tk.Canvas = None
    oval: int = None


def main() -> None:
    def add_text(text: str, colour: str = None) -> None:
        if scrolled_text.yview()[1] == 1.0:
            scroll = True
        else:
            scroll = False

        start = scrolled_text.index(tk.END + "-1c")
        scrolled_text.config(state="normal")
        scrolled_text.insert(tk.END, text)
        scrolled_text.config(state="disabled")
        if colour:
            scrolled_text.tag_add(
                colour, start, scrolled_text.index(start + f"+{len(text)}c"))

        if scroll:
            scrolled_text.see(tk.END)

    def view_message(stranger: Stranger, message: str) -> None:
        label = f"Stranger {stranger.id}: "
        print(label + message)
        add_text(label, stranger.colour)
        add_text(message + "\n")

    def send_and_view_messages(from_stranger: Stranger, to_stranger: Stranger, messages: List[str]) -> None:
        for message in send_messages(to_stranger, messages):
            view_message(from_stranger, message)

    def view_status_update(stranger: Stranger, status_update: str) -> None:
        text = f"Stranger {stranger.id} {status_update}"
        print(text)
        add_text(text + "\n", stranger.colour)

    def get_new_messages(stranger: Stranger) -> List[str]:
        messages = [element.get_attribute("textContent")
                    for element in stranger.driver.find_elements(By.XPATH, "//p[@class='strangermsg']/span")]
        new_messages = messages[stranger.message_count:]
        stranger.message_count = len(messages)

        return new_messages

    def send_messages(stranger: Stranger, messages: List[str]) -> List[str]:
        chat_box = stranger.driver.find_element(By.CLASS_NAME, "chatmsg")

        for message in messages:
            if message:
                try:
                    chat_box.send_keys(message)
                    chat_box.send_keys(Keys.RETURN)
                except:
                    messages.remove(message)

        return messages

    def check_status(stranger: Stranger) -> str:
        source = stranger.driver.page_source

        if "disconnected" in source:
            return Status.DISCONNECTED
        elif "Looking" in source:
            return Status.SEARCHING
        elif "You're now" in source:
            return Status.CHATTING
        else:
            return Status.SEARCHING

    def disconnect(stranger: Stranger) -> None:
        disconnect_button = stranger.driver.find_element(
            By.CLASS_NAME, "disconnectbtn")
        while check_status(stranger) != Status.DISCONNECTED:
            try:
                disconnect_button.click()
            except StaleElementReferenceException:
                disconnect_button = stranger.driver.find_element(
                    By.CLASS_NAME, "disconnectbtn")

    def new(stranger: Stranger) -> None:
        if stranger.status != Status.SEARCHING or stranger.old_interests != stranger.interests:
            disconnect_button = stranger.driver.find_element(
                By.CLASS_NAME, "disconnectbtn")
            while check_status(stranger) != Status.DISCONNECTED:
                try:
                    disconnect_button.click()
                except StaleElementReferenceException:
                    disconnect_button = stranger.driver.find_element(
                        By.CLASS_NAME, "disconnectbtn")

            if stranger.old_interests != stranger.interests:
                elements = stranger.driver.find_elements(By.TAG_NAME, "a")
                for element in elements:
                    if element.text == "(Enable)" or element.text == "(Settings)":
                        element.click()

                        for button in stranger.driver.find_elements(By.CLASS_NAME, "topictagdelete"):
                            button.click()

                        input_field = stranger.driver.find_element(
                            By.CLASS_NAME, "newtopicinput")

                        for interest in stranger.interests:
                            input_field.send_keys(interest)
                            input_field.send_keys(Keys.RETURN)

                        break

                stranger.old_interests = stranger.interests

            while check_status(stranger) != Status.SEARCHING:
                try:
                    disconnect_button.click()
                except StaleElementReferenceException:
                    disconnect_button = stranger.driver.find_element(
                        By.CLASS_NAME, "disconnectbtn")

            if banned:
                try:
                    stranger.driver.find_element(
                        By.XPATH, "//div[span[text()='No']]").click()
                except NoSuchElementException:
                    pass

            stranger.message_count = 0

    def new_both() -> None:
        if stranger1.status == Status.CHATTING:
            view_status_update(stranger1, "disconnected")
        new(stranger1)
        stranger1.status = Status.DISCONNECTED
        if stranger2.status == Status.CHATTING:
            view_status_update(stranger2, "disconnected")
        new(stranger2)
        stranger2.status = Status.DISCONNECTED

    def thread_target() -> None:
        def handle_status_update(stranger: Stranger) -> None:
            previous = stranger.status

            stranger.status = check_status(stranger)

            if previous != stranger.status:
                stranger.canvas.itemconfig(
                    stranger.oval, fill=STATUS_COLOURS[stranger.status], outline=STATUS_COLOURS[stranger.status])

                if stranger.status == Status.CHATTING:
                    interests = ""
                    for element in stranger.driver.find_elements(By.CLASS_NAME, "statuslog"):
                        if "You both like" in element.get_attribute("textContent"):
                            interests = element.get_attribute(
                                "textContent").split("like")[1].strip()[:-1]

                    if interests:
                        view_status_update(stranger, f"found ({interests})")
                    else:
                        view_status_update(stranger, f"found")

                elif previous == Status.CHATTING:
                    view_status_update(stranger, "disconnected")

        def handle_messages(from_stranger: Stranger, to_stranger: Stranger) -> None:
            send_and_view_messages(
                from_stranger, to_stranger, get_new_messages(from_stranger))

        start_time = time.time()

        while not stop.is_set():
            handle_status_update(stranger1)
            handle_status_update(stranger2)

            if stranger1.status == Status.CHATTING and stranger2.status == Status.CHATTING:
                handle_messages(stranger1, stranger2)
                handle_messages(stranger2, stranger1)

                if auto_both_inactivity.get():
                    if stranger1.message_count == 0 and stranger2.message_count == 0 and time.time() - start_time >= NO_MESSAGES_TIMEOUT:
                        new_both()
                else:
                    start_time = time.time()
            elif stranger1.status == Status.DISCONNECTED or stranger2.status == Status.DISCONNECTED:
                start_time = time.time()

                if auto_both_disconnect.get():
                    new_both()
            else:
                start_time = time.time()

        thread_done.set()

    print("Starting... (Might take a sec)")

    stranger1 = Stranger(1, "red", STARTING_INTERESTS)
    stranger2 = Stranger(2, "blue", STARTING_INTERESTS)

    if SHOW_BROWSER:
        stranger1.driver = webdriver.Firefox()
        stranger2.driver = webdriver.Firefox()
    else:
        options = Options()
        options.add_argument("--headless")
        stranger1.driver = webdriver.Firefox(options=options)
        stranger2.driver = webdriver.Firefox(options=options)

    stranger1.driver.get("https://www.omegle.com/")
    stranger2.driver.get("https://www.omegle.com/")

    try:
        stranger1.driver.find_element(By.CLASS_NAME, "newtopicinput")
    except NoSuchElementException:
        banned = True
    else:
        banned = False

    stranger1.driver.find_element(By.ID, "textbtn").click()
    stranger2.driver.find_element(By.ID, "textbtn").click()

    checkboxes1 = stranger1.driver.find_elements(
        By.CSS_SELECTOR, "input[type='checkbox']")
    checkboxes2 = stranger2.driver.find_elements(
        By.CSS_SELECTOR, "input[type='checkbox']")

    if not banned:
        checkboxes1 = checkboxes1[1:]
        checkboxes2 = checkboxes2[1:]

    for checkbox in checkboxes1:
        checkbox.click()
    for checkbox in checkboxes2:
        checkbox.click()

    stranger1.driver.find_element(
        By.XPATH, "//input[@value='Confirm & continue']").click()
    stranger2.driver.find_element(
        By.XPATH, "//input[@value='Confirm & continue']").click()

    disconnect(stranger1)
    disconnect(stranger2)

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

    # Intervene
    intervene_column = 0

    intervene = tk.LabelFrame(controls, text="Intervene")
    intervene.grid(row=0, column=intervene_column, sticky=tk.EW)

    stranger1.canvas = tk.Canvas(intervene, width=20, height=20)
    stranger1.oval = stranger1.canvas.create_oval(
        5, 5, 15, 15, fill=STATUS_COLOURS[stranger1.status], outline=STATUS_COLOURS[stranger1.status])
    stranger1.canvas.grid(row=0, column=0)

    tk.Label(intervene, text="Stranger 1").grid(row=0, column=1)

    stranger1_message = tk.Entry(intervene)
    stranger1_message.grid(row=0, column=2, sticky=tk.EW)

    tk.Button(intervene, text="Send", command=lambda: send_and_view_messages(
        stranger1, stranger2, [stranger1_message.get()])).grid(row=0, column=3)

    tk.Button(intervene, text="Disconnect", command=lambda: disconnect(
        stranger1)).grid(row=0, column=4)

    tk.Button(intervene, text="New", command=lambda: new(
        stranger1)).grid(row=0, column=5)

    stranger2.canvas = tk.Canvas(intervene, width=20, height=20)
    stranger2.oval = stranger2.canvas.create_oval(
        5, 5, 15, 15, fill=STATUS_COLOURS[stranger2.status], outline=STATUS_COLOURS[stranger2.status])
    stranger2.canvas.grid(row=1, column=0)

    tk.Label(intervene, text="Stranger 2").grid(row=1, column=1)

    stranger2_message = tk.Entry(intervene)
    stranger2_message.grid(row=1, column=2, sticky=tk.EW)

    tk.Button(intervene, text="Send", command=lambda: send_and_view_messages(
        stranger2, stranger1, [stranger2_message.get()])).grid(row=1, column=3)

    tk.Button(intervene, text="Disconnect", command=lambda: disconnect(
        stranger2)).grid(row=1, column=4)

    tk.Button(intervene, text="New", command=lambda: new(
        stranger2)).grid(row=1, column=5)

    tk.Label(intervene, text="(Stranger X can't see you sent a message as them)").grid(
        row=2, column=1, columnspan=5, sticky=tk.W)

    tk.Button(intervene, text="New both",
              command=new_both).grid(row=3, column=1)

    tk.Button(intervene, text="Disconnect both", command=lambda: [
              disconnect(stranger1), disconnect(stranger2)]).grid(row=4, column=1)

    def change_interests(stranger: Stranger, interests: str) -> None:
        stranger.interests = [s.strip() for s in interests.split(",") if s]

    # Interests
    interests_column = 1

    interests = tk.LabelFrame(controls, text="Interests")
    interests.grid(row=0, column=interests_column, sticky=tk.EW)

    tk.Label(interests, text="Stranger 1").grid(row=0, column=0)

    stranger1_interests = tk.Entry(interests)
    stranger1_interests.insert(0, ", ".join(STARTING_INTERESTS))
    stranger1_interests.grid(row=0, column=1, sticky=tk.EW)

    tk.Label(interests, text="Stranger 2").grid(row=1, column=0)

    stranger2_interests = tk.Entry(interests)
    stranger2_interests.insert(0, ", ".join(STARTING_INTERESTS))
    stranger2_interests.grid(row=1, column=1, sticky=tk.EW)

    tk.Button(interests, text="Set", command=lambda: [change_interests(stranger1, stranger1_interests.get(
    )), change_interests(stranger2, stranger2_interests.get())]).grid(row=2, column=1, columnspan=2)

    tk.Label(interests, text="Separate interests with a comma (,)").grid(
        row=3, column=0, columnspan=3, sticky=tk.W)

    tk.Label(interests, text="(Interests will apply on the next chat)").grid(
        row=4, column=0, columnspan=3, sticky=tk.W)

    # Settings
    settings_column = 2

    settings = tk.LabelFrame(controls, text="Settings")
    settings.grid(row=0, column=settings_column, sticky=tk.NSEW)

    tk.Checkbutton(settings, variable=auto_both_disconnect).grid(
        row=0, column=0, sticky=tk.NW)
    tk.Label(settings, text="Automatically start new chat for both if one disconnects",
             justify=tk.LEFT).grid(row=0, column=1, sticky=tk.W)

    tk.Checkbutton(settings, variable=auto_both_inactivity).grid(
        row=1, column=0, sticky=tk.NW)
    tk.Label(settings, text=f"Automatically start new chat for both if {NO_MESSAGES_TIMEOUT} seconds pass without a first message\n (useful when the two chats connect with each other)", justify=tk.LEFT
             ).grid(row=1, column=1, sticky=tk.W)

    root.rowconfigure(0, weight=1)
    root.columnconfigure(0, weight=1)

    controls.columnconfigure(intervene_column, weight=3)
    controls.columnconfigure(interests_column, weight=1)

    intervene.columnconfigure(2, weight=1)

    interests.columnconfigure(1, weight=1)

    stop = threading.Event()
    thread_done = threading.Event()

    threading.Thread(target=thread_target).start()

    def on_closing() -> None:
        auto_both_disconnect.set(False)
        auto_both_inactivity.set(False)
        disconnect(stranger1)
        disconnect(stranger2)
        text = "Closing... (Might take a sec)"
        print(text)
        add_text(text)
        stop.set()
        while not thread_done.is_set():
            root.update()
        stranger1.driver.quit()
        stranger2.driver.quit()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
