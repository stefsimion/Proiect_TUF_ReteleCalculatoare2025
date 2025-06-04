import socket
import threading

def listen(sock):
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                break
            print(data.decode(), end="")
        except:
            break

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("localhost", 54321))

    def wait_and_prompt(expected_prompt: str):
        buffer = ""
        while expected_prompt not in buffer:
            data = sock.recv(1024)
            if not data:
                break
            decoded = data.decode()
            print(decoded, end="")
            buffer += decoded

    wait_and_prompt("Username: ")
    sock.send(input().strip().encode() + b"\n")

    wait_and_prompt("Password: ")
    sock.send(input().strip().encode() + b"\n")

    threading.Thread(target=listen, args=(sock,), daemon=True).start()

    while True:
        try:
            msg = input("")
            sock.send((msg + "\n").encode())
        except KeyboardInterrupt:
            break
        except:
            break
    sock.close()


if __name__ == "__main__":
    main()
