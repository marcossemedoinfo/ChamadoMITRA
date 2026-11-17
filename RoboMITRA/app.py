import os
import sys
import threading
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import Optional
from mitra_bot import MitraBot

CONFIG_FILE = "config_usuario.json"

class RoboMitraApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("RoboMITRA - Abertura Automática de Chamados")
        self.geometry("680x880")
        self.minsize(620, 750)
        
        # Cores e Estilo
        self.bg_color = "#f4f6f9"
        self.card_bg = "#ffffff"
        self.primary_color = "#1e88e5"
        self.text_color = "#2c3e50"
        
        self.configure(bg=self.bg_color)
        
        # Variáveis gerais
        self.var_modo = tk.StringVar(value="endereco") # 'endereco' ou 'livre'
        self.var_titulo = tk.StringVar()
        self.var_anexo = tk.StringVar()
        self.var_visual = tk.BooleanVar(value=True)
        self.var_ultimo_protocolo = tk.StringVar(value="-")
        
        # Variáveis do modelo Cadastro de Endereço
        self.var_municipio = tk.StringVar()
        self.var_em = tk.StringVar()
        self.var_inscricao = tk.StringVar()
        self.var_endereco = tk.StringVar()
        self.var_zoneamento = tk.StringVar()
        
        self.bot_thread: Optional[threading.Thread] = None
        
        self._carregar_config()
        self._build_ui()
        self._atualizar_modo()
        
    def _carregar_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.var_municipio.set(data.get("ultimo_municipio", "BEBEDOURO"))
            except Exception:
                self.var_municipio.set("BEBEDOURO")
        else:
            self.var_municipio.set("BEBEDOURO")

    def _salvar_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"ultimo_municipio": self.var_municipio.get().strip()}, f, ensure_ascii=False)
        except Exception:
            pass

    def _build_ui(self):
        # Header Container
        header_frame = tk.Frame(self, bg="#0d47a1", padx=20, pady=14)
        header_frame.pack(fill=tk.X)
        
        lbl_header = tk.Label(
            header_frame,
            text="Robô de Abertura de Chamados - MITRA",
            font=("Segoe UI", 16, "bold"),
            fg="#ffffff",
            bg="#0d47a1"
        )
        lbl_header.pack(anchor="w")
        
        lbl_sub = tk.Label(
            header_frame,
            text="Automação rápida para Cadastro de Endereço e Chamados Gerais",
            font=("Segoe UI", 9),
            fg="#e3f2fd",
            bg="#0d47a1"
        )
        lbl_sub.pack(anchor="w", pady=(2, 0))

        # Container Principal
        main_frame = tk.Frame(self, bg=self.bg_color, padx=18, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Seletor de Modelo / Modo
        mode_box = tk.LabelFrame(
            main_frame,
            text=" Modelo de Chamado ",
            font=("Segoe UI", 9, "bold"),
            bg=self.bg_color,
            fg=self.text_color,
            padx=10,
            pady=6
        )
        mode_box.pack(fill=tk.X, pady=(0, 10))
        
        rb_endereco = tk.Radiobutton(
            mode_box,
            text="📍 Cadastro de Endereço (Preenchimento Rápido)",
            variable=self.var_modo,
            value="endereco",
            font=("Segoe UI", 10, "bold"),
            bg=self.bg_color,
            activebackground=self.bg_color,
            command=self._atualizar_modo
        )
        rb_endereco.pack(side=tk.LEFT, padx=(0, 20))
        
        rb_livre = tk.Radiobutton(
            mode_box,
            text="📝 Chamado Livre / Outro Assunto",
            variable=self.var_modo,
            value="livre",
            font=("Segoe UI", 10),
            bg=self.bg_color,
            activebackground=self.bg_color,
            command=self._atualizar_modo
        )
        rb_livre.pack(side=tk.LEFT)

        # Painel Exclusivo: Campos de Cadastro de Endereço
        self.frame_campos_endereco = tk.LabelFrame(
            main_frame,
            text=" Dados do Cadastro de Endereço ",
            font=("Segoe UI", 9, "bold"),
            bg="#ffffff",
            fg="#1565c0",
            bd=1,
            relief=tk.SOLID,
            padx=12,
            pady=8
        )
        self.frame_campos_endereco.pack(fill=tk.X, pady=(0, 10))

        # Linha 1: Município e Número EM
        row1 = tk.Frame(self.frame_campos_endereco, bg="#ffffff")
        row1.pack(fill=tk.X, pady=2)
        
        lbl_muni = tk.Label(row1, text="Município:", font=("Segoe UI", 9, "bold"), bg="#ffffff", width=12, anchor="w")
        lbl_muni.pack(side=tk.LEFT)
        self.ent_muni = tk.Entry(row1, textvariable=self.var_municipio, font=("Segoe UI", 10), bd=1, relief=tk.SOLID)
        self.ent_muni.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 15), ipady=3)
        self.ent_muni.bind("<KeyRelease>", lambda e: self._gerar_conteudo_endereco())

        lbl_em = tk.Label(row1, text="Nº EM:", font=("Segoe UI", 9, "bold"), bg="#ffffff", width=8, anchor="w")
        lbl_em.pack(side=tk.LEFT)
        self.ent_em = tk.Entry(row1, textvariable=self.var_em, font=("Segoe UI", 10), bd=1, relief=tk.SOLID, width=15)
        self.ent_em.pack(side=tk.LEFT, ipady=3)
        self.ent_em.bind("<KeyRelease>", lambda e: self._gerar_conteudo_endereco())

        # Linha 2: Inscrição
        row2 = tk.Frame(self.frame_campos_endereco, bg="#ffffff")
        row2.pack(fill=tk.X, pady=2)
        lbl_insc = tk.Label(row2, text="Inscrição:", font=("Segoe UI", 9, "bold"), bg="#ffffff", width=12, anchor="w")
        lbl_insc.pack(side=tk.LEFT)
        self.ent_insc = tk.Entry(row2, textvariable=self.var_inscricao, font=("Segoe UI", 10), bd=1, relief=tk.SOLID)
        self.ent_insc.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        self.ent_insc.bind("<KeyRelease>", lambda e: self._gerar_conteudo_endereco())

        # Linha 3: Endereço
        row3 = tk.Frame(self.frame_campos_endereco, bg="#ffffff")
        row3.pack(fill=tk.X, pady=2)
        lbl_end = tk.Label(row3, text="Endereço:", font=("Segoe UI", 9, "bold"), bg="#ffffff", width=12, anchor="w")
        lbl_end.pack(side=tk.LEFT)
        self.ent_end = tk.Entry(row3, textvariable=self.var_endereco, font=("Segoe UI", 10), bd=1, relief=tk.SOLID)
        self.ent_end.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        self.ent_end.bind("<KeyRelease>", lambda e: self._gerar_conteudo_endereco())

        # Linha 4: Zoneamento
        row4 = tk.Frame(self.frame_campos_endereco, bg="#ffffff")
        row4.pack(fill=tk.X, pady=2)
        lbl_zon = tk.Label(row4, text="Zoneamento:", font=("Segoe UI", 9, "bold"), bg="#ffffff", width=12, anchor="w")
        lbl_zon.pack(side=tk.LEFT)
        self.ent_zon = tk.Entry(row4, textvariable=self.var_zoneamento, font=("Segoe UI", 10), bd=1, relief=tk.SOLID)
        self.ent_zon.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        self.ent_zon.bind("<KeyRelease>", lambda e: self._gerar_conteudo_endereco())

        # 1. Campo: Título Final
        self.lbl_titulo = tk.Label(
            main_frame,
            text="Título do Chamado *:",
            font=("Segoe UI", 9, "bold"),
            fg=self.text_color,
            bg=self.bg_color
        )
        self.lbl_titulo.pack(anchor="w", pady=(0, 2))
        
        self.ent_titulo = tk.Entry(
            main_frame,
            textvariable=self.var_titulo,
            font=("Segoe UI", 10),
            relief=tk.SOLID,
            bd=1
        )
        self.ent_titulo.pack(fill=tk.X, ipady=5, pady=(0, 8))
        
        # 2. Campo: Comentário / Descrição Final
        self.lbl_comentario = tk.Label(
            main_frame,
            text="Descrição / Comentário *:",
            font=("Segoe UI", 9, "bold"),
            fg=self.text_color,
            bg=self.bg_color
        )
        self.lbl_comentario.pack(anchor="w", pady=(0, 2))
        
        txt_frame = tk.Frame(main_frame, bg=self.bg_color)
        txt_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        
        self.txt_comentario = tk.Text(
            txt_frame,
            font=("Segoe UI", 9),
            wrap=tk.WORD,
            relief=tk.SOLID,
            bd=1,
            height=5
        )
        scroll_txt = ttk.Scrollbar(txt_frame, command=self.txt_comentario.yview)
        self.txt_comentario.configure(yscrollcommand=scroll_txt.set)
        self.txt_comentario.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_txt.pack(side=tk.RIGHT, fill=tk.Y)

        # 3. Campo: Anexo (Opcional)
        anexo_box = tk.Frame(main_frame, bg=self.bg_color)
        anexo_box.pack(fill=tk.X, pady=(0, 8))
        
        lbl_anexo = tk.Label(anexo_box, text="Anexo:", font=("Segoe UI", 9, "bold"), bg=self.bg_color)
        lbl_anexo.pack(side=tk.LEFT, padx=(0, 6))
        
        self.ent_anexo = tk.Entry(
            anexo_box,
            textvariable=self.var_anexo,
            font=("Segoe UI", 9),
            state="readonly",
            relief=tk.SOLID,
            bd=1
        )
        self.ent_anexo.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=4, padx=(0, 6))
        
        btn_procurar = tk.Button(anexo_box, text="Selecionar...", font=("Segoe UI", 8), command=self._selecionar_anexo, relief=tk.GROOVE)
        btn_procurar.pack(side=tk.LEFT, padx=(0, 4))
        
        btn_limpar_anexo = tk.Button(anexo_box, text="Limpar", font=("Segoe UI", 8), command=self._limpar_anexo, relief=tk.GROOVE)
        btn_limpar_anexo.pack(side=tk.LEFT)

        # Card de Protocolo Gerado
        card_proto = tk.Frame(main_frame, bg="#e8f5e9", bd=1, relief=tk.SOLID, padx=10, pady=6)
        card_proto.pack(fill=tk.X, pady=(0, 8))
        
        lbl_proto_title = tk.Label(card_proto, text="ÚLTIMO PROTOCOLO:", font=("Segoe UI", 8, "bold"), fg="#2e7d32", bg="#e8f5e9")
        lbl_proto_title.pack(side=tk.LEFT, padx=(0, 6))
        
        self.lbl_proto_val = tk.Label(card_proto, textvariable=self.var_ultimo_protocolo, font=("Segoe UI", 11, "bold"), fg="#1b5e20", bg="#e8f5e9")
        self.lbl_proto_val.pack(side=tk.LEFT, padx=(0, 10))
        
        btn_copiar = tk.Button(card_proto, text="📋 Copiar", font=("Segoe UI", 8), command=self._copiar_protocolo, relief=tk.GROOVE)
        btn_copiar.pack(side=tk.RIGHT)

        # Botão Enviar e Opções
        row_action = tk.Frame(main_frame, bg=self.bg_color)
        row_action.pack(fill=tk.X, pady=(0, 6))
        
        chk_visual = tk.Checkbutton(
            row_action,
            text="Visualizar navegador",
            variable=self.var_visual,
            font=("Segoe UI", 8),
            bg=self.bg_color,
            activebackground=self.bg_color
        )
        chk_visual.pack(side=tk.LEFT)

        self.btn_enviar = tk.Button(
            main_frame,
            text="🚀  CRIAR CHAMADO NO MITRA",
            font=("Segoe UI", 11, "bold"),
            bg="#2e7d32",
            fg="#ffffff",
            activebackground="#1b5e20",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            cursor="hand2",
            command=self._iniciar_abertura_chamado,
            pady=8
        )
        self.btn_enviar.pack(fill=tk.X, pady=(0, 6))

        # Barra de Progresso e Log
        self.prog_bar = ttk.Progressbar(main_frame, mode="indeterminate")
        self.prog_bar.pack(fill=tk.X, pady=(0, 4))

        self.txt_log = tk.Text(
            main_frame,
            font=("Consolas", 8),
            wrap=tk.WORD,
            relief=tk.SOLID,
            bd=1,
            height=4,
            bg="#ffffff",
            fg="#333333"
        )
        self.txt_log.pack(fill=tk.BOTH, expand=False)
        self.txt_log.insert(tk.END, "Pronto para abrir chamados.\n")
        self.txt_log.configure(state="disabled")

    def _atualizar_modo(self):
        modo = self.var_modo.get()
        if modo == "endereco":
            self.frame_campos_endereco.pack(fill=tk.X, pady=(0, 10), before=self.lbl_titulo)
            self._gerar_conteudo_endereco()
        else:
            self.frame_campos_endereco.pack_forget()

    def _gerar_conteudo_endereco(self):
        if self.var_modo.get() != "endereco":
            return
            
        muni = self.var_municipio.get().strip().upper()
        em = self.var_em.get().strip().upper()
        if em:
            if not em.startswith("EM-"):
                em_formatado = f"EM-{em}"
            else:
                em_formatado = em
        else:
            em_formatado = "EM-*****"

        muni_txt = muni if muni else "MUNICÍPIO"
        titulo_gerado = f"{muni_txt} - CADASTRO DE ENDEREÇO - {em_formatado}"
        self.var_titulo.set(titulo_gerado)

        insc = self.var_inscricao.get().strip()
        end = self.var_endereco.get().strip()
        zon = self.var_zoneamento.get().strip()

        texto_corpo = (
            "Prezados, bom dia!\n\n"
            "Solicito o cadastro do endereço abaixo:\n"
            f"Inscrição: {insc}\n"
            f"Endereço: {end}\n"
            f"Zoneamento: {zon}"
        )
        self.txt_comentario.delete("1.0", tk.END)
        self.txt_comentario.insert("1.0", texto_corpo)

    def _log(self, text: str):
        self.txt_log.configure(state="normal")
        self.txt_log.insert(tk.END, f"{text}\n")
        self.txt_log.see(tk.END)
        self.txt_log.configure(state="disabled")

    def _copiar_protocolo(self):
        proto = self.var_ultimo_protocolo.get()
        if proto and proto != "-":
            self.clipboard_clear()
            self.clipboard_append(proto)
            messagebox.showinfo("Copiado", f"Protocolo '{proto}' copiado!")

    def _selecionar_anexo(self):
        caminho = filedialog.askopenfilename(title="Selecione o arquivo para anexar ao chamado")
        if caminho:
            self.var_anexo.set(caminho)

    def _limpar_anexo(self):
        self.var_anexo.set("")

    def _iniciar_abertura_chamado(self):
        titulo = self.var_titulo.get().strip()
        comentario = self.txt_comentario.get("1.0", tk.END).strip()
        anexo = self.var_anexo.get().strip() or None
        visual = self.var_visual.get()

        if not titulo or len(titulo) < 4:
            messagebox.showwarning("Atenção", "Por favor, informe o título do chamado.")
            self.ent_titulo.focus()
            return

        if not comentario or len(comentario) < 1:
            messagebox.showwarning("Atenção", "Por favor, digite a descrição do chamado.")
            self.txt_comentario.focus()
            return

        # Salva o município atual para as próximas aberturas
        self._salvar_config()

        confirm = messagebox.askyesno(
            "Confirmar Abertura de Chamado",
            f"Confirma a abertura do chamado no Mitra?\n\n"
            f"Título:\n{titulo}\n\n"
            f"Anexo: {os.path.basename(anexo) if anexo else 'Nenhum'}"
        )
        if not confirm:
            return

        self.btn_enviar.configure(state="disabled", bg="#9e9e9e")
        self.prog_bar.start(15)
        self._log("\n--- Processando abertura de chamado ---")

        def worker():
            bot = MitraBot(
                headless=not visual,
                status_callback=lambda msg: self.after(0, self._log, msg)
            )
            res = bot.criar_chamado(
                titulo=titulo,
                comentario=comentario,
                anexo_path=anexo
            )
            self.after(0, self._finalizar_processo, res, titulo)

        self.bot_thread = threading.Thread(target=worker, daemon=True)
        self.bot_thread.start()

    def _finalizar_processo(self, resultado: dict, titulo_enviado: str):
        self.prog_bar.stop()
        self.btn_enviar.configure(state="normal", bg="#2e7d32")
        
        if resultado.get("success"):
            protocolo = resultado.get("protocolo")
            if protocolo:
                self.var_ultimo_protocolo.set(protocolo)
                self._log(f">>> PROTOCOLO GERADO: {protocolo} <<<")
                self._log(">>> PROCESSO CONCLUÍDO COM SUCESSO! <<<")
                messagebox.showinfo(
                    "Sucesso!",
                    f"🎉 Chamado criado com sucesso no Mitra!\n\n"
                    f"📌 Protocolo: {protocolo}\n"
                    f"📋 Título: {titulo_enviado}"
                )
            else:
                self._log(">>> PROCESSO CONCLUÍDO COM SUCESSO! <<<")
                messagebox.showinfo(
                    "Sucesso!",
                    f"Chamado criado com sucesso no Mitra!\n\nDetalhes:\n{resultado.get('message')}"
                )
            
            # Limpa campos específicos para o próximo (mantém o município)
            self.var_em.set("")
            self.var_inscricao.set("")
            self.var_endereco.set("")
            self.var_zoneamento.set("")
            self.var_anexo.set("")
            if self.var_modo.get() == "endereco":
                self._gerar_conteudo_endereco()
            else:
                self.var_titulo.set("")
                self.txt_comentario.delete("1.0", tk.END)
        else:
            self._log(f">>> FALHA: {resultado.get('message')} <<<")
            messagebox.showerror(
                "Erro",
                f"Não foi possível concluir a abertura do chamado:\n\n{resultado.get('message')}"
            )

def main():
    app = RoboMitraApp()
    app.mainloop()

if __name__ == "__main__":
    main()
