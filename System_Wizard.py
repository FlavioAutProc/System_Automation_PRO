import sys
import os
import json
import sqlite3
import markdown
import csv
import subprocess
import shutil
from datetime import datetime
from PyQt6.QtCore import Qt, QSize, QTimer, QSettings, QUrl
from PyQt6.QtGui import (QIcon, QFont, QAction, QKeySequence, QShortcut,QDesktopServices, QPixmap, QImage, QImageReader)
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QStackedWidget, QLineEdit, QTextEdit,
                             QListWidget, QListWidgetItem, QComboBox, QFileDialog, QMessageBox,QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QToolBar,
                             QStatusBar, QDialog, QFormLayout, QSpinBox, QCheckBox, QGroupBox, QScrollArea, QFrame, QSplitter, QSizePolicy, QSystemTrayIcon, QMenu,  QProgressBar)

class DatabaseManager:
    """Classe para gerenciamento completo do banco de dados SQLite"""
    def __init__(self):
        self.db_path = os.path.join(os.path.expanduser("~"), "AutomatePro", "automate_pro.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()
    def init_db(self):
        """Inicializa o banco de dados com todas as tabelas necessárias"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Tabela de projetos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    type TEXT NOT NULL,  -- 'video', 'audio', 'file'
                    format TEXT,
                    quality TEXT,
                    save_path TEXT,
                    status TEXT DEFAULT 'pending',  -- 'pending', 'downloading', 'paused', 'completed', 'failed', 'cancelled'
                    progress REAL DEFAULT 0,
                    total_size INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Tabela de planilhas
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS spreadsheets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    headers TEXT,
                    data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Tabela de anotações
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT,
                    tags TEXT,
                    is_favorite BOOLEAN DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Tabela de utilitários
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS utilities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,  -- 'app', 'site', 'command'
                    path TEXT,
                    command TEXT,
                    is_favorite BOOLEAN DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Tabela de comandos personalizados
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS custom_commands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    command TEXT NOT NULL,
                    category TEXT,
                    tags TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Tabela de configurações
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL UNIQUE,
                    value TEXT
                )
            ''')

            # Tabela de usuários
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    is_admin BOOLEAN DEFAULT 0,
                    theme TEXT DEFAULT 'dark',
                    language TEXT DEFAULT 'pt',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Tabela de lembretes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    due_date TEXT,
                    is_completed BOOLEAN DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Tabela de histórico
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    module TEXT NOT NULL,
                    details TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Inserir usuário admin padrão se não existir
            cursor.execute('SELECT * FROM users WHERE username = "admin"')
            if not cursor.fetchone():
                cursor.execute('INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)',
                               ('admin', 'admin123', 1))

            conn.commit()
    def execute_query(self, query, params=None, fetchone=False, fetchall=False):
        """Executa uma query no banco de dados"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()

            if fetchone:
                return cursor.fetchone()
            if fetchall:
                return cursor.fetchall()
            return cursor.lastrowid
class SettingsManager:
    """Classe para gerenciamento completo de configurações do sistema"""

    def __init__(self):
        self.db = DatabaseManager()
        self.load_settings()
    def load_settings(self):
        """Carrega as configurações do banco de dados"""
        self.settings = {}
        results = self.db.execute_query('SELECT key, value FROM settings', fetchall=True)

        for key, value in results:
            self.settings[key] = value

        # Configurações padrão
        defaults = {
            'theme': 'dark',
            'language': 'pt',
            'auto_backup': '1',
            'backup_interval': '7',
            'notifications': '1',
            'font_size': '12',
            'font_family': 'Segoe UI',
            'recent_projects_limit': '5',
            'default_project_dir': os.path.expanduser('~/Documents/AutomatePro/Projects'),
            'default_export_dir': os.path.expanduser('~/Documents/AutomatePro/Exports'),
            'backup_dir': os.path.expanduser('~/Documents/AutomatePro/Backups'),
            'portable_mode': '0',
            'auto_update': '1',
            'markdown_preview': '1',
            'terminal_font_size': '10',
            'terminal_font_family': 'Consolas',
            'terminal_theme': 'dark',
            'enable_shortcuts': '1',
            'enable_drag_drop': '1',
            'enable_notifications': '1',
            'default_download_dir': os.path.expanduser('~/Downloads/AutomatePro'),
            'max_parallel_downloads': '3',
            'download_notifications': '1'

        }

        # Aplicar padrões para configurações faltantes
        for key, value in defaults.items():
            if key not in self.settings:
                self.settings[key] = value
                self.save_setting(key, value)
    def save_setting(self, key, value):
        """Salva uma configuração no banco de dados"""
        self.db.execute_query(
            'INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)',
            (key, value)
        )
        self.settings[key] = value
    def get(self, key, default=None):
        """Obtém o valor de uma configuração"""
        return self.settings.get(key, default)
    def get_bool(self, key, default=False):
        """Obtém um valor booleano das configurações"""
        val = self.settings.get(key, str(default))
        return val.lower() in ('1', 'true', 'yes')
class ThemeManager:
    """Classe para gerenciamento completo de temas visuais"""

    def __init__(self, settings):
        self.settings = settings
        self.current_theme = self.settings.get('theme', 'dark')
        self.load_themes()
    def load_themes(self):
        """Carrega todos os temas disponíveis"""
        self.themes = {
            'dark': {
                'background': '#2D2D2D',
                'foreground': '#E0E0E0',
                'primary': '#3498DB',
                'secondary': '#2980B9',
                'success': '#2ECC71',
                'danger': '#E74C3C',
                'warning': '#F39C12',
                'card_bg': '#3D3D3D',
                'card_border': '#4D4D4D',
                'text': '#FFFFFF',
                'text_secondary': '#B0B0B0',
                'highlight': '#4A90E2',
                'disabled': '#555555'
            },
            'light': {
                'background': '#F5F5F5',
                'foreground': '#333333',
                'primary': '#4285F4',
                'secondary': '#3367D6',
                'success': '#0F9D58',
                'danger': '#DB4437',
                'warning': '#F4B400',
                'card_bg': '#FFFFFF',
                'card_border': '#E0E0E0',
                'text': '#333333',
                'text_secondary': '#666666',
                'highlight': '#1A73E8',
                'disabled': '#CCCCCC'
            },
            'blue': {
                'background': '#1A2930',
                'foreground': '#FFFFFF',
                'primary': '#4A90E2',
                'secondary': '#357ABD',
                'success': '#5CB85C',
                'danger': '#D9534F',
                'warning': '#F0AD4E',
                'card_bg': '#22333B',
                'card_border': '#2C3E50',
                'text': '#FFFFFF',
                'text_secondary': '#CCCCCC',
                'highlight': '#5BC0DE',
                'disabled': '#555555'
            }
        }
    def apply_theme(self, app, theme_name=None):
        """Aplica um tema ao aplicativo"""
        if theme_name is None:
            theme_name = self.current_theme
        else:
            self.current_theme = theme_name
            self.settings.save_setting('theme', theme_name)

        theme = self.themes.get(theme_name, self.themes['dark'])

        # Aplicar estilo global
        stylesheet = f"""
            QMainWindow, QDialog {{
                background-color: {theme['background']};
                color: {theme['text']};
                font-family: '{self.settings.get('font_family', 'Segoe UI')}';
                font-size: {self.settings.get('font_size', '12')}px;
            }}

            QPushButton {{
                background-color: {theme['primary']};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }}

            QPushButton:hover {{
                background-color: {theme['secondary']};
            }}

            QPushButton:disabled {{
                background-color: {theme['disabled']};
                color: {theme['text_secondary']};
            }}

            QLineEdit, QTextEdit, QComboBox, QListWidget, QTableWidget {{
                background-color: {theme['card_bg']};
                color: {theme['text']};
                border: 1px solid {theme['card_border']};
                border-radius: 4px;
                padding: 6px;
            }}

            QTabWidget::pane {{
                border: 1px solid {theme['card_border']};
                background: {theme['background']};
            }}

            QTabBar::tab {{
                background: {theme['card_bg']};
                color: {theme['text']};
                padding: 8px;
                border: 1px solid {theme['card_border']};
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}

            QTabBar::tab:selected {{
                background: {theme['primary']};
                color: white;
            }}

            QGroupBox {{
                border: 1px solid {theme['card_border']};
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 15px;
            }}

            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
                color: {theme['text']};
            }}

            QStatusBar {{
                background-color: {theme['card_bg']};
                color: {theme['text']};
                border-top: 1px solid {theme['card_border']};
            }}

            QToolBar {{
                background-color: {theme['card_bg']};
                border: none;
                padding: 2px;
                spacing: 5px;
            }}

            QMenu {{
                background-color: {theme['card_bg']};
                color: {theme['text']};
                border: 1px solid {theme['card_border']};
            }}

            QMenu::item:selected {{
                background-color: {theme['primary']};
                color: white;
            }}

            QScrollBar:vertical {{
                border: none;
                background: {theme['background']};
                width: 10px;
                margin: 0px;
            }}

            QScrollBar::handle:vertical {{
                background: {theme['primary']};
                min-height: 20px;
                border-radius: 5px;
            }}

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                background: none;
            }}

            QListWidget::item {{
                padding: 5px;
            }}

            QListWidget::item:selected {{
                background-color: {theme['primary']};
                color: white;
                border-radius: 3px;
            }}

            QTableWidget {{
                gridline-color: {theme['card_border']};
                selection-background-color: {theme['primary']};
                selection-color: white;
            }}

            QHeaderView::section {{
                background-color: {theme['primary']};
                color: white;
                padding: 5px;
                border: none;
            }}

            QSplitter::handle {{
                background: {theme['card_border']};
                width: 5px;
            }}
        """

        app.setStyleSheet(stylesheet)
class NotificationManager:
    """Classe para gerenciamento de notificações do sistema"""
    def __init__(self, main_window):
        self.main_window = main_window
        self.tray_icon = QSystemTrayIcon(QIcon(":/icons/notification.png"), self.main_window)

        # Criar menu de contexto para o ícone da bandeja
        tray_menu = QMenu()
        show_action = tray_menu.addAction("Mostrar")
        show_action.triggered.connect(self.main_window.show)
        exit_action = tray_menu.addAction("Sair")
        exit_action.triggered.connect(self.main_window.close)
        self.tray_icon.setContextMenu(tray_menu)

        self.tray_icon.show()
    def show_notification(self, title, message, timeout=5000):
        """Mostra uma notificação na bandeja do sistema"""
        if self.main_window.settings.get_bool('enable_notifications', True):
            self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, timeout)
class ProjectManager:
    """Classe para gerenciamento completo de projetos"""
    def __init__(self, db):
        self.db = db
    def create_project(self, name, project_type, base_dir, subfolders, description, tags=""):
        """Cria um novo projeto"""
        try:
            # Criar diretório base
            os.makedirs(base_dir, exist_ok=True)

            # Criar subpastas
            if subfolders:
                for folder in subfolders.split('\n'):
                    if folder.strip():
                        os.makedirs(os.path.join(base_dir, folder.strip()), exist_ok=True)

            # Salvar no banco de dados
            project_id = self.db.execute_query(
                '''INSERT INTO projects (name, type, base_dir, subfolders, description, tags) 
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (name, project_type, base_dir, subfolders, description, tags)
            )

            # Registrar no histórico
            self.db.execute_query(
                '''INSERT INTO history (action, module, details) 
                   VALUES (?, ?, ?)''',
                ('create', 'projects', f'Created project {name}')
            )

            return project_id
        except Exception as e:
            raise Exception(f"Falha ao criar projeto: {str(e)}")
    def get_projects(self, filter_type="all", search_query=""):
        """Obtém projetos com filtro e pesquisa"""
        query = "SELECT * FROM projects"
        params = []

        if filter_type != "all":
            if filter_type == "favorites":
                query += " WHERE is_favorite = 1"
            else:
                query += " WHERE type = ?"
                params.append(filter_type)

        if search_query:
            if "WHERE" in query:
                query += " AND"
            else:
                query += " WHERE"
            query += " (name LIKE ? OR description LIKE ? OR tags LIKE ?)"
            params.extend([f"%{search_query}%"] * 3)

        query += " ORDER BY name"
        return self.db.execute_query(query, params, fetchall=True)
    def update_project(self, project_id, **kwargs):
        """Atualiza um projeto existente"""
        set_clause = ", ".join([f"{k} = ?" for k in kwargs])
        params = list(kwargs.values()) + [project_id]

        self.db.execute_query(
            f"UPDATE projects SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            params
        )

        # Registrar no histórico
        self.db.execute_query(
            '''INSERT INTO history (action, module, details) 
               VALUES (?, ?, ?)''',
            ('update', 'projects', f'Updated project ID {project_id}')
        )
    def delete_project(self, project_id):
        """Exclui um projeto"""
        self.db.execute_query("DELETE FROM projects WHERE id = ?", (project_id,))

        # Registrar no histórico
        self.db.execute_query(
            '''INSERT INTO history (action, module, details) 
               VALUES (?, ?, ?)''',
            ('delete', 'projects', f'Deleted project ID {project_id}')
        )
class SpreadsheetManager:
    """Classe para gerenciamento completo de planilhas"""
    def __init__(self, db):
        self.db = db
    def create_spreadsheet(self, name, headers, data=None):
        """Cria uma nova planilha"""
        headers_str = "\n".join(headers)
        data_str = json.dumps(data or [])

        spreadsheet_id = self.db.execute_query(
            '''INSERT INTO spreadsheets (name, headers, data) 
               VALUES (?, ?, ?)''',
            (name, headers_str, data_str)
        )

        # Registrar no histórico
        self.db.execute_query(
            '''INSERT INTO history (action, module, details) 
               VALUES (?, ?, ?)''',
            ('create', 'spreadsheets', f'Created spreadsheet {name}')
        )

        return spreadsheet_id
    def get_spreadsheets(self, search_query=""):
        """Obtém planilhas com pesquisa"""
        query = "SELECT * FROM spreadsheets"
        params = []

        if search_query:
            query += " WHERE name LIKE ?"
            params.append(f"%{search_query}%")

        query += " ORDER BY name"
        return self.db.execute_query(query, params, fetchall=True)
    def update_spreadsheet(self, spreadsheet_id, **kwargs):
        """Atualiza uma planilha existente"""
        set_clause = ", ".join([f"{k} = ?" for k in kwargs])
        params = list(kwargs.values()) + [spreadsheet_id]

        self.db.execute_query(
            f"UPDATE spreadsheets SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            params
        )

        # Registrar no histórico
        self.db.execute_query(
            '''INSERT INTO history (action, module, details) 
               VALUES (?, ?, ?)''',
            ('update', 'spreadsheets', f'Updated spreadsheet ID {spreadsheet_id}')
        )
def export_to_csv(self, spreadsheet_id, file_path):
    """Exporta planilha para CSV"""
    spreadsheet = self.db.execute_query(
        "SELECT headers, data FROM spreadsheets WHERE id = ?",
        (spreadsheet_id,),
        fetchone=True
    )

    if not spreadsheet:
        raise Exception("Planilha não encontrada")

    try:
        headers = spreadsheet[0].split('\n')
        data = json.loads(spreadsheet[1]) if spreadsheet[1] else []

        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

            if data:
                writer.writerows(data)

        self.db.execute_query(
            '''INSERT INTO history (action, module, details) 
               VALUES (?, ?, ?)''',
            ('export', 'spreadsheets', f'Exported spreadsheet ID {spreadsheet_id} to CSV')
        )

        return True
    except Exception as e:
        raise Exception(f"Erro ao exportar para CSV: {str(e)}")
class NotesManager:
    """Classe para gerenciamento completo de anotações"""
    def __init__(self, db):
        self.db = db
    def create_note(self, title, content, tags=""):
        """Cria uma nova anotação"""
        note_id = self.db.execute_query(
            '''INSERT INTO notes (title, content, tags) 
               VALUES (?, ?, ?)''',
            (title, content, tags)
        )

        # Registrar no histórico
        self.db.execute_query(
            '''INSERT INTO history (action, module, details) 
               VALUES (?, ?, ?)''',
            ('create', 'notes', f'Created note {title}')
        )

        return note_id
    def get_notes(self, search_query="", favorite_only=False):
        """Obtém anotações com pesquisa"""
        query = "SELECT * FROM notes"
        params = []

        conditions = []
        if search_query:
            conditions.append("(title LIKE ? OR content LIKE ? OR tags LIKE ?)")
            params.extend([f"%{search_query}%"] * 3)

        if favorite_only:
            conditions.append("is_favorite = 1")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY title"
        return self.db.execute_query(query, params, fetchall=True)
    def update_note(self, note_id, **kwargs):
        """Atualiza uma anotação existente"""
        set_clause = ", ".join([f"{k} = ?" for k in kwargs])
        params = list(kwargs.values()) + [note_id]

        self.db.execute_query(
            f"UPDATE notes SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            params
        )

        # Registrar no histórico
        self.db.execute_query(
            '''INSERT INTO history (action, module, details) 
               VALUES (?, ?, ?)''',
            ('update', 'notes', f'Updated note ID {note_id}')
        )
    def export_to_markdown(self, note_id, file_path):
        """Exporta anotação para Markdown"""
        note = self.db.execute_query(
            "SELECT title, content FROM notes WHERE id = ?",
            (note_id,),
            fetchone=True
        )

        if not note:
            raise Exception("Anotação não encontrada")

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# {note[0]}\n\n")  # Título
                f.write(note[1])  # Conteúdo

            self.db.execute_query(
                '''INSERT INTO history (action, module, details) 
                   VALUES (?, ?, ?)''',
                ('export', 'notes', f'Exported note ID {note_id} to Markdown')
            )

            return True
        except Exception as e:
            raise Exception(f"Erro ao exportar para Markdown: {str(e)}")
class UtilitiesManager:
    """Classe para gerenciamento completo de utilitários"""
    def __init__(self, db):
        self.db = db
    def add_utility(self, name, utility_type, path=None, command=None):
        """Adiciona um novo utilitário"""
        utility_id = self.db.execute_query(
            '''INSERT INTO utilities (name, type, path, command) 
               VALUES (?, ?, ?, ?)''',
            (name, utility_type, path, command)
        )

        # Registrar no histórico
        self.db.execute_query(
            '''INSERT INTO history (action, module, details) 
               VALUES (?, ?, ?)''',
            ('add', 'utilities', f'Added utility {name}')
        )

        return utility_id
    def get_utilities(self, utility_type=None, search_query=""):
        """Obtém utilitários com filtro e pesquisa"""
        query = "SELECT * FROM utilities"
        params = []

        conditions = []
        if utility_type:
            conditions.append("type = ?")
            params.append(utility_type)

        if search_query:
            conditions.append("name LIKE ?")
            params.append(f"%{search_query}%")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY name"
        return self.db.execute_query(query, params, fetchall=True)
    def execute_utility(self, utility_id):
        """Executa um utilitário"""
        utility = self.db.execute_query(
            "SELECT type, path, command FROM utilities WHERE id = ?",
            (utility_id,),
            fetchone=True
        )

        if not utility:
            raise Exception("Utilitário não encontrado")

        utility_type, path, command = utility

        try:
            if utility_type == "app" and path:
                if os.path.exists(path):
                    if sys.platform == "win32":
                        os.startfile(path)
                    elif sys.platform == "darwin":
                        subprocess.Popen(["open", path])
                    else:
                        subprocess.Popen(["xdg-open", path])
                else:
                    raise Exception("Caminho do aplicativo não encontrado")

            elif utility_type == "site" and path:
                if not path.startswith(('http://', 'https://')):
                    path = 'https://' + path
                QDesktopServices.openUrl(QUrl(path))

            elif utility_type == "command" and command:
                subprocess.Popen(command, shell=True)

            self.db.execute_query(
                '''INSERT INTO history (action, module, details) 
                   VALUES (?, ?, ?)''',
                ('execute', 'utilities', f'Executed utility ID {utility_id}')
            )

            return True
        except Exception as e:
            raise Exception(f"Falha ao executar utilitário: {str(e)}")
class CommandsManager:
    """Classe para gerenciamento completo de comandos personalizados"""
    def __init__(self, db):
        self.db = db
    def add_command(self, name, command, category=None, tags=None):
        """Adiciona um novo comando personalizado"""
        command_id = self.db.execute_query(
            '''INSERT INTO custom_commands (name, command, category, tags) 
               VALUES (?, ?, ?, ?)''',
            (name, command, category, tags)
        )

        # Registrar no histórico
        self.db.execute_query(
            '''INSERT INTO history (action, module, details) 
               VALUES (?, ?, ?)''',
            ('add', 'commands', f'Added command {name}')
        )

        return command_id
    def get_commands(self, search_query=""):
        """Obtém comandos com pesquisa"""
        query = "SELECT * FROM custom_commands"
        params = []

        if search_query:
            query += " WHERE name LIKE ? OR command LIKE ? OR category LIKE ? OR tags LIKE ?"
            params.extend([f"%{search_query}%"] * 4)

        query += " ORDER BY name"
        return self.db.execute_query(query, params, fetchall=True)
    def execute_command(self, command_id):
        """Executa um comando personalizado"""
        command = self.db.execute_query(
            "SELECT command FROM custom_commands WHERE id = ?",
            (command_id,),
            fetchone=True
        )

        if not command or not command[0]:
            raise Exception("Comando não encontrado ou vazio")

        try:
            process = subprocess.Popen(
                command[0],
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()

            self.db.execute_query(
                '''INSERT INTO history (action, module, details) 
                   VALUES (?, ?, ?)''',
                ('execute', 'commands', f'Executed command ID {command_id}')
            )

            if stderr:
                raise Exception(stderr)

            return stdout
        except Exception as e:
            raise Exception(f"Falha ao executar comando: {str(e)}")
class RemindersManager:
    """Classe para gerenciamento completo de lembretes"""
    def __init__(self, db):
        self.db = db
    def add_reminder(self, title, description, due_date):
        """Adiciona um novo lembrete"""
        reminder_id = self.db.execute_query(
            '''INSERT INTO reminders (title, description, due_date) 
               VALUES (?, ?, ?)''',
            (title, description, due_date)
        )

        # Registrar no histórico
        self.db.execute_query(
            '''INSERT INTO history (action, module, details) 
               VALUES (?, ?, ?)''',
            ('add', 'reminders', f'Added reminder {title}')
        )

        return reminder_id
    def get_reminders(self, upcoming_only=True):
        """Obtém lembretes"""
        query = "SELECT * FROM reminders"

        if upcoming_only:
            query += " WHERE is_completed = 0 AND due_date >= datetime('now')"

        query += " ORDER BY due_date"
        return self.db.execute_query(query, fetchall=True)
    def mark_completed(self, reminder_id):
        """Marca um lembrete como concluído"""
        self.db.execute_query(
            "UPDATE reminders SET is_completed = 1 WHERE id = ?",
            (reminder_id,)
        )

        # Registrar no histórico
        self.db.execute_query(
            '''INSERT INTO history (action, module, details) 
               VALUES (?, ?, ?)''',
            ('complete', 'reminders', f'Completed reminder ID {reminder_id}')
        )
class BackupManager:
    """Classe para gerenciamento completo de backups"""
    def __init__(self, db):
        self.db = db
    def create_backup(self, backup_dir):
        """Cria um backup completo do banco de dados"""
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"automatepro_backup_{timestamp}.db")

        # Copiar o arquivo do banco de dados
        shutil.copy2(self.db.db_path, backup_file)

        # Registrar no histórico
        self.db.execute_query(
            '''INSERT INTO history (action, module, details) 
               VALUES (?, ?, ?)''',
            ('backup', 'system', 'Created system backup')
        )

        return backup_file
    def restore_backup(self, backup_file):
        """Restaura um backup"""
        if not os.path.exists(backup_file):
            raise Exception("Arquivo de backup não encontrado")

        # Fazer backup do banco atual antes de restaurar
        current_backup = os.path.join(
            os.path.dirname(self.db.db_path),
            f"automatepro_pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        )
        shutil.copy2(self.db.db_path, current_backup)

        # Restaurar o backup
        shutil.copy2(backup_file, self.db.db_path)

        # Registrar no histórico
        self.db.execute_query(
            '''INSERT INTO history (action, module, details) 
               VALUES (?, ?, ?)''',
            ('restore', 'system', 'Restored system from backup')
        )
class MainWindow(QMainWindow):
    """Classe principal da janela do aplicativo"""

    def __init__(self):
        super().__init__()

        # Configurações iniciais
        self.settings = SettingsManager()
        self.db = DatabaseManager()
        self.theme_manager = ThemeManager(self.settings)

        # Inicializar gerenciadores
        self.project_manager = ProjectManager(self.db)
        self.spreadsheet_manager = SpreadsheetManager(self.db)
        self.notes_manager = NotesManager(self.db)
        self.utilities_manager = UtilitiesManager(self.db)
        self.commands_manager = CommandsManager(self.db)
        self.reminders_manager = RemindersManager(self.db)
        self.backup_manager = BackupManager(self.db)
        self.download_manager = DownloadManager(self.db)

        # Configurar janela principal
        self.setWindowTitle("Automate Pro")
        self.setGeometry(100, 100, 1200, 800)

        # Criar componentes da interface
        self.create_actions()
        self.create_menu()
        self.create_toolbar()
        self.create_statusbar()
        self.create_main_layout()

        # Configurar sistema de notificações
        self.notification_manager = NotificationManager(self)

        # Configurar timer para verificar lembretes
        self.reminder_timer = QTimer(self)
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start(60000)  # Verificar a cada minuto

        # Configurar timer para backups automáticos
        if self.settings.get_bool('auto_backup'):
            self.backup_timer = QTimer(self)
            self.backup_timer.timeout.connect(self.run_auto_backup)
            interval = int(self.settings.get('backup_interval', '7')) * 24 * 3600 * 1000
            self.backup_timer.start(interval)

        # Aplicar tema
        self.theme_manager.apply_theme(QApplication.instance())

        # Carregar dados iniciais
        self.load_initial_data()

    def create_actions(self):
        """Cria ações para menus e atalhos"""
        # Ações de arquivo
        self.new_project_action = QAction(QIcon.fromTheme("document-new"), "&Novo Projeto", self)
        self.new_project_action.setShortcut("Ctrl+N")
        self.new_project_action.triggered.connect(self.show_new_project)

        self.exit_action = QAction(QIcon.fromTheme("application-exit"), "&Sair", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.triggered.connect(self.close)

        # Ações de edição
        self.settings_action = QAction(QIcon.fromTheme("preferences-system"), "&Configurações", self)
        self.settings_action.setShortcut("Ctrl+,")
        self.settings_action.triggered.connect(self.show_settings)

        # Ações de ajuda
        self.about_action = QAction(QIcon.fromTheme("help-about"), "&Sobre", self)
        self.about_action.triggered.connect(self.show_about)

        # Ações de tema
        self.dark_theme_action = QAction("Tema Escuro", self)
        self.dark_theme_action.triggered.connect(lambda: self.change_theme('dark'))

        self.light_theme_action = QAction("Tema Claro", self)
        self.light_theme_action.triggered.connect(lambda: self.change_theme('light'))

        self.blue_theme_action = QAction("Tema Azul", self)
        self.blue_theme_action.triggered.connect(lambda: self.change_theme('blue'))

        # Ações de backup
        self.backup_action = QAction(QIcon.fromTheme("document-save"), "&Backup", self)
        self.backup_action.setShortcut("Ctrl+B")
        self.backup_action.triggered.connect(self.create_manual_backup)

        # Atalhos globais
        self.search_shortcut = QShortcut(QKeySequence("Ctrl+F"), self)
        self.search_shortcut.activated.connect(self.focus_search)

        # Adicione esta nova ação para limpeza do sistema
        self.clean_system_action = QAction(QIcon.fromTheme("edit-clear"), "&Limpar Sistema", self)
        self.clean_system_action.setStatusTip("Limpa diretórios temporários do sistema")
        self.clean_system_action.triggered.connect(self.clean_system)

    def create_menu(self):
        """Cria a barra de menus"""
        menubar = self.menuBar()

        # Menu Arquivo
        # Menu Arquivo (adicione na posição adequada)
        file_menu = menubar.addMenu("&Arquivo")
        file_menu.addAction(self.new_project_action)
        file_menu.addAction(self.backup_action)
        file_menu.addSeparator()
        file_menu.addAction(self.clean_system_action)  # Adicione esta linha
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        # Menu Editar
        edit_menu = menubar.addMenu("&Editar")
        edit_menu.addAction(self.settings_action)

        # Menu Tema
        theme_menu = menubar.addMenu("&Tema")
        theme_menu.addAction(self.dark_theme_action)
        theme_menu.addAction(self.light_theme_action)
        theme_menu.addAction(self.blue_theme_action)

        # Menu Ajuda
        help_menu = menubar.addMenu("&Ajuda")
        help_menu.addAction(self.about_action)

    def create_toolbar(self):
        """Cria a barra de ferramentas"""
        toolbar = QToolBar("Barra de Ferramentas")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)

        toolbar.addAction(self.new_project_action)
        toolbar.addSeparator()
        toolbar.addAction(self.settings_action)
        toolbar.addAction(self.backup_action)
        toolbar.addAction(self.clean_system_action)  # Adicione esta linha

        # Adicionar campo de busca global
        self.global_search = QLineEdit()
        self.global_search.setPlaceholderText("Pesquisar...")
        self.global_search.setClearButtonEnabled(True)
        self.global_search.returnPressed.connect(self.perform_global_search)
        toolbar.addWidget(self.global_search)

    def create_statusbar(self):
        """Cria a barra de status"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)

        # Mostrar mensagem de status inicial
        self.statusbar.showMessage("Pronto", 3000)

        # Adicionar widgets à barra de status
        self.user_label = QLabel("Usuário: admin")
        self.statusbar.addPermanentWidget(self.user_label)

        self.db_status = QLabel("✔ Banco de dados")
        self.statusbar.addPermanentWidget(self.db_status)

    def create_main_layout(self):
        """Cria o layout principal da janela"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Layout principal
        main_layout = QHBoxLayout(central_widget)

        # Barra lateral (menu de navegação)
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar.addItems(["Início", "Projetos", "Planilhas", "Developer", "Utilitários",
                               "PDF Convert", "Image Convert", "Anotações", "Comandos", "Configurações"])
        self.sidebar.currentRowChanged.connect(self.change_page)

        # Área de conteúdo (stacked widget)
        self.content_area = QStackedWidget()

        # Criar páginas do sistema
        self.create_home_page()
        self.create_projects_page()
        self.create_spreadsheets_page()
        self.create_developer_page()
        self.create_utilities_page()
        self.create_pdf_convert_page()
        self.create_image_convert_page()
        self.create_notes_page()
        self.create_commands_page()
        self.create_settings_page()
        self.create_downloads_page()

        # Adicionar widgets ao layout principal
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_area, stretch=1)

        # Selecionar a primeira página
        self.sidebar.setCurrentRow(0)

    # Adicionar este método à classe MainWindow
    def create_downloads_page(self):
        """Cria a página de gerenciamento de downloads"""
        self.downloads_page = DownloadsPage(self)
        self.content_area.addWidget(self.downloads_page)

        # Adicionar à barra lateral
        self.sidebar.addItem("Downloads")

        # Ajustar o índice se necessário
        self.sidebar.setCurrentRow(0)

    def create_home_page(self):
        """Cria a página inicial (dashboard)"""
        page = QWidget()
        layout = QVBoxLayout(page)

        # Título
        title = QLabel("Dashboard")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)

        # Cards de resumo
        cards_layout = QHBoxLayout()

        # Card de projetos
        projects_card = QGroupBox("Projetos")
        projects_layout = QVBoxLayout()
        self.projects_count_label = QLabel("0")
        self.projects_count_label.setStyleSheet("font-size: 32px; font-weight: bold;")
        projects_layout.addWidget(self.projects_count_label, alignment=Qt.AlignmentFlag.AlignCenter)
        projects_layout.addWidget(QLabel("Projetos ativos"))
        projects_card.setLayout(projects_layout)
        cards_layout.addWidget(projects_card)

        # Card de planilhas
        spreadsheets_card = QGroupBox("Planilhas")
        spreadsheets_layout = QVBoxLayout()
        self.spreadsheets_count_label = QLabel("0")
        self.spreadsheets_count_label.setStyleSheet("font-size: 32px; font-weight: bold;")
        spreadsheets_layout.addWidget(self.spreadsheets_count_label, alignment=Qt.AlignmentFlag.AlignCenter)
        spreadsheets_layout.addWidget(QLabel("Planilhas criadas"))
        spreadsheets_card.setLayout(spreadsheets_layout)
        cards_layout.addWidget(spreadsheets_card)

        # Card de anotações
        notes_card = QGroupBox("Anotações")
        notes_layout = QVBoxLayout()
        self.notes_count_label = QLabel("0")
        self.notes_count_label.setStyleSheet("font-size: 32px; font-weight: bold;")
        notes_layout.addWidget(self.notes_count_label, alignment=Qt.AlignmentFlag.AlignCenter)
        notes_layout.addWidget(QLabel("Anotações salvas"))
        notes_card.setLayout(notes_layout)
        cards_layout.addWidget(notes_card)

        # Card de utilitários
        utilities_card = QGroupBox("Utilitários")
        utilities_layout = QVBoxLayout()
        self.utilities_count_label = QLabel("0")
        self.utilities_count_label.setStyleSheet("font-size: 32px; font-weight: bold;")
        utilities_layout.addWidget(self.utilities_count_label, alignment=Qt.AlignmentFlag.AlignCenter)
        utilities_layout.addWidget(QLabel("Utilitários cadastrados"))
        utilities_card.setLayout(utilities_layout)
        cards_layout.addWidget(utilities_card)

        layout.addLayout(cards_layout)

        # Seção de projetos recentes
        recent_projects_group = QGroupBox("Projetos Recentes")
        recent_projects_layout = QVBoxLayout()

        self.recent_projects_list = QListWidget()
        self.recent_projects_list.itemDoubleClicked.connect(self.open_project_from_list)
        recent_projects_layout.addWidget(self.recent_projects_list)

        recent_projects_group.setLayout(recent_projects_layout)
        layout.addWidget(recent_projects_group)

        # Seção de lembretes
        reminders_group = QGroupBox("Lembretes Pendentes")
        reminders_layout = QVBoxLayout()

        self.reminders_list = QListWidget()
        reminders_layout.addWidget(self.reminders_list)

        reminders_group.setLayout(reminders_layout)
        layout.addWidget(reminders_group)

        # Adicionar página ao stacked widget
        self.content_area.addWidget(page)

    def create_projects_page(self):
        """Cria a página de gerenciamento de projetos"""
        page = QWidget()
        layout = QVBoxLayout(page)

        # Título
        title = QLabel("Gerenciador de Projetos")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)

        # Abas
        self.projects_tab = QTabWidget()
        self.projects_new_tab = QWidget()
        self.projects_existing_tab = QWidget()

        self.projects_tab.addTab(self.projects_new_tab, "Novo Projeto")
        self.projects_tab.addTab(self.projects_existing_tab, "Projetos Existentes")

        # Conteúdo da aba "Novo Projeto"
        new_project_layout = QFormLayout(self.projects_new_tab)

        self.project_name_input = QLineEdit()
        self.project_type_combo = QComboBox()
        self.project_type_combo.addItems(["Web", "Desktop", "Mobile", "Script", "Outro"])

        self.project_dir_input = QLineEdit()
        browse_button = QPushButton("Selecionar...")
        browse_button.clicked.connect(self.browse_project_dir)

        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.project_dir_input)
        dir_layout.addWidget(browse_button)

        self.project_subfolders_input = QTextEdit()
        self.project_subfolders_input.setPlaceholderText("Uma pasta por linha")

        self.project_description_input = QTextEdit()
        self.project_tags_input = QLineEdit()
        self.project_tags_input.setPlaceholderText("tags, separadas, por, vírgula")

        new_project_layout.addRow("Nome do Projeto:", self.project_name_input)
        new_project_layout.addRow("Tipo do Projeto:", self.project_type_combo)
        new_project_layout.addRow("Diretório Base:", dir_layout)
        new_project_layout.addRow("Subpastas:", self.project_subfolders_input)
        new_project_layout.addRow("Tags:", self.project_tags_input)
        new_project_layout.addRow("Descrição:", self.project_description_input)

        # Botões de ação
        buttons_layout = QHBoxLayout()
        create_button = QPushButton("Criar Projeto")
        create_button.clicked.connect(self.create_project)
        clear_button = QPushButton("Limpar")
        clear_button.clicked.connect(self.clear_project_form)

        buttons_layout.addWidget(create_button)
        buttons_layout.addWidget(clear_button)
        new_project_layout.addRow(buttons_layout)

        # Conteúdo da aba "Projetos Existentes"
        existing_projects_layout = QVBoxLayout(self.projects_existing_tab)

        # Barra de pesquisa e filtros
        search_layout = QHBoxLayout()
        self.projects_search_input = QLineEdit()
        self.projects_search_input.setPlaceholderText("Pesquisar projetos...")
        self.projects_search_input.textChanged.connect(self.filter_projects)

        self.projects_filter_combo = QComboBox()
        self.projects_filter_combo.addItems(["Todos", "Favoritos", "Web", "Desktop", "Mobile", "Script", "Outro"])
        self.projects_filter_combo.currentTextChanged.connect(self.filter_projects)

        search_layout.addWidget(self.projects_search_input)
        search_layout.addWidget(self.projects_filter_combo)
        existing_projects_layout.addLayout(search_layout)

        # Lista de projetos
        self.projects_list = QListWidget()
        self.projects_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.projects_list.itemDoubleClicked.connect(self.open_project)
        existing_projects_layout.addWidget(self.projects_list)

        # Botões de ação
        projects_buttons_layout = QHBoxLayout()
        open_project_button = QPushButton("Abrir")
        open_project_button.clicked.connect(self.open_selected_project)
        edit_project_button = QPushButton("Editar")
        edit_project_button.clicked.connect(self.edit_project)
        delete_project_button = QPushButton("Excluir")
        delete_project_button.clicked.connect(self.delete_project)
        export_project_button = QPushButton("Exportar")
        export_project_button.clicked.connect(self.export_project)

        projects_buttons_layout.addWidget(open_project_button)
        projects_buttons_layout.addWidget(edit_project_button)
        projects_buttons_layout.addWidget(delete_project_button)
        projects_buttons_layout.addWidget(export_project_button)
        existing_projects_layout.addLayout(projects_buttons_layout)

        layout.addWidget(self.projects_tab)
        self.content_area.addWidget(page)

    def create_spreadsheets_page(self):
        """Cria a página de gerenciamento de planilhas"""
        page = QWidget()
        layout = QVBoxLayout(page)

        # Título
        title = QLabel("Gerenciador de Planilhas")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)

        # Abas
        self.spreadsheets_tab = QTabWidget()
        self.spreadsheets_new_tab = QWidget()
        self.spreadsheets_existing_tab = QWidget()

        self.spreadsheets_tab.addTab(self.spreadsheets_new_tab, "Nova Planilha")
        self.spreadsheets_tab.addTab(self.spreadsheets_existing_tab, "Planilhas Existentes")

        # Conteúdo da aba "Nova Planilha"
        new_spreadsheet_layout = QFormLayout(self.spreadsheets_new_tab)

        self.spreadsheet_name_input = QLineEdit()
        self.spreadsheet_headers_input = QTextEdit()
        self.spreadsheet_headers_input.setPlaceholderText("Um cabeçalho por linha")

        new_spreadsheet_layout.addRow("Nome da Planilha:", self.spreadsheet_name_input)
        new_spreadsheet_layout.addRow("Cabeçalhos:", self.spreadsheet_headers_input)

        # Botões de ação
        buttons_layout = QHBoxLayout()
        create_button = QPushButton("Criar Planilha")
        create_button.clicked.connect(self.create_spreadsheet)
        clear_button = QPushButton("Limpar")
        clear_button.clicked.connect(self.clear_spreadsheet_form)

        buttons_layout.addWidget(create_button)
        buttons_layout.addWidget(clear_button)
        new_spreadsheet_layout.addRow(buttons_layout)

        # Conteúdo da aba "Planilhas Existentes"
        existing_spreadsheets_layout = QVBoxLayout(self.spreadsheets_existing_tab)

        # Barra de pesquisa
        search_layout = QHBoxLayout()
        self.spreadsheets_search_input = QLineEdit()
        self.spreadsheets_search_input.setPlaceholderText("Pesquisar planilhas...")
        self.spreadsheets_search_input.textChanged.connect(self.filter_spreadsheets)

        search_layout.addWidget(self.spreadsheets_search_input)
        existing_spreadsheets_layout.addLayout(search_layout)

        # Lista de planilhas
        self.spreadsheets_list = QListWidget()
        self.spreadsheets_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.spreadsheets_list.itemDoubleClicked.connect(self.open_spreadsheet)
        existing_spreadsheets_layout.addWidget(self.spreadsheets_list)

        # Visualização da tabela
        self.spreadsheet_table = QTableWidget()
        self.spreadsheet_table.setColumnCount(0)
        self.spreadsheet_table.setRowCount(0)
        existing_spreadsheets_layout.addWidget(self.spreadsheet_table)

        # Botões de ação
        spreadsheets_buttons_layout = QHBoxLayout()
        open_spreadsheet_button = QPushButton("Abrir")
        open_spreadsheet_button.clicked.connect(self.open_selected_spreadsheet)
        edit_spreadsheet_button = QPushButton("Editar")
        edit_spreadsheet_button.clicked.connect(self.edit_spreadsheet)
        delete_spreadsheet_button = QPushButton("Excluir")
        delete_spreadsheet_button.clicked.connect(self.delete_spreadsheet)
        export_spreadsheet_button = QPushButton("Exportar")
        export_spreadsheet_button.clicked.connect(self.export_spreadsheet)

        spreadsheets_buttons_layout.addWidget(open_spreadsheet_button)
        spreadsheets_buttons_layout.addWidget(edit_spreadsheet_button)
        spreadsheets_buttons_layout.addWidget(delete_spreadsheet_button)
        spreadsheets_buttons_layout.addWidget(export_spreadsheet_button)
        existing_spreadsheets_layout.addLayout(spreadsheets_buttons_layout)

        layout.addWidget(self.spreadsheets_tab)
        self.content_area.addWidget(page)

    def create_developer_page(self):
        """Cria a página de ferramentas para desenvolvedores"""
        page = QWidget()
        layout = QVBoxLayout(page)

        # Título
        title = QLabel("Ferramentas para Desenvolvedor")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)

        # Formulário para novo projeto
        form_layout = QFormLayout()

        self.dev_project_name_input = QLineEdit()
        self.dev_project_type_combo = QComboBox()
        self.dev_project_type_combo.setEditable(True)  # Permite digitar novos tipos
        self.dev_project_type_combo.addItems([
            "React (Vite)",
            "React (Create-React-App)",
            "Vue",
            "Node.js",
            "Python",
            "HTML/CSS/JS",
            "Outro"
        ])

        self.dev_project_dir_input = QLineEdit()
        browse_dev_button = QPushButton("Selecionar...")
        browse_dev_button.clicked.connect(self.browse_dev_dir)

        dir_layout = QHBoxLayout()
        dir_layout.addWidget(self.dev_project_dir_input)
        dir_layout.addWidget(browse_dev_button)

        self.dev_package_manager_combo = QComboBox()
        self.dev_package_manager_combo.addItems(["npm", "yarn", "pnpm"])

        self.dev_install_deps_check = QCheckBox("Instalar dependências automaticamente")
        self.dev_install_deps_check.setChecked(True)

        form_layout.addRow("Nome do Projeto:", self.dev_project_name_input)
        form_layout.addRow("Tipo do Projeto:", self.dev_project_type_combo)
        form_layout.addRow("Gerenciador de Pacotes:", self.dev_package_manager_combo)
        form_layout.addRow("Diretório:", dir_layout)
        form_layout.addRow(self.dev_install_deps_check)

        # Botão de criação
        create_dev_button = QPushButton("Criar Projeto")
        create_dev_button.clicked.connect(self.create_dev_project)
        form_layout.addRow(create_dev_button)

        layout.addLayout(form_layout)

        # Terminal integrado
        terminal_group = QGroupBox("Terminal Integrado")
        terminal_layout = QVBoxLayout()

        self.terminal_output = QTextEdit()
        self.terminal_output.setReadOnly(True)
        self.terminal_output.setStyleSheet("font-family: monospace;")

        self.terminal_input = QLineEdit()
        self.terminal_input.setPlaceholderText("Digite um comando e pressione Enter...")
        self.terminal_input.returnPressed.connect(self.execute_terminal_command)

        terminal_buttons_layout = QHBoxLayout()
        clear_terminal_button = QPushButton("Limpar Terminal")
        clear_terminal_button.clicked.connect(self.clear_terminal)

        terminal_buttons_layout.addWidget(clear_terminal_button)

        terminal_layout.addWidget(self.terminal_output)
        terminal_layout.addWidget(self.terminal_input)
        terminal_layout.addLayout(terminal_buttons_layout)

        terminal_group.setLayout(terminal_layout)
        layout.addWidget(terminal_group)

        self.content_area.addWidget(page)
        return page

    def create_utilities_page(self):
        """Cria a página de utilitários"""
        page = QWidget()
        layout = QVBoxLayout(page)

        # Título
        title = QLabel("Utilitários")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)

        # Abas
        self.utilities_tab = QTabWidget()
        self.utilities_apps_tab = QWidget()
        self.utilities_sites_tab = QWidget()
        self.utilities_commands_tab = QWidget()

        self.utilities_tab.addTab(self.utilities_apps_tab, "Aplicativos")
        self.utilities_tab.addTab(self.utilities_sites_tab, "Sites")
        self.utilities_tab.addTab(self.utilities_commands_tab, "Comandos")

        # Conteúdo da aba "Aplicativos"
        apps_layout = QVBoxLayout(self.utilities_apps_tab)

        # Barra de pesquisa e adição
        apps_top_layout = QHBoxLayout()
        self.apps_search_input = QLineEdit()
        self.apps_search_input.setPlaceholderText("Pesquisar aplicativos...")
        self.apps_search_input.textChanged.connect(self.filter_apps)

        add_app_button = QPushButton("Adicionar Aplicativo")
        add_app_button.clicked.connect(self.show_add_app_dialog)

        apps_top_layout.addWidget(self.apps_search_input)
        apps_top_layout.addWidget(add_app_button)
        apps_layout.addLayout(apps_top_layout)

        # Lista de aplicativos
        self.apps_list = QListWidget()
        self.apps_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.apps_list.itemDoubleClicked.connect(self.run_app)
        apps_layout.addWidget(self.apps_list)

        # Botões de ação
        apps_buttons_layout = QHBoxLayout()
        run_app_button = QPushButton("Executar")
        run_app_button.clicked.connect(self.run_selected_app)
        edit_app_button = QPushButton("Editar")
        edit_app_button.clicked.connect(self.edit_app)
        delete_app_button = QPushButton("Excluir")
        delete_app_button.clicked.connect(self.delete_app)

        apps_buttons_layout.addWidget(run_app_button)
        apps_buttons_layout.addWidget(edit_app_button)
        apps_buttons_layout.addWidget(delete_app_button)
        apps_layout.addLayout(apps_buttons_layout)

        # Conteúdo da aba "Sites"
        sites_layout = QVBoxLayout(self.utilities_sites_tab)

        # Barra de pesquisa e adição
        sites_top_layout = QHBoxLayout()
        self.sites_search_input = QLineEdit()
        self.sites_search_input.setPlaceholderText("Pesquisar sites...")
        self.sites_search_input.textChanged.connect(self.filter_sites)

        add_site_button = QPushButton("Adicionar Site")
        add_site_button.clicked.connect(self.show_add_site_dialog)

        sites_top_layout.addWidget(self.sites_search_input)
        sites_top_layout.addWidget(add_site_button)
        sites_layout.addLayout(sites_top_layout)

        # Lista de sites
        self.sites_list = QListWidget()
        self.sites_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.sites_list.itemDoubleClicked.connect(self.open_site)
        sites_layout.addWidget(self.sites_list)

        # Botões de ação
        sites_buttons_layout = QHBoxLayout()
        open_site_button = QPushButton("Abrir")
        open_site_button.clicked.connect(self.open_selected_site)
        edit_site_button = QPushButton("Editar")
        edit_site_button.clicked.connect(self.edit_site)
        delete_site_button = QPushButton("Excluir")
        delete_site_button.clicked.connect(self.delete_site)

        sites_buttons_layout.addWidget(open_site_button)
        sites_buttons_layout.addWidget(edit_site_button)
        sites_buttons_layout.addWidget(delete_site_button)
        sites_layout.addLayout(sites_buttons_layout)

        # Conteúdo da aba "Comandos"
        commands_layout = QVBoxLayout(self.utilities_commands_tab)

        # Barra de pesquisa e adição
        commands_top_layout = QHBoxLayout()
        self.commands_search_input = QLineEdit()
        self.commands_search_input.setPlaceholderText("Pesquisar comandos...")
        self.commands_search_input.textChanged.connect(self.filter_commands)

        add_command_button = QPushButton("Adicionar Comando")
        add_command_button.clicked.connect(self.show_add_command_dialog)

        commands_top_layout.addWidget(self.commands_search_input)
        commands_top_layout.addWidget(add_command_button)
        commands_layout.addLayout(commands_top_layout)

        # Lista de comandos
        self.commands_list = QListWidget()
        self.commands_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.commands_list.itemDoubleClicked.connect(self.run_command)
        commands_layout.addWidget(self.commands_list)

        # Botões de ação
        commands_buttons_layout = QHBoxLayout()
        run_command_button = QPushButton("Executar")
        run_command_button.clicked.connect(self.run_selected_command)
        edit_command_button = QPushButton("Editar")
        edit_command_button.clicked.connect(self.edit_command)
        delete_command_button = QPushButton("Excluir")
        delete_command_button.clicked.connect(self.delete_command)

        commands_buttons_layout.addWidget(run_command_button)
        commands_buttons_layout.addWidget(edit_command_button)
        commands_buttons_layout.addWidget(delete_command_button)
        commands_layout.addLayout(commands_buttons_layout)

        layout.addWidget(self.utilities_tab)
        self.content_area.addWidget(page)

    def create_pdf_convert_page(self):
        """Cria a página de conversão de PDF"""
        page = QWidget()
        layout = QVBoxLayout(page)

        # Título
        title = QLabel("Editor e Conversor de PDF")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)

        # Controles de Fonte
        font_group = QGroupBox("Configurações de Fonte")
        font_layout = QFormLayout()

        # Seletor de fonte
        self.font_combo = QComboBox()
        self.load_fonts()

        # Botão para carregar fonte manualmente
        self.browse_font_button = QPushButton("Carregar Fonte...")
        self.browse_font_button.clicked.connect(self.browse_font_file)

        font_layout.addRow("Fonte:", self.font_combo)
        font_layout.addRow(self.browse_font_button)

        # Tamanho da fonte
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 72)
        self.font_size_spin.setValue(12)
        font_layout.addRow("Tamanho da Fonte:", self.font_size_spin)

        font_group.setLayout(font_layout)
        layout.addWidget(font_group)

        # Splitter para dividir a tela
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Editor de estrutura
        editor_group = QGroupBox("Editor")
        editor_layout = QVBoxLayout()

        # Barra de ferramentas do editor
        editor_toolbar = QToolBar()
        add_section_action = QAction(QIcon.fromTheme("list-add"), "Adicionar Seção", self)
        add_section_action.triggered.connect(self.add_pdf_section)
        editor_toolbar.addAction(add_section_action)

        add_image_action = QAction(QIcon.fromTheme("insert-image"), "Adicionar Imagem", self)
        add_image_action.triggered.connect(self.add_pdf_image)
        editor_toolbar.addAction(add_image_action)

        editor_layout.addWidget(editor_toolbar)

        # Área de edição
        self.pdf_structure_editor = QTextEdit()
        editor_layout.addWidget(self.pdf_structure_editor)

        # Botões de ação
        editor_buttons_layout = QHBoxLayout()
        save_structure_button = QPushButton("Salvar Estrutura")
        save_structure_button.clicked.connect(self.save_pdf_structure)
        export_pdf_button = QPushButton("Exportar PDF")
        export_pdf_button.clicked.connect(self.export_pdf)

        editor_buttons_layout.addWidget(save_structure_button)
        editor_buttons_layout.addWidget(export_pdf_button)

        editor_layout.addLayout(editor_buttons_layout)
        editor_group.setLayout(editor_layout)

        # Preview
        preview_group = QGroupBox("Pré-visualização")
        preview_layout = QVBoxLayout()

        self.pdf_preview = QTextEdit()
        self.pdf_preview.setReadOnly(True)

        preview_layout.addWidget(self.pdf_preview)
        preview_group.setLayout(preview_layout)

        # Adicionar grupos ao splitter
        splitter.addWidget(editor_group)
        splitter.addWidget(preview_group)
        splitter.setSizes([400, 400])

        layout.addWidget(splitter)
        self.content_area.addWidget(page)
        return page

    def load_fonts(self):
        """Carrega as fontes disponíveis no diretório fonts/"""
        fonts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
        self.available_fonts = []

        # Criar diretório se não existir
        if not os.path.exists(fonts_dir):
            os.makedirs(fonts_dir)

        # Carregar fontes do diretório
        for file in os.listdir(fonts_dir):
            if file.lower().endswith(('.ttf', '.otf')):
                self.available_fonts.append(file)

        # Adicionar ao combobox
        self.font_combo.clear()
        if self.available_fonts:
            self.font_combo.addItems(self.available_fonts)
        else:
            self.font_combo.addItem("Nenhuma fonte encontrada no diretório fonts/")

    def browse_font_file(self):
        """Abre diálogo para selecionar um arquivo de fonte"""
        font_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Fonte",
            "",
            "Fontes TrueType (*.ttf);;Fontes OpenType (*.otf);;Todos os Arquivos (*)"
        )

        if font_path:
            font_name = os.path.basename(font_path)
            # Adicionar ao combobox se não estiver lá
            if font_name not in [self.font_combo.itemText(i) for i in range(self.font_combo.count())]:
                self.font_combo.addItem(font_name)
            self.font_combo.setCurrentText(font_name)

            # Copiar para o diretório fonts/ se não estiver lá
            fonts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
            dest_path = os.path.join(fonts_dir, font_name)
            if not os.path.exists(dest_path):
                try:
                    shutil.copy2(font_path, dest_path)
                    self.load_fonts()  # Recarregar a lista
                except Exception as e:
                    QMessageBox.warning(self, "Aviso", f"Não foi possível copiar a fonte: {str(e)}")

    def create_image_convert_page(self):
        """Cria a página de conversão de imagens"""
        page = QWidget()
        layout = QVBoxLayout(page)

        # Título
        title = QLabel("Conversor de Imagens")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)

        # Splitter para dividir a tela
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Painel de upload e lista de imagens
        upload_group = QGroupBox("Imagens")
        upload_layout = QVBoxLayout()

        # Botões de upload
        upload_buttons_layout = QHBoxLayout()
        add_images_button = QPushButton("Adicionar Imagens")
        add_images_button.clicked.connect(self.add_images)
        clear_images_button = QPushButton("Limpar Lista")
        clear_images_button.clicked.connect(self.clear_images)

        upload_buttons_layout.addWidget(add_images_button)
        upload_buttons_layout.addWidget(clear_images_button)
        upload_layout.addLayout(upload_buttons_layout)

        # Lista de imagens
        self.image_list = QListWidget()
        self.image_list.setAcceptDrops(True)
        self.image_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        upload_layout.addWidget(self.image_list)

        upload_group.setLayout(upload_layout)

        # Painel de configurações e preview
        settings_group = QGroupBox("Configurações")
        settings_layout = QVBoxLayout()

        # Configurações de conversão
        settings_form = QFormLayout()

        self.image_format_combo = QComboBox()
        self.image_format_combo.addItems(["PNG", "JPEG", "SVG", "ICO", "WEBP"])

        self.image_quality_spin = QSpinBox()
        self.image_quality_spin.setRange(1, 100)
        self.image_quality_spin.setValue(90)

        self.image_resize_check = QCheckBox("Redimensionar imagens")
        self.image_resize_check.stateChanged.connect(self.toggle_resize_options)

        self.image_width_spin = QSpinBox()
        self.image_width_spin.setRange(1, 9999)
        self.image_width_spin.setValue(800)
        self.image_width_spin.setEnabled(False)

        self.image_height_spin = QSpinBox()
        self.image_height_spin.setRange(1, 9999)
        self.image_height_spin.setValue(600)
        self.image_height_spin.setEnabled(False)

        settings_form.addRow("Formato de Saída:", self.image_format_combo)
        settings_form.addRow("Qualidade (%):", self.image_quality_spin)
        settings_form.addRow(self.image_resize_check)
        settings_form.addRow("Largura:", self.image_width_spin)
        settings_form.addRow("Altura:", self.image_height_spin)

        settings_layout.addLayout(settings_form)

        # Preview da imagem
        self.image_preview = QLabel()
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setStyleSheet("background-color: #FFFFFF; border: 1px solid #CCCCCC;")
        settings_layout.addWidget(self.image_preview)

        # Botão de conversão
        convert_button = QPushButton("Converter Imagens")
        convert_button.clicked.connect(self.convert_images)
        settings_layout.addWidget(convert_button)

        settings_group.setLayout(settings_layout)

        # Adicionar grupos ao splitter
        splitter.addWidget(upload_group)
        splitter.addWidget(settings_group)
        splitter.setSizes([300, 500])

        layout.addWidget(splitter)
        self.content_area.addWidget(page)

    def create_notes_page(self):
        """Cria a página de anotações"""
        page = QWidget()
        layout = QVBoxLayout(page)

        # Título
        title = QLabel("Gerenciador de Anotações")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)

        # Abas
        self.notes_tab = QTabWidget()
        self.notes_new_tab = QWidget()
        self.notes_existing_tab = QWidget()

        self.notes_tab.addTab(self.notes_new_tab, "Nova Anotação")
        self.notes_tab.addTab(self.notes_existing_tab, "Anotações Salvas")

        # Conteúdo da aba "Nova Anotação"
        new_note_layout = QFormLayout(self.notes_new_tab)

        self.note_title_input = QLineEdit()
        self.note_tags_input = QLineEdit()
        self.note_tags_input.setPlaceholderText("tags, separadas, por, vírgula")

        # Abas para edição e preview Markdown
        note_editor_tabs = QTabWidget()
        self.note_content_editor = QTextEdit()
        self.note_content_preview = QTextEdit()
        self.note_content_preview.setReadOnly(True)

        note_editor_tabs.addTab(self.note_content_editor, "Editar")
        note_editor_tabs.addTab(self.note_content_preview, "Visualizar")
        note_editor_tabs.currentChanged.connect(self.update_note_preview)

        new_note_layout.addRow("Título:", self.note_title_input)
        new_note_layout.addRow("Tags:", self.note_tags_input)
        new_note_layout.addRow("Conteúdo:", note_editor_tabs)

        # Botões de ação
        buttons_layout = QHBoxLayout()
        save_note_button = QPushButton("Salvar Anotação")
        save_note_button.clicked.connect(self.save_note)
        clear_note_button = QPushButton("Limpar")
        clear_note_button.clicked.connect(self.clear_note_form)

        buttons_layout.addWidget(save_note_button)
        buttons_layout.addWidget(clear_note_button)
        new_note_layout.addRow(buttons_layout)

        # Conteúdo da aba "Anotações Salvas"
        existing_notes_layout = QVBoxLayout(self.notes_existing_tab)

        # Barra de pesquisa
        search_layout = QHBoxLayout()
        self.notes_search_input = QLineEdit()
        self.notes_search_input.setPlaceholderText("Pesquisar anotações...")
        self.notes_search_input.textChanged.connect(self.filter_notes)

        search_layout.addWidget(self.notes_search_input)
        existing_notes_layout.addLayout(search_layout)

        # Lista de anotações
        self.notes_list = QListWidget()
        self.notes_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.notes_list.itemSelectionChanged.connect(self.show_note_details)
        existing_notes_layout.addWidget(self.notes_list)

        # Visualização da anotação selecionada
        self.note_details = QTextEdit()
        self.note_details.setReadOnly(True)
        existing_notes_layout.addWidget(self.note_details)

        # Botões de ação
        notes_buttons_layout = QHBoxLayout()
        edit_note_button = QPushButton("Editar")
        edit_note_button.clicked.connect(self.edit_selected_note)
        delete_note_button = QPushButton("Excluir")
        delete_note_button.clicked.connect(self.delete_note)
        export_note_button = QPushButton("Exportar")
        export_note_button.clicked.connect(self.export_note)

        notes_buttons_layout.addWidget(edit_note_button)
        notes_buttons_layout.addWidget(delete_note_button)
        notes_buttons_layout.addWidget(export_note_button)
        existing_notes_layout.addLayout(notes_buttons_layout)

        layout.addWidget(self.notes_tab)
        self.content_area.addWidget(page)

    def create_commands_page(self):
        """Cria a página de comandos personalizados"""
        page = QWidget()
        layout = QVBoxLayout(page)

        # Título
        title = QLabel("Comandos Personalizados")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)

        # Formulário para novo comando
        form_layout = QFormLayout()

        self.command_name_input = QLineEdit()
        self.command_text_input = QTextEdit()
        self.command_category_input = QLineEdit()
        self.command_tags_input = QLineEdit()

        form_layout.addRow("Nome do Comando:", self.command_name_input)
        form_layout.addRow("Comando:", self.command_text_input)
        form_layout.addRow("Categoria:", self.command_category_input)
        form_layout.addRow("Tags:", self.command_tags_input)

        # Botões de ação
        buttons_layout = QHBoxLayout()
        save_command_button = QPushButton("Salvar Comando")
        save_command_button.clicked.connect(self.save_command)
        clear_command_button = QPushButton("Limpar")
        clear_command_button.clicked.connect(self.clear_command_form)

        buttons_layout.addWidget(save_command_button)
        buttons_layout.addWidget(clear_command_button)
        form_layout.addRow(buttons_layout)

        # Lista de comandos
        self.commands_list = QListWidget()
        self.commands_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.commands_list.itemSelectionChanged.connect(self.show_command_details)
        layout.addWidget(self.commands_list)

        # Botões para comandos
        command_buttons_layout = QHBoxLayout()
        run_command_button = QPushButton("Executar")
        run_command_button.clicked.connect(self.run_selected_command)
        edit_command_button = QPushButton("Editar")
        edit_command_button.clicked.connect(self.edit_selected_command)
        delete_command_button = QPushButton("Excluir")
        delete_command_button.clicked.connect(self.delete_command)
        copy_command_button = QPushButton("Copiar")
        copy_command_button.clicked.connect(self.copy_command)

        command_buttons_layout.addWidget(run_command_button)
        command_buttons_layout.addWidget(edit_command_button)
        command_buttons_layout.addWidget(delete_command_button)
        command_buttons_layout.addWidget(copy_command_button)
        layout.addLayout(command_buttons_layout)

        self.content_area.addWidget(page)

    def create_settings_page(self):
        """Cria a página de configurações"""
        page = QWidget()
        layout = QVBoxLayout(page)

        # Título
        title = QLabel("Configurações do Sistema")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)

        # Abas
        tabs = QTabWidget()
        self.settings_general_tab = QWidget()
        self.settings_appearance_tab = QWidget()
        self.settings_backup_tab = QWidget()
        self.settings_advanced_tab = QWidget()

        tabs.addTab(self.settings_general_tab, "Geral")
        tabs.addTab(self.settings_appearance_tab, "Aparência")
        tabs.addTab(self.settings_backup_tab, "Backup")
        tabs.addTab(self.settings_advanced_tab, "Avançado")

        # Conteúdo da aba "Geral"
        general_layout = QFormLayout(self.settings_general_tab)

        self.language_combo = QComboBox()
        self.language_combo.addItems(["Português", "English", "Español"])
        self.language_combo.setCurrentText(
            "Português" if self.settings.get('language') == 'pt' else
            "English" if self.settings.get('language') == 'en' else
            "Español"
        )

        self.default_project_dir_input = QLineEdit(self.settings.get('default_project_dir'))
        browse_project_dir_button = QPushButton("Selecionar...")
        browse_project_dir_button.clicked.connect(
            lambda: self.browse_directory(self.default_project_dir_input)
        )

        self.default_export_dir_input = QLineEdit(self.settings.get('default_export_dir'))
        browse_export_dir_button = QPushButton("Selecionar...")
        browse_export_dir_button.clicked.connect(
            lambda: self.browse_directory(self.default_export_dir_input)
        )

        project_dir_layout = QHBoxLayout()
        project_dir_layout.addWidget(self.default_project_dir_input)
        project_dir_layout.addWidget(browse_project_dir_button)

        export_dir_layout = QHBoxLayout()
        export_dir_layout.addWidget(self.default_export_dir_input)
        export_dir_layout.addWidget(browse_export_dir_button)

        general_layout.addRow("Idioma:", self.language_combo)
        general_layout.addRow("Diretório Padrão para Projetos:", project_dir_layout)
        general_layout.addRow("Diretório Padrão para Exportação:", export_dir_layout)

        # Conteúdo da aba "Aparência"
        appearance_layout = QFormLayout(self.settings_appearance_tab)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Escuro", "Claro", "Azul"])
        self.theme_combo.setCurrentText(
            "Escuro" if self.settings.get('theme') == 'dark' else
            "Claro" if self.settings.get('theme') == 'light' else
            "Azul"
        )

        self.font_family_combo = QComboBox()
        self.font_family_combo.addItems(["Segoe UI", "Arial", "Verdana", "Courier New", "Times New Roman"])
        self.font_family_combo.setCurrentText(self.settings.get('font_family', 'Segoe UI'))

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(int(self.settings.get('font_size', '12')))

        self.markdown_preview_check = QCheckBox("Visualização Markdown em tempo real")
        self.markdown_preview_check.setChecked(self.settings.get_bool('markdown_preview', True))

        appearance_layout.addRow("Tema:", self.theme_combo)
        appearance_layout.addRow("Fonte:", self.font_family_combo)
        appearance_layout.addRow("Tamanho da Fonte:", self.font_size_spin)
        appearance_layout.addRow(self.markdown_preview_check)

        # Conteúdo da aba "Backup"
        backup_layout = QFormLayout(self.settings_backup_tab)

        self.auto_backup_check = QCheckBox("Backup Automático")
        self.auto_backup_check.setChecked(self.settings.get_bool('auto_backup', True))

        self.backup_interval_spin = QSpinBox()
        self.backup_interval_spin.setRange(1, 30)
        self.backup_interval_spin.setValue(int(self.settings.get('backup_interval', '7')))

        self.backup_dir_input = QLineEdit(self.settings.get('backup_dir'))
        browse_backup_dir_button = QPushButton("Selecionar...")
        browse_backup_dir_button.clicked.connect(
            lambda: self.browse_directory(self.backup_dir_input)
        )

        backup_dir_layout = QHBoxLayout()
        backup_dir_layout.addWidget(self.backup_dir_input)
        backup_dir_layout.addWidget(browse_backup_dir_button)

        backup_now_button = QPushButton("Fazer Backup Agora")
        backup_now_button.clicked.connect(self.create_manual_backup)

        backup_layout.addRow(self.auto_backup_check)
        backup_layout.addRow("Intervalo de Backup (dias):", self.backup_interval_spin)
        backup_layout.addRow("Diretório de Backup:", backup_dir_layout)
        backup_layout.addRow(backup_now_button)

        # Conteúdo da aba "Avançado"
        advanced_layout = QFormLayout(self.settings_advanced_tab)

        self.portable_mode_check = QCheckBox("Modo Portátil")
        self.portable_mode_check.setChecked(self.settings.get_bool('portable_mode', False))

        self.auto_update_check = QCheckBox("Atualizações Automáticas")
        self.auto_update_check.setChecked(self.settings.get_bool('auto_update', True))

        self.enable_shortcuts_check = QCheckBox("Ativar atalhos de teclado")
        self.enable_shortcuts_check.setChecked(self.settings.get_bool('enable_shortcuts', True))

        self.enable_notifications_check = QCheckBox("Ativar notificações")
        self.enable_notifications_check.setChecked(self.settings.get_bool('enable_notifications', True))

        self.enable_drag_drop_check = QCheckBox("Ativar arrastar e soltar")
        self.enable_drag_drop_check.setChecked(self.settings.get_bool('enable_drag_drop', True))

        advanced_layout.addRow(self.portable_mode_check)
        advanced_layout.addRow(self.auto_update_check)
        advanced_layout.addRow(self.enable_shortcuts_check)
        advanced_layout.addRow(self.enable_notifications_check)
        advanced_layout.addRow(self.enable_drag_drop_check)

        # Botões de ação
        buttons_layout = QHBoxLayout()
        save_settings_button = QPushButton("Salvar Configurações")
        save_settings_button.clicked.connect(self.save_settings)
        reset_settings_button = QPushButton("Restaurar Padrões")
        reset_settings_button.clicked.connect(self.reset_settings)

        buttons_layout.addWidget(save_settings_button)
        buttons_layout.addWidget(reset_settings_button)

        layout.addWidget(tabs)
        layout.addLayout(buttons_layout)
        self.content_area.addWidget(page)

    def load_initial_data(self):
        """Carrega dados reais para o dashboard"""
        try:
            # Get real counts from database
            projects_count = len(self.project_manager.get_projects())
            spreadsheets_count = len(self.spreadsheet_manager.get_spreadsheets())
            notes_count = len(self.notes_manager.get_notes())
            utilities_count = len(self.utilities_manager.get_utilities())

            self.projects_count_label.setText(str(projects_count))
            self.spreadsheets_count_label.setText(str(spreadsheets_count))
            self.notes_count_label.setText(str(notes_count))
            self.utilities_count_label.setText(str(utilities_count))

            # Get recent projects (5 most recent)
            recent_projects = self.db.execute_query(
                "SELECT id, name FROM projects ORDER BY created_at DESC LIMIT 5",
                fetchall=True
            )
            self.recent_projects_list.clear()
            for project in recent_projects:
                item = QListWidgetItem(project[1])  # project name
                item.setData(Qt.ItemDataRole.UserRole, project[0])  # project id
                self.recent_projects_list.addItem(item)

            # Get upcoming reminders
            reminders = self.db.execute_query(
                "SELECT id, title, due_date FROM reminders "
                "WHERE is_completed = 0 AND due_date >= datetime('now') "
                "ORDER BY due_date LIMIT 5",
                fetchall=True
            )
            self.reminders_list.clear()
            for reminder in reminders:
                item = QListWidgetItem(f"{reminder[1]} - {reminder[2]}")
                item.setData(Qt.ItemDataRole.UserRole, reminder[0])
                self.reminders_list.addItem(item)

            # Load other data as needed
            self.filter_projects()
            self.filter_spreadsheets()
            self.filter_notes()
            self.filter_apps()
            self.filter_sites()
            self.filter_commands()
            self.filter_custom_commands()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar dados iniciais: {str(e)}")

    def change_page(self, index):
        """Muda a página exibida com base no índice selecionado"""
        self.content_area.setCurrentIndex(index)

        # Atualizar dados da página quando selecionada
        if index == 0:  # Dashboard
            self.load_initial_data()
        elif index == 1:  # Projetos
            self.filter_projects()
        elif index == 2:  # Planilhas
            self.filter_spreadsheets()
        elif index == 4:  # Utilitários
            self.filter_apps()
            self.filter_sites()
            self.filter_commands()
        elif index == 7:  # Anotações
            self.filter_notes()
        elif index == 8:  # Comandos
            self.filter_custom_commands()

    def browse_project_dir(self):
        """Abre o diálogo para selecionar diretório do projeto"""
        default_dir = self.settings.get('default_project_dir', os.path.expanduser('~'))
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Selecionar Diretório do Projeto",
            default_dir
        )
        if dir_path:
            self.project_dir_input.setText(dir_path)

    def browse_dev_dir(self):
        """Abre o diálogo para selecionar diretório de desenvolvimento"""
        default_dir = self.settings.get('default_project_dir', os.path.expanduser('~'))
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Selecionar Diretório de Desenvolvimento",
            default_dir
        )
        if dir_path:
            self.dev_project_dir_input.setText(dir_path)

    def browse_directory(self, line_edit):
        """Abre o diálogo para selecionar um diretório e atualiza o QLineEdit"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Selecionar Diretório",
            line_edit.text() or os.path.expanduser('~')
        )
        if dir_path:
            line_edit.setText(dir_path)

    def create_project(self):
        """Cria um novo projeto com pasta raiz correta"""
        name = self.project_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Aviso", "Por favor, insira um nome para o projeto.")
            return

        base_dir = self.project_dir_input.text().strip()
        if not base_dir:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um diretório base para o projeto.")
            return

        try:
            # Create root project directory
            project_dir = os.path.join(base_dir, name)
            os.makedirs(project_dir, exist_ok=True)

            # Create subfolders inside project directory
            subfolders = self.project_subfolders_input.toPlainText()
            if subfolders:
                for folder in subfolders.split('\n'):
                    if folder.strip():
                        os.makedirs(os.path.join(project_dir, folder.strip()), exist_ok=True)

            # Save to database
            project_id = self.project_manager.create_project(
                name=name,
                project_type=self.project_type_combo.currentText(),
                base_dir=project_dir,  # Use project_dir instead of base_dir
                subfolders=subfolders,
                description=self.project_description_input.toPlainText(),
                tags=self.project_tags_input.text()
            )

            QMessageBox.information(
                self,
                "Sucesso",
                f"Projeto '{name}' criado com sucesso em:\n{project_dir}"
            )
            self.clear_project_form()
            self.filter_projects()
            self.load_initial_data()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao criar projeto: {str(e)}")

    def clear_project_form(self):
        """Limpa o formulário de projeto"""
        self.project_name_input.clear()
        self.project_type_combo.setCurrentIndex(0)
        self.project_dir_input.clear()
        self.project_subfolders_input.clear()
        self.project_tags_input.clear()
        self.project_description_input.clear()

    def filter_projects(self):
        """Filtra a lista de projetos com base nos critérios de pesquisa"""
        filter_type = self.projects_filter_combo.currentText().lower()
        search_query = self.projects_search_input.text().strip()

        if filter_type == "todos":
            filter_type = "all"
        elif filter_type == "favoritos":
            filter_type = "favorites"

        projects = self.project_manager.get_projects(filter_type, search_query)

        self.projects_list.clear()
        for project in projects:
            item = QListWidgetItem(project[1])  # project name
            item.setData(Qt.ItemDataRole.UserRole, project[0])  # project id
            self.projects_list.addItem(item)

    def open_selected_project(self):
        """Abre o projeto selecionado na lista"""
        selected_items = self.projects_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um projeto.")
            return

        self.open_project(selected_items[0])

    def open_project(self, item):
        """Abre um projeto específico"""
        project_id = item.data(Qt.ItemDataRole.UserRole)
        project = self.db.execute_query(
            "SELECT base_dir FROM projects WHERE id = ?",
            (project_id,),
            fetchone=True
        )

        if project and project[0]:
            if os.path.exists(project[0]):
                if sys.platform == "win32":
                    os.startfile(project[0])
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", project[0]])
                else:
                    subprocess.Popen(["xdg-open", project[0]])
            else:
                QMessageBox.warning(self, "Aviso", f"Diretório não encontrado: {project[0]}")
        else:
            QMessageBox.warning(self, "Aviso", "Projeto não encontrado")

    def open_project_from_list(self, item):
        """Abre um projeto da lista de projetos recentes"""
        self.open_project(item)

    def edit_project(self):
        """Edita o projeto selecionado"""
        selected_items = self.projects_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um projeto.")
            return

        project_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        project = self.db.execute_query(
            "SELECT * FROM projects WHERE id = ?",
            (project_id,),
            fetchone=True
        )

        if project:
            # Preencher o formulário com os dados existentes
            self.project_name_input.setText(project[1])
            self.project_type_combo.setCurrentText(project[2])
            self.project_dir_input.setText(project[3])
            self.project_subfolders_input.setPlainText(project[4] if project[4] else "")
            self.project_tags_input.setText(project[6] if project[6] else "")
            self.project_description_input.setPlainText(project[5] if project[5] else "")

            # Mudar para a aba de edição
            self.projects_tab.setCurrentIndex(0)

            # Criar botão de atualização
            if hasattr(self, 'update_project_button'):
                self.update_project_button.deleteLater()

            self.update_project_button = QPushButton("Atualizar Projeto")
            self.update_project_button.clicked.connect(lambda: self.update_project_data(project_id))

            # Adicionar o botão ao layout
            layout = self.projects_new_tab.layout()
            if layout:
                layout.addRow(self.update_project_button)

    def update_project_data(self, project_id):
        """Atualiza os dados do projeto"""
        name = self.project_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Aviso", "Por favor, insira um nome para o projeto.")
            return

        base_dir = self.project_dir_input.text().strip()
        if not base_dir:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um diretório base para o projeto.")
            return

        try:
            self.project_manager.update_project(
                project_id,
                name=name,
                type=self.project_type_combo.currentText(),
                base_dir=base_dir,
                subfolders=self.project_subfolders_input.toPlainText(),
                description=self.project_description_input.toPlainText(),
                tags=self.project_tags_input.text()
            )

            QMessageBox.information(self, "Sucesso", "Projeto atualizado com sucesso!")
            self.clear_project_form()
            self.filter_projects()

            # Remover o botão de atualização
            if hasattr(self, 'update_project_button'):
                self.update_project_button.deleteLater()
                del self.update_project_button

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao atualizar projeto: {str(e)}")

    def delete_project(self):
        """Exclui o projeto selecionado"""
        selected_items = self.projects_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um projeto.")
            return

        project_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        project_name = selected_items[0].text()

        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o projeto '{project_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.project_manager.delete_project(project_id)
                self.filter_projects()
                self.load_initial_data()  # Atualizar dashboard
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao excluir projeto: {str(e)}")

    def export_project(self):
        """Exporta o projeto selecionado"""
        selected_items = self.projects_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um projeto.")
            return

        project_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        project = self.db.execute_query(
            "SELECT * FROM projects WHERE id = ?",
            (project_id,),
            fetchone=True
        )

        if not project:
            QMessageBox.warning(self, "Aviso", "Projeto não encontrado.")
            return

        default_dir = self.settings.get('default_export_dir', os.path.expanduser('~'))
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar Projeto",
            os.path.join(default_dir, f"{project[1]}.json"),
            "JSON Files (*.json)"
        )

        if file_path:
            try:
                project_data = {
                    'id': project[0],
                    'name': project[1],
                    'type': project[2],
                    'base_dir': project[3],
                    'subfolders': project[4],
                    'description': project[5],
                    'tags': project[6],
                    'is_favorite': bool(project[7]),
                    'created_at': project[8],
                    'updated_at': project[9]
                }

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(project_data, f, indent=4, ensure_ascii=False)

                QMessageBox.information(self, "Sucesso", "Projeto exportado com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao exportar projeto: {str(e)}")

    def create_spreadsheet(self):
        """Cria uma nova planilha"""
        name = self.spreadsheet_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Aviso", "Por favor, insira um nome para a planilha.")
            return

        headers = self.spreadsheet_headers_input.toPlainText().strip()
        if not headers:
            QMessageBox.warning(self, "Aviso", "Por favor, insira pelo menos um cabeçalho.")
            return

        try:
            spreadsheet_id = self.spreadsheet_manager.create_spreadsheet(
                name=name,
                headers=headers.split('\n')
            )

            QMessageBox.information(self, "Sucesso", f"Planilha '{name}' criada com sucesso!")
            self.clear_spreadsheet_form()
            self.filter_spreadsheets()

            # Atualizar dashboard
            self.load_initial_data()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao criar planilha: {str(e)}")

    def clear_spreadsheet_form(self):
        """Limpa o formulário de planilha"""
        self.spreadsheet_name_input.clear()
        self.spreadsheet_headers_input.clear()

    def filter_spreadsheets(self):
        """Filtra a lista de planilhas com base na pesquisa"""
        search_query = self.spreadsheets_search_input.text().strip()
        spreadsheets = self.spreadsheet_manager.get_spreadsheets(search_query)

        self.spreadsheets_list.clear()
        for spreadsheet in spreadsheets:
            item = QListWidgetItem(spreadsheet[1])  # spreadsheet name
            item.setData(Qt.ItemDataRole.UserRole, spreadsheet[0])  # spreadsheet id
            self.spreadsheets_list.addItem(item)

    def open_selected_spreadsheet(self):
        """Abre a planilha selecionada na lista"""
        selected_items = self.spreadsheets_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione uma planilha.")
            return

        self.open_spreadsheet(selected_items[0])

    def open_spreadsheet(self, item):
        """Abre uma planilha específica"""
        spreadsheet_id = item.data(Qt.ItemDataRole.UserRole)
        spreadsheet = self.db.execute_query(
            "SELECT headers, data FROM spreadsheets WHERE id = ?",
            (spreadsheet_id,),
            fetchone=True
        )

        if spreadsheet:
            headers = spreadsheet[0].split('\n') if spreadsheet[0] else []
            data = json.loads(spreadsheet[1]) if spreadsheet[1] else []

            self.spreadsheet_table.clear()
            self.spreadsheet_table.setColumnCount(len(headers))
            self.spreadsheet_table.setHorizontalHeaderLabels(headers)
            self.spreadsheet_table.setRowCount(len(data))

            for row_idx, row_data in enumerate(data):
                for col_idx, cell_data in enumerate(row_data):
                    item = QTableWidgetItem(str(cell_data))
                    self.spreadsheet_table.setItem(row_idx, col_idx, item)

    def edit_spreadsheet(self):
        """Edita a planilha selecionada"""
        selected_items = self.spreadsheets_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione uma planilha.")
            return

        spreadsheet_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        spreadsheet = self.db.execute_query(
            "SELECT * FROM spreadsheets WHERE id = ?",
            (spreadsheet_id,),
            fetchone=True
        )

        if spreadsheet:
            # Preencher o formulário com os dados existentes
            self.spreadsheet_name_input.setText(spreadsheet[1])
            self.spreadsheet_headers_input.setPlainText(spreadsheet[2] if spreadsheet[2] else "")

            # Mudar para a aba de edição
            self.spreadsheets_tab.setCurrentIndex(0)

            # Criar botão de atualização
            if hasattr(self, 'update_spreadsheet_button'):
                self.update_spreadsheet_button.deleteLater()

            self.update_spreadsheet_button = QPushButton("Atualizar Planilha")
            self.update_spreadsheet_button.clicked.connect(lambda: self.update_spreadsheet_data(spreadsheet_id))

            # Adicionar o botão ao layout
            layout = self.spreadsheets_new_tab.layout()
            if layout:
                layout.addRow(self.update_spreadsheet_button)

    def update_spreadsheet_data(self, spreadsheet_id):
        """Atualiza os dados da planilha"""
        name = self.spreadsheet_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Aviso", "Por favor, insira um nome para a planilha.")
            return

        headers = self.spreadsheet_headers_input.toPlainText().strip()
        if not headers:
            QMessageBox.warning(self, "Aviso", "Por favor, insira pelo menos um cabeçalho.")
            return

        try:
            self.spreadsheet_manager.update_spreadsheet(
                spreadsheet_id,
                name=name,
                headers=headers
            )

            QMessageBox.information(self, "Sucesso", "Planilha atualizada com sucesso!")
            self.clear_spreadsheet_form()
            self.filter_spreadsheets()

            # Remover o botão de atualização
            if hasattr(self, 'update_spreadsheet_button'):
                self.update_spreadsheet_button.deleteLater()
                del self.update_spreadsheet_button

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao atualizar planilha: {str(e)}")

    def delete_spreadsheet(self):
        """Exclui a planilha selecionada"""
        selected_items = self.spreadsheets_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione uma planilha.")
            return

        spreadsheet_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        spreadsheet_name = selected_items[0].text()

        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Tem certeza que deseja excluir a planilha '{spreadsheet_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.spreadsheet_manager.delete_spreadsheet(spreadsheet_id)
                self.filter_spreadsheets()
                self.load_initial_data()  # Atualizar dashboard
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao excluir planilha: {str(e)}")

    def export_spreadsheet(self):
        """Exporta a planilha selecionada"""
        selected_items = self.spreadsheets_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione uma planilha.")
            return

        spreadsheet_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        spreadsheet_name = selected_items[0].text()

        default_dir = self.settings.get('default_export_dir', os.path.expanduser('~'))
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Exportar Planilha",
            os.path.join(default_dir, f"{spreadsheet_name}"),
            "CSV Files (*.csv);;Excel Files (*.xlsx)"
        )

        if file_path:
            try:
                spreadsheet = self.db.execute_query(
                    "SELECT headers, data FROM spreadsheets WHERE id = ?",
                    (spreadsheet_id,),
                    fetchone=True
                )

                if not spreadsheet:
                    raise Exception("Planilha não encontrada")

                headers = spreadsheet[0].split('\n') if spreadsheet[0] else []
                data = json.loads(spreadsheet[1]) if spreadsheet[1] else []

                if file_path.endswith('.xlsx'):
                    from openpyxl import Workbook
                    wb = Workbook()
                    ws = wb.active

                    # Add headers
                    ws.append(headers)

                    # Add data
                    for row in data:
                        ws.append(row)

                    wb.save(file_path)
                else:
                    with open(file_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        writer.writerow(headers)
                        writer.writerows(data)

                QMessageBox.information(self, "Sucesso", "Planilha exportada com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao exportar planilha: {str(e)}")

    def create_dev_project(self):
        """Cria um novo projeto de desenvolvimento"""
        name = self.dev_project_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Aviso", "Por favor, insira um nome para o projeto.")
            return

        base_dir = self.dev_project_dir_input.text().strip()
        if not base_dir:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um diretório para o projeto.")
            return

        project_type = self.dev_project_type_combo.currentText()
        package_manager = self.dev_package_manager_combo.currentText()
        install_deps = self.dev_install_deps_check.isChecked()

        try:
            project_path = os.path.join(base_dir, name)
            os.makedirs(project_path, exist_ok=True)

            # Execute commands based on project type
            commands = []

            if "Vite" in project_type:
                commands.append(f"{package_manager} create vite@latest {name} -- --template react")
            elif "Create-React-App" in project_type:
                commands.append(f"npx create-react-app {name}")
            elif "Vue" in project_type:
                commands.append(f"{package_manager} create vue@latest")
            elif "Node.js" in project_type:
                commands.append(f"{package_manager} init -y")
                # Create basic structure
                with open(os.path.join(project_path, "index.js"), 'w') as f:
                    f.write("console.log('Hello World');\n")
            elif "Python" in project_type:
                commands.append("python -m venv venv")
                # Create requirements.txt
                with open(os.path.join(project_path, "requirements.txt"), 'w') as f:
                    f.write("# Lista de dependências\n")
            elif "HTML/CSS/JS" in project_type:
                # Create basic files
                os.makedirs(os.path.join(project_path, "src"), exist_ok=True)
                with open(os.path.join(project_path, "index.html"), 'w') as f:
                    f.write(
                        "<!DOCTYPE html>\n<html>\n<head>\n<title>My Project</title>\n</head>\n<body>\n<h1>Hello World</h1>\n</body>\n</html>")

            # Execute commands in terminal
            for cmd in commands:
                self.run_terminal_command(f"cd {project_path} && {cmd}")

            QMessageBox.information(
                self,
                "Sucesso",
                f"Projeto '{name}' criado com sucesso em:\n{project_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao criar projeto: {str(e)}")

    def clear_dev_form(self):
        """Limpa o formulário de desenvolvimento"""
        self.dev_project_name_input.clear()
        self.dev_project_dir_input.clear()
        self.dev_project_type_combo.setCurrentIndex(0)
        self.dev_install_deps_check.setChecked(True)

    def run_terminal_command(self, command):
        """Executa um comando no terminal integrado"""
        try:
            self.terminal_output.append(f"> {command}\n")

            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.expanduser('~')
            )

            # Read output in real-time
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.terminal_output.append(output)

            # Check for errors
            stderr = process.stderr.read()
            if stderr:
                self.terminal_output.append(f"Erro: {stderr}\n")

            self.terminal_output.append(f"Processo finalizado com código {process.returncode}\n")

        except Exception as e:
            self.terminal_output.append(f"Erro ao executar comando: {str(e)}\n")

    def execute_terminal_command(self):
        """Executa o comando digitado no terminal"""
        command = self.terminal_input.text().strip()
        if not command:
            return

        self.run_terminal_command(command)
        self.terminal_input.clear()

    def clear_terminal(self):
        """Limpa o terminal integrado"""
        self.terminal_output.clear()

    def filter_apps(self):
        """Filtra a lista de aplicativos com base na pesquisa"""
        search_query = self.apps_search_input.text().strip()
        apps = self.utilities_manager.get_utilities("app", search_query)

        self.apps_list.clear()
        for app in apps:
            item = QListWidgetItem(app[1])  # app name
            item.setData(Qt.ItemDataRole.UserRole, app[0])  # app id
            self.apps_list.addItem(item)

    def show_add_app_dialog(self):
        """Mostra o diálogo para adicionar um novo aplicativo"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Adicionar Aplicativo")
        dialog.setModal(True)

        layout = QFormLayout(dialog)

        name_input = QLineEdit()
        path_input = QLineEdit()
        browse_button = QPushButton("Selecionar...")

        def browse_app():
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Selecionar Aplicativo",
                "",
                "Executáveis (*.exe *.app *.sh);;Todos os Arquivos (*)"
            )
            if file_path:
                path_input.setText(file_path)

        browse_button.clicked.connect(browse_app)

        path_layout = QHBoxLayout()
        path_layout.addWidget(path_input)
        path_layout.addWidget(browse_button)

        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Salvar")
        cancel_button = QPushButton("Cancelar")

        def save_app():
            name = name_input.text().strip()
            path = path_input.text().strip()

            if not name or not path:
                QMessageBox.warning(dialog, "Aviso", "Por favor, preencha todos os campos.")
                return

            try:
                self.utilities_manager.add_utility(
                    name=name,
                    utility_type="app",
                    path=path
                )

                dialog.accept()
                self.filter_apps()
                self.load_initial_data()  # Atualizar dashboard
            except Exception as e:
                QMessageBox.critical(dialog, "Erro", f"Falha ao adicionar aplicativo: {str(e)}")

        save_button.clicked.connect(save_app)
        cancel_button.clicked.connect(dialog.reject)

        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)

        layout.addRow("Nome:", name_input)
        layout.addRow("Caminho:", path_layout)
        layout.addRow(buttons_layout)

        dialog.exec()

    def run_selected_app(self):
        """Executa o aplicativo selecionado"""
        selected_items = self.apps_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um aplicativo.")
            return

        self.run_app(selected_items[0])

    def run_app(self, item):
        """Executa um aplicativo específico"""
        app_id = item.data(Qt.ItemDataRole.UserRole)

        try:
            if self.utilities_manager.execute_utility(app_id):
                self.statusbar.showMessage(f"Aplicativo executado: {item.text()}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao executar aplicativo: {str(e)}")

    def edit_app(self):
        """Edita o aplicativo selecionado"""
        selected_items = self.apps_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um aplicativo.")
            return

        app_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        app = self.db.execute_query(
            "SELECT * FROM utilities WHERE id = ?",
            (app_id,),
            fetchone=True
        )

        if app:
            dialog = QDialog(self)
            dialog.setWindowTitle("Editar Aplicativo")
            dialog.setModal(True)
            dialog.setFixedSize(400, 200)

            layout = QFormLayout(dialog)

            name_input = QLineEdit(app[1])
            path_input = QLineEdit(app[3])
            browse_button = QPushButton("Selecionar...")

            def browse_app():
                file_path, _ = QFileDialog.getOpenFileName(
                    dialog,
                    "Selecionar Aplicativo",
                    path_input.text(),
                    "Executáveis (*.exe *.app *.sh);;Todos os Arquivos (*)"
                )
                if file_path:
                    path_input.setText(file_path)

            browse_button.clicked.connect(browse_app)

            path_layout = QHBoxLayout()
            path_layout.addWidget(path_input)
            path_layout.addWidget(browse_button)

            buttons_layout = QHBoxLayout()
            save_button = QPushButton("Salvar")
            cancel_button = QPushButton("Cancelar")

            def save_app():
                name = name_input.text().strip()
                path = path_input.text().strip()

                if not name or not path:
                    QMessageBox.warning(dialog, "Aviso", "Por favor, preencha todos os campos.")
                    return

                try:
                    self.db.execute_query(
                        "UPDATE utilities SET name = ?, path = ? WHERE id = ?",
                        (name, path, app_id)
                    )
                    dialog.accept()
                    self.filter_apps()
                except Exception as e:
                    QMessageBox.critical(dialog, "Erro", f"Falha ao atualizar aplicativo: {str(e)}")

            save_button.clicked.connect(save_app)
            cancel_button.clicked.connect(dialog.reject)

            buttons_layout.addWidget(save_button)
            buttons_layout.addWidget(cancel_button)

            layout.addRow("Nome:", name_input)
            layout.addRow("Caminho:", path_layout)
            layout.addRow(buttons_layout)

            dialog.exec()

    def delete_app(self):
        """Exclui o aplicativo selecionado"""
        selected_items = self.apps_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um aplicativo.")
            return

        app_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        app_name = selected_items[0].text()

        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o aplicativo '{app_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.execute_query("DELETE FROM utilities WHERE id = ?", (app_id,))
                self.filter_apps()
                self.load_initial_data()  # Atualizar dashboard
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao excluir aplicativo: {str(e)}")

    def filter_sites(self):
        """Filtra a lista de sites com base na pesquisa"""
        search_query = self.sites_search_input.text().strip()
        sites = self.utilities_manager.get_utilities("site", search_query)

        self.sites_list.clear()
        for site in sites:
            item = QListWidgetItem(site[1])  # site name
            item.setData(Qt.ItemDataRole.UserRole, site[0])  # site id
            self.sites_list.addItem(item)

    def show_add_site_dialog(self):
        """Mostra o diálogo para adicionar um novo site"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Adicionar Site")
        dialog.setModal(True)

        layout = QFormLayout(dialog)

        name_input = QLineEdit()
        url_input = QLineEdit()

        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Salvar")
        cancel_button = QPushButton("Cancelar")

        def save_site():
            name = name_input.text().strip()
            url = url_input.text().strip()

            if not name or not url:
                QMessageBox.warning(dialog, "Aviso", "Por favor, preencha todos os campos.")
                return

            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            try:
                self.utilities_manager.add_utility(
                    name=name,
                    utility_type="site",
                    path=url
                )

                dialog.accept()
                self.filter_sites()
                self.load_initial_data()  # Atualizar dashboard
            except Exception as e:
                QMessageBox.critical(dialog, "Erro", f"Falha ao adicionar site: {str(e)}")

        save_button.clicked.connect(save_site)
        cancel_button.clicked.connect(dialog.reject)

        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)

        layout.addRow("Nome:", name_input)
        layout.addRow("URL:", url_input)
        layout.addRow(buttons_layout)

        dialog.exec()

    def open_selected_site(self):
        """Abre o site selecionado na lista"""
        selected_items = self.sites_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um site.")
            return

        self.open_site(selected_items[0])

    def open_site(self, item):
        """Abre um site específico"""
        site_id = item.data(Qt.ItemDataRole.UserRole)

        try:
            if self.utilities_manager.execute_utility(site_id):
                self.statusbar.showMessage(f"Site aberto: {item.text()}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao abrir site: {str(e)}")

    def edit_site(self):
        """Edita o site selecionado"""
        selected_items = self.sites_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um site.")
            return

        site_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        site = self.db.execute_query(
            "SELECT * FROM utilities WHERE id = ?",
            (site_id,),
            fetchone=True
        )

        if site:
            dialog = QDialog(self)
            dialog.setWindowTitle("Editar Site")
            dialog.setModal(True)
            dialog.setFixedSize(400, 200)

            layout = QFormLayout(dialog)

            name_input = QLineEdit(site[1])
            url_input = QLineEdit(site[3])

            buttons_layout = QHBoxLayout()
            save_button = QPushButton("Salvar")
            cancel_button = QPushButton("Cancelar")

            def save_site():
                name = name_input.text().strip()
                url = url_input.text().strip()

                if not name or not url:
                    QMessageBox.warning(dialog, "Aviso", "Por favor, preencha todos os campos.")
                    return

                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url

                try:
                    self.db.execute_query(
                        "UPDATE utilities SET name = ?, path = ? WHERE id = ?",
                        (name, url, site_id)
                    )
                    dialog.accept()
                    self.filter_sites()
                except Exception as e:
                    QMessageBox.critical(dialog, "Erro", f"Falha ao atualizar site: {str(e)}")

            save_button.clicked.connect(save_site)
            cancel_button.clicked.connect(dialog.reject)

            buttons_layout.addWidget(save_button)
            buttons_layout.addWidget(cancel_button)

            layout.addRow("Nome:", name_input)
            layout.addRow("URL:", url_input)
            layout.addRow(buttons_layout)

            dialog.exec()

    def delete_site(self):
        """Exclui o site selecionado"""
        selected_items = self.sites_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um site.")
            return

        site_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        site_name = selected_items[0].text()

        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o site '{site_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.execute_query("DELETE FROM utilities WHERE id = ?", (site_id,))
                self.filter_sites()
                self.load_initial_data()  # Atualizar dashboard
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao excluir site: {str(e)}")

    def filter_commands(self):
        """Filtra a lista de comandos com base na pesquisa"""
        search_query = self.commands_search_input.text().strip()
        commands = self.utilities_manager.get_utilities("command", search_query)

        self.commands_list.clear()
        for command in commands:
            item = QListWidgetItem(command[1])  # command name
            item.setData(Qt.ItemDataRole.UserRole, command[0])  # command id
            self.commands_list.addItem(item)

    def show_add_command_dialog(self):
        """Mostra o diálogo para adicionar um novo comando"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Adicionar Comando")
        dialog.setModal(True)

        layout = QFormLayout(dialog)

        name_input = QLineEdit()
        command_input = QTextEdit()

        buttons_layout = QHBoxLayout()
        save_button = QPushButton("Salvar")
        cancel_button = QPushButton("Cancelar")

        def save_command():
            name = name_input.text().strip()
            command = command_input.toPlainText().strip()

            if not name or not command:
                QMessageBox.warning(dialog, "Aviso", "Por favor, preencha todos os campos.")
                return

            try:
                self.utilities_manager.add_utility(
                    name=name,
                    utility_type="command",
                    command=command
                )

                dialog.accept()
                self.filter_commands()
                self.load_initial_data()  # Atualizar dashboard
            except Exception as e:
                QMessageBox.critical(dialog, "Erro", f"Falha ao adicionar comando: {str(e)}")

        save_button.clicked.connect(save_command)
        cancel_button.clicked.connect(dialog.reject)

        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)

        layout.addRow("Nome:", name_input)
        layout.addRow("Comando:", command_input)
        layout.addRow(buttons_layout)

        dialog.exec()

    def run_selected_command(self):
        """Executa o comando selecionado na lista"""
        selected_items = self.commands_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um comando.")
            return

        self.run_command(selected_items[0])

    def run_command(self, item):
        """Executa um comando específico"""
        command_id = item.data(Qt.ItemDataRole.UserRole)

        try:
            if self.utilities_manager.execute_utility(command_id):
                self.statusbar.showMessage(f"Comando executado: {item.text()}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao executar comando: {str(e)}")

    def edit_command(self):
        """Edita o comando selecionado"""
        selected_items = self.commands_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um comando.")
            return

        command_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        command = self.db.execute_query(
            "SELECT * FROM utilities WHERE id = ?",
            (command_id,),
            fetchone=True
        )

        if command:
            dialog = QDialog(self)
            dialog.setWindowTitle("Editar Comando")
            dialog.setModal(True)
            dialog.setFixedSize(500, 300)

            layout = QVBoxLayout(dialog)

            name_input = QLineEdit(command[1])
            command_input = QTextEdit(command[4])
            command_input.setAcceptRichText(False)

            buttons_layout = QHBoxLayout()
            save_button = QPushButton("Salvar")
            cancel_button = QPushButton("Cancelar")

            def save_command():
                name = name_input.text().strip()
                command_text = command_input.toPlainText().strip()

                if not name or not command_text:
                    QMessageBox.warning(dialog, "Aviso", "Por favor, preencha todos os campos.")
                    return

                try:
                    self.db.execute_query(
                        "UPDATE utilities SET name = ?, command = ? WHERE id = ?",
                        (name, command_text, command_id)
                    )
                    dialog.accept()
                    self.filter_commands()
                except Exception as e:
                    QMessageBox.critical(dialog, "Erro", f"Falha ao atualizar comando: {str(e)}")

            save_button.clicked.connect(save_command)
            cancel_button.clicked.connect(dialog.reject)

            form_layout = QFormLayout()
            form_layout.addRow("Nome:", name_input)
            form_layout.addRow("Comando:", command_input)

            buttons_layout.addWidget(save_button)
            buttons_layout.addWidget(cancel_button)

            layout.addLayout(form_layout)
            layout.addLayout(buttons_layout)

            dialog.exec()

    def delete_command(self):
        """Exclui o comando selecionado"""
        selected_items = self.commands_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um comando.")
            return

        command_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        command_name = selected_items[0].text()

        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o comando '{command_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.execute_query("DELETE FROM utilities WHERE id = ?", (command_id,))
                self.filter_commands()
                self.load_initial_data()  # Atualizar dashboard
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao excluir comando: {str(e)}")

    def add_pdf_section(self):
        """Adiciona uma nova seção ao editor de PDF"""
        self.pdf_structure_editor.append("# Nova Seção\n\nConteúdo da seção...")

    def add_pdf_image(self):
        """Adiciona uma imagem ao editor de PDF"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Imagem",
            "",
            "Imagens (*.png *.jpg *.jpeg *.gif *.bmp);;Todos os Arquivos (*)"
        )

        if file_path:
            self.pdf_structure_editor.append(f"\n![Descrição da Imagem]({file_path})\n")

    def save_pdf_structure(self):
        """Salva a estrutura do PDF"""
        content = self.pdf_structure_editor.toPlainText()
        if not content.strip():
            QMessageBox.warning(self, "Aviso", "Por favor, adicione conteúdo ao PDF.")
            return

        default_dir = self.settings.get('default_export_dir', os.path.expanduser('~'))
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Estrutura do PDF",
            os.path.join(default_dir, "estrutura_pdf.md"),
            "Markdown Files (*.md);;Text Files (*.txt)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                QMessageBox.information(self, "Sucesso", "Estrutura do PDF salva com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao salvar estrutura: {str(e)}")

    def export_pdf(self):
        """Exporta o conteúdo para PDF com todas as validações e suporte a Unicode"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer,
                                            Image, PageBreak, Table, TableStyle)
            from reportlab.lib.units import inch, cm
            from reportlab.lib import colors
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            import emoji
            import re
            import tempfile
        except ImportError as e:
            QMessageBox.critical(
                self,
                "Erro de Dependência",
                f"Bibliotecas necessárias não encontradas:\n\n{str(e)}\n\n"
                "Instale com: pip install reportlab pyphen emoji"
            )
            return

        # 1. VALIDAÇÃO INICIAL
        selected_font = self.font_combo.currentText()
        if selected_font == "Nenhuma fonte encontrada no diretório fonts/":
            QMessageBox.warning(self, "Aviso", "Por favor, selecione ou carregue uma fonte válida.")
            return

        content = self.pdf_structure_editor.toPlainText()
        if not content.strip():
            QMessageBox.warning(self, "Aviso", "Por favor, adicione conteúdo ao PDF.")
            return

        # 2. CONFIGURAÇÃO DE FONTES
        fonts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
        font_path = os.path.join(fonts_dir, selected_font)

        # Se não estiver no diretório fonts/, assumir que é um caminho completo
        if not os.path.exists(font_path):
            font_path = selected_font

        # 3. REGISTRO DE FONTES
        try:
            # Registrar a fonte principal
            font_name = os.path.splitext(os.path.basename(font_path))[0]
            pdfmetrics.registerFont(TTFont(font_name, font_path))

            # Registrar fontes de fallback para Unicode
            fallback_fonts = [
                ('DejaVuSans', 'DejaVuSans.ttf'),
                ('Symbola', 'Symbola.ttf'),
                ('NotoEmoji', 'NotoEmoji.ttf'),
                ('NotoSans', 'NotoSans.ttf')
            ]

            for name, filename in fallback_fonts:
                path = os.path.join(fonts_dir, filename)
                if os.path.exists(path):
                    try:
                        pdfmetrics.registerFont(TTFont(name, path))
                    except Exception as e:
                        print(f"Erro ao registrar fonte {name}: {str(e)}")
                        continue

            # Testar a fonte principal
            test_canvas = canvas.Canvas(os.path.join(tempfile.gettempdir(), "font_test.pdf"))
            test_canvas.setFont(font_name, 10)
            test_canvas.drawString(10, 10, "Teste de fonte ABCabc123")
            test_canvas.save()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro na Fonte",
                f"Não foi possível usar a fonte selecionada:\n\n{str(e)}\n\n"
                "Por favor, selecione uma fonte TrueType (TTF) ou OpenType (OTF) válida."
            )
            return

        # 4. VALIDAÇÃO DE CARACTERES
        unsupported_chars = self.check_unsupported_characters(content, font_name)
        if unsupported_chars:
            # Tentar identificar o tipo de caracteres problemáticos
            problem_types = {
                'emoji': [c for c in unsupported_chars if c in emoji.EMOJI_DATA],
                'acentos': [c for c in unsupported_chars if ord(c) > 127 and c not in emoji.EMOJI_DATA],
                'especiais': [c for c in unsupported_chars if ord(c) < 32 or (ord(c) > 126 and ord(c) < 161)]
            }

            msg = "A fonte selecionada não suporta alguns caracteres:\n\n"

            if problem_types['emoji']:
                msg += "• Emojis: " + " ".join(problem_types['emoji'][:5]) + (
                    "..." if len(problem_types['emoji']) > 5 else "") + "\n"
            if problem_types['acentos']:
                msg += "• Caracteres acentuados: " + " ".join(problem_types['acentos'][:5]) + (
                    "..." if len(problem_types['acentos']) > 5 else "") + "\n"
            if problem_types['especiais']:
                msg += "• Símbolos especiais\n"

            msg += "\nSolução: Use uma fonte Unicode como:\n"
            msg += "- DejaVu Sans (texto geral)\n"
            msg += "- Symbola (emojis/símbolos)\n"
            msg += "- Noto Sans (multilíngue)"

            QMessageBox.warning(self, "Caracteres Não Suportados", msg)
            return

        # 5. CONFIGURAÇÃO DO DOCUMENTO
        default_dir = self.settings.get('default_export_dir', os.path.expanduser('~'))
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar PDF",
            os.path.join(default_dir, "documento.pdf"),
            "PDF Files (*.pdf)"
        )

        if not file_path:
            return

        try:
            # 6. ESTILOS DO DOCUMENTO - SOLUÇÃO DEFINITIVA PARA O PROBLEMA DE ESTILOS
            # Obter a stylesheet base
            styles = getSampleStyleSheet()

            # SOLUÇÃO PARA O ERRO "style Normal already defined":
            # 1. Criar um novo dicionário de estilos baseado no sample
            # 2. Modificar apenas os estilos que precisamos

            # Definir estilos personalizados com nomes únicos
            my_styles = {
                'MyNormal': ParagraphStyle(
                    'MyNormal',
                    parent=styles['Normal'],
                    fontName=font_name,
                    fontSize=self.font_size_spin.value(),
                    leading=self.font_size_spin.value() + 2,
                    spaceAfter=6,
                    encoding='UTF-8'
                ),
                'MyHeading1': ParagraphStyle(
                    'MyHeading1',
                    parent=styles['Heading1'],
                    fontName=font_name,
                    fontSize=self.font_size_spin.value() + 8,
                    leading=self.font_size_spin.value() + 10,
                    spaceAfter=12,
                    textColor=colors.HexColor('#2C3E50'),
                    encoding='UTF-8'
                ),
                'MyHeading2': ParagraphStyle(
                    'MyHeading2',
                    parent=styles['Heading2'],
                    fontName=font_name,
                    fontSize=self.font_size_spin.value() + 4,
                    leading=self.font_size_spin.value() + 6,
                    spaceAfter=8,
                    textColor=colors.HexColor('#3498DB'),
                    encoding='UTF-8'
                ),
                'MyCode': ParagraphStyle(
                    'MyCode',
                    parent=None,
                    fontName='Courier',
                    fontSize=self.font_size_spin.value() - 1,
                    backColor=colors.HexColor('#F5F5F5'),
                    borderColor=colors.HexColor('#DDDDDD'),
                    borderWidth=1,
                    borderPadding=(3, 3, 1),
                    leading=self.font_size_spin.value() + 1,
                    encoding='UTF-8'
                )
            }

            # 7. PROCESSAMENTO DO CONTEÚDO
            story = []
            lines = content.split('\n')
            current_paragraph = []
            in_code_block = False

            for line in lines:
                # Processar blocos de código
                if line.strip().startswith('```'):
                    if in_code_block:
                        # Finalizar bloco de código
                        code_text = '\n'.join(current_paragraph)
                        story.append(Paragraph(f"<code>{code_text}</code>", my_styles['MyCode']))
                        current_paragraph = []
                        in_code_block = False
                    else:
                        # Iniciar bloco de código
                        if current_paragraph:
                            story.append(Paragraph('<br/>'.join(current_paragraph), my_styles['MyNormal']))
                            current_paragraph = []
                        in_code_block = True
                    continue

                if in_code_block:
                    current_paragraph.append(line)
                    continue

                # Processar cabeçalhos
                if line.startswith('# '):
                    if current_paragraph:
                        story.append(Paragraph('<br/>'.join(current_paragraph), my_styles['MyNormal']))
                        current_paragraph = []
                    story.append(Paragraph(line[2:], my_styles['MyHeading1']))
                    continue

                if line.startswith('## '):
                    if current_paragraph:
                        story.append(Paragraph('<br/>'.join(current_paragraph), my_styles['MyNormal']))
                        current_paragraph = []
                    story.append(Paragraph(line[3:], my_styles['MyHeading2']))
                    continue

                # Processar imagens
                img_match = re.match(r'!\[(.*?)\]\((.*?)\)', line)
                if img_match:
                    if current_paragraph:
                        story.append(Paragraph('<br/>'.join(current_paragraph), my_styles['MyNormal']))
                        current_paragraph = []

                    alt_text, img_path = img_match.groups()
                    if os.path.exists(img_path):
                        try:
                            story.append(Spacer(1, 0.2 * inch))
                            story.append(Paragraph(f"<i>Imagem: {alt_text}</i>", my_styles['MyNormal']))
                            img = Image(img_path, width=5 * inch, height=3 * inch)
                            story.append(img)
                            story.append(Spacer(1, 0.2 * inch))
                        except:
                            story.append(Paragraph(f"[Erro ao carregar imagem: {alt_text}]", my_styles['MyNormal']))
                    else:
                        story.append(Paragraph(f"[Imagem não encontrada: {alt_text}]", my_styles['MyNormal']))
                    continue

                # Processar quebras de página
                if line.strip() == '---':
                    if current_paragraph:
                        story.append(Paragraph('<br/>'.join(current_paragraph), my_styles['MyNormal']))
                        current_paragraph = []
                    story.append(PageBreak())
                    continue

                # Adicionar linha ao parágrafo atual
                if line.strip():
                    current_paragraph.append(line)
                else:
                    if current_paragraph:
                        story.append(Paragraph('<br/>'.join(current_paragraph), my_styles['MyNormal']))
                        current_paragraph = []
                    story.append(Spacer(1, 0.2 * inch))

            # Adicionar qualquer conteúdo restante
            if current_paragraph:
                story.append(Paragraph('<br/>'.join(current_paragraph), my_styles['MyNormal']))

            # 8. CRIAÇÃO DO PDF
            doc = SimpleDocTemplate(
                file_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72,
                title="Documento Gerado pelo Automate Pro",
                author="Automate Pro",
                subject="Documento exportado",
                creator=f"Automate Pro v1.0 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                encoding='utf-8'
            )

            doc.build(story)

            # 9. NOTIFICAÇÃO DE SUCESSO
            self.notification_manager.show_notification(
                "PDF Exportado",
                f"Documento salvo com sucesso em:\n{file_path}"
            )

            # Abrir o PDF no visualizador padrão
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # macOS e Linux
                subprocess.run(['open', file_path] if sys.platform == 'darwin' else ['xdg-open', file_path])

        except Exception as e:
            error_msg = f"Erro ao gerar PDF:\n\n{str(e)}"

            # Tratamento especial para erros comuns
            if "Font" in str(e) and "not found" in str(e):
                error_msg += "\n\nA fonte selecionada não suporta todos os caracteres usados."
            elif "Style" in str(e) and "already defined" in str(e):
                error_msg += "\n\nConflito de estilos no documento."

            QMessageBox.critical(
                self,
                "Erro na Exportação",
                error_msg
            )


    def check_font_compatibility(self, font_path, text):
        """Verifica se a fonte suporta todos os caracteres do texto"""
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        try:
            font_name = os.path.splitext(os.path.basename(font_path))[0]
            pdfmetrics.registerFont(TTFont(font_name, font_path))

            # Testar cada caractere único
            unique_chars = set(text)
            problem_chars = []

            test_canvas = canvas.Canvas("temp_compatibility_test.pdf")

            for char in unique_chars:
                try:
                    test_canvas.setFont(font_name, 10)
                    test_canvas.drawString(10, 10, char)
                except:
                    problem_chars.append(char)

            test_canvas.save()
            os.remove("temp_compatibility_test.pdf")

            return problem_chars
        except Exception as e:
            return ["Erro ao testar a fonte: " + str(e)]

    def check_unsupported_characters(self, text, font_name):
        """Verifica caracteres não suportados pela fonte"""
        from reportlab.pdfgen import canvas
        from reportlab.pdfbase import pdfmetrics

        # Caracteres Unicode comuns que podem causar problemas
        test_chars = set(text)
        unsupported = []

        # Testar cada caractere único
        for char in test_chars:
            try:
                # Criar um PDF temporário para teste
                c = canvas.Canvas("char_test.pdf")
                c.setFont(font_name, 10)
                c.drawString(10, 10, char)
                c.save()
                os.remove("char_test.pdf")
            except:
                unsupported.append(char)

        return unsupported

    def add_images(self):
        """Adiciona imagens à lista de conversão"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar Imagens",
            "",
            "Imagens (*.png *.jpg *.jpeg *.gif *.bmp *.webp);;Todos os Arquivos (*)"
        )

        if file_paths:
            for file_path in file_paths:
                item = QListWidgetItem(file_path)
                self.image_list.addItem(item)

            # Mostrar preview da primeira imagem
            if self.image_list.count() > 0:
                self.show_image_preview(self.image_list.item(0))

    def clear_images(self):
        """Limpa a lista de imagens"""
        self.image_list.clear()
        self.image_preview.clear()

    def show_image_preview(self, item):
        """Mostra a pré-visualização da imagem selecionada"""
        file_path = item.text()

        try:
            if file_path.lower().endswith('.svg'):
                # Special handling for SVG files
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    # Scale SVG while maintaining aspect ratio
                    max_size = QSize(400, 400)
                    pixmap = pixmap.scaled(
                        max_size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.image_preview.setPixmap(pixmap)
            else:
                # Existing handling for other image formats
                reader = QImageReader(file_path)
                reader.setAutoTransform(True)
                image = reader.read()

                if not image.isNull():
                    max_size = QSize(400, 400)
                    image = image.scaled(
                        max_size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.image_preview.setPixmap(QPixmap.fromImage(image))
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao carregar imagem: {str(e)}")

    def toggle_resize_options(self, state):
        """Ativa/desativa as opções de redimensionamento"""
        enabled = state == Qt.CheckState.Checked.value
        self.image_width_spin.setEnabled(enabled)
        self.image_height_spin.setEnabled(enabled)

    def convert_images(self):
        """Converte as imagens selecionadas para o formato especificado"""
        if self.image_list.count() == 0:
            QMessageBox.warning(self, "Aviso", "Por favor, adicione pelo menos uma imagem.")
            return

        output_format = self.image_format_combo.currentText().lower()
        quality = self.image_quality_spin.value()
        resize = self.image_resize_check.isChecked()
        width = self.image_width_spin.value() if resize else None
        height = self.image_height_spin.value() if resize else None

        default_dir = self.settings.get('default_export_dir', os.path.expanduser('~'))
        output_dir = QFileDialog.getExistingDirectory(
            self,
            "Selecionar Diretório de Saída",
            default_dir
        )

        if not output_dir:
            return

        try:
            for i in range(self.image_list.count()):
                item = self.image_list.item(i)
                input_path = item.text()
                file_name = os.path.splitext(os.path.basename(input_path))[0]
                output_path = os.path.join(output_dir, f"{file_name}.{output_format}")

                # Carregar imagem original
                image = QImage(input_path)
                if image.isNull():
                    raise Exception(f"Falha ao carregar imagem: {input_path}")

                # Redimensionar se necessário
                if resize:
                    image = image.scaled(
                        width, height,
                        Qt.AspectRatioMode.IgnoreAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )

                # Salvar no novo formato
                if not image.save(output_path, quality=quality):
                    raise Exception(f"Falha ao salvar imagem: {output_path}")

            QMessageBox.information(
                self,
                "Sucesso",
                f"{self.image_list.count()} imagens convertidas com sucesso!"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao converter imagens: {str(e)}")

    def save_note(self):
        """Salva uma nova anotação"""
        title = self.note_title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Aviso", "Por favor, insira um título para a anotação.")
            return

        content = self.note_content_editor.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "Aviso", "Por favor, adicione conteúdo à anotação.")
            return

        try:
            note_id = self.notes_manager.create_note(
                title=title,
                content=content,
                tags=self.note_tags_input.text()
            )

            QMessageBox.information(self, "Sucesso", "Anotação salva com sucesso!")
            self.clear_note_form()
            self.filter_notes()

            # Atualizar dashboard
            self.load_initial_data()

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar anotação: {str(e)}")

    def clear_note_form(self):
        """Limpa o formulário de anotação"""
        self.note_title_input.clear()
        self.note_tags_input.clear()
        self.note_content_editor.clear()
        self.note_content_preview.clear()

    def clean_system(self):
        """Limpa diretórios temporários do sistema"""
        # Definir os diretórios a serem limpos (relativos à pasta do aplicativo)
        temp_dirs = [
            os.path.join(os.path.dirname(self.db.db_path), "temp"),
            os.path.join(os.path.dirname(self.db.db_path), "cache"),
            os.path.join(os.path.dirname(self.db.db_path), "logs"),
            os.path.join(os.path.dirname(self.db.db_path), "relatorios_temp")
        ]

        # Pedir confirmação antes de limpar
        reply = QMessageBox.question(
            self, 'Confirmar Limpeza',
            'Tem certeza que deseja limpar todos os diretórios temporários?\n'
            'Esta ação não pode ser desfeita.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            cleaned_dirs = []
            for directory in temp_dirs:
                if os.path.exists(directory):
                    # Limpar o diretório
                    shutil.rmtree(directory)
                    # Recriar o diretório vazio
                    os.makedirs(directory, exist_ok=True)
                    cleaned_dirs.append(directory)

            # Mostrar resultado
            if cleaned_dirs:
                message = "Diretórios limpos com sucesso:\n"
                message += "\n".join(f"• {d}" for d in cleaned_dirs)

                # Registrar no histórico
                self.db.execute_query(
                    '''INSERT INTO history (action, module, details) 
                       VALUES (?, ?, ?)''',
                    ('cleanup', 'system', 'Limpeza de diretórios temporários realizada')
                )
            else:
                message = "Nenhum diretório temporário encontrado para limpeza."

            QMessageBox.information(
                self,
                "Limpeza Concluída",
                message
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro na Limpeza",
                f"Falha ao limpar diretórios:\n{str(e)}"
            )

    def update_note_preview(self, index):
        """Atualiza a pré-visualização Markdown quando a aba é alterada"""
        if index == 1:  # Aba de visualização
            markdown_text = self.note_content_editor.toPlainText()
            html = markdown.markdown(markdown_text)
            self.note_content_preview.setHtml(html)

    def filter_notes(self):
        """Filtra a lista de anotações com base na pesquisa"""
        search_query = self.notes_search_input.text().strip()
        notes = self.notes_manager.get_notes(search_query)

        self.notes_list.clear()
        for note in notes:
            item = QListWidgetItem(note[1])  # note title
            item.setData(Qt.ItemDataRole.UserRole, note[0])  # note id
            self.notes_list.addItem(item)

    def show_note_details(self):
        """Mostra os detalhes da anotação selecionada"""
        selected_items = self.notes_list.selectedItems()
        if not selected_items:
            self.note_details.clear()
            return

        note_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        note = self.db.execute_query(
            "SELECT title, content, tags, created_at, updated_at FROM notes WHERE id = ?",
            (note_id,),
            fetchone=True
        )

        if note:
            title, content, tags, created_at, updated_at = note
            html = f"""
            <div style='font-family: {self.settings.get('font_family', 'Segoe UI')}; font-size: {self.settings.get('font_size', '12')}px;'>
                <h2>{title}</h2>
                <p><strong>Tags:</strong> {tags or 'Nenhuma'}</p>
                <p><strong>Criada em:</strong> {created_at}</p>
                <p><strong>Atualizada em:</strong> {updated_at}</p>
                <hr>
                {markdown.markdown(content)}
            </div>
            """
            self.note_details.setHtml(html)

    def edit_selected_note(self):
        """Edita a anotação selecionada"""
        selected_items = self.notes_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione uma anotação.")
            return

        note_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        note = self.db.execute_query(
            "SELECT * FROM notes WHERE id = ?",
            (note_id,),
            fetchone=True
        )

        if note:
            # Mudar para a aba de edição
            self.notes_tab.setCurrentIndex(0)

            # Preencher os campos
            self.note_title_input.setText(note[1])
            self.note_tags_input.setText(note[3] if note[3] else "")
            self.note_content_editor.setPlainText(note[2] if note[2] else "")

            # Substituir o botão Salvar por Atualizar
            if hasattr(self, 'update_note_button'):
                self.update_note_button.deleteLater()

            self.update_note_button = QPushButton("Atualizar Anotação")
            self.update_note_button.clicked.connect(lambda: self.update_note_data(note_id))

            # Adicionar o botão ao layout
            layout = self.notes_new_tab.layout()
            if layout:
                layout.addRow(self.update_note_button)

    def update_note_data(self, note_id):
        """Atualiza os dados da anotação"""
        title = self.note_title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Aviso", "Por favor, insira um título para a anotação.")
            return

        content = self.note_content_editor.toPlainText().strip()
        if not content:
            QMessageBox.warning(self, "Aviso", "Por favor, adicione conteúdo à anotação.")
            return

        try:
            self.notes_manager.update_note(
                note_id,
                title=title,
                content=content,
                tags=self.note_tags_input.text()
            )

            QMessageBox.information(self, "Sucesso", "Anotação atualizada com sucesso!")
            self.clear_note_form()
            self.filter_notes()

            # Remover o botão de atualização
            if hasattr(self, 'update_note_button'):
                self.update_note_button.deleteLater()
                del self.update_note_button

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao atualizar anotação: {str(e)}")

    def delete_note(self):
        """Exclui a anotação selecionada"""
        selected_items = self.notes_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione uma anotação.")
            return

        note_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        note_title = selected_items[0].text()

        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Tem certeza que deseja excluir a anotação '{note_title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.execute_query("DELETE FROM notes WHERE id = ?", (note_id,))
                self.filter_notes()
                self.load_initial_data()  # Atualizar dashboard
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao excluir anotação: {str(e)}")

    def export_note(self):
            """Exporta a anotação selecionada"""
            selected_items = self.notes_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Aviso", "Por favor, selecione uma anotação.")
                return

            note_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
            note = self.db.execute_query(
                "SELECT title, content FROM notes WHERE id = ?",
                (note_id,),
                fetchone=True
            )

            if not note:
                QMessageBox.warning(self, "Aviso", "Anotação não encontrada.")
                return

            default_dir = self.settings.get('default_export_dir', os.path.expanduser('~'))
            file_path, selected_filter = QFileDialog.getSaveFileName(
                self,
                "Exportar Anotação",
                os.path.join(default_dir, f"{note[0]}.md"),
                "Markdown (*.md);;HTML (*.html);;Texto (*.txt)"
            )

            if file_path:
                try:
                    if selected_filter == "HTML (*.html)":
                        html_content = markdown.markdown(note[1])
                        full_html = f"""<!DOCTYPE html>
    <html>
    <head>
        <title>{note[0]}</title>
        <meta charset="UTF-8">
    </head>
    <body>
        <h1>{note[0]}</h1>
        {html_content}
    </body>
    </html>"""
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(full_html)
                    else:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(f"# {note[0]}\n\n{note[1]}")

                    QMessageBox.information(self, "Sucesso", "Anotação exportada com sucesso!")
                except Exception as e:
                    QMessageBox.critical(self, "Erro", f"Falha ao exportar anotação: {str(e)}")

    def save_command(self):
        """Salva um novo comando personalizado"""
        name = self.command_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Aviso", "Por favor, insira um nome para o comando.")
            return

        command = self.command_text_input.toPlainText().strip()
        if not command:
            QMessageBox.warning(self, "Aviso", "Por favor, insira o comando.")
            return

        try:
            # Use the commands_manager to save the command
            self.commands_manager.add_command(
                name=name,
                command=command,
                category=self.command_category_input.text(),
                tags=self.command_tags_input.text()
            )

            QMessageBox.information(self, "Sucesso", "Comando salvo com sucesso!")
            self.clear_command_form()
            self.filter_custom_commands()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar comando: {str(e)}")

    def clear_command_form(self):
        """Limpa o formulário de comando"""
        self.command_name_input.clear()
        self.command_text_input.clear()
        self.command_category_input.clear()
        self.command_tags_input.clear()

    def filter_custom_commands(self):
        """Filtra a lista de comandos personalizados com base na pesquisa"""
        search_query = ""  # Você pode adicionar um campo de pesquisa se necessário
        commands = self.commands_manager.get_commands(search_query)

        self.commands_list.clear()
        for command in commands:
            item = QListWidgetItem(command[1])  # command name
            item.setData(Qt.ItemDataRole.UserRole, command[0])  # command id
            self.commands_list.addItem(item)

    def show_command_details(self):
        """Mostra os detalhes do comando selecionado"""
        selected_items = self.commands_list.selectedItems()
        if not selected_items:
            return

        command_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        command = self.db.execute_query(
            "SELECT name, command, category, tags FROM custom_commands WHERE id = ?",
            (command_id,),
            fetchone=True
        )

        if command:
            name, cmd, category, tags = command
            details = f"""
            <b>Nome:</b> {name}<br>
            <b>Categoria:</b> {category or 'Nenhuma'}<br>
            <b>Tags:</b> {tags or 'Nenhuma'}<br><br>
            <b>Comando:</b><br>
            <pre>{cmd}</pre>
            """
            QMessageBox.information(self, "Detalhes do Comando", details)

    def run_selected_command(self):
        """Executa o comando personalizado selecionado"""
        selected_items = self.commands_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um comando.")
            return

        command_id = selected_items[0].data(Qt.ItemDataRole.UserRole)

        try:
            output = self.commands_manager.execute_command(command_id)
            if output:
                QMessageBox.information(self, "Saída do Comando", output)
            else:
                self.statusbar.showMessage("Comando executado com sucesso!", 3000)
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao executar comando: {str(e)}")

    def edit_selected_command(self):
        """Edita o comando personalizado selecionado"""
        selected_items = self.commands_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um comando.")
            return

        command_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        command = self.db.execute_query(
            "SELECT * FROM custom_commands WHERE id = ?",
            (command_id,),
            fetchone=True
        )

        if command:
            # Preencher os campos com os dados do comando
            self.command_name_input.setText(command[1])
            self.command_text_input.setPlainText(command[2])
            self.command_category_input.setText(command[3] if command[3] else "")
            self.command_tags_input.setText(command[4] if command[4] else "")

            # Substituir o botão Salvar por Atualizar
            if hasattr(self, 'update_command_button'):
                self.update_command_button.deleteLater()

            self.update_command_button = QPushButton("Atualizar Comando")
            self.update_command_button.clicked.connect(lambda: self.update_command_data(command_id))

            # Adicionar o botão ao layout
            layout = self.findChild(QFormLayout)
            if layout:
                layout.addRow(self.update_command_button)

    def update_command_data(self, command_id):
        """Atualiza os dados do comando"""
        name = self.command_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Aviso", "Por favor, insira um nome para o comando.")
            return

        command = self.command_text_input.toPlainText().strip()
        if not command:
            QMessageBox.warning(self, "Aviso", "Por favor, insira o comando.")
            return

        try:
            self.db.execute_query(
                "UPDATE custom_commands SET name = ?, command = ?, category = ?, tags = ? WHERE id = ?",
                (name, command, self.command_category_input.text(), self.command_tags_input.text(), command_id)
            )

            QMessageBox.information(self, "Sucesso", "Comando atualizado com sucesso!")
            self.clear_command_form()
            self.filter_custom_commands()

            # Remover o botão de atualização
            if hasattr(self, 'update_command_button'):
                self.update_command_button.deleteLater()
                del self.update_command_button

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao atualizar comando: {str(e)}")

    def delete_command(self):
        """Exclui o comando personalizado selecionado"""
        selected_items = self.commands_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um comando.")
            return

        command_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        command_name = selected_items[0].text()

        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            f"Tem certeza que deseja excluir o comando '{command_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.execute_query("DELETE FROM custom_commands WHERE id = ?", (command_id,))
                self.filter_custom_commands()
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao excluir comando: {str(e)}")

    def copy_command(self):
        """Copia o comando selecionado para a área de transferência"""
        selected_items = self.commands_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Aviso", "Por favor, selecione um comando.")
            return

        command_id = selected_items[0].data(Qt.ItemDataRole.UserRole)
        command = self.db.execute_query(
            "SELECT command FROM custom_commands WHERE id = ?",
            (command_id,),
            fetchone=True
        )

        if command and command[0]:
            clipboard = QApplication.clipboard()
            clipboard.setText(command[0])
            self.statusbar.showMessage("Comando copiado para a área de transferência!", 3000)

    def save_settings(self):
        """Salva as configurações do sistema"""
        try:
            # Geral
            language_map = {
                "Português": "pt",
                "English": "en",
                "Español": "es"
            }
            language = language_map.get(self.language_combo.currentText(), "pt")
            self.settings.save_setting('language', language)

            self.settings.save_setting('default_project_dir', self.default_project_dir_input.text())
            self.settings.save_setting('default_export_dir', self.default_export_dir_input.text())

            # Aparência
            theme_map = {
                "Escuro": "dark",
                "Claro": "light",
                "Azul": "blue"
            }
            theme = theme_map.get(self.theme_combo.currentText(), "dark")
            self.settings.save_setting('theme', theme)

            self.settings.save_setting('font_family', self.font_family_combo.currentText())
            self.settings.save_setting('font_size', str(self.font_size_spin.value()))
            self.settings.save_setting('markdown_preview', '1' if self.markdown_preview_check.isChecked() else '0')

            # Backup
            self.settings.save_setting('auto_backup', '1' if self.auto_backup_check.isChecked() else '0')
            self.settings.save_setting('backup_interval', str(self.backup_interval_spin.value()))
            self.settings.save_setting('backup_dir', self.backup_dir_input.text())

            # Avançado
            self.settings.save_setting('portable_mode', '1' if self.portable_mode_check.isChecked() else '0')
            self.settings.save_setting('auto_update', '1' if self.auto_update_check.isChecked() else '0')
            self.settings.save_setting('enable_shortcuts', '1' if self.enable_shortcuts_check.isChecked() else '0')
            self.settings.save_setting('enable_notifications',
                                       '1' if self.enable_notifications_check.isChecked() else '0')
            self.settings.save_setting('enable_drag_drop', '1' if self.enable_drag_drop_check.isChecked() else '0')

            # Aplicar tema imediatamente
            self.theme_manager.apply_theme(QApplication.instance(), theme)

            QMessageBox.information(self, "Sucesso", "Configurações salvas com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar configurações: {str(e)}")

    def reset_settings(self):
        """Restaura as configurações padrão"""
        reply = QMessageBox.question(
            self, "Confirmar Restauração",
            "Tem certeza que deseja restaurar as configurações padrão?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Excluir todas as configurações
                self.db.execute_query("DELETE FROM settings")

                # Recarregar configurações padrão
                self.settings.load_settings()

                # Recarregar a página de configurações para refletir as mudanças
                self.settings_tab.setCurrentIndex(0)
                self.load_initial_data()

                QMessageBox.information(self, "Sucesso", "Configurações restauradas com sucesso!")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao restaurar configurações: {str(e)}")

    def create_manual_backup(self):
        """Cria um backup manual do sistema"""
        backup_dir = self.settings.get('backup_dir')
        if not backup_dir:
            QMessageBox.warning(self, "Aviso", "Por favor, configure um diretório de backup nas configurações.")
            return

        try:
            backup_file = self.backup_manager.create_backup(backup_dir)
            QMessageBox.information(
                self,
                "Backup Concluído",
                f"Backup criado com sucesso:\n{backup_file}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao criar backup: {str(e)}")

    def run_auto_backup(self):
        """Executa o backup automático baseado nas configurações"""
        if self.settings.get_bool('auto_backup'):
            backup_dir = self.settings.get('backup_dir')
            if backup_dir:
                try:
                    self.backup_manager.create_backup(backup_dir)
                    self.notification_manager.show_notification(
                        "Backup Automático",
                        "Backup do sistema realizado com sucesso."
                    )
                except Exception as e:
                    self.notification_manager.show_notification(
                        "Erro no Backup",
                        f"Falha ao realizar backup automático: {str(e)}"
                    )

    def check_reminders(self):
        """Verifica lembretes pendentes e mostra notificações"""
        if not self.settings.get_bool('enable_notifications'):
            return

        reminders = self.reminders_manager.get_reminders(upcoming_only=True)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        for reminder in reminders:
            if reminder[3] <= now and not reminder[4]:  # due_date <= now and not completed
                self.notification_manager.show_notification(
                    f"Lembrete: {reminder[1]}",  # title
                    reminder[2] or "Sem descrição"  # description
                )

                # Marcar como concluído para não notificar novamente
                self.reminders_manager.mark_completed(reminder[0])

    def focus_search(self):
        """Coloca o foco no campo de busca global"""
        self.global_search.setFocus()

    def perform_global_search(self):
        """Realiza uma busca global no sistema"""
        query = self.global_search.text().strip()
        if not query:
            return

        # Aqui você pode implementar a busca em todos os módulos
        # e mostrar os resultados em uma nova janela ou aba
        QMessageBox.information(
            self,
            "Busca Global",
            f"Resultados da busca por: {query}\n\nEsta funcionalidade será implementada."
        )

    def show_new_project(self):
        """Mostra a página de novo projeto"""
        self.sidebar.setCurrentRow(1)  # Índice da página de projetos
        self.projects_tab.setCurrentIndex(0)  # Índice da aba "Novo Projeto"

    def show_settings(self):
        """Mostra a página de configurações"""
        self.sidebar.setCurrentRow(9)  # Índice da página de configurações

    def show_about(self):
        """Mostra a caixa de diálogo 'Sobre'"""
        QMessageBox.about(self, "Sobre Automate Pro",
                          "Automate Pro v1.0\n\n"
                          "Sistema de automação pessoal e produtividade.\n"
                          "© 2023 Automate Pro. Todos os direitos reservados.")

    def change_theme(self, theme_name):
        """Muda o tema visual do aplicativo"""
        self.theme_manager.apply_theme(QApplication.instance(), theme_name)

    def closeEvent(self, event):
        """Evento chamado quando a janela está sendo fechada"""
        # Salvar configurações antes de sair
        reply = QMessageBox.question(
            self, "Sair",
            "Tem certeza que deseja sair do Automate Pro?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()
class DownloadManager:
    """Classe para gerenciamento completo de downloads"""

    def __init__(self, db):
        self.db = db
        self.downloads_dir = os.path.join(os.path.expanduser("~"), "AutomatePro", "Downloads")
        os.makedirs(self.downloads_dir, exist_ok=True)

        # Verificar e instalar dependências necessárias
        self.check_dependencies()

    def check_dependencies(self):
        """Verifica e instala dependências necessárias"""
        try:
            import yt_dlp
            import ffmpeg
        except ImportError:
            # Tentar instalar automaticamente (em ambiente controlado)
            try:
                import subprocess
                subprocess.run([sys.executable, "-m", "pip", "install", "yt-dlp", "ffmpeg-python"], check=True)
            except Exception as e:
                print(f"Erro ao instalar dependências: {str(e)}")

    def add_download(self, url, download_type, format, quality, save_path=None):
        """Adiciona um novo download à fila"""
        if save_path is None:
            save_path = self.downloads_dir

        download_id = self.db.execute_query(
            '''INSERT INTO downloads (url, type, format, quality, save_path, status) 
               VALUES (?, ?, ?, ?, ?, ?)''',
            (url, download_type, format, quality, save_path, 'pending')
        )

        # Registrar no histórico
        self.db.execute_query(
            '''INSERT INTO history (action, module, details) 
               VALUES (?, ?, ?)''',
            ('add', 'downloads', f'Added download {url}')
        )

        return download_id

    def start_download(self, download_id):
        """Inicia um download específico"""
        download = self.db.execute_query(
            "SELECT * FROM downloads WHERE id = ?",
            (download_id,),
            fetchone=True
        )

        if not download:
            raise Exception("Download não encontrado")

        url = download[1]
        download_type = download[2]
        format = download[3]
        quality = download[4]
        save_path = download[5]

        try:
            self.db.execute_query(
                "UPDATE downloads SET status = ? WHERE id = ?",
                ('downloading', download_id))

            if 'youtube.com' in url or 'youtu.be' in url:
                self.download_youtube(url, format, quality, save_path, download_id)
            elif 'vimeo.com' in url:
                self.download_vimeo(url, format, quality, save_path, download_id)
            else:
                self.download_generic(url, save_path, download_id)

            self.db.execute_query(
                "UPDATE downloads SET status = ? WHERE id = ?",
                ('completed', download_id))

            # Registrar no histórico
            self.db.execute_query(
                '''INSERT INTO history (action, module, details) 
                   VALUES (?, ?, ?)''',
                ('complete', 'downloads', f'Completed download ID {download_id}'))

            return True
        except Exception as e:
            self.db.execute_query(
                "UPDATE downloads SET status = ? WHERE id = ?",
                ('failed', download_id))
            raise Exception(f"Falha ao baixar: {str(e)}")

    def download_youtube(self, url, format, quality, save_path, download_id):
        """Download de vídeos do YouTube"""
        import yt_dlp

        ydl_opts = {
            'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
            'progress_hooks': [lambda d: self.progress_hook(d, download_id)],
        }

        # Configurações baseadas no formato desejado
        if format == 'mp3':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality,
                }],
            })
        elif format == 'mp4':
            ydl_opts.update({
                'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]',
            })
        else:
            ydl_opts.update({
                'format': 'best',
            })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    def download_vimeo(self, url, format, quality, save_path, download_id):
        """Download de vídeos do Vimeo"""
        # Implementação similar ao YouTube
        self.download_youtube(url, format, quality, save_path, download_id)

    def download_generic(self, url, save_path, download_id):
        """Download de arquivos genéricos"""
        import requests
        from urllib.parse import urlparse

        local_filename = os.path.join(save_path, os.path.basename(urlparse(url).path))

        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))

            self.db.execute_query(
                "UPDATE downloads SET total_size = ? WHERE id = ?",
                (total_size, download_id))

            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        # Atualizar progresso
                        current_size = os.path.getsize(local_filename)
                        progress = (current_size / total_size) * 100 if total_size > 0 else 0

                        self.db.execute_query(
                            "UPDATE downloads SET progress = ? WHERE id = ?",
                            (progress, download_id))

    def progress_hook(self, d, download_id):
        """Atualiza o progresso do download"""
        if d['status'] == 'downloading':
            progress = d.get('_percent_str', '0%').replace('%', '')
            self.db.execute_query(
                "UPDATE downloads SET progress = ? WHERE id = ?",
                (float(progress), download_id))

    def get_downloads(self, status=None):
        """Obtém a lista de downloads"""
        query = "SELECT * FROM downloads"
        params = []

        if status:
            query += " WHERE status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC"
        return self.db.execute_query(query, params, fetchall=True)

    def pause_download(self, download_id):
        """Pausa um download em andamento"""
        # Implementação mais complexa requerida para pausar downloads reais
        self.db.execute_query(
            "UPDATE downloads SET status = ? WHERE id = ?",
            ('paused', download_id))

    def resume_download(self, download_id):
        """Retoma um download pausado"""
        download = self.db.execute_query(
            "SELECT * FROM downloads WHERE id = ? AND status = 'paused'",
            (download_id,),
            fetchone=True)

        if download:
            self.start_download(download_id)

    def cancel_download(self, download_id):
        """Cancela um download"""
        self.db.execute_query(
            "UPDATE downloads SET status = ? WHERE id = ?",
            ('cancelled', download_id))

    def get_available_formats(self, url):
        """Obtém formatos disponíveis para um URL"""
        try:
            import yt_dlp

            with yt_dlp.YoutubeDL() as ydl:
                info = ydl.extract_info(url, download=False)

                if 'entries' in info:
                    # É uma playlist
                    info = info['entries'][0]

                formats = {}
                if 'formats' in info:
                    for f in info['formats']:
                        if f.get('vcodec') != 'none':
                            # Formato de vídeo
                            resolution = f.get('height', '?')
                            formats[f'video-{resolution}p'] = f.get('format_note', f'Format {f["format_id"]}')

                if 'requested_formats' in info:
                    for f in info['requested_formats']:
                        if f.get('acodec') != 'none':
                            # Formato de áudio
                            formats['audio'] = f'Audio ({f.get("abr", "?")} kbps)'

                return formats
        except Exception:
            # Para URLs não-YouTube, retornar formatos genéricos
            return {
                'original': 'Original',
                'pdf': 'PDF (para páginas web)',
                'html': 'HTML completo'
            }
class DownloadDialog(QDialog):
    """Diálogo para adicionar novos downloads"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar Download")
        self.setFixedSize(500, 300)

        self.download_manager = parent.download_manager
        self.settings = parent.settings

        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Campo para URL
        url_layout = QHBoxLayout()
        url_label = QLabel("URL:")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Cole o link aqui (YouTube, Vimeo, arquivo, etc.)")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)

        # Botão para detectar formato
        detect_button = QPushButton("Detectar Formato")
        detect_button.clicked.connect(self.detect_format)

        # Local de salvamento
        save_layout = QHBoxLayout()
        save_label = QLabel("Salvar em:")
        self.save_input = QLineEdit(self.download_manager.downloads_dir)
        browse_button = QPushButton("Procurar...")
        browse_button.clicked.connect(self.browse_save_location)
        save_layout.addWidget(save_label)
        save_layout.addWidget(self.save_input)
        save_layout.addWidget(browse_button)

        # Formato e qualidade
        format_layout = QHBoxLayout()
        format_label = QLabel("Formato:")
        self.format_combo = QComboBox()
        self.format_combo.addItems(["Auto", "MP4", "MP3", "AVI", "WAV", "WEBM", "PDF"])
        format_layout.addWidget(format_label)
        format_layout.addWidget(self.format_combo)

        quality_label = QLabel("Qualidade:")
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Máxima", "1080p", "720p", "480p", "360p"])
        format_layout.addWidget(quality_label)
        format_layout.addWidget(self.quality_combo)

        # Botões
        button_layout = QHBoxLayout()
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        download_button = QPushButton("Iniciar Download")
        download_button.clicked.connect(self.start_download)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(download_button)

        # Adicionar widgets ao layout principal
        layout.addLayout(url_layout)
        layout.addWidget(detect_button)
        layout.addLayout(save_layout)
        layout.addLayout(format_layout)
        layout.addLayout(button_layout)

    def browse_save_location(self):
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Selecionar Pasta de Downloads",
            self.settings.get('default_download_dir', os.path.expanduser('~'))
        )

        if dir_path:
            self.save_input.setText(dir_path)

    def detect_format(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Aviso", "Por favor, insira um URL primeiro.")
            return

        try:
            formats = self.download_manager.get_available_formats(url)

            self.format_combo.clear()
            if formats:
                self.format_combo.addItems(formats.values())
            else:
                self.format_combo.addItems(["Auto"])

            QMessageBox.information(
                self,
                "Formatos Disponíveis",
                "Formatos detectados com sucesso!" if formats else "Usando formato padrão.")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro",
                f"Não foi possível detectar formatos: {str(e)}")

    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Aviso", "Por favor, insira um URL válido.")
            return

        save_path = self.save_input.text().strip()
        format = self.format_combo.currentText()
        quality = self.quality_combo.currentText()

        try:
            download_id = self.download_manager.add_download(
                url=url,
                download_type='video' if 'youtube' in url or 'vimeo' in url else 'file',
                format=format.lower(),
                quality=quality,
                save_path=save_path
            )

            # Iniciar download em uma thread separada
            import threading
            threading.Thread(
                target=self.download_manager.start_download,
                args=(download_id,),
                daemon=True
            ).start()

            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao iniciar download: {str(e)}")
class DownloadItemWidget(QWidget):
    """Widget personalizado para exibir um item de download na lista"""

    def __init__(self, download_data, parent=None):
        super().__init__(parent)
        self.download_data = download_data
        self.download_manager = parent.download_manager

        self.setup_ui()
        self.update_display()

    def setup_ui(self):
        self.layout = QHBoxLayout(self)

        # Ícone do tipo de arquivo
        self.icon_label = QLabel()
        self.set_file_icon()

        # Informações do download
        info_layout = QVBoxLayout()

        self.name_label = QLabel()
        self.name_label.setStyleSheet("font-weight: bold;")

        self.progress_label = QLabel()
        self.status_label = QLabel()

        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.progress_label)
        info_layout.addWidget(self.status_label)

        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)

        # Botões de ação
        button_layout = QHBoxLayout()

        self.pause_button = QPushButton("Pausar")
        self.pause_button.clicked.connect(self.toggle_pause)

        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.cancel_download)

        self.open_button = QPushButton("Abrir")
        self.open_button.clicked.connect(self.open_file)
        self.open_button.setEnabled(False)

        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.open_button)

        # Adicionar widgets ao layout
        self.layout.addWidget(self.icon_label)
        self.layout.addLayout(info_layout)
        self.layout.addWidget(self.progress_bar)
        self.layout.addLayout(button_layout)

    def set_file_icon(self):
        # Configurar ícone baseado no tipo de arquivo
        file_type = self.download_data[2]  # type (video, audio, file)
        icon_name = {
            'video': 'video-x-generic',
            'audio': 'audio-x-generic',
            'file': 'text-x-generic'
        }.get(file_type, 'text-x-generic')

        self.icon_label.setPixmap(QIcon.fromTheme(icon_name).pixmap(32, 32))

    def update_display(self):
        """Atualiza a exibição com os dados mais recentes"""
        _, url, download_type, format, _, save_path, status, progress, total_size, _ = self.download_data

        # Extrair nome do arquivo da URL ou do caminho
        file_name = os.path.basename(url)
        if not file_name or '.' not in file_name:
            file_name = f"download.{format.lower()}"

        self.name_label.setText(file_name)

        # Atualizar barra de progresso
        self.progress_bar.setValue(int(progress))

        # Atualizar labels de status e progresso
        self.status_label.setText(f"Status: {status}")

        if total_size:
            size_mb = total_size / (1024 * 1024)
            self.progress_label.setText(f"{progress:.1f}% de {size_mb:.1f} MB")
        else:
            self.progress_label.setText(f"{progress:.1f}%")

        # Atualizar botões baseado no status
        if status == 'completed':
            self.pause_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
            self.open_button.setEnabled(True)
        elif status == 'downloading':
            self.pause_button.setEnabled(True)
            self.cancel_button.setEnabled(True)
            self.open_button.setEnabled(False)
        elif status == 'paused':
            self.pause_button.setText("Retomar")
            self.cancel_button.setEnabled(True)
            self.open_button.setEnabled(False)

    def toggle_pause(self):
        """Pausa ou retoma o download"""
        download_id = self.download_data[0]

        if self.download_data[7] == 'paused':  # status
            self.download_manager.resume_download(download_id)
            self.pause_button.setText("Pausar")
        else:
            self.download_manager.pause_download(download_id)
            self.pause_button.setText("Retomar")

        self.update_display()

    def cancel_download(self):
        """Cancela o download"""
        download_id = self.download_data[0]
        self.download_manager.cancel_download(download_id)
        self.update_display()

    def open_file(self):
        """Abre o arquivo baixado"""
        _, _, _, _, _, save_path, _, _, _, _ = self.download_data

        if os.path.exists(save_path):
            if sys.platform == "win32":
                os.startfile(save_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", save_path])
            else:
                subprocess.Popen(["xdg-open", save_path])
        else:
            QMessageBox.warning(self, "Aviso", "Arquivo não encontrado.")
class DownloadsPage(QWidget):
    """Página de gerenciamento de downloads"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.download_manager = parent.download_manager

        self.setup_ui()
        self.load_downloads()

        # Configurar timer para atualizar a lista
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.load_downloads)
        self.update_timer.start(5000)  # Atualizar a cada 5 segundos

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Barra de ferramentas
        toolbar = QToolBar()
        add_button = QAction(QIcon.fromTheme("list-add"), "Adicionar Download", self)
        add_button.triggered.connect(self.show_add_download_dialog)

        refresh_button = QAction(QIcon.fromTheme("view-refresh"), "Atualizar", self)
        refresh_button.triggered.connect(self.load_downloads)

        toolbar.addAction(add_button)
        toolbar.addAction(refresh_button)

        # Filtros
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Filtrar:")
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Todos", "Em andamento", "Concluídos", "Pausados", "Falhas"])
        self.filter_combo.currentIndexChanged.connect(self.load_downloads)

        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_combo)

        # Lista de downloads
        self.downloads_list = QListWidget()
        self.downloads_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.downloads_list.setStyleSheet("QListWidget::item { border-bottom: 1px solid #ddd; }")

        # Adicionar widgets ao layout
        layout.addWidget(toolbar)
        layout.addLayout(filter_layout)
        layout.addWidget(self.downloads_list)

    def show_add_download_dialog(self):
        dialog = DownloadDialog(self.main_window)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_downloads()

    def load_downloads(self):
        """Carrega a lista de downloads"""
        filter_text = self.filter_combo.currentText()
        status_map = {
            "Todos": None,
            "Em andamento": "downloading",
            "Concluídos": "completed",
            "Pausados": "paused",
            "Falhas": "failed"
        }

        status = status_map.get(filter_text)
        downloads = self.download_manager.get_downloads(status)

        self.downloads_list.clear()

        for download in downloads:
            item = QListWidgetItem()
            widget = DownloadItemWidget(download, self)

            item.setSizeHint(widget.sizeHint())
            self.downloads_list.addItem(item)
            self.downloads_list.setItemWidget(item, widget)

    def clear_downloads_list(self):
        """Limpa a lista de downloads concluídos ou não"""
        reply = QMessageBox.question(
            self,
            "Confirmar Limpeza",
            "Tem certeza que deseja limpar toda a lista de downloads?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.db.execute_query("DELETE FROM downloads")
                self.load_downloads()  # Recarrega a lista vazia
                self.notification_manager.show_notification(
                    "Lista Limpa",
                    "A lista de downloads foi limpa com sucesso!"
                )
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Falha ao limpar lista: {str(e)}")


    def create_downloads_page(self):
        """Cria a página de gerenciamento de downloads"""
        self.downloads_page = DownloadsPage(self)
        self.content_area.addWidget(self.downloads_page)

        clear_downloads_button = QPushButton("Limpar Lista")
        clear_downloads_button.clicked.connect(self.clear_downloads_list)

        # Adicionar à barra lateral
        self.sidebar.addItem("Downloads")

        # Ajustar o índice se necessário
        self.sidebar.setCurrentRow(0)

def main():
    """Função principal para iniciar o aplicativo"""
    app = QApplication(sys.argv)

    # Configurar fonte padrão
    font = QFont()
    font.setFamily("Segoe UI")
    font.setPointSize(10)
    app.setFont(font)

    # Criar e mostrar janela principal
    window = MainWindow()
    window.show()

    # Executar loop de eventos
    sys.exit(app.exec())


if __name__ == "__main__":
    main()