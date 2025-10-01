import socket #программный интерфейс для обеспечения информационного обмена между процессами. 
import getpass #содержит функцию getuser(), которая возвращает имя пользователя, используя переменные окружения или базу паролей системы. 
import shlex # реализует функции для анализа синтаксиса оболочки Unix
import argparse # модуль для обработки аргументов командной строки
import csv
import base64


class VFSNode:
    def __init__(self, name, node_type, content=None):
        self.name = name
        self.type = node_type
        self.content = content
        self.children = {}
        self.parent = None
        
class VFS:
    def __init__(self):
        self.root = VFSNode(name='/', node_type='dir', content=None)
        self.current = self.root
        self.current_path = '/'
    def get_cur_dir(self):
        if self.current_path == '/':
            return '/'
        return self.current_path.split('/')[-1]
    def parse_path(self, path):
        return [comp for comp in path.split('/') if comp]
    def find_node(self, path):
        if not path:
            return None
        if path[0] != '/':
            path = self.get_abs_path(path)
        current = self.root
        path_comp = self.parse_path(path)
        
        for comp in path_comp:
            if current and current.type=='dir' and comp in current.children:
                current = current.children[comp]
            else:
                return None
        return current
        
    def decode_content(self, content):
        if not isinstance(content, str) or not content:
            return content
        try:
            decoded_bytes = base64.b64decode(content)
            return decoded_bytes.decode('utf-8', errors='ignore')
        except Exception:
            return content
    def load_from_csv(self, vfs_path):
        try:
            with open(vfs_path, 'r', newline='') as f:
                reader = csv.DictReader(f, delimiter=';')
                self.root = VFSNode(name='/', node_type='dir', content=None)
                
                for row in reader:
                    path = row['path']
                    node_type1 = row['type']
                    content = row['content']
                    
                    if not path or not node_type1:
                        raise ValueError(f"Missing 'path' or 'type in row:{row}")
                    if path=='/':
                        continue
                    # вычисляем имя узла и путь родителя
                    comps = [c for c in path.split('/') if c]
                    node_name = comps[-1]
                    parent_path = '/' + '/'.join(comps[:-1]) if len(comps) > 1 else '/'
                    parent_node = self.find_node(parent_path)
                    if parent_node is None or parent_node.type != 'dir':
                        raise ValueError(f"Invalid VFS structure: Parent directory not found for {path}")
                    new_node = VFSNode(name=node_name, node_type=node_type1, content=content)
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
    def get_abs_path(self, path):
        if path[0] == '/':
            return path
        base_path = self.current_path
        if base_path[-1] != '/':
            base_path += '/'
        return base_path + path
    def change_dir_logic(self, target_path):
        if target_path == '..':
            if self.current.parent:
                return self.current.parent
            return self.current
        elif target_path == '.':
            return self.current
        
        abs_path = self.get_abs_path(target_path)
        target_node = self.find_node(abs_path)
        if target_node and target_node.type == 'dir':
            return target_node
        return None

# создание приглашения к вводу
def get_prompt():
    username = getpass.getuser()
    hostname = socket.gethostname()
    if vfs.current_path == '/':
        cur_display = '~'
    else:
        cur_display = vfs.current_path
    return f"{username}@{hostname}%{cur_display}$"

vfs = VFS()


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
    if not args:
        target_node = vfs.current
    else:
        path = args[0]
        abs_path = vfs.get_abs_path(path)
        target_node = vfs.find_node(abs_path)
    if not target_node:
        print(f"ls: cannot access '{args[0]}': No such file or directory")
        return
    if target_node.type != 'dir':
        print(target_node.name)
        return
    if not target_node.children:
        return
    
    for name in sorted(target_node.children.keys()):
        node = target_node.children[name]
        indicator = '/' if node.type == 'dir' else ''
        print(f"{name}{indicator}")
def cd_command(args):
    if not args or args[0] == '~':
        vfs.current = vfs.root
        vfs.current_path = '/'
        return
    target_path = args[0]
    new_node = vfs.change_dir_logic(target_path)
    if not new_node:
        print(f"cd: no such file or directory: {target_path}")
        return
    
    if new_node != vfs.current:
        vfs.current = new_node
        if target_path == '..':
            if vfs.current_path.count('/')>1:
                vfs.current_path = '/'.join(vfs.current_path.split('/')[:-1])
                if not vfs.current_path:
                    vfs.current_path = '/'
        elif target_path == '.':
            pass
        else:
            vfs.current_path = vfs.get_abs_path(target_path)

def exit_command(args):
    print("Exit")
    raise SystemExit

def du_command(args):
    def count_nodes(node):
        count = 1
        if node.type == 'dir':
            for child in node.children.values():
                count += count_nodes(child)
        return count

    path = args[0] if args else vfs.current_path
    abs_path = vfs.get_abs_path(path)
    target_node = vfs.find_node(abs_path)
    if not target_node:
        print(f"du: cannot access '{path}': No such file or directory")
        return
    
    size = count_nodes(target_node)
    
    print(f"{size}\t{path}")

def echo_command(args):
    print(" ".join(args))

commands = {
    'ls' :ls_command,
    'cd' : cd_command,
    'exit' : exit_command,
    'du' : du_command,
    'echo' : echo_command
}  

# функция запуска скрипта
def run_script(script_path):
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
        vfs.load_from_csv(args.vfs_path)
        vfs.display_motd()

    if args.script_path:
        run_script(args.script_path)
    elif not args.script_path:
        main_repl()
    
if __name__ == "__main__":
    main()
