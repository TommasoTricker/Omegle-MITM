from stranger import Stranger

stranger1 = Stranger(["English"])
stranger2 = Stranger(["English"])

strangerIds = {
    stranger1: 1,
    stranger2: 2
}


def handle_messages(fromStranger: Stranger, toStranger: Stranger, oldMsgCount: int) -> int:
    msgList = fromStranger.get_messages()
    # There are new messages if the new message list is longer than the previous one
    if len(msgList) > oldMsgCount:
        for msg in msgList[oldMsgCount:]:
            print(f"Stranger {strangerIds[fromStranger]}: {msg}")
            # Send message to the other stranger
            toStranger.send_message(msg)
        # Save the message count
        return len(msgList)

    return oldMsgCount


def main() -> None:
    stranger1.setup()
    stranger2.setup()

    stranger1.start()
    stranger2.start()

    msgCount1 = 0
    msgCount2 = 0

    skipped1 = False
    skipped2 = False

    stranger1.wait_till_chat_found()
    stranger2.wait_till_chat_found()

    while True:
        if stranger1.skipped():
            skipped1 = True
        elif skipped1:
            print("Stranger 1 skipped")
            skipped1 = False
            msgCount1 = 0
        else:
            msgCount2 = handle_messages(stranger2, stranger1, msgCount2)

        if stranger2.skipped():
            skipped2 = True
        elif skipped2:
            print("Stranger 2 skipped")
            skipped2 = False
            msgCount2 = 0
        else:
            msgCount1 = handle_messages(stranger1, stranger2, msgCount1)


if __name__ == "__main__":
    main()
