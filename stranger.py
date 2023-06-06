from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import List

PAGE_LOAD_TIME = 1
NEW_CHAT_FOUND_TIMEOUT = 20


class Stranger:
    def __init__(self, interests: List[str]) -> None:
        self.driver = webdriver.Firefox()
        self.banned = False
        self.waitLoad = WebDriverWait(self.driver, PAGE_LOAD_TIME)
        self.waitChat = WebDriverWait(self.driver, NEW_CHAT_FOUND_TIMEOUT)
        self.interests = interests

    def setup(self) -> None:
        self.driver.get("https://www.omegle.com/")

        self.waitLoad.until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        try:
            input_field = self.driver.find_element(By.CLASS_NAME, "newtopicinput")
            for interest in self.interests:
                input_field.send_keys(interest)
                input_field.send_keys(Keys.RETURN)
        except:
            self.banned = True

        element = self.driver.find_element(By.ID, "textbtn")
        element.click()

        checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")

        if self.banned == False:
            checkboxes = checkboxes[1:]

        for checkbox in checkboxes:
            checkbox.click()

    def start(self) -> None:
        button = self.driver.find_element(By.XPATH, "//input[@value='Confirm & continue']")
        button.click()

    def skipped(self) -> bool:
        return self.driver.find_elements(By.CLASS_NAME, "chatmsg.disabled")

    def click_disconnect(self) -> None:
        button = self.waitLoad.until(EC.element_to_be_clickable((By.CLASS_NAME, "disconnectbtn")))
        button.click()

    def new_chatting(self) -> None:
        self.click_disconnect()
        self.click_disconnect()
        self.click_disconnect()

    def new_not_chatting(self) -> None:
        self.click_disconnect()

    def wait_till_chat_found(self) -> None:
        if self.banned:
            try:
                element = self.waitLoad.until(EC.element_to_be_clickable(
                    (By.XPATH, '//div[@style="position: absolute; right: 0px; bottom: 0px; border-top: 1px solid rgb(63, 159, 255); border-left: 1px solid rgb(63, 159, 255); padding: 0.5em; text-align: center; cursor: pointer; height: 1em; background: white; color: black;"]/span[text()="No"]')))
                element.click()
            except:
                pass

        self.waitChat.until(EC.element_to_be_clickable((By.CLASS_NAME, "sendbtn")))

    def get_messages(self) -> List[str]:
        try:
            return [x.text for x in self.waitLoad.until(EC.presence_of_all_elements_located((By.XPATH, '//p[@class="strangermsg"]/span')))]
        except:
            return []

    def send_message(self, contents: str) -> None:
        textarea = self.driver.find_element(By.CLASS_NAME, "chatmsg")
        textarea.send_keys(contents)
        textarea.send_keys(Keys.RETURN)
