import socket
import getpass
import shlex

def get_prompt():
    username = getpass.getuser()
    hostname = socket.gethostname()
    curr_dir = "~"
    return f"{username}@{hostname}%{curr_dir}$"

#парсер команд, отделяет команду от аргументов
def parser_comm(commLine):
    parts = shlex.split(commLine) # "умное" разделение, правильно обарабтывает кавычки и пробелы
    if len(parts) == 0:
        return None, []
    command = parts[0]
    args = parts[1:]
    return command, args

def ls_command(args):
    print(f"ls: stub command with arguments: {' '.join(args)}")

def cd_command(args):
    print(f"cd: stub command with arguments: {' '.join(args)}")

def exit_command(args):
    print("Exit")
    raise SystemExit

commands = {
    'ls' :ls_command,
    'cd' : cd_command,
    'exit' : exit_command
}  

def main_repl():
    while True:
        try:
            prompt = input(get_prompt()) # получение команды
            command, args = parser_comm(prompt) # разедление команды
            if command == None:
                continue
            elif command not in commands:
                print(f"{command}: command not found")
            else:
                commands[command](args)
        except SystemExit:
            break
        except KeyboardInterrupt:
            print("\n^C")
    
if __name__ == "__main__":
    main_repl()