# RoboMITRA - Automação de Abertura de Chamados

Robô inteligente desenvolvido em Python com Playwright para automatizar o processo de abertura de chamados no portal **Mitra Online**.

---

### 🚀 O que o robô faz automaticamente?
1. Faz login no sistema com suas credenciais;
2. Acessa o módulo de **Chamados**;
3. Clica na ação correspondente (ícone verde de chamado);
4. Clica em **Adicionar novo chamado**;
5. Preenche automaticamente com base nas regras fixas:
   - **Destinatário:** `DIOGO CESAR CANDIDO - SETOR DE SUPORTE E IMPLANTACAO`
   - **Categoria:** `OUTROS`
   - **Tipo:** `SOLICITACAO DE SUPORTE TECNICO`
   - **Participantes:**
     - `EDVANI DE LIMA JUNIOR - EMPRESA FACIL`
     - `GABRIEL CARVALHO DAVELLI - EMPRESA FACIL`
     - `GUILHERME DE ALMEIDA PULICE BERNOLDI - EMPRESA FACIL`
     - `NATAN PINA FARIAS - EMPRESA FACIL`
     - `SUPORTE TECNICO - SETOR DE SUPORTE E IMPLANTACAO` (MITRA)
6. Monta o **Título** e o **Comentário** no padrão exato solicitado;
7. Faz o envio do anexo (se selecionado);
8. Submete e **captura o número de protocolo gerado**, exibindo-o na tela com botão de copiar!

---

### 📍 Modelo Especial: Cadastro de Endereço

O aplicativo vem por padrão no modo **Cadastro de Endereço**, onde você só precisa preencher:
- **Município** (ex: BEBEDOURO - o robô lembra do último digitado!)
- **Nº EM** (ex: 16919 ou EM-16919)
- **Inscrição**
- **Endereço**
- **Zoneamento**

O robô formata automaticamente em tempo real:
- **Título:** `MUNICÍPIO - CADASTRO DE ENDEREÇO - EM-*****`
- **Descrição:**
```
Prezados, bom dia!

Solicito o cadastro do endereço abaixo:
Inscrição: ...
Endereço: ...
Zoneamento: ...
```

---

### 🖥️ Como usar:

Dê **dois cliques** em:
👉 **`iniciar_robo.bat`**
