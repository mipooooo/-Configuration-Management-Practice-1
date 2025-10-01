import socket #программный интерфейс для обеспечения информационного обмена между процессами. 
import getpass #содержит функцию getuser(), которая возвращает имя пользователя, используя переменные окружения или базу паролей системы. 
import shlex # реализует функции для анализа синтаксиса оболочки Unix
import argparse # модуль для обработки аргументов командной строки
import csv
import base64
from io import *


class VFSNode:
    def __init__(self, name, type, content):
        self.name = name
        self.type = type
        self.content = content
        self.children = {}
        self.parent = None
        
class VFS:
    def __init__(self):
        self.root = VFSNode(name='/', type='dir', content=None)
        self.current = self.root
        self.current_path = '/'
    def get_cur_dir(self):
        if self.current_path == '/':
            return '/'
        return self.current_path.split('/')[-1]
    def parse_path(self, path):
        return [comp for comp in path.split('/') if comp]
    def find_node(self, path):
        current = self.root
        path_comp = self.parse_path(path)
        
        for comp in path_comp:
            if current and current.type=='dir' and comp in current.children:
                current = current.children[comp]
            else:
                return None
        return current
        
    def decode_content(self, content):
        if not isinstance(content, str) or not content: # Добавьте эту проверку
            return content
        try:
            decoded_bytes = base64.b64decode(content)
            return decoded_bytes.decode('utf-8', errors='ignore')
        except Exception as e:
            return content
    def load_from_csv(self, vfs_path):
        try:
            with open(vfs_path, 'r', newline='') as f:
                reader = csv.DictReader(f, delimiter=';')
                self.root = VFSNode(name='/', type='dir', content=None)
                
                for row in reader:
                    path = row['path']
                    node_type = row['type']
                    content = row['content']
                    
                    if not path or not node_type:
                        raise ValueError(f"Missing 'path' or 'type in row:{row}")
                    if path=='/':
                        continue
                    node_name = path.split('/')[-1]
                    parent_path = '/'.join(path.split('/')[:-1]) if len(path.split('/')) > 2 else '/'
                    parent_node = self.find_node(parent_path)
                    if parent_node is None or parent_node.type != 'dir':
                        raise ValueError(f"Invalid VFS structure: Parent directory not found for {path}")
                    new_node = VFSNode(name=node_name, type=node_type, content=content)
                    new_node.parent = parent_node
                    
                    parent_node.children[node_name] = new_node
        except FileNotFoundError:
            print(f"VFS file not found: {vfs_path}. Shell terminating") 
            exit(1)
        except ValueError as e:
            print(f"Error in VFS structure: {e}. Shell terminating")
            exit(1)
        except Exception as e:
            print(f"Error loading VFS from CSV: {e}. Shell terminating")
            exit(1)
        print(f"VFS loaded successfully from {vfs_path}.")
    def display_motd(self):
        motd_node = self.find_node('/motd')
        if motd_node and motd_node.type == 'file':
            content = self.decode_content(motd_node.content)
            print("\n--- Message of the Day ---")
            print(content)
            print("--------------------------\n")

# создание приглашения к вводу
def get_prompt():
    username = getpass.getuser()
    hostname = socket.gethostname()
    curr_dir = "~"
    return f"{username}@{hostname}%{curr_dir}$"

VFS = VFS()


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
    
    if args.vfs_path:
        VFS.load_from_csv(args.vfs_path)
        VFS.display_motd()
    elif args.script_path:
        run_scrpit(args.script_path)
    else:
        main_repl()
    
if __name__ == "__main__":
    main()
