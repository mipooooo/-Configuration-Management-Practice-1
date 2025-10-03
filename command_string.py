import socket #программный интерфейс для обеспечения информационного обмена между процессами. 
import getpass #содержит функцию getuser(), которая возвращает имя пользователя, используя переменные окружения или базу паролей системы. 
import shlex # реализует функции для анализа синтаксиса оболочки Unix
import argparse # модуль для обработки аргументов командной строки
import csv
import base64


# Класс для представления узла в VFS
class VFSNode:
    def __init__(self, name, node_type, content=None):
        self.name = name
        self.type = node_type
        self.content = content
        self.children = {} #словарь для дочерних узлов
        self.parent = None #родительский узел

#Класс, управляющий VFS
class VFS:
    def __init__(self):
        self.root = VFSNode(name='/', node_type='dir', content=None) #корневой узел
        self.current = self.root
        self.current_path = '/'

#Поиск узла по пути
    def find_node(self, path):
        if not path:
            return None
        if path[0] != '/': #если путь не абсолютный, преобразуем его
            path = self.get_abs_path(path)
        current = self.root
        path_comp = [comp for comp in path.split('/') if comp] #разделяем путь на компоненты
        for comp in path_comp:
            #ищем компонент в дочерних узлах текущего узла и проверяем, что он директория
            if current and current.type=='dir' and comp in current.children:
                current = current.children[comp]
            else:
                return None #путь не найден
        return current

    #Декодирование содержимого файла из base64   
    def decode_content(self, content):
        if not isinstance(content, str) or not content:
            return content
        try:
            decoded_bytes = base64.b64decode(content)
            return decoded_bytes.decode('utf-8', errors='ignore')
        except Exception: #текст не в base64
            return content
        
    #Загрузка VFS из CSV файла
    def load_from_csv(self, vfs_path):
        try:
            with open(vfs_path, 'r', newline='') as f:
                reader = csv.DictReader(f, delimiter=';')
                self.root = VFSNode(name='/', node_type='dir', content=None) #сброс корня перед загрузкой
                
                for row in reader:
                    path = row['path']
                    node_type1 = row['type']
                    content = row['content']
                    # проверка на корректность данных в строке CSV.
                    if not path or not node_type1:
                        raise ValueError(f"Missing 'path' or 'type in row:{row}")
                    # пропускаем корневой узел, он уже создан
                    if path=='/':
                        continue
                    # вычисляем имя узла и путь родителя
                    comps = [c for c in path.split('/') if c]
                    node_name = comps[-1] #имя текущего узла - последний компонетнт
                    parent_path = '/' + '/'.join(comps[:-1]) if len(comps) > 1 else '/' #формируем путь родителя
                    parent_node = self.find_node(parent_path) #находим родительский узел
                    # проверяем, что родительский узел существует и является директорией
                    if parent_node is None or parent_node.type != 'dir':
                        raise ValueError(f"Invalid VFS structure: Parent directory not found for {path}")
                    
                    #создаем новый узел и добавляем его в дочерние узлы родителя
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

    #Отображение сообщения дня (motd)
    def display_motd(self):
        motd_node = self.find_node('/motd')
        if motd_node and motd_node.type == 'file':
            content = self.decode_content(motd_node.content) #мы не уверены, что содержимое в base64, но метод decode_content обработает и дочиный, и обычный файл
            print("\n--- Message of the Day ---")
            print(content)
            print("--------------------------\n")
            
    #Получение абсолютного пути
    def get_abs_path(self, path):
        if path[0] == '/': #уже абсолютный путь
            return path
        base_path = self.current_path #текущий путь
        if base_path[-1] != '/':   #добавляем слеш, если его нет
            base_path += '/'
        return base_path + path #формируем абсолютный путь
    
    #Логика изменения директории
    def change_dir_logic(self, target_path):
        if target_path == '..': #если цель - родительская директория
            if self.current.parent: #мы не в корне
                return self.current.parent 
            return self.current
        elif target_path == '.': #если цель - текущая директория
            return self.current
        
        abs_path = self.get_abs_path(target_path) #получаем абсолютный путь к цели
        target_node = self.find_node(abs_path)#ищем целевой узел
        if target_node and target_node.type == 'dir':
            return target_node
        return None

# создание приглашения к вводу
def get_prompt():
    username = getpass.getuser()
    hostname = socket.gethostname()
    if vfs.current_path == '/':
        cur_display = '~' # корневая директория отображается как ~
    else:
        cur_display = vfs.current_path
    return f"{username}@{hostname}%{cur_display}$"

#парсер команд, отделяет команду от аргументов
def parser_comm(commLine):
    parts = shlex.split(commLine) # "умное" разделение, правильно обарабтывает кавычки и пробелы
    if len(parts) == 0:
        return None, []
    command = parts[0]
    args = parts[1:]
    return command, args

#инициализация VFS
vfs = VFS()

# реализация команд
#вывод содержимого директории или имя файла
def ls_command(args):
    if not args:
        target_node = vfs.current #если нет аргументов, цель -  текущая директория
    else:
        path = args[0]
        abs_path = vfs.get_abs_path(path)
        target_node = vfs.find_node(abs_path)
    if not target_node:
        print(f"ls: cannot access '{args[0]}': No such file or directory")
        return
    if target_node.type != 'dir': #если цель - файл, просто выводим его имя
        print(target_node.name)
        return
    if not target_node.children: #если директория пуста
        return
    #выводим имена дочерних узлов
    for name in sorted(target_node.children.keys()):
        node = target_node.children[name]
        indicator = '/' if node.type == 'dir' else '' #добавляем слеш к директориям
        print(f"{name}{indicator}")
        
#смена директории
def cd_command(args):
    if not args or args[0] == '~': #если нет аргументов или аргумент - ~, переходим в корень
        vfs.current = vfs.root
        vfs.current_path = '/'
        return
    target_path = args[0] #цель - первый аргумент
    new_node = vfs.change_dir_logic(target_path)
    if not new_node:
        print(f"cd: no such file or directory: {target_path}")
        return
    #смена текущего узла и пути, если узел изменился
    if new_node != vfs.current:
        vfs.current = new_node # обновляем текущий узел
        if target_path == '..': # переход в родительскую директорию
            if vfs.current_path.count('/')>1: # если мы не в корне
                vfs.current_path = '/'.join(vfs.current_path.split('/')[:-1])
                if not vfs.current_path:
                    vfs.current_path = '/' #если путь пустой, значит мы в корне
        elif target_path == '.':
            pass #текущий путь не меняется
        else:
            vfs.current_path = vfs.get_abs_path(target_path) #обновляем текущий путь

# завершает работу оболочки
def exit_command(args):
    print("Exit")
    raise SystemExit

# реализация команды подсчета узлов
def du_command(args):
    # рекурсивная функция для подсчета узлов
    def count_nodes(node):
        count = 1 # считаем текущий узел
        if node.type == 'dir': # если директория, считаем дочерние узлы
            for child in node.children.values():
                count += count_nodes(child)
        return count

    path = args[0] if args else vfs.current_path # определяем путь: аргумент или текущая директория
    abs_path = vfs.get_abs_path(path)
    target_node = vfs.find_node(abs_path)
    if not target_node:
        print(f"du: cannot access '{path}': No such file or directory")
        return
    
    size = count_nodes(target_node)
    
    print(f"{size}\t{path}")

# выводит аргументы на экран
def echo_command(args):
    print(" ".join(args))

# создание директории
def mkdir_command(args):
    if not args:
        print("mkdir: missing operand")
        return
    elif len(args) > 1: 
        print("mkdir: too many arguments")
        return
    path = args[0] #путь новой директории
    abs_path = vfs.get_abs_path(path)
    comp = [c for c in abs_path.split('/') if c]
    if not comp:
        print(f"mkdir: cannot create directory '{path}': File exists")
        return
    new_dir_name = comp[-1] #имя новой директории
    parent_path = '/' + '/'.join(comp[:-1]) if len(comp)>1 else '/' #путь родительской директории
    parent_node = vfs.find_node(parent_path) #находим родительский узел
    if not parent_node or parent_node.type != 'dir':
        print (f"mkdir: cannot create directory '{path}': No such file or directory")
        return
    if new_dir_name in parent_node.children:
        print (f"mkdir: cannot create directory '{path}': File exists")
        return
    
    #создаем новый узел и добавляем его в дочерние узлы родителя
    new_node = VFSNode(name = new_dir_name, node_type='dir',content= None)
    new_node.parent = parent_node
    parent_node.children[new_dir_name] = new_node
    
# перемещение или переименование файла/директории
def mv_command(args):
    if len(args) != 2: # должно быть 2 аргумента: источник и цель
        print("mv: missing file operand")
        return
    source_node_path = args[0] #путь источника
    target_node_path = args[1] #путь цели
    if source_node_path == '/': 
        print(f"mv: cannot move root '{source_node_path}': Invalid source path")
        return
    
    source_abs_path =vfs.get_abs_path(source_node_path) 
    source_node = vfs.find_node(source_abs_path)
    
    if not source_node:
        print(f"mv: cannot stat '{source_node_path}': No such file or directory")
        return
    
    target_abs_path = vfs.get_abs_path(target_node_path)
    target_node = vfs.find_node(target_abs_path)
    
    if not target_node:
        #Переименовываем (цель не существует)
        target_comps = [c for c in target_abs_path.split('/') if c]
        if not target_comps:
            print(f"mv: invalid target '{target_node_path}'")
            return
        new_name = target_comps[-1] #новое имя - последний компонент пути цели
        parent_path = '/' + '/'.join(target_comps[:-1]) if len(target_comps)>1 else '/' #путь родителя цели
        parent_target_node = vfs.find_node(parent_path) #находим родительский узел цели

        # проверяем, что родительский узел существует и является директорией
        if not parent_target_node or parent_target_node.type != 'dir':
            print(f"mv: cannot overwrite '{target_node_path}': No such file or directory")
            return

        # проверяем, что новое имя не занято
        if new_name in parent_target_node.children:
            print(f"mv: cannot overwrite '{target_node_path}': File exists")
            return
        #Удаляем из старого родителя
        old_parent = source_node.parent
        old_name = source_node.name
        if not old_parent:
            print(f"mv: cannot overwrite '{source_node_path}': Invalid source path")
            return
        del old_parent.children[old_name]
        #Добавляем в новый родитель
        source_node.name = new_name
        parent_target_node.children[new_name] = source_node
        source_node.parent = parent_target_node
    else:
        #Перемещение
        # цель должна быть директорией
        if target_node.type != 'dir':
            print(f"mv: target '{target_node_path}' is not a directory")
            return
        # проверяем, что новое имя не занято
        if source_node.name in target_node.children:
            print(f"mv: cannot move '{source_node_path}': File exists in target directory")
            return
        #Удаляем из старого родителя и добавляем в новый
        old_parent = source_node.parent
        del old_parent.children[source_node.name]
        target_node.children[source_node.name] = source_node
        source_node.parent = target_node
        
# словарь команд     
commands = {
    'ls' :ls_command,
    'cd' : cd_command,
    'exit' : exit_command,
    'du' : du_command,
    'echo' : echo_command,
    'mkdir': mkdir_command,
    'mv': mv_command
}  

# функция запуска скрипта
def run_script(script_path):
    try:
        f = open(script_path, 'r') 
        for line in f:
            command_line = line.strip() # удаление пробелов в начале и конце строки
            if command_line=="" or command_line[0]=="#" or command_line[:1]=="//": #пустая строка или комментарий 
                continue
    
            print(f"{get_prompt()}{command_line}") # эмуляция ввода команды
            command, args = parser_comm(command_line) #парсим команду
            
            if command in commands: #если команда известна, выполняем ее
                try:
                    commands[command](args)
                except SystemExit:
                    return
                except KeyboardInterrupt:
                    print("\n^C") # обрабатываем прерывание
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

# функция основного цикла REPL(Read-Eval-Print Loop) для работы в интерактивном режиме
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


# главная функция: парсит аргументы, загружает VFS и запускает скрипт/REPL.
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

if __name__ == "__main__": # точка входа в программу
    main()
