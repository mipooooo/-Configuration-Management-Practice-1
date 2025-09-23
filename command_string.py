import socket #программный интерфейс для обеспечения информационного обмена между процессами. 
import getpass #содержит функцию getuser(), которая возвращает имя пользователя, используя переменные окружения или базу паролей системы. 
import shlex # реализует функции для анализа синтаксиса оболочки Unix
import argparse # модуль для обработки аргументов командной строки

# создание приглашения к вводу
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

#временные команды заглушки
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

# функция запуска скрипта
def run_scrpit(script_path):
    try:
        f = open(script_path, 'r') 
        for line in f:
            command_line = line.strip()
            if command_line=="" or command_line[0]=="#" or command_line[:1]=="//": #пустая строка или комментарий 
                continue
    
            print(f"{get_prompt()}{command_line}")
            command, args = parser_comm(command_line)
            
            if command in commands:
                try:
                    commands[command](args)
                except SystemExit:
                    return
                except KeyboardInterrupt:
                    print("\n^C")
            else:
                print(f"{command}: command not found")
                print("Script execution stopped due to error.")
                return

    except FileNotFoundError:
            print(f"file not found: {script_path}")   
        
# параметры командной строки
def parse_args():
    parser = argparse.ArgumentParser(description="UNIX-like emulator")
    parser.add_argument('--vfs-path', type=str, help='Path to the VFS file')
    parser.add_argument('--script-path', type=str, help='Path to a startup script')
    return parser.parse_args()


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
    
def main():
    args = parse_args()
    
    print(f"VFS path: {args.vfs_path}")
    print(f"Script path: {args.script_path}")
    
    if args.script_path:
        run_scrpit(args.script_path)
    else:
        main_repl()
    
if __name__ == "__main__":
    main()