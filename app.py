from PIL import Image
import os
from fpdf.enums import XPos, YPos
import json
import subprocess
import threading
import datetime
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from fpdf import FPDF


# Configuração inicial
ctk.set_appearance_mode("Dark")  # Modo escuro padrão
ctk.set_default_color_theme("blue")  # Tema azul


class PAS(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Configuração da janela principal
        self.title("Personal Automation System")
        self.geometry("1200x700")
        self.minsize(1000, 600)

        # Carregar configurações
        self.load_settings()

        # Inicializar dados
        self.load_data()

        # Layout principal
        self.create_main_layout()

        # Exibir página inicial
        self.show_home_page()
    def load_settings(self):
        """Carrega as configurações do arquivo settings.json"""
        self.settings_file = "data/settings.json"
        default_settings = {
            "theme": "Dark",
            "language": "pt",
            "default_dir": os.path.expanduser("~"),
            "auto_save": True,
            "recent_projects": []
        }

        try:
            os.makedirs("data", exist_ok=True)
            if not os.path.exists(self.settings_file):
                with open(self.settings_file, "w") as f:
                    json.dump(default_settings, f, indent=4)

            with open(self.settings_file, "r") as f:
                self.settings = json.load(f)

            # Aplicar tema
            ctk.set_appearance_mode(self.settings["theme"])

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao carregar configurações: {e}")
            self.settings = default_settings
    def save_settings(self):
        """Salva as configurações no arquivo settings.json"""
        try:
            with open(self.settings_file, "w") as f:
                json.dump(self.settings, f, indent=4)
            return True
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar configurações: {e}")
            return False
    def load_data(self):
        """Carrega todos os dados necessários para o sistema"""
        self.data_files = {
            "projects": "data/projects.json",
            "utilities": "data/utilities.json",
            "notes": "data/notes.json",
            "commands": "data/commands.json"
        }

        self.data = {}

        for key, file in self.data_files.items():
            default_data = []

            try:
                if not os.path.exists(file):
                    with open(file, "w") as f:
                        json.dump(default_data, f, indent=4)

                with open(file, "r") as f:
                    self.data[key] = json.load(f)

            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao carregar dados de {key}: {e}")
                self.data[key] = default_data
    def save_data(self, key):
        """Salva os dados no arquivo correspondente"""
        if key not in self.data_files:
            return False

        try:
            with open(self.data_files[key], "w") as f:
                json.dump(self.data[key], f, indent=4)
            return True
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar dados de {key}: {e}")
            return False
    def create_main_layout(self):
        """Cria o layout principal da aplicação"""
        # Grid layout (4x4)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Sidebar (menu lateral)
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)

        # Logo
        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="System Automate PRO",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Botões do menu
        menu_buttons = [
            ("Início", self.show_home_page),
            ("Projetos", self.show_projects_page),
            ("Planilhas", self.show_spreadsheets_page),
            ("Developer", self.show_dev_page),
            ("Utilitários", self.show_utilities_page),
            ("PDF", self.show_pdf_page),  # Nova opção
            ("Conversor de Imagens", self.show_image_converter_page),  # Nova opção
            ("Anotações", self.show_notes_page),
            ("Limpeza", self.show_cleanup_page),
            ("Comandos", self.show_commands_page),
            ("Guia", self.show_guide_page)
        ]

        for i, (text, command) in enumerate(menu_buttons, start=1):
            btn = ctk.CTkButton(
                self.sidebar,
                text=text,
                command=command,
                fg_color="transparent",
                anchor="w"
            )
            btn.grid(row=i, column=0, padx=20, pady=5, sticky="ew")

        # Botão de configurações
        self.settings_btn = ctk.CTkButton(
            self.sidebar,
            text="Configurações",
            command=self.show_settings_page,
            fg_color="transparent",
            anchor="w"
        )
        self.settings_btn.grid(row=9, column=0, padx=20, pady=(5, 20), sticky="ew")

        # Frame principal para conteúdo
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
    def clear_main_frame(self):
        """Limpa o frame principal"""
        for widget in self.main_frame.winfo_children():
            widget.destroy()
    def show_home_page(self):
        """Exibe a página inicial"""
        self.clear_main_frame()

        # Título
        title = ctk.CTkLabel(
            self.main_frame,
            text="Sistema de Automação Pessoal",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.pack(pady=(20, 10))

        # Subtítulo
        subtitle = ctk.CTkLabel(
            self.main_frame,
            text="Seu sistema de automação pessoal completo",
            font=ctk.CTkFont(size=16)
        )
        subtitle.pack(pady=(0, 30))

        # Cards de resumo
        cards_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        cards_frame.pack(fill="x", padx=20, pady=10)

        cards = [
            ("Projetos", len(self.data["projects"])),
            ("Utilitários", len(self.data["utilities"])),
            ("Anotações", len(self.data["notes"])),
            ("Comandos", len(self.data["commands"]))
        ]

        for i, (text, count) in enumerate(cards):
            card = ctk.CTkFrame(cards_frame, width=200, height=100)
            card.grid(row=0, column=i, padx=10, pady=10)

            label = ctk.CTkLabel(card, text=text, font=ctk.CTkFont(size=14))
            label.pack(pady=(15, 5))

            count_label = ctk.CTkLabel(card, text=str(count), font=ctk.CTkFont(size=24, weight="bold"))
            count_label.pack(pady=5)

        # Projetos recentes
        recent_frame = ctk.CTkFrame(self.main_frame)
        recent_frame.pack(fill="both", expand=True, padx=20, pady=20)

        recent_title = ctk.CTkLabel(
            recent_frame,
            text="Projetos Recentes",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        recent_title.pack(pady=(10, 5))

        if not self.settings["recent_projects"]:
            empty_label = ctk.CTkLabel(recent_frame, text="Nenhum projeto recente")
            empty_label.pack(pady=20)
        else:
            for project in self.settings["recent_projects"][:5]:  # Mostrar apenas os 5 mais recentes
                project_frame = ctk.CTkFrame(recent_frame, height=40)
                project_frame.pack(fill="x", padx=10, pady=5)

                name_label = ctk.CTkLabel(project_frame, text=project["name"], width=150, anchor="w")
                name_label.pack(side="left", padx=10)

                path_label = ctk.CTkLabel(project_frame, text=project["path"], anchor="w")
                path_label.pack(side="left", fill="x", expand=True, padx=10)

                date_label = ctk.CTkLabel(project_frame, text=project["date"], width=100, anchor="w")
                date_label.pack(side="left", padx=10)
    def show_projects_page(self):
        """Exibe a página de gerenciamento de projetos"""
        self.clear_main_frame()

        # Título
        title = ctk.CTkLabel(
            self.main_frame,
            text="Gerenciamento de Projetos",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(10, 20))

        # Frame principal com abas
        tabview = ctk.CTkTabview(self.main_frame)
        tabview.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Abas
        tabview.add("Novo Projeto")
        tabview.add("Projetos Existentes")

        # Formulário de novo projeto
        new_project_frame = ctk.CTkFrame(tabview.tab("Novo Projeto"))
        new_project_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Campos do formulário
        fields = [
            ("Nome/Tipo do Projeto:", "entry", ""),
            ("Diretório base:", "entry_button", self.settings["default_dir"]),
            ("Subpastas (uma por linha):", "textbox", ""),
            ("Descrição:", "textbox", ""),
            ("Tags (separadas por vírgula):", "entry", "")
        ]

        self.project_entries = {}

        for i, (label_text, field_type, default_value) in enumerate(fields):
            label = ctk.CTkLabel(new_project_frame, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=5, sticky="e")

            if field_type == "entry":
                entry = ctk.CTkEntry(new_project_frame, width=400)
                entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
                self.project_entries[label_text] = entry
            elif field_type == "entry_button":
                frame = ctk.CTkFrame(new_project_frame, fg_color="transparent")
                frame.grid(row=i, column=1, padx=10, pady=5, sticky="ew")

                entry = ctk.CTkEntry(frame, width=350)
                entry.pack(side="left", fill="x", expand=True)
                entry.insert(0, default_value)

                button = ctk.CTkButton(
                    frame,
                    text="Selecionar...",
                    width=80,
                    command=lambda e=entry: self.select_directory(e)
                )
                button.pack(side="left", padx=5)

                self.project_entries[label_text] = entry
            elif field_type == "textbox":
                height = 100 if "Subpastas" in label_text else 60
                textbox = ctk.CTkTextbox(new_project_frame, width=400, height=height)
                textbox.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
                self.project_entries[label_text] = textbox

        # Botões de ação
        buttons_frame = ctk.CTkFrame(new_project_frame, fg_color="transparent")
        buttons_frame.grid(row=len(fields), column=1, padx=10, pady=10, sticky="e")

        create_btn = ctk.CTkButton(
            buttons_frame,
            text="Criar Projeto",
            command=self.create_project
        )
        create_btn.pack(side="left", padx=5)

        clear_btn = ctk.CTkButton(
            buttons_frame,
            text="Limpar",
            fg_color="gray",
            command=self.clear_project_form
        )
        clear_btn.pack(side="left", padx=5)
    def select_directory(self, entry_widget):
        """Abre o diálogo para selecionar um diretório e atualiza o entry"""
        directory = filedialog.askdirectory(initialdir=self.settings["default_dir"])
        if directory:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, directory)
    def clear_project_form(self):
        """Limpa o formulário de novo projeto"""
        for widget in self.project_entries.values():
            if isinstance(widget, ctk.CTkEntry):
                widget.delete(0, "end")
            elif isinstance(widget, ctk.CTkTextbox):
                widget.delete("1.0", "end")

        # Restaura o diretório padrão
        dir_entry = self.project_entries["Diretório base:"]
        dir_entry.delete(0, "end")
        dir_entry.insert(0, self.settings["default_dir"])
    def create_project(self):
        """Cria um novo projeto com base nos dados do formulário"""
        try:
            # Obter dados do formulário
            project_type = self.project_entries["Nome/Tipo do Projeto:"].get().strip()
            base_dir = self.project_entries["Diretório base:"].get().strip()
            subfolders_text = self.project_entries["Subpastas (uma por linha):"].get("1.0", "end").strip()
            description = self.project_entries["Descrição:"].get("1.0", "end").strip()
            tags = [tag.strip() for tag in self.project_entries["Tags (separadas por vírgula):"].get().split(",") if
                    tag.strip()]

            # Validar campos obrigatórios
            if not project_type or not base_dir:
                messagebox.showwarning("Aviso", "Tipo/Nome e diretório base são obrigatórios!")
                return

            # Criar diretório do projeto
            project_dir = os.path.join(base_dir, project_type)
            os.makedirs(project_dir, exist_ok=True)

            # Criar subpastas
            subfolders = [sf.strip() for sf in subfolders_text.split("\n") if sf.strip()]
            for folder in subfolders:
                os.makedirs(os.path.join(project_dir, folder), exist_ok=True)

            # Criar arquivo README com a descrição
            if description:
                with open(os.path.join(project_dir, "README.md"), "w") as f:
                    f.write(f"# {project_type}\n\n")
                    f.write(f"{description}\n\n")
                    if tags:
                        f.write(f"**Tags:** {', '.join(tags)}\n")

            # Criar objeto do projeto
            project = {
                "type": project_type,
                "base_dir": base_dir,
                "project_dir": project_dir,
                "subfolders": subfolders,
                "description": description,
                "tags": tags,
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            # Adicionar aos dados e salvar
            self.data["projects"].append(project)
            self.save_data("projects")

            # Adicionar aos projetos recentes
            recent_project = {
                "name": project_type,
                "path": project_dir,
                "date": project["date"]
            }

            self.settings["recent_projects"].insert(0, recent_project)
            self.save_settings()

            # Limpar formulário e mostrar mensagem
            self.clear_project_form()
            messagebox.showinfo("Sucesso", f"Projeto '{project_type}' criado com sucesso em:\n{project_dir}")

            # Atualizar a lista de projetos
            self.show_projects_page()

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao criar projeto: {e}")
    def show_image_converter_page(self):
        """Exibe a página de conversão de imagens"""
        self.clear_main_frame()

        # Título
        title = ctk.CTkLabel(
            self.main_frame,
            text="Conversor de Imagens",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(10, 20))

        # Frame principal
        main_frame = ctk.CTkFrame(self.main_frame)
        main_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Formulário de conversão
        form_frame = ctk.CTkFrame(main_frame)
        form_frame.pack(fill="x", padx=10, pady=10)

        # Campos do formulário
        fields = [
            ("Arquivo de imagem:", "entry_button", ""),
            ("Formato de saída:", "optionmenu", ["PNG", "JPG", "BMP", "GIF", "TIFF", "WEBP", "ICO", "SVG"]),
            ("Qualidade (JPG):", "slider", (0, 100, 85)),
            ("Tamanho (ICO - múltiplos de 16):", "entry", "16,32,48,64,128,256")
        ]

        self.image_converter_entries = {}
        self.quality_value_label = None  # Vamos armazenar a referência diretamente

        for i, (label_text, field_type, options_or_default) in enumerate(fields):
            label = ctk.CTkLabel(form_frame, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=5, sticky="e")

            if field_type == "entry_button":
                frame = ctk.CTkFrame(form_frame, fg_color="transparent")
                frame.grid(row=i, column=1, padx=10, pady=5, sticky="ew")

                entry = ctk.CTkEntry(frame)
                entry.pack(side="left", fill="x", expand=True)

                button = ctk.CTkButton(
                    frame,
                    text="Selecionar...",
                    width=80,
                    command=lambda e=entry: self.select_image_file(e)
                )
                button.pack(side="left", padx=5)

                self.image_converter_entries[label_text] = entry

            elif field_type == "optionmenu":
                optionmenu = ctk.CTkOptionMenu(form_frame, values=options_or_default)
                optionmenu.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
                optionmenu.set(options_or_default[0])
                self.image_converter_entries[label_text] = optionmenu
                optionmenu.configure(command=self.update_visibility)

            elif field_type == "slider":
                min_val, max_val, default_val = options_or_default
                slider = ctk.CTkSlider(
                    form_frame,
                    from_=min_val,
                    to=max_val,
                    number_of_steps=max_val - min_val
                )
                slider.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
                slider.set(default_val)
                self.image_converter_entries[label_text] = slider

                # Label para mostrar o valor
                self.quality_value_label = ctk.CTkLabel(form_frame, text=str(default_val))
                self.quality_value_label.grid(row=i, column=2, padx=5, pady=5)
                slider.configure(command=lambda v, lbl=self.quality_value_label: lbl.configure(text=str(int(float(v)))))

            elif field_type == "entry":
                entry = ctk.CTkEntry(form_frame)
                entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
                entry.insert(0, options_or_default)
                self.image_converter_entries[label_text] = entry

        # Atualizar visibilidade inicial
        self.update_visibility(self.image_converter_entries["Formato de saída:"].get())

        # Pré-visualização da imagem
        preview_frame = ctk.CTkFrame(main_frame)
        preview_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.preview_label = ctk.CTkLabel(
            preview_frame,
            text="Pré-visualização aparecerá aqui",
            width=300,
            height=300
        )
        self.preview_label.pack(pady=20)

        # Botão de conversão
        convert_btn = ctk.CTkButton(
            main_frame,
            text="Converter Imagem",
            command=self.convert_image
        )
        convert_btn.pack(pady=10)
    def select_image_file(self, entry_widget):
        """Seleciona um arquivo de imagem e atualiza a pré-visualização"""
        filetypes = [
            ("Imagens", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp"),
            ("Todos os arquivos", "*.*")
        ]

        file_path = filedialog.askopenfilename(
            initialdir=self.settings["default_dir"],
            filetypes=filetypes
        )

        if file_path:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, file_path)
            self.update_image_preview(file_path)
    def update_image_preview(self, image_path):
        """Atualiza a pré-visualização da imagem"""
        try:
            img = Image.open(image_path)

            # Redimensionar mantendo proporção para caber no preview
            img.thumbnail((300, 300))

            # Converter para CTkImage
            ctk_img = ctk.CTkImage(
                light_image=img,
                dark_image=img,
                size=img.size
            )

            self.preview_label.configure(image=ctk_img, text="")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível carregar a imagem: {str(e)}")
            self.preview_label.configure(text="Pré-visualização não disponível", image=None)
    def update_visibility(self, selected_format):
        """Atualiza a visibilidade dos campos baseado no formato selecionado"""
        try:
            # Obter referências aos widgets
            quality_slider = self.image_converter_entries.get("Qualidade (JPG):")
            ico_entry = self.image_converter_entries.get("Tamanho (ICO - múltiplos de 16):")

            # Obter widgets de label
            quality_label = None
            ico_label = None

            # Encontrar os labels pelos textos
            for widget in self.main_frame.winfo_children():
                if isinstance(widget, ctk.CTkFrame):
                    for child in widget.winfo_children():
                        if isinstance(child, ctk.CTkLabel):
                            if child.cget("text") == "Qualidade (JPG):":
                                quality_label = child
                            elif child.cget("text") == "Tamanho (ICO - múltiplos de 16):":
                                ico_label = child

            # Mostrar/ocultar campos conforme o formato
            if selected_format == "JPG":
                if quality_label:
                    quality_label.grid()
                if quality_slider:
                    quality_slider.grid()
                if self.quality_value_label:
                    self.quality_value_label.grid()
                if ico_label:
                    ico_label.grid_remove()
                if ico_entry:
                    ico_entry.grid_remove()
            elif selected_format == "ICO":
                if quality_label:
                    quality_label.grid_remove()
                if quality_slider:
                    quality_slider.grid_remove()
                if self.quality_value_label:
                    self.quality_value_label.grid_remove()
                if ico_label:
                    ico_label.grid()
                if ico_entry:
                    ico_entry.grid()
            else:
                if quality_label:
                    quality_label.grid_remove()
                if quality_slider:
                    quality_slider.grid_remove()
                if self.quality_value_label:
                    self.quality_value_label.grid_remove()
                if ico_label:
                    ico_label.grid_remove()
                if ico_entry:
                    ico_entry.grid_remove()
        except Exception as e:
            print(f"Erro ao atualizar visibilidade: {e}")
    def convert_image(self):
        """Converte a imagem para o formato selecionado"""
        try:
            # Obter parâmetros do formulário
            input_path = self.image_converter_entries["Arquivo de imagem:"].get().strip()
            output_format = self.image_converter_entries["Formato de saída:"].get().lower()

            # Validações básicas
            if not input_path:
                messagebox.showwarning("Aviso", "Selecione um arquivo de imagem primeiro!")
                return

            if not os.path.exists(input_path):
                messagebox.showerror("Erro", "O arquivo de origem não existe!")
                return

            # Carregar imagem original
            img = Image.open(input_path)

            # Configurar diálogo de salvamento
            filename = os.path.splitext(os.path.basename(input_path))[0]
            default_dir = os.path.dirname(input_path) if os.path.dirname(input_path) else self.settings["default_dir"]
            output_path = filedialog.asksaveasfilename(
                initialdir=default_dir,
                initialfile=f"{filename}_converted.{output_format}",
                defaultextension=f".{output_format}",
                filetypes=[(f"{output_format.upper()} files", f"*.{output_format}")]
            )

            if not output_path:
                return

            # Configurações específicas por formato
            if output_format in ['jpg', 'jpeg']:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(output_path,
                         quality=int(self.image_converter_entries["Qualidade (JPG):"].get()),
                         optimize=True)

            elif output_format == 'ico':
                try:
                    # Obter e validar os tamanhos para ICO
                    sizes_str = self.image_converter_entries["Tamanho (ICO - múltiplos de 16):"].get()
                    sizes = []

                    if sizes_str.strip():  # Se não estiver vazio
                        for size in sizes_str.split(','):
                            try:
                                size_int = int(size.strip())
                                if size_int % 16 == 0 and 16 <= size_int <= 256:
                                    sizes.append((size_int, size_int))
                            except ValueError:
                                continue

                    # Usar padrão se nenhum tamanho válido foi fornecido
                    if not sizes:
                        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

                    # Garantir que a imagem seja quadrada para melhor resultado
                    if img.width != img.height:
                        # Criar imagem quadrada com fundo transparente
                        size = max(img.width, img.height)
                        square_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
                        square_img.paste(img, ((size - img.width) // 2, (size - img.height) // 2))
                        img = square_img

                    # Salvar como ICO
                    img.save(output_path, sizes=sizes, format='ICO')

                except Exception as e:
                    messagebox.showerror("Erro", f"Falha ao converter para ICO: {str(e)}")
                    return

            elif output_format == 'svg':
                from io import BytesIO
                import base64

                buffer = BytesIO()
                img.save(buffer, format="PNG")
                img_data = base64.b64encode(buffer.getvalue()).decode('ascii')

                svg_template = f"""<?xml version="1.0" encoding="UTF-8"?>
                <svg width="{img.width}" height="{img.height}" xmlns="http://www.w3.org/2000/svg">
                    <image href="data:image/png;base64,{img_data}" width="{img.width}" height="{img.height}"/>
                </svg>"""

                with open(output_path, 'w') as f:
                    f.write(svg_template)

            else:  # PNG, BMP, GIF, TIFF, WEBP
                img.save(output_path)

            # Atualizar diretório padrão
            dir_path = os.path.dirname(output_path)
            if dir_path != self.settings["default_dir"]:
                self.settings["default_dir"] = dir_path
                self.save_settings()

            messagebox.showinfo("Sucesso", f"Imagem convertida em:\n{output_path}")

        except Exception as e:
            messagebox.showerror("Erro", f"Falha na conversão: {str(e)}")
    def show_pdf_page(self):
        """Exibe a página de criação de documentos PDF"""
        self.clear_main_frame()

        # Título
        title = ctk.CTkLabel(
            self.main_frame,
            text="Criar Documento PDF",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(10, 20))

        # Frame principal
        main_frame = ctk.CTkFrame(self.main_frame)
        main_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Documento atual
        self.current_pdf_document = {
            "title": "",
            "sections": []
        }

        # Formulário do documento
        doc_frame = ctk.CTkFrame(main_frame)
        doc_frame.pack(fill="x", padx=10, pady=10)

        # Título do documento
        ctk.CTkLabel(doc_frame, text="Título do Documento:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.pdf_title_entry = ctk.CTkEntry(doc_frame, width=400)
        self.pdf_title_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        # Seções do documento
        self.sections_frame = ctk.CTkScrollableFrame(main_frame)
        self.sections_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Botão para adicionar seção
        add_section_btn = ctk.CTkButton(
            main_frame,
            text="+ Adicionar Seção",
            command=self.add_pdf_section
        )
        add_section_btn.pack(pady=(0, 10))

        # Botões de ação
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=10, pady=10)

        save_btn = ctk.CTkButton(
            buttons_frame,
            text="Salvar Estrutura",
            command=self.save_pdf_structure
        )
        save_btn.pack(side="left", padx=5)

        export_btn = ctk.CTkButton(
            buttons_frame,
            text="Exportar PDF",
            fg_color="green",
            command=self.export_to_pdf
        )
        export_btn.pack(side="left", padx=5)

        preview_btn = ctk.CTkButton(
            buttons_frame,
            text="Visualizar",
            command=self.preview_pdf_structure
        )
        preview_btn.pack(side="left", padx=5)

        # Adiciona uma seção inicial
        self.add_pdf_section()
    def add_pdf_section(self, section_data=None):
        """Adiciona uma nova seção ao documento"""
        section_frame = ctk.CTkFrame(self.sections_frame)
        section_frame.pack(fill="x", padx=5, pady=5)

        # Título da seção
        ctk.CTkLabel(section_frame, text="Título da Seção:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        title_entry = ctk.CTkEntry(section_frame)
        title_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        if section_data and "title" in section_data:
            title_entry.insert(0, section_data["title"])

        # Texto da seção
        ctk.CTkLabel(section_frame, text="Texto:").grid(row=1, column=0, padx=10, pady=5, sticky="ne")
        text_box = ctk.CTkTextbox(section_frame, height=100)
        text_box.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        if section_data and "text" in section_data:
            text_box.insert("1.0", section_data["text"])

        # Imagem
        image_path = None
        if section_data and "image" in section_data and section_data["image"]:
            # Verificar se o caminho existe antes de usar
            if os.path.exists(section_data["image"]):
                image_path = section_data["image"]
            else:
                print(f"Caminho da imagem inválido: {section_data['image']}")

        image_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        image_frame.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        image_btn = ctk.CTkButton(
            image_frame,
            text="Adicionar Imagem",
            command=lambda: self.select_pdf_image(image_path_label)
        )
        image_btn.pack(side="left", padx=5)

        image_path_label = ctk.CTkLabel(image_frame, text=image_path if image_path else "Nenhuma imagem selecionada")
        image_path_label.pack(side="left", padx=5, fill="x", expand=True)

        # Botão para remover seção
        remove_btn = ctk.CTkButton(
            section_frame,
            text="Remover Seção",
            fg_color="red",
            hover_color="darkred",
            command=lambda: section_frame.destroy()
        )
        remove_btn.grid(row=0, column=2, rowspan=2, padx=10, pady=5, sticky="ns")
    def select_pdf_image(self, path_label):
        """Seleciona uma imagem para a seção do PDF"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png *.jpg *.jpeg"), ("All Files", "*.*")]
        )
        if file_path:
            path_label.configure(text=file_path)
    def save_pdf_structure(self):
        """Salva a estrutura do documento como JSON"""
        try:
            # Coletar dados do documento
            self.current_pdf_document["title"] = self.pdf_title_entry.get().strip()
            self.current_pdf_document["sections"] = []

            # Coletar dados das seções
            for section_frame in self.sections_frame.winfo_children():
                if isinstance(section_frame, ctk.CTkFrame):
                    children = section_frame.winfo_children()
                    title_entry = children[1] if len(children) > 1 else None
                    text_box = children[3] if len(children) > 3 else None
                    image_path_label = children[5].winfo_children()[1] if len(children) > 5 else None

                    if title_entry and text_box:
                        section_data = {
                            "title": title_entry.get().strip(),
                            "text": text_box.get("1.0", "end").strip(),
                            "image": image_path_label.cget("text") if image_path_label and image_path_label.cget(
                                "text") != "Nenhuma imagem selecionada" else None
                        }
                        self.current_pdf_document["sections"].append(section_data)

            # Salvar em arquivo
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile=f"{self.current_pdf_document['title'] or 'documento'}.json"
            )

            if file_path:
                with open(file_path, "w") as f:
                    json.dump(self.current_pdf_document, f, indent=4)

                messagebox.showinfo("Sucesso", f"Estrutura do documento salva em:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar estrutura: {e}")
    def export_to_pdf(self):
        """Exporta o documento como PDF"""
        try:
            from fpdf import FPDF
            from fpdf.enums import XPos, YPos
            from PIL import Image as PILImage

            # Coletar dados (reutiliza a função de salvar)
            self.save_pdf_structure()

            # Criar PDF
            pdf = FPDF()

            # Adicionar fontes (modificação principal)
            try:
                # Tentar usar as fontes padrão que já vêm com o FPDF
                pdf.add_font("DejaVu", "", "fonts/DejaVuSans.ttf")
                pdf.add_font("DejaVu", "B", "fonts/DejaVuSans-Bold.ttf")
            except RuntimeError as e:
                # Se não encontrar as fontes, usar as padrão
                messagebox.showwarning("Aviso", f"Fontes DejaVu não encontradas. Usando fontes padrão.\nErro: {e}")
                pdf.add_font("Helvetica", "", "")
                pdf.add_font("Helvetica", "B", "")

            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()

            # Usar fonte
            try:
                pdf.set_font("DejaVu", "B", 16)
            except:
                pdf.set_font("Helvetica", "B", 16)

            # Adicionar título
            pdf.cell(0, 10, self.current_pdf_document["title"], new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            pdf.ln(10)

            # Adicionar seções
            try:
                pdf.set_font("DejaVu", "", 12)
            except:
                pdf.set_font("Helvetica", "", 12)

            for section in self.current_pdf_document["sections"]:
                # Título da seção
                try:
                    pdf.set_font("DejaVu", "B", 14)
                except:
                    pdf.set_font("Helvetica", "B", 14)

                pdf.cell(0, 10, section["title"], new_x=XPos.LMARGIN, new_y=YPos.NEXT)

                try:
                    pdf.set_font("DejaVu", "", 12)
                except:
                    pdf.set_font("Helvetica", "", 12)

                # Texto da seção
                pdf.multi_cell(0, 10, section["text"])
                pdf.ln(5)

                # Imagem (se houver)
                if section["image"]:
                    try:
                        # Redimensionar imagem para caber na página
                        img = PILImage.open(section["image"])
                        width, height = img.size
                        max_width = 180  # Largura máxima em mm (A4 tem ~210mm)

                        if width > max_width:
                            ratio = max_width / float(width)
                            new_height = int(float(height) * float(ratio))
                            img = img.resize((max_width, new_height), PILImage.LANCZOS)
                            temp_path = "temp_resized_image.jpg"
                            img.save(temp_path)
                            section["image"] = temp_path

                        pdf.image(section["image"], x=10, w=180)
                        pdf.ln(10)

                        # Remover arquivo temporário se criado
                        if "temp_resized_image.jpg" in section["image"]:
                            os.remove("temp_resized_image.jpg")
                    except Exception as e:
                        print(f"Erro ao adicionar imagem: {e}")

            # Salvar PDF
            default_dir = os.path.join(self.settings["default_dir"], "documentos_gerados")
            os.makedirs(default_dir, exist_ok=True)

            file_path = filedialog.asksaveasfilename(
                initialdir=default_dir,
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
                initialfile=f"{self.current_pdf_document['title'] or 'documento'}.pdf"
            )

            if file_path:
                pdf.output(file_path)
                messagebox.showinfo("Sucesso", f"Documento PDF gerado em:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar PDF: {e}")
    def preview_pdf_structure(self):
        """Mostra uma prévia da estrutura do documento"""
        try:
            # Coletar dados (reutiliza a função de salvar)
            self.save_pdf_structure()

            preview_text = f"Título: {self.current_pdf_document['title']}\n\n"
            preview_text += "Seções:\n"

            for i, section in enumerate(self.current_pdf_document["sections"], 1):
                preview_text += f"\n{i}. {section['title']}\n"
                preview_text += f"   Texto: {section['text'][:50]}...\n"
                preview_text += f"   Imagem: {section['image'] or 'Nenhuma'}\n"

            messagebox.showinfo("Prévia do Documento", preview_text)

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar prévia: {e}")
    def edit_project(self, project):
        """Preenche o formulário com os dados do projeto para edição"""
        # Muda para a aba de novo projeto
        tabview = self.main_frame.winfo_children()[1]  # Acessa o tabview
        tabview.set("Novo Projeto")

        # Preenche os campos
        self.clear_project_form()

        self.project_entries["Nome:"].insert(0, project["name"])
        self.project_entries["Diretório base:"].insert(0, project["base_dir"])

        subfolders_text = "\n".join(project["subfolders"])
        self.project_entries["Subpastas (uma por linha):"].insert("1.0", subfolders_text)

        self.project_entries["Descrição:"].insert(0, project["description"])
        self.project_entries["Tags (separadas por vírgula):"].insert(0, ", ".join(project["tags"]))

        # TODO: Implementar lógica para atualizar o projeto ao invés de criar um novo
    def delete_project(self, project):
        """Exclui um projeto da lista"""
        confirm = messagebox.askyesno(
            "Confirmar",
            f"Tem certeza que deseja excluir o projeto '{project['name']}'?\n\nEsta ação não exclui os arquivos do projeto."
        )

        if confirm:
            self.data["projects"] = [p for p in self.data["projects"] if p != project]
            self.save_data("projects")
            self.show_projects_page()
    def show_spreadsheets_page(self):
        """Exibe a página de gerenciamento de planilhas"""
        self.clear_main_frame()

        # Título
        title = ctk.CTkLabel(
            self.main_frame,
            text="Gerenciamento de Planilhas",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(10, 20))

        # Frame principal
        main_content = ctk.CTkFrame(self.main_frame)
        main_content.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Formulário de geração de planilha
        form_frame = ctk.CTkFrame(main_content)
        form_frame.pack(fill="x", padx=10, pady=10)

        # Campos do formulário
        fields = [
            ("Nome da Planilha:", "entry", "minha_planilha.xlsx"),
            ("Cabeçalhos (um por linha):", "textbox", "Coluna 1\nColuna 2\nColuna 3"),
            ("Número de linhas:", "entry", "10"),
            ("Dados iniciais (opcional, um valor por linha):", "textbox", "")
        ]

        self.spreadsheet_entries = {}

        for i, (label_text, field_type, default_value) in enumerate(fields):
            label = ctk.CTkLabel(form_frame, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=5, sticky="e")

            if field_type == "entry":
                entry = ctk.CTkEntry(form_frame, width=300)
                entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
                entry.insert(0, default_value)
                self.spreadsheet_entries[label_text] = entry
            elif field_type == "textbox":
                height = 60 if "Dados" in label_text else 100
                textbox = ctk.CTkTextbox(form_frame, width=300, height=height)
                textbox.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
                textbox.insert("1.0", default_value)
                self.spreadsheet_entries[label_text] = textbox

        # Botão de gerar
        generate_btn = ctk.CTkButton(
            form_frame,
            text="Gerar Planilha",
            command=self.generate_spreadsheet
        )
        generate_btn.grid(row=len(fields), column=1, padx=10, pady=10, sticky="e")
    def generate_spreadsheet(self):
        """Gera uma planilha Excel com base nos parâmetros fornecidos"""
        try:
            # Obter parâmetros
            filename = self.spreadsheet_entries["Nome da Planilha:"].get().strip()
            headers_text = self.spreadsheet_entries["Cabeçalhos (um por linha):"].get("1.0", "end").strip()
            num_rows = self.spreadsheet_entries["Número de linhas:"].get().strip()
            initial_data_text = self.spreadsheet_entries["Dados iniciais (opcional, um valor por linha):"].get("1.0",
                                                                                                               "end").strip()

            # Validar campos obrigatórios
            if not filename:
                messagebox.showwarning("Aviso", "Nome da planilha é obrigatório!")
                return

            if not filename.endswith(".xlsx"):
                filename += ".xlsx"

            # Processar cabeçalhos
            headers = [h.strip() for h in headers_text.split("\n") if h.strip()]
            if not headers:
                messagebox.showwarning("Aviso", "Pelo menos um cabeçalho é necessário!")
                return

            # Processar número de linhas
            try:
                num_rows = int(num_rows) if num_rows else 0
                if num_rows < 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Aviso", "Número de linhas deve ser um valor inteiro positivo!")
                return

            # Processar dados iniciais (opcional)
            initial_data = [d.strip() for d in initial_data_text.split("\n") if d.strip()]

            # Criar DataFrame
            data = {header: [""] * num_rows for header in headers}
            df = pd.DataFrame(data)

            # Preencher com dados iniciais se fornecidos
            for i, value in enumerate(initial_data):
                if i < num_rows and len(headers) > 0:
                    df.at[i, headers[0]] = value

            # Salvar arquivo
            default_dir = self.settings["default_dir"]
            save_path = filedialog.asksaveasfilename(
                initialdir=default_dir,
                initialfile=filename,
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )

            if save_path:
                df.to_excel(save_path, index=False)
                messagebox.showinfo("Sucesso", f"Planilha gerada com sucesso em:\n{save_path}")

                # Atualizar diretório padrão se necessário
                dir_path = os.path.dirname(save_path)
                if dir_path != self.settings["default_dir"]:
                    self.settings["default_dir"] = dir_path
                    self.save_settings()

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao gerar planilha: {e}")
    def show_dev_page(self):
        """Exibe a página de projetos de desenvolvimento"""
        self.clear_main_frame()

        # Título
        title = ctk.CTkLabel(
            self.main_frame,
            text="Projetos de Desenvolvimento",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(10, 20))

        # Frame principal
        main_content = ctk.CTkFrame(self.main_frame)
        main_content.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Formulário
        form_frame = ctk.CTkFrame(main_content)
        form_frame.pack(fill="x", padx=10, pady=10)

        # Tipo de projeto
        type_label = ctk.CTkLabel(form_frame, text="Tipo do projeto:")
        type_label.grid(row=0, column=0, padx=10, pady=5, sticky="e")

        project_types = ["React + Vite", "Node + Express", "Python + Flask", "HTML/CSS/JS"]
        self.project_type = ctk.CTkOptionMenu(form_frame, values=project_types)
        self.project_type.grid(row=0, column=1, padx=10, pady=5, sticky="ew")

        # Nome do projeto
        name_label = ctk.CTkLabel(form_frame, text="Nome do projeto:")
        name_label.grid(row=1, column=0, padx=10, pady=5, sticky="e")

        self.project_name = ctk.CTkEntry(form_frame)
        self.project_name.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # Diretório
        dir_label = ctk.CTkLabel(form_frame, text="Diretório:")
        dir_label.grid(row=2, column=0, padx=10, pady=5, sticky="e")

        dir_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        dir_frame.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        self.project_dir = ctk.CTkEntry(dir_frame)
        self.project_dir.pack(side="left", fill="x", expand=True)
        self.project_dir.insert(0, self.settings["default_dir"])

        dir_btn = ctk.CTkButton(
            dir_frame,
            text="Selecionar...",
            width=80,
            command=lambda: self.select_directory(self.project_dir)
        )
        dir_btn.pack(side="left", padx=5)

        # Opções específicas
        self.options_frame = ctk.CTkFrame(form_frame)
        self.options_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=5, sticky="ew")

        # Atualizar opções quando o tipo mudar
        self.project_type.configure(command=self.update_dev_options)
        self.update_dev_options()

        # Terminal de saída
        terminal_label = ctk.CTkLabel(form_frame, text="Saída:")
        terminal_label.grid(row=4, column=0, padx=10, pady=5, sticky="ne")

        self.terminal = ctk.CTkTextbox(
            form_frame,
            width=600,
            height=200,
            font=ctk.CTkFont(family="Courier", size=12)
        )
        self.terminal.grid(row=4, column=1, padx=10, pady=5, sticky="nsew")

        # Botões
        buttons_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        buttons_frame.grid(row=5, column=1, padx=10, pady=10, sticky="e")

        create_btn = ctk.CTkButton(
            buttons_frame,
            text="Criar Projeto",
            command=self.create_dev_project
        )
        create_btn.pack(side="left", padx=5)

        clear_btn = ctk.CTkButton(
            buttons_frame,
            text="Limpar Terminal",
            fg_color="gray",
            command=lambda: self.terminal.delete("1.0", "end")
        )
        clear_btn.pack(side="left", padx=5)
    def update_dev_options(self, *args):
        """Atualiza as opções específicas com base no tipo de projeto selecionado"""
        # Limpa o frame de opções
        for widget in self.options_frame.winfo_children():
            widget.destroy()

        project_type = self.project_type.get()

        if project_type == "React + Vite":
            # Opções para React
            self.react_vite = ctk.CTkCheckBox(self.options_frame, text="Usar Vite")
            self.react_vite.pack(side="left", padx=5, pady=5)
            self.react_vite.select()  # Selecionado por padrão

            self.react_ts = ctk.CTkCheckBox(self.options_frame, text="TypeScript")
            self.react_ts.pack(side="left", padx=5, pady=5)

            self.react_tailwind = ctk.CTkCheckBox(self.options_frame, text="Tailwind CSS")
            self.react_tailwind.pack(side="left", padx=5, pady=5)

        elif project_type == "Node + Express":
            # Opções para Node
            self.node_nodemon = ctk.CTkCheckBox(self.options_frame, text="Usar nodemon")
            self.node_nodemon.pack(side="left", padx=5, pady=5)

            self.node_express = ctk.CTkCheckBox(self.options_frame, text="Express.js")
            self.node_express.pack(side="left", padx=5, pady=5)
            self.node_express.select()  # Selecionado por padrão

        elif project_type == "Python + Flask":
            # Opções para Python
            self.python_venv = ctk.CTkCheckBox(self.options_frame, text="Criar venv")
            self.python_venv.pack(side="left", padx=5, pady=5)

            self.python_flask = ctk.CTkCheckBox(self.options_frame, text="Flask")
            self.python_flask.pack(side="left", padx=5, pady=5)
            self.python_flask.select()  # Selecionado por padrão

            # Opção para estrutura de pastas personalizada
            self.python_custom_folders = ctk.CTkCheckBox(self.options_frame, text="Estrutura personalizada")
            self.python_custom_folders.pack(side="left", padx=5, pady=5)
            self.python_custom_folders.bind("<Button-1>", self.show_folder_structure_dialog)

        elif project_type == "HTML/CSS/JS":
            # Opções para projeto básico
            self.basic_html = ctk.CTkCheckBox(self.options_frame, text="HTML")
            self.basic_html.pack(side="left", padx=5, pady=5)
            self.basic_html.select()  # Selecionado por padrão

            self.basic_css = ctk.CTkCheckBox(self.options_frame, text="CSS")
            self.basic_css.pack(side="left", padx=5, pady=5)
            self.basic_css.select()  # Selecionado por padrão

            self.basic_js = ctk.CTkCheckBox(self.options_frame, text="JavaScript")
            self.basic_js.pack(side="left", padx=5, pady=5)
            self.basic_js.select()  # Selecionado por padrão

            # Opção para estrutura de pastas personalizada
            self.basic_custom_folders = ctk.CTkCheckBox(self.options_frame, text="Estrutura personalizada")
            self.basic_custom_folders.pack(side="left", padx=5, pady=5)
            self.basic_custom_folders.bind("<Button-1>", self.show_folder_structure_dialog)
    def show_folder_structure_dialog(self, event):
        """Mostra o diálogo para definir a estrutura de pastas"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Estrutura de Pastas Personalizada")
        dialog.geometry("500x400")
        dialog.transient(self)
        dialog.grab_set()

        # Frame principal
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Instruções
        ctk.CTkLabel(
            main_frame,
            text="Defina a estrutura de pastas (uma por linha):",
            font=ctk.CTkFont(weight="bold")
        ).pack(pady=(0, 10))

        # Área de texto para as pastas
        self.folders_textbox = ctk.CTkTextbox(main_frame, height=250)
        self.folders_textbox.pack(fill="both", expand=True, padx=5, pady=5)

        # Exemplo de estrutura padrão baseada no tipo de projeto
        project_type = self.project_type.get()
        if project_type == "HTML/CSS/JS":
            example_structure = "assets/\nassets/css/\nassets/js/\nassets/images/\nmodules/\ncore/\nui/"
        else:  # Python
            example_structure = "src/\ntests/\ndocs/\nconfig/\nmodules/\ncore/\nutils/"

        self.folders_textbox.insert("1.0", example_structure)

        # Botões
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.pack(pady=10)

        save_btn = ctk.CTkButton(
            buttons_frame,
            text="Salvar Estrutura",
            command=lambda: self.save_folder_structure(dialog)
        )
        save_btn.pack(side="left", padx=5)

        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Cancelar",
            fg_color="gray",
            command=dialog.destroy
        )
        cancel_btn.pack(side="left", padx=5)
    def save_folder_structure(self, dialog):
        """Salva a estrutura de pastas definida pelo usuário"""
        self.custom_folder_structure = [
            line.strip() for line in self.folders_textbox.get("1.0", "end").split("\n")
            if line.strip()
        ]
        dialog.destroy()
        messagebox.showinfo("Sucesso", "Estrutura de pastas salva!")
    def create_dev_project(self):
        """Cria um projeto de desenvolvimento com base nas configurações"""
        try:
            # Obter parâmetros
            project_type = self.project_type.get()
            project_name = self.project_name.get().strip()
            project_dir = self.project_dir.get().strip()

            # Validar
            if not project_name or not project_dir:
                messagebox.showwarning("Aviso", "Nome e diretório do projeto são obrigatórios!")
                return

            # Criar diretório do projeto
            full_path = os.path.join(project_dir, project_name)
            os.makedirs(full_path, exist_ok=True)

            # Montar lista de comandos para execução
            commands = []

            # Criar estrutura de pastas personalizada se selecionado
            if (project_type in ["HTML/CSS/JS", "Python + Flask"] and
                    hasattr(self, 'custom_folder_structure') and
                    self.custom_folder_structure):

                for folder in self.custom_folder_structure:
                    folder_path = os.path.join(full_path, folder)
                    os.makedirs(folder_path, exist_ok=True)

                # Remove a estrutura após uso para não interferir em próximos projetos
                del self.custom_folder_structure

            # Configurações específicas por tipo de projeto
            if project_type == "HTML/CSS/JS":
                if self.basic_html.get():
                    html_path = os.path.join(full_path, "index.html")
                    with open(html_path, "w") as f:
                        f.write("<!DOCTYPE html>\n")
                        f.write('<html lang="en">\n')
                        f.write("<head>\n")
                        f.write('    <meta charset="UTF-8">\n')
                        f.write('    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n')
                        f.write(f'    <title>{project_name}</title>\n')
                        if self.basic_css.get():
                            f.write('    <link rel="stylesheet" href="style.css">\n')
                        f.write("</head>\n")
                        f.write("<body>\n")
                        f.write('    <h1>Hello World!</h1>\n')
                        if self.basic_js.get():
                            f.write('    <script src="script.js"></script>\n')
                        f.write("</body>\n")
                        f.write("</html>\n")

                if self.basic_css.get():
                    css_path = os.path.join(full_path, "style.css")
                    with open(css_path, "w") as f:
                        f.write("body {\n")
                        f.write("    font-family: Arial, sans-serif;\n")
                        f.write("    margin: 0;\n")
                        f.write("    padding: 20px;\n")
                        f.write("}\n")

                if self.basic_js.get():
                    js_path = os.path.join(full_path, "script.js")
                    with open(js_path, "w") as f:
                        f.write("console.log('Hello from JavaScript!');\n")

            elif project_type == "Python + Flask":
                if self.python_venv.get():
                    commands.append((
                        f"cd {full_path} && python -m venv venv",
                        "Criando ambiente virtual Python"
                    ))

                if self.python_flask.get():
                    app_path = os.path.join(full_path, "app.py")
                    with open(app_path, "w") as f:
                        f.write("from flask import Flask\n\n")
                        f.write("app = Flask(__name__)\n\n")
                        f.write("@app.route('/')\n")
                        f.write("def home():\n")
                        f.write('    return "Hello, Flask!"\n\n')
                        f.write("if __name__ == '__main__':\n")
                        f.write("    app.run(debug=True)\n")

                    # Criar requirements.txt se for projeto Flask
                    req_path = os.path.join(full_path, "requirements.txt")
                    with open(req_path, "w") as f:
                        f.write("flask\n")

            elif project_type == "React + Vite":
                use_vite = self.react_vite.get()
                use_ts = self.react_ts.get()
                use_tailwind = self.react_tailwind.get()

                if use_vite:
                    cmd = f"npm create vite@latest {project_name} --template"
                    cmd += " react-ts" if use_ts else " react"
                    commands.append((f"cd {project_dir} && {cmd}", "Criando projeto React com Vite"))

                    if use_tailwind:
                        commands.append((
                            f"cd {full_path} && npm install -D tailwindcss postcss autoprefixer && npx tailwindcss init -p",
                            "Instalando Tailwind CSS"
                        ))

            elif project_type == "Node + Express":
                use_nodemon = self.node_nodemon.get()
                use_express = self.node_express.get()

                commands.append((
                    f"cd {full_path} && npm init -y",
                    "Inicializando projeto Node.js"
                ))

                if use_express:
                    commands.append((
                        f"cd {full_path} && npm install express",
                        "Instalando Express.js"
                    ))

                    # Criar arquivo server.js
                    server_path = os.path.join(full_path, "server.js")
                    with open(server_path, "w") as f:
                        f.write("const express = require('express');\n")
                        f.write("const app = express();\n\n")
                        f.write("app.get('/', (req, res) => {\n")
                        f.write("  res.send('Hello from Express!');\n")
                        f.write("});\n\n")
                        f.write("const PORT = process.env.PORT || 3000;\n")
                        f.write("app.listen(PORT, () => {\n")
                        f.write("  console.log(`Server running on port ${PORT}`);\n")
                        f.write("});\n")

                if use_nodemon:
                    commands.append((
                        f"cd {full_path} && npm install --save-dev nodemon",
                        "Instalando nodemon"
                    ))

            # Executar comandos em uma thread separada
            if commands:
                threading.Thread(
                    target=self.execute_dev_commands,
                    args=(commands,),
                    daemon=True
                ).start()
            else:
                messagebox.showinfo("Sucesso", f"Projeto '{project_name}' criado em:\n{full_path}")

            # Atualizar projetos recentes
            recent_project = {
                "name": project_name,
                "path": full_path,
                "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            self.settings["recent_projects"].insert(0, recent_project)
            self.save_settings()

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao criar projeto: {str(e)}")
    def execute_dev_commands(self, commands):
        """Executa os comandos do projeto de desenvolvimento e exibe a saída no terminal"""
        for cmd, description in commands:
            self.append_to_terminal(f"> {description}...\n")

            try:
                process = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )

                # Ler saída em tempo real
                for line in process.stdout:
                    self.append_to_terminal(line)

                for line in process.stderr:
                    self.append_to_terminal(f"ERROR: {line}")

                process.wait()

                if process.returncode == 0:
                    self.append_to_terminal(f"✔ {description} concluído com sucesso!\n\n")
                else:
                    self.append_to_terminal(f"✖ Falha ao executar: {description}\n\n")

            except Exception as e:
                self.append_to_terminal(f"✖ Erro ao executar comando: {e}\n\n")
    def append_to_terminal(self, text):
        """Adiciona texto ao terminal de forma thread-safe"""
        self.after(0, lambda: self._append_text(text))
    def _append_text(self, text):
        """Adiciona texto ao terminal (deve ser chamado na thread principal)"""
        self.terminal.insert("end", text)
        self.terminal.see("end")
    def show_utilities_page(self):
        """Exibe a página de utilitários"""
        self.clear_main_frame()

        # Título
        title = ctk.CTkLabel(
            self.main_frame,
            text="Utilitários",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(10, 20))

        # Frame principal com abas
        tabview = ctk.CTkTabview(self.main_frame)
        tabview.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Abas
        tabview.add("Aplicativos")
        tabview.add("Links Web")

        # Frame para aplicativos
        apps_frame = ctk.CTkFrame(tabview.tab("Aplicativos"))
        apps_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Frame para links web
        links_frame = ctk.CTkFrame(tabview.tab("Links Web"))
        links_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Separar utilitários em aplicativos e links
        apps = [u for u in self.data["utilities"] if not u["path"].startswith(("http://", "https://"))]
        links = [u for u in self.data["utilities"] if u["path"].startswith(("http://", "https://"))]

        # Mostrar aplicativos em cards
        if not apps:
            empty_label = ctk.CTkLabel(apps_frame, text="Nenhum aplicativo cadastrado")
            empty_label.pack(pady=50)
        else:
            # Grid para os cards
            apps_frame.grid_columnconfigure((0, 1, 2), weight=1)  # 3 colunas
            apps_frame.grid_rowconfigure(tuple(range((len(apps) + 2) // 3)), weight=1)  # Linhas necessárias

            for i, utility in enumerate(apps):
                row = i // 3
                col = i % 3

                card = ctk.CTkFrame(apps_frame, width=200, height=150, corner_radius=10)
                card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

                # Nome do aplicativo
                name_label = ctk.CTkLabel(card, text=utility["name"], font=ctk.CTkFont(weight="bold"))
                name_label.pack(pady=(10, 5))

                # Ícone (simulado)
                icon_label = ctk.CTkLabel(card, text="📁", font=ctk.CTkFont(size=24))
                icon_label.pack(pady=5)

                # Botões de ação
                btn_frame = ctk.CTkFrame(card, fg_color="transparent")
                btn_frame.pack(pady=10)

                run_btn = ctk.CTkButton(
                    btn_frame,
                    text="Abrir",
                    width=70,
                    command=lambda p=utility["path"]: self.run_utility(p)
                )
                run_btn.pack(side="left", padx=2)

                edit_btn = ctk.CTkButton(
                    btn_frame,
                    text="Editar",
                    width=70,
                    command=lambda u=utility: self.edit_utility(u)
                )
                edit_btn.pack(side="left", padx=2)

                delete_btn = ctk.CTkButton(
                    btn_frame,
                    text="Excluir",
                    width=70,
                    fg_color="red",
                    hover_color="darkred",
                    command=lambda u=utility: self.delete_utility(u)
                )
                delete_btn.pack(side="left", padx=2)

        # Mostrar links em uma lista organizada
        if not links:
            empty_label = ctk.CTkLabel(links_frame, text="Nenhum link web cadastrado")
            empty_label.pack(pady=50)
        else:
            # Cabeçalho
            headers_frame = ctk.CTkFrame(links_frame, fg_color="transparent")
            headers_frame.pack(fill="x", padx=10, pady=5)

            ctk.CTkLabel(headers_frame, text="Nome", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5, pady=5,
                                                                                           fill="x", expand=True)
            ctk.CTkLabel(headers_frame, text="URL", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5, pady=5,
                                                                                          fill="x", expand=True)
            ctk.CTkLabel(headers_frame, text="Ações", font=ctk.CTkFont(weight="bold"), width=150).pack(side="left",
                                                                                                       padx=5, pady=5)

            # Lista de links
            scroll_frame = ctk.CTkScrollableFrame(links_frame)
            scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)

            for link in links:
                link_frame = ctk.CTkFrame(scroll_frame)
                link_frame.pack(fill="x", padx=5, pady=5)

                # Nome
                name_label = ctk.CTkLabel(link_frame, text=link["name"], anchor="w")
                name_label.pack(side="left", padx=5, pady=5, fill="x", expand=True)

                # URL
                url_label = ctk.CTkLabel(link_frame, text=link["path"], anchor="w")
                url_label.pack(side="left", padx=5, pady=5, fill="x", expand=True)

                # Botões de ação
                action_frame = ctk.CTkFrame(link_frame, fg_color="transparent")
                action_frame.pack(side="left", padx=5, pady=5)

                open_btn = ctk.CTkButton(
                    action_frame,
                    text="Abrir",
                    width=50,
                    command=lambda p=link["path"]: self.run_utility(p)
                )
                open_btn.pack(side="left", padx=2)

                edit_btn = ctk.CTkButton(
                    action_frame,
                    text="Editar",
                    width=50,
                    command=lambda u=link: self.edit_utility(u)
                )
                edit_btn.pack(side="left", padx=2)

                delete_btn = ctk.CTkButton(
                    action_frame,
                    text="Excluir",
                    width=50,
                    fg_color="red",
                    hover_color="darkred",
                    command=lambda u=link: self.delete_utility(u)
                )
                delete_btn.pack(side="left", padx=2)

        # Botão para adicionar novo utilitário (comum para ambas as abas)
        add_btn = ctk.CTkButton(
            self.main_frame,
            text="+ Novo Utilitário",
            command=self.show_add_utility_dialog
        )
        add_btn.pack(pady=10)
    def show_add_utility_dialog(self, utility=None):
        """Mostra o diálogo para adicionar/editar um utilitário"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Adicionar Utilitário" if not utility else "Editar Utilitário")
        dialog.geometry("500x200")
        dialog.transient(self)
        dialog.grab_set()

        # Campos do formulário
        fields = [
            ("Nome:", "entry", utility["name"] if utility else ""),
            ("Caminho/Link:", "entry", utility["path"] if utility else "")
        ]

        entries = {}

        for i, (label_text, field_type, default_value) in enumerate(fields):
            label = ctk.CTkLabel(dialog, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=5, sticky="e")

            entry = ctk.CTkEntry(dialog, width=300)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            entry.insert(0, default_value)

            entries[label_text] = entry

        # Botões
        buttons_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons_frame.grid(row=len(fields), column=0, columnspan=2, padx=10, pady=10, sticky="e")

        save_btn = ctk.CTkButton(
            buttons_frame,
            text="Salvar",
            command=lambda: self.save_utility(entries, dialog, utility)
        )
        save_btn.pack(side="left", padx=5)

        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Cancelar",
            fg_color="gray",
            command=dialog.destroy
        )
        cancel_btn.pack(side="left", padx=5)
    def save_utility(self, entries, dialog, utility=None):
        """Salva um novo utilitário ou atualiza um existente"""
        try:
            name = entries["Nome:"].get().strip()
            path = entries["Caminho/Link:"].get().strip()

            if not name or not path:
                messagebox.showwarning("Aviso", "Nome e caminho são obrigatórios!")
                return

            if utility:
                # Atualizar utilitário existente
                utility["name"] = name
                utility["path"] = path
            else:
                # Adicionar novo utilitário
                new_utility = {
                    "name": name,
                    "path": path
                }
                self.data["utilities"].append(new_utility)

            self.save_data("utilities")
            dialog.destroy()
            self.show_utilities_page()

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar utilitário: {e}")
    def run_utility(self, path):
        """Executa um utilitário"""
        try:
            if path.startswith(("http://", "https://")):
                import webbrowser
                webbrowser.open(path)
            else:
                os.startfile(path) if os.name == 'nt' else subprocess.Popen(['xdg-open', path])
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao executar utilitário: {e}")
    def edit_utility(self, utility):
        """Abre o diálogo para editar um utilitário"""
        self.show_add_utility_dialog(utility)
    def delete_utility(self, utility):
        """Exclui um utilitário"""
        confirm = messagebox.askyesno(
            "Confirmar",
            f"Tem certeza que deseja excluir o utilitário '{utility['name']}'?"
        )

        if confirm:
            self.data["utilities"] = [u for u in self.data["utilities"] if u != utility]
            self.save_data("utilities")
            self.show_utilities_page()
    def show_cleanup_page(self):
        """Exibe a página de limpeza"""
        self.clear_main_frame()

        # Título
        title = ctk.CTkLabel(
            self.main_frame,
            text="Limpeza e Manutenção",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(10, 20))

        # Frame principal
        main_content = ctk.CTkFrame(self.main_frame)
        main_content.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Opções de limpeza
        options = [
            ("Esvaziar Lixeira", "empty_trash"),
            ("Limpar pasta TEMP", "clean_temp"),
            ("Deletar logs da aplicação", "delete_logs")
        ]

        self.cleanup_vars = {}

        for i, (text, key) in enumerate(options):
            var = ctk.BooleanVar(value=False)
            checkbox = ctk.CTkCheckBox(
                main_content,
                text=text,
                variable=var
            )
            checkbox.pack(pady=5, padx=20, anchor="w")
            self.cleanup_vars[key] = var

        # Botão de execução
        run_btn = ctk.CTkButton(
            main_content,
            text="Executar Agora",
            command=self.run_cleanup
        )
        run_btn.pack(pady=20)
    def run_cleanup(self):
        """Executa as tarefas de limpeza selecionadas"""
        try:
            if self.cleanup_vars["empty_trash"].get():
                self.empty_trash()

            if self.cleanup_vars["clean_temp"].get():
                self.clean_temp_folder()

            if self.cleanup_vars["delete_logs"].get():
                self.delete_app_logs()

            messagebox.showinfo("Sucesso", "Tarefas de limpeza concluídas!")

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao executar limpeza: {e}")
    def empty_trash(self):
        """Esvazia a lixeira"""
        try:
            if os.name == 'nt':  # Windows
                os.system('rd /s /q %systemdrive%\\$Recycle.bin')
            else:  # Linux/Mac
                os.system('rm -rf ~/.local/share/Trash/*')
        except Exception as e:
            raise Exception(f"Falha ao esvaziar lixeira: {e}")
    def clean_temp_folder(self):
        """Limpa a pasta TEMP"""
        try:
            if os.name == 'nt':  # Windows
                temp_dir = os.environ.get('TEMP', 'C:\\Windows\\Temp')
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        try:
                            os.remove(os.path.join(root, file))
                        except:
                            pass
            else:  # Linux/Mac
                temp_dir = '/tmp'
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        try:
                            os.remove(os.path.join(root, file))
                        except:
                            pass
        except Exception as e:
            raise Exception(f"Falha ao limpar pasta TEMP: {e}")
    def delete_app_logs(self):
        """Deleta os logs da aplicação"""
        try:
            log_dir = "logs"
            if os.path.exists(log_dir):
                for file in os.listdir(log_dir):
                    try:
                        os.remove(os.path.join(log_dir, file))
                    except:
                        pass
        except Exception as e:
            raise Exception(f"Falha ao deletar logs: {e}")
    def show_notes_page(self):
        """Exibe a página de anotações"""
        self.clear_main_frame()

        # Título
        title = ctk.CTkLabel(
            self.main_frame,
            text="Anotações",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(10, 20))

        # Frame principal
        main_content = ctk.CTkFrame(self.main_frame)
        main_content.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Abas
        tabview = ctk.CTkTabview(main_content)
        tabview.pack(fill="both", expand=True, padx=10, pady=10)

        tabview.add("Nova Anotação")
        tabview.add("Anotações Existentes")

        # Formulário de nova anotação
        new_note_frame = ctk.CTkFrame(tabview.tab("Nova Anotação"))
        new_note_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Campos do formulário
        fields = [
            ("Título:", "entry", ""),
            ("Data:", "entry", datetime.datetime.now().strftime("%Y-%m-%d")),
            ("Tags (separadas por vírgula):", "entry", ""),
            ("Conteúdo:", "textbox", "")
        ]

        self.note_entries = {}

        for i, (label_text, field_type, default_value) in enumerate(fields):
            label = ctk.CTkLabel(new_note_frame, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=5, sticky="ne")

            if field_type == "entry":
                entry = ctk.CTkEntry(new_note_frame, width=400)
                entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
                entry.insert(0, default_value)
                self.note_entries[label_text] = entry
            elif field_type == "textbox":
                textbox = ctk.CTkTextbox(new_note_frame, width=400, height=200)
                textbox.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
                self.note_entries[label_text] = textbox

        # Botões de ação
        buttons_frame = ctk.CTkFrame(new_note_frame, fg_color="transparent")
        buttons_frame.grid(row=len(fields), column=1, padx=10, pady=10, sticky="e")

        self.save_note_btn = ctk.CTkButton(
            buttons_frame,
            text="Salvar Anotação",
            command=self.save_note
        )
        self.save_note_btn.pack(side="left", padx=5)

        clear_btn = ctk.CTkButton(
            buttons_frame,
            text="Limpar",
            fg_color="gray",
            command=self.clear_note_form
        )
        clear_btn.pack(side="left", padx=5)

        import_btn = ctk.CTkButton(
            buttons_frame,
            text="Importar Arquivo",
            command=self.import_note_file
        )
        import_btn.pack(side="left", padx=5)

        # Lista de anotações existentes
        existing_frame = ctk.CTkFrame(tabview.tab("Anotações Existentes"))
        existing_frame.pack(fill="both", expand=True, padx=10, pady=10)

        if not self.data["notes"]:
            empty_label = ctk.CTkLabel(existing_frame, text="Nenhuma anotação cadastrada")
            empty_label.pack(pady=50)
        else:
            # Cabeçalho
            headers_frame = ctk.CTkFrame(existing_frame, fg_color="transparent")
            headers_frame.pack(fill="x", padx=10, pady=5)

            ctk.CTkLabel(headers_frame, text="Título", font=ctk.CTkFont(weight="bold"), width=150).pack(side="left",
                                                                                                        padx=5, pady=5)
            ctk.CTkLabel(headers_frame, text="Data", font=ctk.CTkFont(weight="bold"), width=100).pack(side="left",
                                                                                                      padx=5, pady=5)
            ctk.CTkLabel(headers_frame, text="Tags", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5, pady=5,
                                                                                           fill="x", expand=True)
            ctk.CTkLabel(headers_frame, text="Ações", font=ctk.CTkFont(weight="bold"), width=150).pack(side="left",
                                                                                                       padx=5, pady=5)

            # Lista de anotações
            scroll_frame = ctk.CTkScrollableFrame(existing_frame)
            scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)

            for note in self.data["notes"]:
                note_frame = ctk.CTkFrame(scroll_frame)
                note_frame.pack(fill="x", padx=5, pady=5)

                # Título
                title_label = ctk.CTkLabel(note_frame, text=note["title"], width=150, anchor="w")
                title_label.pack(side="left", padx=5, pady=5)

                # Data
                date_label = ctk.CTkLabel(note_frame, text=note["date"], width=100, anchor="w")
                date_label.pack(side="left", padx=5, pady=5)

                # Tags
                tags_label = ctk.CTkLabel(note_frame, text=", ".join(note["tags"]), anchor="w")
                tags_label.pack(side="left", padx=5, pady=5, fill="x", expand=True)

                # Botões de ação
                action_frame = ctk.CTkFrame(note_frame, fg_color="transparent")
                action_frame.pack(side="left", padx=5, pady=5)

                view_btn = ctk.CTkButton(
                    action_frame,
                    text="Ver",
                    width=50,
                    command=lambda n=note: self.view_note(n)
                )
                view_btn.pack(side="left", padx=2)

                edit_btn = ctk.CTkButton(
                    action_frame,
                    text="Editar",
                    width=50,
                    command=lambda n=note: self.edit_note(n)
                )
                edit_btn.pack(side="left", padx=2)

                delete_btn = ctk.CTkButton(
                    action_frame,
                    text="Excluir",
                    width=50,
                    fg_color="red",
                    hover_color="darkred",
                    command=lambda n=note: self.delete_note(n)
                )
                delete_btn.pack(side="left", padx=2)
    def clear_note_form(self):
        """Limpa o formulário de anotação"""
        for label_text, widget in self.note_entries.items():
            if isinstance(widget, ctk.CTkEntry):
                if "Data:" in label_text:
                    widget.delete(0, "end")
                    widget.insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))
                else:
                    widget.delete(0, "end")
            elif isinstance(widget, ctk.CTkTextbox):
                widget.delete("1.0", "end")

        # Restaura o botão para o estado de "Salvar" e remove a referência da nota em edição
        self.save_note_btn.configure(text="Salvar Anotação", command=self.save_note)
        if hasattr(self, 'current_note_being_edited'):
            del self.current_note_being_edited
    def save_note(self):
        """Salva uma nova anotação"""
        try:
            # Obter dados do formulário
            title = self.note_entries["Título:"].get().strip()
            date = self.note_entries["Data:"].get().strip()
            tags = [tag.strip() for tag in self.note_entries["Tags (separadas por vírgula):"].get().split(",") if
                    tag.strip()]
            content = self.note_entries["Conteúdo:"].get("1.0", "end").strip()

            # Validar campos obrigatórios
            if not title or not content:
                messagebox.showwarning("Aviso", "Título e conteúdo são obrigatórios!")
                return

            # Criar objeto da anotação
            note = {
                "title": title,
                "date": date,
                "tags": tags,
                "content": content
            }

            # Adicionar aos dados e salvar
            self.data["notes"].append(note)
            self.save_data("notes")

            # Limpar formulário e mostrar mensagem
            self.clear_note_form()
            messagebox.showinfo("Sucesso", "Anotação salva com sucesso!")

            # Atualizar a lista de anotações
            self.show_notes_page()

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar anotação: {e}")
    def import_note_file(self):
        """Importa o conteúdo de um arquivo para a anotação"""
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
            )

            if file_path:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                self.note_entries["Conteúdo:"].insert("1.0", content)

                # Definir o título como o nome do arquivo (sem extensão)
                filename = os.path.basename(file_path)
                title = os.path.splitext(filename)[0]
                self.note_entries["Título:"].delete(0, "end")
                self.note_entries["Título:"].insert(0, title)

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao importar arquivo: {e}")
    def view_note(self, note):
        """Exibe o conteúdo completo de uma anotação"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(note["title"])
        dialog.geometry("600x500")
        dialog.transient(self)
        dialog.grab_set()

        # Frame principal
        main_frame = ctk.CTkFrame(dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Cabeçalho
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(header_frame, text=f"Data: {note['date']}").pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text=f"Tags: {', '.join(note['tags'])}").pack(side="left", padx=5)

        # Conteúdo
        content_text = ctk.CTkTextbox(
            main_frame,
            wrap="word",
            font=ctk.CTkFont(size=14)
        )
        content_text.pack(fill="both", expand=True, padx=5, pady=5)
        content_text.insert("1.0", note["content"])
        content_text.configure(state="disabled")  # Somente leitura
    def edit_note(self, note):
        """Preenche o formulário com os dados da anotação para edição"""
        # Muda para a aba de novo projeto
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, ctk.CTkTabview):
                widget.set("Nova Anotação")
                break

        # Preenche os campos
        self.clear_note_form()

        # Guarda a referência da anotação que está sendo editada
        self.current_note_being_edited = note

        self.note_entries["Título:"].insert(0, note["title"])
        self.note_entries["Data:"].insert(0, note["date"])
        self.note_entries["Tags (separadas por vírgula):"].insert(0, ", ".join(note["tags"]))
        self.note_entries["Conteúdo:"].insert("1.0", note["content"])

        # Altera o texto e comando do botão para "Atualizar"
        self.save_note_btn.configure(text="Atualizar Anotação", command=self.update_existing_note)
    def update_existing_note(self):
        """Atualiza uma anotação existente com os dados do formulário"""
        try:
            if not hasattr(self, 'current_note_being_edited') or not self.current_note_being_edited:
                messagebox.showwarning("Aviso", "Nenhuma anotação selecionada para edição!")
                return

            # Obter dados do formulário
            title = self.note_entries["Título:"].get().strip()
            date = self.note_entries["Data:"].get().strip()
            tags = [tag.strip() for tag in self.note_entries["Tags (separadas por vírgula):"].get().split(",") if
                    tag.strip()]
            content = self.note_entries["Conteúdo:"].get("1.0", "end").strip()

            # Validar campos obrigatórios
            if not title or not content:
                messagebox.showwarning("Aviso", "Título e conteúdo são obrigatórios!")
                return

            # Atualizar a anotação existente nos dados
            for note in self.data["notes"]:
                if note == self.current_note_being_edited:
                    note["title"] = title
                    note["date"] = date
                    note["tags"] = tags
                    note["content"] = content
                    break

            # Salvar as alterações
            self.save_data("notes")

            # Limpar formulário e mostrar mensagem
            self.clear_note_form()
            messagebox.showinfo("Sucesso", "Anotação atualizada com sucesso!")

            # Atualizar a lista de anotações
            self.show_notes_page()

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao atualizar anotação: {e}")
    def restore_save_button(self):
        """Restaura o botão de salvar para o estado original"""
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, ctk.CTkTabview):
                for tab_name in widget._tab_dict:
                    if tab_name == "Nova Anotação":
                        tab = widget._tab_dict[tab_name]
                        for frame in tab.winfo_children():
                            if isinstance(frame, ctk.CTkFrame):
                                for button_frame in frame.winfo_children():
                                    if isinstance(button_frame, ctk.CTkFrame):
                                        for button in button_frame.winfo_children():
                                            if button.cget("text") == "Atualizar Anotação":
                                                button.configure(
                                                    text="Salvar Anotação",
                                                    command=self.save_note
                                                )
    def delete_note(self, note):
        """Exclui uma anotação"""
        confirm = messagebox.askyesno(
            "Confirmar",
            f"Tem certeza que deseja excluir a anotação '{note['title']}'?"
        )

        if confirm:
            self.data["notes"] = [n for n in self.data["notes"] if n != note]
            self.save_data("notes")
            self.show_notes_page()
    def show_commands_page(self):
        """Exibe a página de comandos personalizados"""
        self.clear_main_frame()

        # Título
        title = ctk.CTkLabel(
            self.main_frame,
            text="Comandos Personalizados",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(10, 20))

        # Frame principal
        main_content = ctk.CTkFrame(self.main_frame)
        main_content.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Lista de comandos existentes
        if not self.data["commands"]:
            empty_label = ctk.CTkLabel(main_content, text="Nenhum comando cadastrado")
            empty_label.pack(pady=50)
        else:
            # Cabeçalho
            headers_frame = ctk.CTkFrame(main_content, fg_color="transparent")
            headers_frame.pack(fill="x", padx=10, pady=5)

            ctk.CTkLabel(headers_frame, text="Título", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5,
                                                                                             pady=5, fill="x",
                                                                                             expand=True)
            ctk.CTkLabel(headers_frame, text="Comando", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5,
                                                                                              pady=5, fill="x",
                                                                                              expand=True)
            ctk.CTkLabel(headers_frame, text="Ações", font=ctk.CTkFont(weight="bold"), width=150).pack(side="left",
                                                                                                       padx=5, pady=5)

            # Lista de comandos
            scroll_frame = ctk.CTkScrollableFrame(main_content)
            scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)

            for cmd in self.data["commands"]:
                cmd_frame = ctk.CTkFrame(scroll_frame)
                cmd_frame.pack(fill="x", padx=5, pady=5)

                # Título
                title_label = ctk.CTkLabel(cmd_frame, text=cmd["title"], anchor="w")
                title_label.pack(side="left", padx=5, pady=5, fill="x", expand=True)

                # Comando
                command_label = ctk.CTkLabel(cmd_frame, text=cmd["command"], anchor="w")
                command_label.pack(side="left", padx=5, pady=5, fill="x", expand=True)

                # Botões de ação
                action_frame = ctk.CTkFrame(cmd_frame, fg_color="transparent")
                action_frame.pack(side="left", padx=5, pady=5)

                run_btn = ctk.CTkButton(
                    action_frame,
                    text="Executar",
                    width=50,
                    command=lambda c=cmd["command"]: self.run_command(c)
                )
                run_btn.pack(side="left", padx=2)

                edit_btn = ctk.CTkButton(
                    action_frame,
                    text="Editar",
                    width=50,
                    command=lambda c=cmd: self.edit_command(c)
                )
                edit_btn.pack(side="left", padx=2)

                delete_btn = ctk.CTkButton(
                    action_frame,
                    text="Excluir",
                    width=50,
                    fg_color="red",
                    hover_color="darkred",
                    command=lambda c=cmd: self.delete_command(c)
                )
                delete_btn.pack(side="left", padx=2)

        # Botão para adicionar novo comando
        add_btn = ctk.CTkButton(
            main_content,
            text="+ Novo Comando",
            command=self.show_add_command_dialog
        )
        add_btn.pack(pady=10)
    def show_add_command_dialog(self, command=None):
        """Mostra o diálogo para adicionar/editar um comando"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Adicionar Comando" if not command else "Editar Comando")
        dialog.geometry("600x200")
        dialog.transient(self)
        dialog.grab_set()

        # Campos do formulário
        fields = [
            ("Título:", "entry", command["title"] if command else ""),
            ("Comando:", "entry", command["command"] if command else "")
        ]

        entries = {}

        for i, (label_text, field_type, default_value) in enumerate(fields):
            label = ctk.CTkLabel(dialog, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=5, sticky="e")

            entry = ctk.CTkEntry(dialog, width=400)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
            entry.insert(0, default_value)

            entries[label_text] = entry

        # Botões
        buttons_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        buttons_frame.grid(row=len(fields), column=0, columnspan=2, padx=10, pady=10, sticky="e")

        save_btn = ctk.CTkButton(
            buttons_frame,
            text="Salvar",
            command=lambda: self.save_command(entries, dialog, command)
        )
        save_btn.pack(side="left", padx=5)

        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Cancelar",
            fg_color="gray",
            command=dialog.destroy
        )
        cancel_btn.pack(side="left", padx=5)
    def save_command(self, entries, dialog, command=None):
        """Salva um novo comando ou atualiza um existente"""
        try:
            title = entries["Título:"].get().strip()
            cmd = entries["Comando:"].get().strip()

            if not title or not cmd:
                messagebox.showwarning("Aviso", "Título e comando são obrigatórios!")
                return

            if command:
                # Atualizar comando existente
                command["title"] = title
                command["command"] = cmd
            else:
                # Adicionar novo comando
                new_command = {
                    "title": title,
                    "command": cmd
                }
                self.data["commands"].append(new_command)

            self.save_data("commands")
            dialog.destroy()
            self.show_commands_page()

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar comando: {e}")
    def run_command(self, command):
        """Executa um comando personalizado"""
        try:
            # Executar em uma thread separada para não travar a UI
            threading.Thread(
                target=self._execute_command,
                args=(command,),
                daemon=True
            ).start()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao executar comando: {e}")
    def _execute_command(self, command):
        """Executa o comando e mostra a saída"""
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Criar janela para mostrar a saída
            self.after(0, lambda: self._show_command_output(process))

        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Erro", f"Falha ao executar comando: {e}"))
    def _show_command_output(self, process):
        """Mostra a saída do comando em uma janela"""
        output_window = ctk.CTkToplevel(self)
        output_window.title("Saída do Comando")
        output_window.geometry("800x600")

        # Terminal de saída
        terminal = ctk.CTkTextbox(
            output_window,
            width=780,
            height=580,
            font=ctk.CTkFont(family="Courier", size=12)
        )
        terminal.pack(fill="both", expand=True, padx=10, pady=10)

        # Função para atualizar a saída
        def update_output():
            for line in process.stdout:
                terminal.insert("end", line)
                terminal.see("end")
                output_window.update()

            for line in process.stderr:
                terminal.insert("end", f"ERROR: {line}")
                terminal.see("end")
                output_window.update()

            process.wait()
            if process.returncode == 0:
                terminal.insert("end", "\n✔ Comando executado com sucesso!\n")
            else:
                terminal.insert("end", "\n✖ Falha ao executar comando\n")

            terminal.see("end")

        # Iniciar a atualização em uma thread separada
        threading.Thread(
            target=update_output,
            daemon=True
        ).start()
    def edit_command(self, command):
        """Abre o diálogo para editar um comando"""
        self.show_add_command_dialog(command)
    def delete_command(self, command):
        """Exclui um comando"""
        confirm = messagebox.askyesno(
            "Confirmar",
            f"Tem certeza que deseja excluir o comando '{command['title']}'?"
        )

        if confirm:
            self.data["commands"] = [c for c in self.data["commands"] if c != command]
            self.save_data("commands")
            self.show_commands_page()
    def show_guide_page(self):
        """Exibe a página do guia do sistema"""
        self.clear_main_frame()

        # Título
        title = ctk.CTkLabel(
            self.main_frame,
            text="Guia do Sistema",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(10, 20))

        # Frame principal
        main_content = ctk.CTkFrame(self.main_frame)
        main_content.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Texto do guia
        guide_text = """
        Personal Automation System (PAS) - Guia do Usuário

        1. Projetos
        - Crie e gerencie projetos com estrutura de pastas automatizada
        - Defina um diretório base e subpastas para organização

        2. Planilhas
        - Gere planilhas Excel personalizadas com cabeçalhos e linhas
        - Escolha entre modelos pré-definidos ou crie os seus

        3. Developer
        - Crie projetos de desenvolvimento com stacks populares
        - React, Node, Python e projetos básicos HTML/CSS/JS
        - Configurações específicas para cada tipo de projeto

        4. Utilitários
        - Acesso rápido a programas e sites favoritos
        - Adicione atalhos personalizados para eficiência

        5. Limpeza
        - Ferramentas de manutenção do sistema
        - Esvaziar lixeira, limpar pasta TEMP e logs

        6. Anotações
        - Crie e organize notas com tags e datas
        - Importe conteúdo de arquivos de texto

        7. Comandos
        - Salve e execute comandos personalizados
        - Acesse rapidamente comandos usados frequentemente

        8. Configurações
        - Personalize o tema e comportamento do sistema
        - Defina diretórios padrão e preferências
        """

        textbox = ctk.CTkTextbox(
            main_content,
            wrap="word",
            font=ctk.CTkFont(size=14)
        )
        textbox.pack(fill="both", expand=True, padx=10, pady=10)
        textbox.insert("1.0", guide_text)
        textbox.configure(state="disabled")  # Somente leitura
    def show_settings_page(self):
        """Exibe a página de configurações"""
        self.clear_main_frame()

        # Título
        title = ctk.CTkLabel(
            self.main_frame,
            text="Configurações",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title.pack(pady=(10, 20))

        # Frame principal
        main_content = ctk.CTkFrame(self.main_frame)
        main_content.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Formulário de configurações
        form_frame = ctk.CTkFrame(main_content)
        form_frame.pack(fill="x", padx=10, pady=10)

        # Campos do formulário
        fields = [
            ("Tema:", "optionmenu", ["Claro", "Escuro", "Sistema"], self.settings["theme"]),
            ("Idioma:", "optionmenu", ["Português", "Inglês"],
             "Português" if self.settings["language"] == "pt" else "Inglês"),
            ("Diretório padrão:", "entry_button", self.settings["default_dir"]),
            ("Salvar dados automaticamente:", "checkbox", self.settings["auto_save"])
        ]

        self.settings_entries = {}

        for i, (label_text, field_type, options_or_default, current_value) in enumerate(fields):
            label = ctk.CTkLabel(form_frame, text=label_text)
            label.grid(row=i, column=0, padx=10, pady=5, sticky="e")

            if field_type == "optionmenu":
                optionmenu = ctk.CTkOptionMenu(form_frame, values=options_or_default)
                optionmenu.grid(row=i, column=1, padx=10, pady=5, sticky="ew")
                optionmenu.set(current_value)
                self.settings_entries[label_text] = optionmenu
            elif field_type == "entry_button":
                frame = ctk.CTkFrame(form_frame, fg_color="transparent")
                frame.grid(row=i, column=1, padx=10, pady=5, sticky="ew")

                entry = ctk.CTkEntry(frame)
                entry.pack(side="left", fill="x", expand=True)
                entry.insert(0, current_value)

                button = ctk.CTkButton(
                    frame,
                    text="Selecionar...",
                    width=80,
                    command=lambda e=entry: self.select_directory(e)
                )
                button.pack(side="left", padx=5)

                self.settings_entries[label_text] = entry
            elif field_type == "checkbox":
                var = ctk.BooleanVar(value=current_value)
                checkbox = ctk.CTkCheckBox(form_frame, text="", variable=var)
                checkbox.grid(row=i, column=1, padx=10, pady=5, sticky="w")
                self.settings_entries[label_text] = var

        # Botões de ação
        buttons_frame = ctk.CTkFrame(main_content, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=10, pady=10)

        save_btn = ctk.CTkButton(
            buttons_frame,
            text="Salvar Configurações",
            command=self.save_app_settings
        )
        save_btn.pack(side="left", padx=5)

        export_btn = ctk.CTkButton(
            buttons_frame,
            text="Exportar Dados",
            fg_color="green",
            command=self.export_data
        )
        export_btn.pack(side="left", padx=5)

        import_btn = ctk.CTkButton(
            buttons_frame,
            text="Importar Dados",
            fg_color="blue",
            command=self.import_data
        )
        import_btn.pack(side="left", padx=5)

        reset_btn = ctk.CTkButton(
            buttons_frame,
            text="Redefinir Tudo",
            fg_color="red",
            hover_color="darkred",
            command=self.reset_data
        )
        reset_btn.pack(side="left", padx=5)
    def save_app_settings(self):
        """Salva as configurações da aplicação"""
        try:
            # Obter valores dos campos
            theme = self.settings_entries["Tema:"].get()
            language = "pt" if self.settings_entries["Idioma:"].get() == "Português" else "en"
            default_dir = self.settings_entries["Diretório padrão:"].get().strip()
            auto_save = self.settings_entries["Salvar dados automaticamente:"].get()

            # Validar diretório
            if not os.path.isdir(default_dir):
                messagebox.showwarning("Aviso", "Diretório padrão inválido!")
                return

            # Atualizar configurações
            self.settings["theme"] = theme
            self.settings["language"] = language
            self.settings["default_dir"] = default_dir
            self.settings["auto_save"] = auto_save

            # Salvar e aplicar
            if self.save_settings():
                ctk.set_appearance_mode(theme)
                messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!")

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar configurações: {e}")
    def export_data(self):
        """Exporta todos os dados para um arquivo JSON"""
        try:
            # Criar objeto com todos os dados
            export_data = {
                "settings": self.settings,
                "projects": self.data["projects"],
                "utilities": self.data["utilities"],
                "notes": self.data["notes"],
                "commands": self.data["commands"]
            }

            # Solicitar local para salvar
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile="pas_export.json"
            )

            if file_path:
                with open(file_path, "w") as f:
                    json.dump(export_data, f, indent=4)

                messagebox.showinfo("Sucesso", f"Dados exportados com sucesso para:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao exportar dados: {e}")
    def import_data(self):
        """Importa dados de um arquivo JSON"""
        try:
            # Solicitar arquivo
            file_path = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )

            if file_path:
                with open(file_path, "r") as f:
                    import_data = json.load(f)

                # Validar estrutura básica
                if not all(key in import_data for key in ["settings", "projects", "utilities", "notes", "commands"]):
                    messagebox.showwarning("Aviso", "Arquivo de importação inválido!")
                    return

                # Confirmar substituição
                confirm = messagebox.askyesno(
                    "Confirmar",
                    "Isso substituirá todos os dados atuais. Continuar?"
                )

                if confirm:
                    self.settings = import_data["settings"]
                    self.data["projects"] = import_data["projects"]
                    self.data["utilities"] = import_data["utilities"]
                    self.data["notes"] = import_data["notes"]
                    self.data["commands"] = import_data["commands"]

                    # Salvar tudo
                    self.save_settings()
                    for key in self.data_files:
                        self.save_data(key)

                    # Aplicar configurações
                    ctk.set_appearance_mode(self.settings["theme"])

                    messagebox.showinfo("Sucesso", "Dados importados com sucesso!")

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao importar dados: {e}")
    def reset_data(self):
        """Redefine todos os dados para os padrões"""
        confirm = messagebox.askyesno(
            "Confirmar",
            "Isso apagará TODOS os dados e redefinirá as configurações. Continuar?"
        )

        if confirm:
            try:
                # Redefinir configurações
                self.settings = {
                    "theme": "Dark",
                    "language": "pt",
                    "default_dir": os.path.expanduser("~"),
                    "auto_save": True,
                    "recent_projects": []
                }

                # Redefinir dados
                self.data = {
                    "projects": [],
                    "utilities": [],
                    "notes": [],
                    "commands": []
                }

                # Salvar tudo
                self.save_settings()
                for key in self.data_files:
                    self.save_data(key)

                # Aplicar configurações
                ctk.set_appearance_mode(self.settings["theme"])

                messagebox.showinfo("Sucesso", "Todos os dados foram redefinidos!")
                self.show_home_page()

            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao redefinir dados: {e}")
    def validate_font_selection(self):
        """Valida se a fonte selecionada suporta os caracteres do texto"""
        try:
            selected_font = self.font_combobox.get()
            if " (padrão)" in selected_font:
                messagebox.showinfo("Validação", "Usando fonte padrão - compatibilidade garantida")
                return True

            # Obter texto de todas as seções
            all_text = self.pdf_title_entry.get()
            for section_frame in self.sections_frame.winfo_children():
                if isinstance(section_frame, ctk.CTkFrame):
                    children = section_frame.winfo_children()
                    text_box = children[3] if len(children) > 3 else None
                    if text_box:
                        all_text += text_box.get("1.0", "end")

            # Verificar caracteres únicos
            unique_chars = set(all_text)

            # Carregar a fonte para verificação
            from fontTools.ttLib import TTFont
            font_path = os.path.join("fonts", selected_font)
            font = TTFont(font_path)

            # Verificar tabela de caracteres suportados
            cmap = font.getBestCmap()
            unsupported_chars = []

            for char in unique_chars:
                char_code = ord(char)
                if char_code not in cmap:
                    unsupported_chars.append(char)

            if unsupported_chars:
                messagebox.showwarning(
                    "Aviso de Compatibilidade",
                    f"A fonte selecionada não suporta os seguintes caracteres:\n"
                    f"{', '.join(unsupported_chars)}\n\n"
                    "Estes caracteres podem aparecer incorretamente no PDF."
                )
                return False
            else:
                messagebox.showinfo("Validação", "Fonte compatível com todos os caracteres do documento!")
                return True

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao validar fonte: {e}")
            return False
    def get_available_fonts(self, fonts_dir="fonts"):
        """Retorna lista de fontes TTF/OTF disponíveis no diretório"""
        font_files = []
        if os.path.exists(fonts_dir):
            for file in os.listdir(fonts_dir):
                if file.lower().endswith(('.ttf', '.otf')):
                    font_files.append(file)
        return font_files
if __name__ == "__main__":
    app = PAS()
    app.mainloop()