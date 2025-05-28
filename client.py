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
