from chat_gui import ChatGUI
from Client import Client
import argparse

def load_args():
    arg = argparse.ArgumentParser()
    arg.add_argument('-ci', '--client_ip', type=str, default='localhost', help='ip the client is on')
    arg.add_argument('-cp', '--client_port', type=int, default=None, help='port the client is on')
    arg.add_argument('-si', '--server_ip', type=str, required=True, help='ip to listen on')
    arg.add_argument('-sp', '--server_port', type=int, required=True, help='port to listen on')
    arg.add_argument('-un', '--username', type=str, default='User', help='username of the client')
    return arg.parse_args()

if __name__ == '__main__':
    args = load_args()
    client = Client(username=args.username,
                    client_ip=args.client_ip,
                    client_port=None,
                    server_ip=args.server_ip,
                    server_port=args.server_port)
    gui = ChatGUI(client)
    gui.run()
