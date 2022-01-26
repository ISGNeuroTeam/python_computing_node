from .json_server import run


if __name__ == "__main__":
    from sys import argv
    port = int(argv[1])
    print(port)
    if len(argv) > 1:
        run(port=port)
    else:
        run()
