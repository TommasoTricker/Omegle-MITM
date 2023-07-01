from typing import List

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

SHOW_BROWSER = False


class Stranger:
    def __init__(self, id: int, colour: str):
        self.id = id
        self.colour = colour
        
        self.status = "searching"

        self.interests = []

        self.old_interests = []
        self.message_count = 0

        if SHOW_BROWSER:
            self.driver = webdriver.Firefox()
        else:
            options = Options()
            options.headless = True
            self.driver = webdriver.Firefox(options=options)

        self.driver.get("https://www.omegle.com/")

        try:
            self.driver.find_element(By.CLASS_NAME, "newtopicinput")
        except NoSuchElementException:
            self.banned = True
        else:
            self.banned = False

        self.driver.find_element(By.ID, "textbtn").click()

        checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")

        if self.banned:
            checkboxes = checkboxes
        else:
            checkboxes = checkboxes[1:]

        for checkbox in checkboxes:
            checkbox.click()

        self.driver.find_element(By.XPATH, "//input[@value='Confirm & continue']").click()

        self.disconnect()

    def check_status(self) -> str:
        source = self.driver.page_source

        if source.__contains__("disconnected"):
            return "disconnected"
        elif source.__contains__("Looking"):
            return "searching"
        elif source.__contains__("You're now"):
            return "chatting"
        else:
            return "searching"

    def send_messages(self, messages: List[str]) -> List[str]:
        chat_box = self.driver.find_element(By.CLASS_NAME, "chatmsg")

        for message in messages:
            if message:
                try:
                    chat_box.send_keys(message)
                    chat_box.send_keys(Keys.RETURN)
                except:
                    messages.remove(message)

        return messages

    def disconnect(self) -> None:
        if self.check_status() != "disconnected":
            disconnect_button = self.driver.find_element(By.CLASS_NAME, "disconnectbtn")
            disconnect_button.click()
            disconnect_button.click()

    def new(self) -> None:
        disconnect_button = self.driver.find_element(By.CLASS_NAME, "disconnectbtn")
        if self.check_status() != "disconnected":
            disconnect_button.click()
            disconnect_button.click()

        if self.old_interests != self.interests:
            elements = self.driver.find_elements(By.TAG_NAME, "a")
            for element in elements:
                if element.text == "(Enable)" or element.text == "(Settings)":
                    element.click()

                    for button in self.driver.find_elements(By.CLASS_NAME, "topictagdelete"):
                        button.click()

                    input_field = self.driver.find_element(By.CLASS_NAME, "newtopicinput")

                    for interest in self.interests:
                        input_field.send_keys(interest)
                        input_field.send_keys(Keys.RETURN)

                    break

            self.old_interests = self.interests

        try:
            disconnect_button.click()
        except StaleElementReferenceException:
            self.new()

        if self.banned:
            try:
                WebDriverWait(self.driver, 1).until(EC.element_to_be_clickable(
                    (By.XPATH, "//div[span[text()='No']]"))).click()
            except TimeoutException:
                pass
                
        self.message_count = 0

    def get_new_messages(self) -> List[str]:
        messages = [x.get_attribute('textContent')
                    for x in self.driver.find_elements(By.XPATH, '//p[@class="strangermsg"]/span')]
        new_messages = messages[self.message_count:]
        self.message_count = len(messages)

        return new_messages

    def get_common_interests(self) -> List[str]:
        for element in self.driver.find_elements(By.CLASS_NAME, "statuslog"):
            if element.get_attribute('textContent').__contains__("You both like"):
                return element.get_attribute('textContent').split("like")[1].strip()[:-1]
