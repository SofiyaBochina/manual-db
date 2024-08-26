from database import Database

args_len = {
    "set": 2,
    "get": 1,
    "unset": 1,
    "find": 1,
    "counts": 1,
    "begin": 0,
    "rollback": 0,
    "commit": 0,
}


def main():
    db = Database()
    while True:
        try:
            command = input("> ").split()
            if command:
                action = command[0].lower()
                if action == "end":
                    break
                if hasattr(db, action):
                    func = getattr(db, action)
                    args = command[1:]

                    if len(args) == args_len.get(action, -1):
                        res = func(*args)
                        if res is not None:
                            print(res)
                    else:
                        print("INCORRECT ARGUMENTS")
                else:
                    print("UNKNOWN COMMAND")
        except (EOFError, KeyboardInterrupt):
            break


if __name__ == "__main__":
    main()
