import json
import os
import asyncio
import requests
import platform
import ssl
import logging
from datetime import datetime
from telethon import TelegramClient, events, Button
from telethon.errors import FloodWaitError
from telethon.tl.functions.users import GetFullUserRequest
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# ══════════════════════════════════════════════
# 🔒  SSL / REQUESTS CONFIG
# ══════════════════════════════════════════════
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = "TLS_AES_128_GCM_SHA256:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_256_GCM_SHA384:TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256:TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256:TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256:TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256:TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384:TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384:TLS_ECDHE_ECDSA_WITH_AES_256_CBC_SHA:TLS_ECDHE_ECDSA_WITH_AES_128_CBC_SHA:TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA:TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA:TLS_RSA_WITH_AES_128_GCM_SHA256:TLS_RSA_WITH_AES_256_GCM_SHA384:TLS_RSA_WITH_AES_128_CBC_SHA:TLS_RSA_WITH_AES_256_CBC_SHA:TLS_RSA_WITH_3DES_EDE_CBC_SHA:TLS13-CHACHA20-POLY1305-SHA256:TLS13-AES-128-GCM-SHA256:TLS13-AES-256-GCM-SHA384:ECDHE:!COMP:TLS13-AES-256-GCM-SHA384:TLS13-CHACHA20-POLY1305-SHA256:TLS13-AES-128-GCM-SHA256"
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
logging.captureWarnings(True)

try:
    ssl._create_default_https_context = ssl._create_unverified_context
except Exception:
    pass

# ══════════════════════════════════════════════
# ⚙️  CONFIGURAÇÕES
# ══════════════════════════════════════════════
API_ID = 29214781                        # Obtenha em https://my.telegram.org
API_HASH = "9fc77b4f32302f4d4081a4839cc7ae1f"
PHONE = "+5588998225077"
BOT_TOKEN = "8618840827:AAEQx9qnUiDpjqzlMAoyjIxxGXbM_I71wQw"
OWNER_ID = 2061557102                    # Edivaldo Silva @Edkd1

# API de consulta
API_CONSULTA_URL = "https://searchapi.dnnl.live/consulta"
API_CONSULTA_TOKEN = "4150"

FOLDER_PATH = "data"
CONFIG_PATH = os.path.join(FOLDER_PATH, "grupos_config.json")
LOG_PATH = os.path.join(FOLDER_PATH, "bot_interacao.log")
SESSION_USER = "session_monitor"
SESSION_BOT = "session_bot"

ITEMS_PER_PAGE = 8

# ══════════════════════════════════════════════
# 📁  CONFIGURAÇÃO DE GRUPOS (JSON)
# ══════════════════════════════════════════════
os.makedirs(FOLDER_PATH, exist_ok=True)


def carregar_config() -> dict:
    """Carrega configuração dos grupos monitorados."""
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"grupos": {}, "respostas_auto": True}
    return {"grupos": {}, "respostas_auto": True}


def salvar_config(config: dict):
    """Salva configuração dos grupos."""
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except IOError as e:
        log(f"❌ Erro ao salvar config: {e}")


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(line + "\n")
    except IOError:
        pass


# ══════════════════════════════════════════════
# 🤖  CLIENTES TELETHON
# ══════════════════════════════════════════════
user_client = TelegramClient(SESSION_USER, API_ID, API_HASH)
bot = TelegramClient(SESSION_BOT, API_ID, API_HASH)


def is_admin(user_id: int) -> bool:
    """Verifica se o usuário é o administrador/dono do bot."""
    return user_id == OWNER_ID


# ══════════════════════════════════════════════
# 🔍  CONSULTA CPF (API)
# ══════════════════════════════════════════════

def consultar_cpf(cpf: str) -> str:
    """Consulta CPF na API e retorna texto formatado."""
    params = {
        "token_api": API_CONSULTA_TOKEN,
        "cpf": cpf
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (educational script)",
        "Accept": "application/json"
    }

    try:
        response = requests.get(API_CONSULTA_URL, params=params, headers=headers, timeout=10)
    except requests.exceptions.RequestException as e:
        return f"❌ **Erro de conexão com a API**\n`{e}`"

    try:
        data = response.json()
    except json.JSONDecodeError:
        return "⚠️ Resposta da API não está em JSON."

    if response.status_code != 200:
        mensagem = data.get("mensagem", "Erro desconhecido da API")
        return f"❌ **Erro:** {mensagem}"

    if "dados" not in data or not data["dados"]:
        return "❌ Nenhum registro encontrado para este CPF."

    registro = data["dados"][0]

    def s(v):
        return str(v) if v else "Não informado"

    return f"""╔══════════════════════════╗
║  📄 **CONSULTA CPF**       ║
╚══════════════════════════╝

👤 **Nome:** `{s(registro.get('NOME'))}`
🔢 **CPF:** `{s(registro.get('CPF'))}`
📅 **Nascimento:** `{s(registro.get('NASC'))}`
⚧ **Sexo:** `{s(registro.get('SEXO'))}`

👩 **Mãe:** `{s(registro.get('NOME_MAE'))}`
👨 **Pai:** `{s(registro.get('NOME_PAI'))}`

🪪 **RG:** `{s(registro.get('RG'))}`
🏛️ **Órgão Emissor:** `{s(registro.get('ORGAO_EMISSOR'))}`
📍 **UF Emissão:** `{s(registro.get('UF_EMISSAO'))}`

🗳️ **Título Eleitor:** `{s(registro.get('TITULO_ELEITOR'))}`
💰 **Renda:** `{s(registro.get('RENDA'))}`
📱 **SO:** `{s(registro.get('SO'))}`

▬▬▬ஜ۩𝑬𝒅𝒊𝒗𝒂𝒍𝒅𝒐۩ஜ▬▬▬"""


# ══════════════════════════════════════════════
# 🔔  NOTIFICAÇÃO
# ══════════════════════════════════════════════
async def notificar(texto: str):
    try:
        await bot.send_message(OWNER_ID, texto, parse_mode='md')
    except Exception as e:
        log(f"Erro notificação: {e}")


# ══════════════════════════════════════════════
# 🎨  INTERFACE — MENUS INLINE
# ══════════════════════════════════════════════

def menu_principal_buttons(user_id: int = 0):
    btns = [
        [Button.inline("🔍 Consultar CPF", b"cmd_consultar"),
         Button.inline("📊 Status", b"cmd_stats")],
    ]
    if is_admin(user_id):
        btns.append(
            [Button.inline("⚙️ Configurar Grupos", b"cmd_config_grupos"),
             Button.inline("🔄 Respostas Auto", b"cmd_toggle_auto")]
        )
        btns.append(
            [Button.inline("📋 Grupos Ativos", b"cmd_listar_grupos"),
             Button.inline("⚙️ Configurações", b"cmd_config")]
        )
    btns.append([Button.inline("ℹ️ Sobre", b"cmd_about")])
    return btns


def voltar_button():
    return [[Button.inline("🔙 Menu Principal", b"cmd_menu")]]


def paginar_buttons(prefix: str, page: int, total_pages: int):
    btns = []
    nav = []
    if page > 0:
        nav.append(Button.inline("◀️ Anterior", f"{prefix}_page_{page - 1}".encode()))
    nav.append(Button.inline(f"📄 {page + 1}/{total_pages}", b"noop"))
    if page < total_pages - 1:
        nav.append(Button.inline("Próxima ▶️", f"{prefix}_page_{page + 1}".encode()))
    btns.append(nav)
    btns.append([Button.inline("🔙 Menu Principal", b"cmd_menu")])
    return btns


# ══════════════════════════════════════════════
# 📡  AUTO-RESPOSTA EM GRUPOS
# ══════════════════════════════════════════════

def grupo_esta_configurado(chat_id: int) -> bool:
    """Verifica se o grupo está na lista de grupos configurados."""
    config = carregar_config()
    return str(chat_id) in config.get("grupos", {})


def extrair_cpf(texto: str) -> str:
    """Extrai CPF de uma mensagem — com ou sem pontuação.
    Aceita: 123.456.789-00, 123456789-00, 12345678900, etc."""
    import re
    # 1) Tenta formato com pontuação: 000.000.000-00
    match = re.search(r'(\d{3}[.\s]?\d{3}[.\s]?\d{3}[-.\s]?\d{2})', texto)
    if match:
        return re.sub(r'[.\-/\s]', '', match.group(1))
    # 2) Tenta 11 dígitos seguidos
    match = re.search(r'(\d{11})', texto)
    if match:
        return match.group(1)
    return ""


async def processar_mencao_grupo(event):
    """Processa menção ao dono em grupo configurado."""
    config = carregar_config()
    if not config.get("respostas_auto", True):
        return

    chat_id = str(event.chat_id)
    if chat_id not in config.get("grupos", {}):
        return

    # Verifica se a mensagem é uma resposta a uma mensagem do dono
    # ou se menciona o dono
    eh_mencao = False

    # Verifica reply
    if event.is_reply:
        try:
            replied = await event.get_reply_message()
            if replied and replied.sender_id == OWNER_ID:
                eh_mencao = True
        except Exception:
            pass

    # Verifica menção direta (@username do dono)
    if not eh_mencao and event.mentioned:
        eh_mencao = True

    # Verifica se mencionou por entidades
    if not eh_mencao and event.message.entities:
        for entity in event.message.entities:
            if hasattr(entity, 'user_id') and entity.user_id == OWNER_ID:
                eh_mencao = True
                break

    if not eh_mencao:
        return

    # Pessoa mencionou o dono — processar a mensagem
    texto = event.text or ""
    sender = await event.get_sender()
    nome_sender = f"{sender.first_name or ''} {sender.last_name or ''}".strip() if sender else "Alguém"

    log(f"📩 Menção recebida de {nome_sender} no grupo {chat_id}: {texto[:80]}")

    # Tenta extrair CPF da mensagem
    cpf = extrair_cpf(texto)

    if cpf:
        # Consulta CPF automaticamente
        resultado = consultar_cpf(cpf)
        await event.reply(resultado, parse_mode='md')
        log(f"✅ Consulta CPF automática respondida para {nome_sender}")
    else:
        # Resposta genérica — reconhece a menção
        grupo_config = config["grupos"][chat_id]
        resposta_padrao = grupo_config.get("resposta_padrao", "")

        if resposta_padrao:
            await event.reply(resposta_padrao, parse_mode='md')
        else:
            await event.reply(
                f"👋 Olá **{nome_sender}**!\n\n"
                f"Vi que me mencionou. Como posso ajudar?\n\n"
                f"💡 **Dica:** Envie um CPF (11 dígitos) na mensagem que eu consulto automaticamente.\n\n"
                f"_▬▬▬ஜ۩𝑬𝒅𝒊𝒗𝒂𝒍𝒅𝒐۩ஜ▬▬▬_",
                parse_mode='md'
            )


# ══════════════════════════════════════════════
# 🎮  HANDLERS DO BOT
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(pattern='/start'))
async def cmd_start(event):
    sender = await event.get_sender()
    uid = sender.id if sender else 0
    await event.respond(
        f"""╔══════════════════════════════╗
║  🤖 **Bot Interação v4.0**      ║
╚══════════════════════════════╝

Bem-vindo ao bot de interação pessoal!

🔍 **Consulte** CPF diretamente
⚙️ **Configure** grupos para auto-resposta
📡 **Responda** automaticamente quando citado

━━━━━━━━━━━━━━━━━━━━━
👨‍💻 _Créditos: Edivaldo Silva @Edkd1_
⚡ _Powered by 773H_
━━━━━━━━━━━━━━━━━━━━━

Selecione uma opção abaixo:""",
        parse_mode='md',
        buttons=menu_principal_buttons(uid)
    )


@bot.on(events.NewMessage(pattern='/menu'))
async def cmd_menu_msg(event):
    await cmd_start(event)


# ══════════════════════════════════════════════
# 🔘  HANDLERS DE CALLBACK (BOTÕES INLINE)
# ══════════════════════════════════════════════

# Estados temporários por chat
pending_action = {}

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode()
    chat_id = event.chat_id
    sender_id = event.sender_id

    try:
        message = await event.get_message()

        # ── Menu Principal ──
        if data == "cmd_menu":
            await message.edit(
                f"""╔══════════════════════════════╗
║  🤖 **Bot Interação v4.0**      ║
╚══════════════════════════════╝

Selecione uma opção:""",
                parse_mode='md',
                buttons=menu_principal_buttons(sender_id)
            )

        # ── Consultar CPF ──
        elif data == "cmd_consultar":
            pending_action[chat_id] = "aguardando_cpf"
            await message.edit(
                """🔍 **Modo Consulta CPF**

━━━━━━━━━━━━━━━━━━━━━
📝 **Envie o CPF** (apenas números):

• Exemplo: `12345678900`
• Ou com pontuação: `123.456.789-00`

━━━━━━━━━━━━━━━━━━━━━
_Aguardando CPF..._""",
                parse_mode='md',
                buttons=voltar_button()
            )

        # ── Status ──
        elif data == "cmd_stats":
            config = carregar_config()
            total_grupos = len(config.get("grupos", {}))
            auto_ativo = "✅ Ativo" if config.get("respostas_auto", True) else "❌ Desativado"

            await message.edit(
                f"""╔══════════════════════════╗
║  📊 **STATUS DO BOT**      ║
╚══════════════════════════╝

🤖 **Bot Interação v4.0**

📡 **Grupos Configurados:** **{total_grupos}**
🔄 **Auto-Resposta:** {auto_ativo}
🔍 **API Consulta:** Ativa

⚙️ **Sistema:**
├ 💾 Config: `{CONFIG_PATH}`
├ 📝 Logs: `{LOG_PATH}`
└ 🕐 Uptime: `Ativo`

_Créditos: @Edkd1_""",
                parse_mode='md',
                buttons=voltar_button()
            )

        # ── Configurar Grupos (ADMIN) ──
        elif data == "cmd_config_grupos":
            if not is_admin(sender_id):
                await event.answer("🔒 Apenas o administrador.", alert=True)
                return

            await message.edit(
                """⚙️ **Configurar Grupos**

━━━━━━━━━━━━━━━━━━━━━
Escolha uma ação:

• **Adicionar** — Cadastra um grupo pelo ID
• **Remover** — Remove grupo da lista
• **Resposta** — Define resposta padrão

━━━━━━━━━━━━━━━━━━━━━
_Grupos configurados receberão auto-resposta quando você for citado._""",
                parse_mode='md',
                buttons=[
                    [Button.inline("➕ Adicionar Grupo", b"cmd_add_grupo"),
                     Button.inline("➖ Remover Grupo", b"cmd_rem_grupo")],
                    [Button.inline("💬 Definir Resposta Padrão", b"cmd_set_resposta")],
                    [Button.inline("📋 Ver Grupos Ativos", b"cmd_listar_grupos")],
                    [Button.inline("🔙 Menu Principal", b"cmd_menu")]
                ]
            )

        # ── Adicionar Grupo ──
        elif data == "cmd_add_grupo":
            if not is_admin(sender_id):
                await event.answer("🔒 Apenas o administrador.", alert=True)
                return
            pending_action[chat_id] = "aguardando_grupo_id"
            await message.edit(
                """➕ **Adicionar Grupo**

━━━━━━━━━━━━━━━━━━━━━
📝 **Envie o ID do grupo** (número negativo):

• Exemplo: `-1001234567890`
• Ou encaminhe uma mensagem do grupo

💡 Para descobrir o ID, adicione o bot ao grupo e use `/id` lá.

━━━━━━━━━━━━━━━━━━━━━
_Aguardando ID do grupo..._""",
                parse_mode='md',
                buttons=voltar_button()
            )

        # ── Remover Grupo ──
        elif data == "cmd_rem_grupo":
            if not is_admin(sender_id):
                await event.answer("🔒 Apenas o administrador.", alert=True)
                return

            config = carregar_config()
            grupos = config.get("grupos", {})

            if not grupos:
                await message.edit(
                    "❌ **Nenhum grupo configurado.**\n\nAdicione um grupo primeiro.",
                    parse_mode='md',
                    buttons=voltar_button()
                )
                return

            btns = []
            for gid, info in grupos.items():
                nome = info.get("nome", gid)
                btns.append([Button.inline(f"🗑️ {nome} ({gid})", f"remover_{gid}".encode())])
            btns.append([Button.inline("🔙 Voltar", b"cmd_config_grupos")])

            await message.edit(
                "➖ **Selecione o grupo para remover:**",
                parse_mode='md',
                buttons=btns
            )

        # ── Confirmar remoção ──
        elif data.startswith("remover_"):
            if not is_admin(sender_id):
                await event.answer("🔒 Apenas o administrador.", alert=True)
                return

            gid = data.replace("remover_", "")
            config = carregar_config()
            grupos = config.get("grupos", {})

            if gid in grupos:
                nome = grupos[gid].get("nome", gid)
                del grupos[gid]
                config["grupos"] = grupos
                salvar_config(config)
                log(f"➖ Grupo removido: {nome} ({gid})")
                await message.edit(
                    f"✅ **Grupo removido com sucesso!**\n\n🗑️ `{nome}` (`{gid}`)",
                    parse_mode='md',
                    buttons=voltar_button()
                )
            else:
                await event.answer("❌ Grupo não encontrado.", alert=True)

        # ── Definir Resposta Padrão ──
        elif data == "cmd_set_resposta":
            if not is_admin(sender_id):
                await event.answer("🔒 Apenas o administrador.", alert=True)
                return

            config = carregar_config()
            grupos = config.get("grupos", {})

            if not grupos:
                await message.edit(
                    "❌ **Nenhum grupo configurado.**\n\nAdicione um grupo primeiro.",
                    parse_mode='md',
                    buttons=voltar_button()
                )
                return

            btns = []
            for gid, info in grupos.items():
                nome = info.get("nome", gid)
                btns.append([Button.inline(f"💬 {nome}", f"setresp_{gid}".encode())])
            btns.append([Button.inline("🔙 Voltar", b"cmd_config_grupos")])

            await message.edit(
                "💬 **Selecione o grupo para definir resposta padrão:**\n\n"
                "_A resposta padrão é enviada quando você é citado mas não há CPF na mensagem._",
                parse_mode='md',
                buttons=btns
            )

        elif data.startswith("setresp_"):
            if not is_admin(sender_id):
                await event.answer("🔒 Apenas o administrador.", alert=True)
                return

            gid = data.replace("setresp_", "")
            pending_action[chat_id] = f"aguardando_resposta_{gid}"

            config = carregar_config()
            resp_atual = config.get("grupos", {}).get(gid, {}).get("resposta_padrao", "Nenhuma definida")

            await message.edit(
                f"💬 **Definir Resposta Padrão**\n\n"
                f"📍 Grupo: `{gid}`\n"
                f"📝 Atual: _{resp_atual}_\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"**Envie a nova resposta padrão:**\n\n"
                f"_Suporta Markdown. Envie `limpar` para remover._",
                parse_mode='md',
                buttons=voltar_button()
            )

        # ── Toggle Auto-Resposta ──
        elif data == "cmd_toggle_auto":
            if not is_admin(sender_id):
                await event.answer("🔒 Apenas o administrador.", alert=True)
                return

            config = carregar_config()
            config["respostas_auto"] = not config.get("respostas_auto", True)
            salvar_config(config)

            estado = "✅ Ativado" if config["respostas_auto"] else "❌ Desativado"
            await event.answer(f"Auto-resposta: {estado}", alert=True)
            # Atualiza menu
            await message.edit(
                f"""╔══════════════════════════════╗
║  🤖 **Bot Interação v4.0**      ║
╚══════════════════════════════╝

🔄 Auto-resposta: **{estado}**

Selecione uma opção:""",
                parse_mode='md',
                buttons=menu_principal_buttons(sender_id)
            )

        # ── Listar Grupos ──
        elif data == "cmd_listar_grupos":
            config = carregar_config()
            grupos = config.get("grupos", {})

            if not grupos:
                await message.edit(
                    "📋 **Nenhum grupo configurado.**\n\n"
                    "Use ⚙️ Configurar Grupos para adicionar.",
                    parse_mode='md',
                    buttons=voltar_button()
                )
                return

            text = "📋 **Grupos Configurados:**\n\n"
            for i, (gid, info) in enumerate(grupos.items(), 1):
                nome = info.get("nome", "Sem nome")
                resp = info.get("resposta_padrao", "Padrão")
                adicionado = info.get("adicionado_em", "N/A")
                text += f"**{i}.** `{nome}`\n"
                text += f"   🔢 ID: `{gid}`\n"
                text += f"   💬 Resposta: _{resp[:30] if resp else 'Padrão'}{'...' if resp and len(resp) > 30 else ''}_\n"
                text += f"   📅 Desde: `{adicionado}`\n\n"

            auto = "✅" if config.get("respostas_auto", True) else "❌"
            text += f"🔄 Auto-resposta: {auto}"

            await message.edit(text, parse_mode='md', buttons=[
                [Button.inline("⚙️ Configurar", b"cmd_config_grupos")],
                [Button.inline("🔙 Menu Principal", b"cmd_menu")]
            ])

        # ── Configurações ──
        elif data == "cmd_config":
            config = carregar_config()
            auto = "✅ Ativo" if config.get("respostas_auto", True) else "❌ Desativado"
            total_grupos = len(config.get("grupos", {}))

            await message.edit(
                f"""⚙️ **Configurações Atuais**

━━━━━━━━━━━━━━━━━━━━━
🔄 Auto-resposta: **{auto}**
📡 Grupos configurados: **{total_grupos}**
🔍 API Token: `{API_CONSULTA_TOKEN}`
💾 Config: `{CONFIG_PATH}`
📝 Logs: `{LOG_PATH}`
━━━━━━━━━━━━━━━━━━━━━

_Para alterar token da API, edite as constantes no código._
_Créditos: @Edkd1_""",
                parse_mode='md',
                buttons=voltar_button()
            )

        # ── Sobre ──
        elif data == "cmd_about":
            await message.edit(
                """╔══════════════════════════════╗
║  ℹ️ **SOBRE O BOT**           ║
╚══════════════════════════════╝

🤖 **Bot Interação v4.0**
_Bot pessoal de interação e consulta_

━━━━━━━━━━━━━━━━━━━━━
**Funcionalidades:**
• 🔍 Consulta CPF via API
• ⚙️ Configuração de grupos
• 📡 Auto-resposta quando citado
• 💬 Respostas personalizadas por grupo
• 📊 Status e configurações

**Como funciona a auto-resposta:**
1. Configure um grupo pelo ID
2. Quando alguém te citar no grupo:
   - Se enviar CPF → Consulta automática
   - Sem CPF → Resposta padrão definida

**Tecnologia:**
• ⚡ Telethon (asyncio)
• 🔍 API de consulta integrada
• 💾 Config JSON local

━━━━━━━━━━━━━━━━━━━━━
👨‍💻 **Criado por:** Edivaldo Silva
📱 **Contato:** @Edkd1
🔖 **Versão:** 4.0 (773H)
━━━━━━━━━━━━━━━━━━━━━""",
                parse_mode='md',
                buttons=voltar_button()
            )

        # ── Noop ──
        elif data == "noop":
            await event.answer()

        else:
            await event.answer("⚠️ Ação não reconhecida.")

        try:
            await event.answer()
        except:
            pass

    except Exception as e:
        log(f"❌ Callback error: {e}")
        try:
            await event.answer("❌ Erro interno.")
        except:
            pass


# ══════════════════════════════════════════════
# 💬  HANDLER: TEXTO LIVRE (PRIVADO)
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(func=lambda e: e.is_private and not e.text.startswith('/')))
async def text_handler(event):
    chat_id = event.chat_id
    texto = event.text.strip()

    action = pending_action.get(chat_id)

    # ── Aguardando CPF ──
    if action == "aguardando_cpf":
        del pending_action[chat_id]
        import re
        cpf = re.sub(r'[.\-/\s]', '', texto)

        if not cpf.isdigit() or len(cpf) != 11:
            await event.reply(
                "❌ **CPF inválido.**\n\nEnvie 11 dígitos numéricos.\nExemplo: `12345678900`",
                parse_mode='md',
                buttons=voltar_button()
            )
            return

        await event.reply("🔍 **Consultando...**", parse_mode='md')
        resultado = consultar_cpf(cpf)
        await event.reply(resultado, parse_mode='md', buttons=voltar_button())

    # ── Aguardando ID do grupo ──
    elif action == "aguardando_grupo_id":
        del pending_action[chat_id]
        import re
        grupo_id = re.sub(r'[^\d\-]', '', texto)

        if not grupo_id or not grupo_id.lstrip('-').isdigit():
            await event.reply(
                "❌ **ID inválido.**\n\nEnvie o ID numérico do grupo.\nExemplo: `-1001234567890`",
                parse_mode='md',
                buttons=voltar_button()
            )
            return

        # Tenta obter nome do grupo
        nome_grupo = "Grupo"
        try:
            entity = await user_client.get_entity(int(grupo_id))
            nome_grupo = getattr(entity, 'title', None) or getattr(entity, 'first_name', None) or "Grupo"
        except Exception:
            pass

        config = carregar_config()
        config["grupos"][grupo_id] = {
            "nome": nome_grupo,
            "adicionado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "resposta_padrao": ""
        }
        salvar_config(config)
        log(f"➕ Grupo adicionado: {nome_grupo} ({grupo_id})")

        await event.reply(
            f"✅ **Grupo adicionado com sucesso!**\n\n"
            f"📍 Nome: **{nome_grupo}**\n"
            f"🔢 ID: `{grupo_id}`\n\n"
            f"_Agora quando alguém te citar nesse grupo, o bot responderá automaticamente._",
            parse_mode='md',
            buttons=[
                [Button.inline("💬 Definir Resposta Padrão", f"setresp_{grupo_id}".encode())],
                [Button.inline("🔙 Menu Principal", b"cmd_menu")]
            ]
        )

    # ── Aguardando resposta padrão ──
    elif action and action.startswith("aguardando_resposta_"):
        gid = action.replace("aguardando_resposta_", "")
        del pending_action[chat_id]

        config = carregar_config()
        if gid in config.get("grupos", {}):
            if texto.lower() == "limpar":
                config["grupos"][gid]["resposta_padrao"] = ""
                salvar_config(config)
                await event.reply(
                    "✅ **Resposta padrão removida!**\n\n_O bot usará a resposta genérica._",
                    parse_mode='md',
                    buttons=voltar_button()
                )
            else:
                config["grupos"][gid]["resposta_padrao"] = texto
                salvar_config(config)
                await event.reply(
                    f"✅ **Resposta padrão definida!**\n\n"
                    f"📍 Grupo: `{gid}`\n"
                    f"💬 Resposta:\n_{texto}_",
                    parse_mode='md',
                    buttons=voltar_button()
                )
        else:
            await event.reply("❌ Grupo não encontrado na config.", buttons=voltar_button())

    # ── Sem ação pendente ──
    else:
        # Tenta interpretar como CPF direto
        import re
        cpf = re.sub(r'[.\-/\s]', '', texto)
        if cpf.isdigit() and len(cpf) == 11:
            await event.reply("🔍 **Consultando CPF...**", parse_mode='md')
            resultado = consultar_cpf(cpf)
            await event.reply(resultado, parse_mode='md', buttons=voltar_button())
        else:
            await event.reply(
                "💡 Use o menu para navegar ou envie um CPF para consultar.\n\n"
                "Comandos: /start | /menu | /cpf 12345678900",
                parse_mode='md',
                buttons=menu_principal_buttons(event.sender_id)
            )


# ══════════════════════════════════════════════
# 📡  HANDLER: MENSAGENS EM GRUPOS (USER CLIENT)
# ══════════════════════════════════════════════

@user_client.on(events.NewMessage(func=lambda e: e.is_group or e.is_channel))
async def grupo_handler(event):
    """Detecta menções ao dono em grupos configurados."""
    try:
        await processar_mencao_grupo(event)
    except Exception as e:
        log(f"⚠️ Erro no handler de grupo: {e}")


# ══════════════════════════════════════════════
# 🆔  COMANDO /id EM GRUPOS
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(pattern='/id'))
async def cmd_id(event):
    """Retorna o ID do chat atual."""
    await event.reply(
        f"🔢 **ID deste chat:** `{event.chat_id}`\n\n"
        f"_Use este ID para configurar o grupo no bot._",
        parse_mode='md'
    )


# ══════════════════════════════════════════════
# 🔍  COMANDO /cpf DIRETO
# ══════════════════════════════════════════════

@bot.on(events.NewMessage(pattern=r'/cpf\s+(.+)'))
async def cmd_cpf_direto(event):
    """Consulta CPF diretamente via comando."""
    import re
    texto = event.pattern_match.group(1).strip()
    cpf = re.sub(r'[.\-/\s]', '', texto)

    if not cpf.isdigit() or len(cpf) != 11:
        await event.reply(
            "❌ **CPF inválido.**\nUse: `/cpf 12345678900`",
            parse_mode='md'
        )
        return

    await event.reply("🔍 **Consultando...**", parse_mode='md')
    resultado = consultar_cpf(cpf)
    await event.reply(resultado, parse_mode='md', buttons=voltar_button())


# ══════════════════════════════════════════════
# 🚀  MAIN
# ══════════════════════════════════════════════

async def main():
    await user_client.start(PHONE)
    await bot.start(bot_token=BOT_TOKEN)

    log("🚀 Bot Interação v4.0 iniciado!")
    log("👨‍💻 Créditos: Edivaldo Silva @Edkd1")

    config = carregar_config()
    total_grupos = len(config.get("grupos", {}))
    auto = "Ativo" if config.get("respostas_auto", True) else "Desativado"
    log(f"📡 Grupos configurados: {total_grupos}")
    log(f"🔄 Auto-resposta: {auto}")

    await notificar(
        f"🚀 **Bot Interação v4.0 iniciado!**\n\n"
        f"📡 Grupos: **{total_grupos}**\n"
        f"🔄 Auto-resposta: **{auto}**\n\n"
        f"_Use /start para acessar o menu._"
    )

    print("✅ Bot ativo! Use /start, /cpf ou /id")
    await bot.run_until_disconnected()


if __name__ == "__main__":
    try:
        bot.loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n👋 Bot finalizado com segurança!")
        log("Bot encerrado pelo usuário")
