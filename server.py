import socket
import threading
import time
import shlex

users = {
    "user1": "pass1",
    "user2": "pass2"
}

logged_in_users = {}
programs = {}
program_threads = {}
breakpoints = {}
attached_client = {}

def run_program(name, lines):
    vars_local = {}
    line_no = 0
    while line_no < len(lines):
        line = lines[line_no]
        if name in breakpoints and line_no in breakpoints[name]:
            if name in attached_client:
                sock = attached_client[name]
                sock.send(f"BREAK at {name} line {line_no}: {line}\n".encode())

                while True:
                    cmd = sock.recv(1024).decode().strip()
                    try:
                        cmd_parts = shlex.split(cmd)
                    except ValueError:
                        sock.send(b"Invalid input format\n")
                        continue

                    if not cmd_parts:
                        sock.send(b"Empty command\n")
                        continue

                    if cmd_parts[0] == "eval":
                        if len(cmd_parts) != 2:
                            sock.send(b"Usage: eval <var>\n")
                            continue
                        var = cmd_parts[1]
                        val = vars_local.get(var, "undefined")
                        sock.send(f"{var} = {val}\n".encode())

                    elif cmd_parts[0] == "set":
                        if len(cmd_parts) != 3:
                            sock.send(b"Usage: set <var> <value>\n")
                            continue
                        var, val = cmd_parts[1], cmd_parts[2]
                        try:
                            vars_local[var] = int(val)
                            sock.send(b"OK\n")
                        except ValueError:
                            sock.send(b"Invalid value\n")

                    elif cmd_parts[0] == "continue":
                        break

                    else:
                        sock.send(b"Unknown command inside breakpoint\n")

        if '=' in line:
            var, expr = [x.strip() for x in line.split('=', 1)]
            try:
                result = eval(expr, {}, vars_local)
                vars_local[var] = result
            except Exception as e:
                print(f"[{name}] Error: {e}")
                break
        time.sleep(1)
        line_no += 1

    if name in attached_client:
        sock = attached_client[name]
        sock.send(f"[{name}] Execution finished.\n".encode())
        del attached_client[name]

# Client
def handle_client(sock):
    authenticated = False
    username = None

    sock.send(b"Welcome. Please log in:\nUsername: ")
    user = sock.recv(1024).decode().strip()
    sock.send(b"Password: ")
    passwd = sock.recv(1024).decode().strip()

    if user in users and users[user] == passwd:
        sock.send(b"Login successful.\n")
        authenticated = True
        username = user
        logged_in_users[user] = sock
    else:
        sock.send(b"Login failed. Disconnecting...\n")
        sock.close()
        return

    while True:
        try:
            data = sock.recv(1024)
            if not data:
                break

            msg = data.decode().strip()
            try:
                parts = shlex.split(msg)
            except ValueError:
                sock.send(b"Invalid command format\n")
                continue

            if not parts:
                continue

            command = parts[0].lower()

            if command == "list":
                names = ", ".join(programs.keys())
                sock.send(f"Programs: {names}\n".encode())

            elif command == "attach":
                if len(parts) != 2:
                    sock.send(b"Usage: attach <program>\n")
                    continue
                prog = parts[1]
                if prog in attached_client:
                    sock.send(b"Program already attached\n")
                else:
                    if prog not in programs:
                        sock.send(b"Program not found\n")
                        continue
                    attached_client[prog] = sock
                    sock.send(f"Attached to {prog}. Starting program...\n".encode())
                    t = threading.Thread(target=run_program, args=(prog, programs[prog]))
                    program_threads[prog] = t
                    t.start()

            elif command == "addbp":
                if len(parts) != 3:
                    sock.send(b"Usage: addbp <program> <line_number>\n")
                    continue
                prog = parts[1]
                try:
                    line = int(parts[2])
                except ValueError:
                    sock.send(b"Line number must be an integer\n")
                    continue

                if prog in attached_client:
                    sock.send(b"Cannot modify breakpoints while attached\n")
                else:
                    if prog not in breakpoints:
                        breakpoints[prog] = set()
                    breakpoints[prog].add(line)
                    sock.send(b"Breakpoint added\n")

            elif command == "rmbp":
                if len(parts) != 3:
                    sock.send(b"Usage: rmbp <program> <line_number>\n")
                    continue
                prog = parts[1]
                try:
                    line = int(parts[2])
                except ValueError:
                    sock.send(b"Line number must be an integer\n")
                    continue

                if prog in attached_client:
                    sock.send(b"Cannot modify breakpoints while attached\n")
                else:
                    if prog in breakpoints and line in breakpoints[prog]:
                        breakpoints[prog].remove(line)
                        sock.send(b"Breakpoint removed\n")
                    else:
                        sock.send(b"Breakpoint not found\n")

            elif command == "detach":
                if len(parts) != 2:
                    sock.send(b"Usage: detach <program>\n")
                    continue
                prog = parts[1]
                if prog in attached_client and attached_client[prog] == sock:
                    del attached_client[prog]
                    sock.send(b"Detached\n")
                else:
                    sock.send(b"Not attached or not your session\n")

            else:
                sock.send(b"Unknown command\n")

        except Exception as e:
            print(f"[{username}] Error: {e}")
            break

    sock.close()
    if username in logged_in_users:
        del logged_in_users[username]

def start_server():
    programs["prog1"] = ["a = 2", "b = a + 3", "c = b * 2"]
    programs["prog2"] = ["x = 5", "y = x + 1", "z = y / 2"]

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("localhost", 54321))
    server.listen(5)
    print("Server listening on port 54321...")

    while True:
        client_sock, _ = server.accept()
        threading.Thread(target=handle_client, args=(client_sock,), daemon=True).start()

if __name__ == "__main__":
    start_server()
