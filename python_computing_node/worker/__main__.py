import argparse
from .socket_server import Server



# from .json_server import run
#
#
# if __name__ == "__main__":
#     from sys import argv
#     port = int(argv[1])
#     print(port)
#     if len(argv) > 1:
#         run(port=port)
#     else:
#         run()


def main():
    parser = argparse.ArgumentParser(description='Server for node job execution')

    parser.add_argument('port', type=int, help='port for server')
    parser.add_argument('inter_proc_storage', type=str, help='interprocessing storage mount point')
    parser.add_argument('shared_storage', type=str, help='shared storage mount point')
    parser.add_argument('local_storage', type=str, help='local storage mount point')


    args = parser.parse_args()

    server = Server(
        args.port, args.inter_proc_storage, args.shared_storage, args.local_storage
    )
    server.run()


if __name__ == '__main__':
    main()


