from stranger import Stranger
import time

SECONDS_BEFORE_AUTOSKIP = 15


class OmegleMITM:
    def __init__(self) -> None:
        pass

    def start(self) -> None:
        stranger1 = Stranger("Stranger 1")
        stranger2 = Stranger("Stranger 2")

        stranger1.setup()
        stranger2.setup()

        stranger1.start()
        stranger2.start()

        self.wait_till_chat_found_both(stranger1, stranger2)

        msgCount1 = 0
        msgCount2 = 0

        while True:
            # Check if strangers skipped and if so start new a new chat for both
            skipped1 = stranger1.skipped()
            skipped2 = stranger2.skipped()

            if skipped1 and skipped2:
                stranger1.new_not_chatting()
                stranger2.new_not_chatting()

                print("New chat, both skipped")
            elif skipped1:
                stranger1.new_not_chatting()
                stranger2.new_chatting()

                print(f"New chat, {stranger1.label} skipped")
            elif skipped2:
                stranger1.new_chatting()
                stranger2.new_not_chatting()

                print(f"New chat, {stranger2.label} skipped")

            # If new chat, reset the message variables
            if skipped1 or skipped2:
                self.wait_till_chat_found_both(stranger1, stranger2)
                msgCount1 = 0
                msgCount2 = 0

            msgCount1 = self.handle_messages(msgCount1, stranger1, stranger2)
            msgCount2 = self.handle_messages(msgCount2, stranger2, stranger1)

    def handle_messages(self, oldMsgCount: int, fromStranger: Stranger, toStranger: Stranger) -> None:
        msgList = fromStranger.get_messages()
        # There are new messages if the new message list is longer than the previous one
        if len(msgList) > oldMsgCount:
            for msg in msgList[oldMsgCount:]:
                print(f"{fromStranger.label}: {msg}")
                # Send message to the other stranger
                toStranger.send_message(msg)
            # Save the message count
            return len(msgList)

        return oldMsgCount

    def wait_till_chat_found_both(self, stranger1: Stranger, stranger2: Stranger) -> None:
        stranger1.wait_till_chat_found()
        stranger2.wait_till_chat_found()
