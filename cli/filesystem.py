import os
from abc import ABC, abstractmethod
from typing import Optional

from infra.io import IDisplay
from core.text.document import Document, Paragraph, Heading
from cli.commands import Command
from cli.router import Router

class IAppState(ABC):
    def __init__(self, context: 'FileManager', display: IDisplay):
        self.context = context
        self.display = display
        self.router = Router()
        self.register_commands()

    @abstractmethod
    def register_commands(self):
        pass

    @abstractmethod
    def render(self):
        pass

    def handle_input(self, inp: str):
        self.router.handle_input(inp)

class FileManager:
    def __init__(self, display: IDisplay):
        self.display = display
        self.current_state: IAppState = DirectoryState(self, display, os.getcwd())
        self.is_running = True

    def change_state(self, state: IAppState):
        self.current_state = state
        self.current_state.render()

    def run(self):
        self.display.show("\n= FILE MANAGER STARTED =")
        self.current_state.render()
        
        while self.is_running:
            try:
                prompt = self._get_prompt()
                inp = self.display.prompt(prompt).strip()
                
                if not inp: continue
                
                self.current_state.handle_input(inp)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.display.show(f"Error: {e}")
        
        self.display.show("= FILE MANAGER CLOSED =\n")

    def _get_prompt(self) -> str:
        if isinstance(self.current_state, DirectoryState):
            return f"{os.path.basename(self.current_state.current_path)}/ > "
        elif isinstance(self.current_state, FileViewState):
            return "VIEW > "
        elif isinstance(self.current_state, FileEditState):
            return "EDIT > "
        return "> "

class DirectoryState(IAppState):
    def __init__(self, context: FileManager, display: IDisplay, path: str):
        self.current_path = path
        super().__init__(context, display)

    def register_commands(self):
        self.router.register("ls", ListDirCommand(self))
        self.router.register("cd", ChangeDirCommand(self))
        self.router.register("open", OpenFileCommand(self))
        self.router.register("exit", ExitFileManagerCommand(self.context))
        self.router.register("help", HelpCommand(self.display, ["ls", "cd <path>", "open <file>", "exit"]))

    def render(self):
        self.display.show(f"\n- Directory: {self.current_path} -")
        self.router.handle("ls", [])

class ListDirCommand(Command):
    def __init__(self, state: DirectoryState):
        self.state = state

    def execute(self, args: list):
        try:
            items = os.listdir(self.state.current_path)
            dirs = [d for d in items if os.path.isdir(os.path.join(self.state.current_path, d))]
            files = [f for f in items if os.path.isfile(os.path.join(self.state.current_path, f))]
            
            for d in dirs: self.state.display.show(f"[DIR]  {d}")
            for f in files: self.state.display.show(f"[FILE] {f}")
        except PermissionError:
            self.state.display.show("Permission denied")

class ChangeDirCommand(Command):
    def __init__(self, state: DirectoryState):
        self.state = state

    def execute(self, args: list):
        if not args: return
        target = " ".join(args)
        
        new_path = os.path.normpath(os.path.join(self.state.current_path, target))
        
        if os.path.isdir(new_path):
            self.state.current_path = new_path
            self.state.render()
        else:
            self.state.display.show(f"Directory not found: {target}")

class OpenFileCommand(Command):
    def __init__(self, state: DirectoryState):
        self.state = state

    def execute(self, args: list):
        if not args: 
            self.state.display.show("Usage: open <filename>")
            return
        filename = " ".join(args)
        
        filepath = os.path.join(self.state.current_path, filename)
        if os.path.isfile(filepath):
            new_state = FileViewState(self.state.context, self.state.display, filepath, self.state)
            self.state.context.change_state(new_state)
        else:
            self.state.display.show(f"File not found: {filename}")

class FileViewState(IAppState):
    def __init__(self, context: FileManager, display: IDisplay, filepath: str, prev_state: DirectoryState):
        self.filepath = filepath
        self.prev_state = prev_state
        super().__init__(context, display)

    def register_commands(self):
        self.router.register("cat", CatCommand(self))
        self.router.register("edit", GoToEditModeCommand(self))
        self.router.register("close", CloseFileCommand(self))
        self.router.register("help", HelpCommand(self.display, ["cat", "edit", "close"]))

    def render(self):
        self.display.show(f"\n-- Viewing: {os.path.basename(self.filepath)} --")
        self.router.handle("cat", [])

class CatCommand(Command):
    def __init__(self, state: FileViewState):
        self.state = state

    def execute(self, args: list):
        try:
            with open(self.state.filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                self.state.display.show(content)
        except Exception as e:
            self.state.display.show(f"Error reading file: {e}")

class GoToEditModeCommand(Command):
    def __init__(self, state: FileViewState):
        self.state = state

    def execute(self, args: list):
        edit_state = FileEditState(self.state.context, self.state.display, self.state.filepath, self.state)
        self.state.context.change_state(edit_state)

class CloseFileCommand(Command):
    def __init__(self, state: FileViewState):
        self.state = state

    def execute(self, args: list):
        self.state.context.change_state(self.state.prev_state)


class FileEditState(IAppState):
    def __init__(self, context: FileManager, display: IDisplay, filepath: str, prev_state: FileViewState):
        self.filepath = filepath
        self.prev_state = prev_state
        self.document = Document() 
        super().__init__(context, display)
        self._load_file_to_document()

    def _load_file_to_document(self):
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    clean_line = line.strip()
                    if clean_line:
                        if clean_line.isupper() and len(clean_line) < 50:
                            self.document.add(Heading(clean_line))
                        else:
                            self.document.add(Paragraph(clean_line))
        except FileNotFoundError:
            pass

    def register_commands(self):
        self.router.register("add", EditorAddTextCommand(self.document, self.display, is_heading=False))
        self.router.register("add_h", EditorAddTextCommand(self.document, self.display, is_heading=True))
        self.router.register("show", EditorShowCommand(self.document, self.display))
        self.router.register("save", EditorSaveCommand(self))
        self.router.register("cancel", EditorCancelCommand(self))
        self.router.register("help", HelpCommand(self.display, ["add <text>", "add_h <text>", "show", "save", "cancel"]))

    def render(self):
        self.display.show(f"\n--- Editing: {os.path.basename(self.filepath)} ---")
        self.display.show("(Use 'add <text>' or 'add_h <text>' to append content. 'save' to write to disk)")
        self.router.handle("show", [])


class EditorAddTextCommand(Command):
    def __init__(self, doc: Document, display: IDisplay, is_heading: bool):
        self.doc = doc
        self.display = display
        self.is_heading = is_heading

    def execute(self, args: list):
        if not args: return
        text = " ".join(args)
        if self.is_heading:
            self.doc.add(Heading(text))
        else:
            self.doc.add(Paragraph(text))
        self.display.show("Line added")

class EditorShowCommand(Command):
    def __init__(self, doc: Document, display: IDisplay):
        self.doc = doc
        self.display = display

    def execute(self, args: list):
        self.display.show("--- DOCUMENT PREVIEW ---")
        self.display.show(self.doc.render_full())
        self.display.show("------------------------")

class EditorSaveCommand(Command):
    def __init__(self, state: FileEditState):
        self.state = state

    def execute(self, args: list):
        try:
            content = self.state.document.render_full()
            with open(self.state.filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            self.state.display.show("File saved successfully")
            self.state.context.change_state(self.state.prev_state)
        except Exception as e:
            self.state.display.show(f"Error saving: {e}")

class EditorCancelCommand(Command):
    def __init__(self, state: FileEditState):
        self.state = state

    def execute(self, args: list):
        self.state.display.show("Changes discarded")
        self.state.context.change_state(self.state.prev_state)


class ExitFileManagerCommand(Command):
    def __init__(self, context: FileManager):
        self.context = context

    def execute(self, args: list):
        self.context.is_running = False

class HelpCommand(Command):
    def __init__(self, display: IDisplay, commands_list: list):
        self.display = display
        self.commands_list = commands_list

    def execute(self, args: list):
        self.display.show("Available commands: " + ", ".join(self.commands_list))