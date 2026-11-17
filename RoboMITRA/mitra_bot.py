import os
import re
import time
from typing import Optional, Callable, List
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

load_dotenv()

class MitraBot:
    def __init__(
        self,
        user: Optional[str] = None,
        password: Optional[str] = None,
        url: Optional[str] = None,
        headless: bool = False,
        status_callback: Optional[Callable[[str], None]] = None
    ):
        self.user = user or os.getenv("MITRA_USER", "")
        self.password = password or os.getenv("MITRA_PASSWORD", "")
        self.url = url or os.getenv("MITRA_URL", "https://chamado.mitraonline.com.br/")
        self.headless = headless
        self.status_callback = status_callback or (lambda msg: print(f"[MITRA] {msg}"))
        
        # Dados padrão da regra de negócio solicitada
        self.default_destinatario_nome = "DIOGO CESAR CANDIDO - SETOR DE SUPORTE E IMPLANTACAO"
        self.default_destinatario_id = "643"
        self.default_categoria_nome = "OUTROS"
        self.default_categoria_id = "148"
        self.default_tipo_nome = "SOLICITACAO DE SUPORTE TECNICO"
        self.default_tipo_id = "1"
        self.default_participantes_ids = ["579", "768", "572", "927", "897"]
        self.default_participantes_nomes = [
            "EDVANI DE LIMA JUNIOR - EMPRESA FACIL",
            "GABRIEL CARVALHO DAVELLI - EMPRESA FACIL",
            "GUILHERME DE ALMEIDA PULICE BERNOLDI - EMPRESA FACIL",
            "NATAN PINA FARIAS - EMPRESA FACIL",
            "SUPORTE TECNICO - SETOR DE SUPORTE E IMPLANTACAO"
        ]

    def log(self, message: str):
        if self.status_callback:
            self.status_callback(message)

    def _safe_screenshot(self, page: Page, path: str):
        """Captura screenshot de forma segura sem interromper o fluxo principal se falhar."""
        try:
            page.screenshot(path=path, timeout=3000)
        except Exception:
            pass

    def extrair_protocolo(self, html: str, titulo_buscado: str) -> Optional[str]:
        """
        Extrai o número do protocolo do HTML da listagem de chamados.
        Tenta primeiro casar com o título recém-criado, e depois pega o mais recente no topo.
        """
        # Formato das células de chamado no Mitra: <td width="82%" ...>
        matches = re.findall(r'<td\s+width=["\']82%["\'][^>]*>(.*?)</td>', html, re.DOTALL | re.IGNORECASE)
        
        # 1. Tentar encontrar a linha que contenha o título enviado
        titulo_limpo = titulo_buscado.strip().lower()
        for m in matches:
            clean = re.sub(r'<[^>]+>', '\n', m)
            lines = [l.strip() for l in clean.splitlines() if l.strip()]
            if len(lines) >= 2:
                num_proto = lines[0]
                titulo_linha = lines[1].lower()
                if titulo_limpo in titulo_linha or titulo_linha in titulo_limpo:
                    if re.match(r'^\d{3,6}\.\d{4}$', num_proto):
                        return num_proto

        # 2. Se não casou exatamente pelo título, pega o primeiro chamado do topo da lista
        for m in matches:
            clean = re.sub(r'<[^>]+>', '\n', m)
            lines = [l.strip() for l in clean.splitlines() if l.strip()]
            if lines and re.match(r'^\d{3,6}\.\d{4}$', lines[0]):
                return lines[0]

        # 3. Fallback genérico: busca o primeiro padrão \d+\.\d{4} presente no HTML
        todos_protocolos = re.findall(r"\b(\d{3,6}\.\d{4})\b", html)
        if todos_protocolos:
            return todos_protocolos[0]

        return None

    def criar_chamado(
        self,
        titulo: str,
        comentario: str,
        anexo_path: Optional[str] = None
    ) -> dict:
        """
        Executa o fluxo completo de abertura de chamado no sistema Mitra.
        Retorna: {'success': bool, 'protocolo': str, 'message': str}
        """
        if not self.user or not self.password:
            return {"success": False, "protocolo": None, "message": "Usuário ou senha não configurados no arquivo .env."}
        
        if not titulo or len(titulo.strip()) < 4:
            return {"success": False, "protocolo": None, "message": "O título precisa ter no mínimo 4 caracteres."}
            
        if not comentario or len(comentario.strip()) < 1:
            return {"success": False, "protocolo": None, "message": "O comentário não pode ficar vazio."}
            
        if anexo_path and not os.path.exists(anexo_path):
            return {"success": False, "protocolo": None, "message": f"Arquivo de anexo não encontrado: {anexo_path}"}

        self.log("Iniciando navegador...")
        with sync_playwright() as p:
            browser: Browser = p.chromium.launch(headless=self.headless, slow_mo=100)
            context: BrowserContext = browser.new_context()
            page: Page = context.new_page()

            # Capturar diálogos/alertas nativos do navegador
            dialog_messages = []
            def handle_dialog(dialog):
                msg = dialog.message
                dialog_messages.append(msg)
                self.log(f"Alerta do sistema: {msg}")
                try:
                    dialog.accept()
                except Exception:
                    pass

            page.on("dialog", handle_dialog)

            try:
                # 1. Login
                self.log("Acessando página de login do Mitra...")
                page.goto(self.url, wait_until="networkidle", timeout=45000)
                
                self.log(f"Autenticando usuário '{self.user}'...")
                page.fill("#txt_usuario", self.user)
                page.fill("#txt_senha", self.password)
                page.click("#conectar")
                page.wait_for_load_state("networkidle", timeout=30000)

                if "principal" not in page.url and page.locator("text=Chamados").count() == 0:
                    self._safe_screenshot(page, "erro_login.png")
                    return {"success": False, "protocolo": None, "message": "Falha no login. Verifique seu usuário e senha."}

                self.log("Login realizado com sucesso!")

                # 2. Navegar para Chamados
                self.log("Acessando módulo de Chamados...")
                page.click("text=Chamados")
                page.wait_for_load_state("networkidle", timeout=30000)

                # 3. Clicar no ícone de ação (papel com ícone verde)
                self.log("Acessando listagem de chamados (Ações)...")
                acao_btn = page.locator("img[src*='page-finsh-icon']").first
                if not acao_btn.is_visible():
                    acao_btn = page.locator("a:has(img[src*='page-finsh-icon'])").first
                
                if not acao_btn.is_visible():
                    self._safe_screenshot(page, "erro_acao.png")
                    return {"success": False, "protocolo": None, "message": "Não foi possível localizar o botão de Ações da tabela."}
                    
                acao_btn.click()
                page.wait_for_load_state("networkidle", timeout=30000)

                # 4. Clicar em "Adicionar novo chamado"
                self.log("Abrindo formulário de novo chamado...")
                novo_chamado_btn = page.locator("text=Adicionar novo chamado").first
                if not novo_chamado_btn.is_visible():
                    self._safe_screenshot(page, "erro_novo_chamado.png")
                    return {"success": False, "protocolo": None, "message": "Botão 'Adicionar novo chamado' não encontrado."}

                novo_chamado_btn.click()
                page.wait_for_load_state("networkidle", timeout=30000)
                page.wait_for_timeout(1500)

                # 5. Selecionar Destinatário: DIOGO CESAR CANDIDO (ID: 643)
                self.log(f"Selecionando Destinatário: {self.default_destinatario_nome}...")
                page.evaluate(f"""
                    $('#selDestinatario').val('{self.default_destinatario_id}').trigger('chosen:updated').trigger('change');
                """)
                
                # Aguardar AJAX de Categorias
                self.log("Carregando categorias vinculadas ao destinatário...")
                page.wait_for_timeout(2500)

                # 6. Selecionar Categoria: OUTROS (ID: 148 ou busca dinâmica)
                self.log(f"Selecionando Categoria: {self.default_categoria_nome}...")
                categoria_id = page.evaluate("""(nomeDesejado) => {
                    let encontrado = null;
                    $('#selCategoria option').each(function() {
                        if ($(this).text().trim().toUpperCase() === nomeDesejado.toUpperCase()) {
                            encontrado = $(this).val();
                        }
                    });
                    if (!encontrado) {
                        $('#selCategoria option').each(function() {
                            if ($(this).text().toUpperCase().indexOf(nomeDesejado.toUpperCase()) !== -1) {
                                encontrado = $(this).val();
                            }
                        });
                    }
                    return encontrado;
                }""", self.default_categoria_nome) or self.default_categoria_id

                page.evaluate(f"""
                    $('#selCategoria').val('{categoria_id}').trigger('chosen:updated').trigger('change');
                """)
                page.wait_for_timeout(500)

                # 7. Selecionar Tipo: SOLICITACAO DE SUPORTE TECNICO (ID: 1)
                self.log(f"Selecionando Tipo: {self.default_tipo_nome}...")
                page.evaluate(f"""
                    $('#selTipo').val('{self.default_tipo_id}').trigger('chosen:updated').trigger('change');
                """)
                page.wait_for_timeout(500)

                # 8. Selecionar Participantes
                self.log("Adicionando participantes (Edvani, Gabriel, Guilherme, Natan, Suporte Técnico)...")
                page.evaluate("""(ids) => {
                    $('#selParticipante').val(ids).trigger('chosen:updated').trigger('change');
                    $('#listaParticipantes').val(ids.join(','));
                }""", self.default_participantes_ids)
                page.wait_for_timeout(500)

                # 9. Preencher Título
                self.log(f"Preenchendo Título: '{titulo}'...")
                page.fill("#txtTitulo", titulo.strip())

                # 10. Preencher Comentário no TinyMCE
                self.log("Inserindo texto do comentário...")
                comentario_html = "".join(f"<p>{linha.strip()}</p>" for linha in comentario.strip().split("\n") if linha.strip())
                page.evaluate("""(htmlContent) => {
                    if (typeof tinymce !== 'undefined' && tinymce.get('txaComentario')) {
                        tinymce.get('txaComentario').setContent(htmlContent);
                    }
                    $('#txaComentario').val(htmlContent);
                }""", comentario_html)

                # 11. Anexo (se fornecido)
                if anexo_path:
                    abs_anexo = os.path.abspath(anexo_path)
                    self.log(f"Anexando arquivo: {os.path.basename(abs_anexo)}...")
                    page.set_input_files("#flAnexo", abs_anexo)
                    page.wait_for_timeout(1000)

                # 12. Submeter chamado
                self.log("Clicando no botão 'Adicionar'...")
                self._safe_screenshot(page, "ultimo_envio_preenchido.png")
                page.click("#btn_adicionar")
                
                # 13. Aguardar processamento do servidor
                self.log("Aguardando confirmação do servidor...")
                page.wait_for_load_state("networkidle", timeout=30000)
                page.wait_for_timeout(3000)

                # 14. Fechar modal de sucesso se estiver visível (botão OK)
                try:
                    btn_ok = page.locator("button:has-text('OK'), input[value='OK'], .ui-dialog-buttonpane button").first
                    if btn_ok.is_visible(timeout=3000):
                        self.log("Fechando caixa de mensagem de sucesso...")
                        btn_ok.click()
                        page.wait_for_timeout(1000)
                except Exception:
                    pass

                self._safe_screenshot(page, "resultado_pos_envio.png")

                # 15. Extração do Protocolo
                self.log("Localizando o número de protocolo gerado...")
                html_final = page.content()
                protocolo = self.extrair_protocolo(html_final, titulo)
                
                if protocolo:
                    self.log(f"Protocolo identificado: {protocolo}")
                    msg_sucesso = f"Chamado criado com sucesso!\n\nProtocolo: {protocolo}"
                else:
                    self.log("Chamado criado com sucesso, mas o protocolo não pôde ser lido na tela.")
                    msg_sucesso = "Chamado criado com sucesso no sistema Mitra!"

                return {
                    "success": True,
                    "protocolo": protocolo,
                    "message": msg_sucesso,
                    "url": page.url
                }

            except Exception as e:
                self.log(f"Erro durante o processo: {str(e)}")
                self._safe_screenshot(page, "erro_excecao.png")
                return {"success": False, "protocolo": None, "message": f"Erro de execução: {str(e)}"}
            finally:
                context.close()
                browser.close()

if __name__ == "__main__":
    bot = MitraBot(headless=False)
    print("Módulo MitraBot pronto.")
