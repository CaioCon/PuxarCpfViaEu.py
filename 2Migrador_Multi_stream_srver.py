#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import threading
import os
import time
import sys
import random
from datetime import datetime
from colorama import Fore, init

# Caminhos fixos
HOSTS_FILE = "/sdcard/server/hosts.txt"
SAVE_FILE = "/sdcard/hits/7773H_souiptv_migrado.txt"
URLS_FILE = "/sdcard/hits/novas_urls.txt"

hits = 0
fails = 0
lock = threading.Lock()
primeira_info_salva = False


# ----------------------------------------------------------------------
# USER-AGENTS ROTATIVOS
# ----------------------------------------------------------------------
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edg/120.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2) AppleWebKit/605.1.15 Version/16.3 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 SamsungBrowser/22.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Brave/1.60",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) OPR/105.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (compatible; YandexBrowser/23.9)"
]

def contar_linhas_hosts():
    if not os.path.exists(HOSTS_FILE):
        return 0
    with open(HOSTS_FILE, "r", encoding="utf-8") as f:
        return sum(1 for l in f if l.strip())

os.makedirs("/sdcard/hits", exist_ok=True)

# ----------------------------------------------------------------------
# SESSION NOVA (SEMPRE LIMPA)
# ----------------------------------------------------------------------
def nova_session():
    s = requests.Session()
    s.headers.update({"User-Agent": random.choice(USER_AGENTS)})
    return s

# ----------------------------------------------------------------------
# FUNÇÕES BASE
# ----------------------------------------------------------------------
def salvar_resultado(texto):
    try:
        with lock:
            with open(SAVE_FILE, "a", encoding="utf-8") as arq:
                arq.write(texto + "\n")
                arq.flush()
                try:
                    os.fsync(arq.fileno())
                except Exception:
                    pass
    except Exception as e:
        print(Fore.RED + f"Erro ao salvar resultado: {e}")

# ----------------------------------------------------------------------
# VALIDA SE DADOS ESTÃO COMPLETOS
# ----------------------------------------------------------------------
def dados_completos(userinfo, criado, expira):
    campos = [
        userinfo.get("username"),
        userinfo.get("password"),
        criado,
        expira,
        userinfo.get("max_connections"),
        userinfo.get("active_cons")
    ]
    for c in campos:
        if c is None or str(c).strip() == "" or str(c) == "N/A":
            return False
    return True

# ----------------------------------------------------------------------
# SALVA BLOCO COMPLETO NO ARQUIVO novas_urls.txt (FORMATO LINEAR)
# ----------------------------------------------------------------------
def salvar_estrutura_completa(username, password, criado, expira,
                              userinfo, serverinfo, server,
                              url_server, live, vod, series, m3u_link):
    global primeira_info_salva
    if primeira_info_salva:
        return

    with lock:
        if primeira_info_salva:
            return

        def safe(v): return str(v) if v is not None else "N/A"

        texto = f"""
🟢STATUS: ATIVO
👤USUÁRIO: {username}
🔑SENHA: {password}
📅CRIADO: {criado}
⏰EXPIRA: {expira}
🔗CONEXÕES MAX: {safe(userinfo.get('max_connections'))}
📡CONEXÕES ATIVAS: {safe(userinfo.get('active_cons'))}
📺CANAIS: {live}
🎬FILMES: {vod}
📺SÉRIES: {series}
🌍TIMEZONE: {safe(serverinfo.get('timezone'))}
🕒HORA ATUAL: {safe(serverinfo.get('time_now'))}
🌐HOST: {server}
🔎URL: {url_server}
🔗M3U: {m3u_link}
▬▬▬ஜ۩𝑬𝒅𝒊𝒗𝒂𝒍𝒅𝒐۩ஜ▬▬▬
"""
        try:
            with open(URLS_FILE, "w", encoding="utf-8") as f:
                f.write(texto)
                f.flush()
                try:
                    os.fsync(f.fileno())
                except Exception:
                    pass
            primeira_info_salva = True
        except Exception as e:
            print(Fore.RED + f"Erro ao salvar estrutura completa: {e}")

# ----------------------------------------------------------------------
# SALVA URL NUMERADA SEM DUPLICAR
# ----------------------------------------------------------------------
def salvar_url_estrutura(url_server):
    if not url_server or url_server == "N/A":
        return

    url_server = url_server.strip()

    with lock:
        if not os.path.exists(URLS_FILE):
            return
        try:
            with open(URLS_FILE, "r", encoding="utf-8") as f:
                linhas = [l.strip() for l in f if l.strip()]
        except Exception:
            return

        for l in linhas:
            if url_server in l:
                return

        num = 1
        for l in linhas:
            if l.startswith("🔎URL"):
                num += 1

        try:
            with open(URLS_FILE, "a", encoding="utf-8") as f:
                f.write(f"🔎URL {num}: {url_server}\n")
                f.flush()
                try:
                    os.fsync(f.fileno())
                except Exception:
                    pass
        except Exception:
            pass

# ----------------------------------------------------------------------
def salvar_novo_host(url_server):
    if not url_server or url_server == "N/A":
        return

    url_server = url_server.strip().lower()
    base = url_server.split(":", 1)[0] if ":" in url_server else url_server

    with lock:
        if not os.path.exists(HOSTS_FILE):
            try:
                os.makedirs(os.path.dirname(HOSTS_FILE), exist_ok=True)
            except Exception:
                pass
            with open(HOSTS_FILE, "a", encoding="utf-8") as f:
                f.write(url_server + "\n")
            return

        try:
            with open(HOSTS_FILE, "r", encoding="utf-8") as f:
                hosts = [h.strip().lower() for h in f if h.strip()]
        except Exception:
            hosts = []

        for h in hosts:
            if h.split(":", 1)[0] == base:
                return

        with open(HOSTS_FILE, "a", encoding="utf-8") as f:
            f.write(url_server + "\n")

# ----------------------------------------------------------------------
def carregar_hosts():
    if not os.path.exists(HOSTS_FILE):
        print(Fore.RED + "ERRO: Arquivo hosts não encontrado!")
        return []

    with open(HOSTS_FILE, "r", encoding="utf-8") as f:
        hosts = list(dict.fromkeys([h.strip() for h in f if h.strip()]))
    print(Fore.GREEN + f"Servidores carregados: {len(hosts)}")
    return hosts

# ----------------------------------------------------------------------
def formatar_data(ts):
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return "N/A"

# ----------------------------------------------------------------------
def contar_conteudo(base_url, user, pwd):
    def req(action):
        s = nova_session()
        try:
            r = s.get(
                f"{base_url}?username={user}&password={pwd}&action={action}",
                timeout=7
            )
            return len(r.json())
        except Exception:
            return 0
        finally:
            s.close()

    return req("get_live_streams"), req("get_vod_streams"), req("get_series")

# ----------------------------------------------------------------------
# ✅ NOVA FUNÇÃO: CONVERTER URL PARA player_api.php
# ----------------------------------------------------------------------
def converter_para_player_api(url_original):
    """
    Converte qualquer formato de URL IPTV para o formato player_api.php.
    Suporta: get.php, m3u direto, .m3u8, .ts, player_api.php
    Retorna: (base_url_api, username, password) ou (None, None, None)
    """
    try:
        url_original = url_original.strip()

        # Remover protocolo para normalizar
        url_limpa = url_original.replace("http://", "").replace("https://", "")
        protocolo = "https://" if "https://" in url_original else "http://"

        # Caso 1: Já é player_api.php
        if "player_api.php" in url_original:
            partes = url_original.split("player_api.php")[0]
            base = partes.rstrip("/")
            # Extrair user/pass dos parâmetros
            if "username=" in url_original and "password=" in url_original:
                params = url_original.split("?")[1] if "?" in url_original else ""
                user = ""
                pwd = ""
                for p in params.split("&"):
                    if p.startswith("username="):
                        user = p.split("=", 1)[1]
                    elif p.startswith("password="):
                        pwd = p.split("=", 1)[1]
                return f"{base}/player_api.php", user, pwd
            return None, None, None

        # Caso 2: get.php (m3u)
        if "get.php" in url_original:
            partes = url_original.split("get.php")[0]
            base = partes.rstrip("/")
            if "username=" in url_original and "password=" in url_original:
                params = url_original.split("?")[1] if "?" in url_original else ""
                user = ""
                pwd = ""
                for p in params.split("&"):
                    if p.startswith("username="):
                        user = p.split("=", 1)[1]
                    elif p.startswith("password="):
                        pwd = p.split("=", 1)[1]
                return f"{base}/player_api.php", user, pwd
            return None, None, None

        # Caso 3: URL direta de stream /live/user/pass/id.ts ou .m3u8
        if "/live/" in url_original or "/movie/" in url_original or "/series/" in url_original:
            # Formato: http://host:port/live/user/pass/stream_id.ts
            segmentos = url_limpa.split("/")
            if len(segmentos) >= 4:
                host_port = segmentos[0]
                # user e pass são os segmentos após live/movie/series
                tipo_idx = -1
                for i, seg in enumerate(segmentos):
                    if seg in ("live", "movie", "series"):
                        tipo_idx = i
                        break

                if tipo_idx >= 0 and len(segmentos) > tipo_idx + 2:
                    user = segmentos[tipo_idx + 1]
                    pwd = segmentos[tipo_idx + 2]
                    base = f"{protocolo}{host_port}"
                    return f"{base}/player_api.php", user, pwd
            return None, None, None

        # Caso 4: M3U link direto com credenciais na URL
        if ".m3u" in url_original and "username=" in url_original:
            partes = url_original.split("?")[0]
            base = partes.rsplit("/", 1)[0] if "/" in partes else partes
            params = url_original.split("?")[1] if "?" in url_original else ""
            user = ""
            pwd = ""
            for p in params.split("&"):
                if p.startswith("username="):
                    user = p.split("=", 1)[1]
                elif p.startswith("password="):
                    pwd = p.split("=", 1)[1]
            if user and pwd:
                return f"{base}/player_api.php", user, pwd

        return None, None, None

    except Exception:
        return None, None, None

# ----------------------------------------------------------------------
# ✅ FUNÇÃO CORRIGIDA: OBTER STREAM BASE URL (APENAS servidor:porta)
# ----------------------------------------------------------------------
def obter_stream_base(server, username, password):
    """
    Obtém a URL base do stream (apenas http://servidor:porta).
    1. Autentica via player_api.php
    2. Obtém lista de canais (get_live_streams)
    3. Escolhe um stream válido
    4. Faz requisição HTTP para forçar redirecionamento
    5. Captura URL final e extrai APENAS http://servidor:porta
    Retorna a URL base (http://ip:porta) ou None em caso de falha.
    """
    s = nova_session()
    try:
        server_clean = server.replace("http://", "").replace("https://", "")
        base_url = f"http://{server_clean}/player_api.php"

        # 1. Obter lista de canais ao vivo
        streams_url = f"{base_url}?username={username}&password={password}&action=get_live_streams"
        try:
            r = s.get(streams_url, timeout=7)
            streams = r.json()
        except Exception:
            return None

        if not streams or not isinstance(streams, list):
            return None

        # 2. Escolher um stream válido (tentar os primeiros 5)
        formatos = ["ts", "m3u8"]

        for stream in streams[:5]:
            stream_id = stream.get("stream_id")
            if not stream_id:
                continue

            for fmt in formatos:
                # 3. Montar URL do stream
                stream_url = f"http://{server_clean}/live/{username}/{password}/{stream_id}.{fmt}"

                try:
                    # 4. Fazer requisição para forçar redirecionamento
                    r2 = s.get(stream_url, timeout=6, stream=True, allow_redirects=True)

                    # 5. Capturar URL final (após redirecionamentos)
                    url_final = r2.url

                    # Fechar a conexão imediatamente
                    r2.close()

                    # 6. EXTRAIR APENAS http://servidor:porta
                    #    De: http://208.115.225.194:80/auth/W3_lRv_Zbat...
                    #    Para: http://208.115.225.194:80
                    try:
                        from urllib.parse import urlparse
                        parsed = urlparse(url_final)
                        if parsed.scheme and parsed.hostname:
                            if parsed.port:
                                stream_base_url = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}"
                            else:
                                stream_base_url = f"{parsed.scheme}://{parsed.hostname}"
                            return stream_base_url
                    except Exception:
                        # Fallback manual
                        url_sem_proto = url_final.split("://", 1)
                        if len(url_sem_proto) == 2:
                            proto = url_sem_proto[0]
                            resto = url_sem_proto[1]
                            # Pegar tudo antes do primeiro /
                            servidor_porta = resto.split("/", 1)[0]
                            return f"{proto}://{servidor_porta}"

                except Exception:
                    continue

        return None

    except Exception:
        return None
    finally:
        s.close()

# ----------------------------------------------------------------------
# ✅ FUNÇÃO CORRIGIDA: SALVA URL BASE NUMERADA SEM DUPLICAR
# ----------------------------------------------------------------------
def salvar_url_base_estrutura(stream_base):
    """
    Salva a URL base do stream (http://servidor:porta) no arquivo novas_urls.txt
    com numeração sequencial no formato:
    🔰 URL BASE 1: http://208.115.225.194:80
    Evita duplicatas verificando se a URL já existe no arquivo.
    """
    if not stream_base or stream_base == "N/A":
        return

    stream_base = stream_base.strip()

    with lock:
        if not os.path.exists(URLS_FILE):
            return

        try:
            with open(URLS_FILE, "r", encoding="utf-8") as f:
                linhas = [l.strip() for l in f if l.strip()]
        except Exception:
            return

        # Verificar duplicata
        for l in linhas:
            if stream_base in l:
                return

        # Contar URLs base existentes para numerar
        num = 1
        for l in linhas:
            if l.startswith("🔰 URL BASE"):
                num += 1

        try:
            with open(URLS_FILE, "a", encoding="utf-8") as f:
                f.write(f"🔰URL BASE BD {num}: {stream_base}\n")
                f.flush()
                try:
                    os.fsync(f.fileno())
                except Exception:
                    pass
            print(Fore.GREEN + f"  🔰 URL BASE {num} salva em: {URLS_FILE}")
        except Exception:
            pass

# ----------------------------------------------------------------------
# TESTE PRINCIPAL
# ----------------------------------------------------------------------
def testar_servidor(server, username, password):
    global hits, fails

    server = server.replace("http://", "").replace("https://", "")
    base_url = f"http://{server}/player_api.php"
    auth_url = f"{base_url}?username={username}&password={password}"

    total_hosts = contar_linhas_hosts()
    print(Fore.YELLOW + "▬▬▬ஜ۩𝑬𝒅𝒊𝒗𝒂𝒍𝒅𝒐۩ஜ▬▬▬")
    print(Fore.YELLOW + f" MIGRAÇÃO EM: {server}")
    print(Fore.MAGENTA + f" USER/PASS: {username}:{password}")
    print(Fore.GREEN + f" HITS: {hits} " + Fore.RED + f"OFF: {fails}")
    print(Fore.WHITE + f" TOTAL DE LINHAS HOSTS: {total_hosts}\n")

    s = nova_session()
    try:
        r = s.get(auth_url, timeout=8)
        data = r.json()
    except Exception:
        with lock:
            fails += 1
        return
    finally:
        s.close()

    if "user_info" not in data or data["user_info"].get("auth") != 1:
        with lock:
            fails += 1
        return

    with lock:
        hits += 1

    userinfo = data["user_info"]
    serverinfo = data.get("server_info", {})
    criado = formatar_data(userinfo.get("created_at", 0))
    expira = formatar_data(userinfo.get("exp_date", 0))
    live, vod, series = contar_conteudo(base_url, username, password)
    url_server = serverinfo.get("url", "N/A")

    salvar_novo_host(url_server)

    def safe(v): return str(v) if v is not None else "N/A"

    m3u_link = f"http://{server}/get.php?username={safe(userinfo.get('username'))}&password={safe(userinfo.get('password'))}&type=m3u"

    # 🔥 NOVA LÓGICA PARA novas_urls.txt
    if dados_completos(userinfo, criado, expira):
        salvar_estrutura_completa(
            username, password, criado, expira,
            userinfo, serverinfo, server,
            url_server, live, vod, series, m3u_link
        )
        salvar_url_estrutura(url_server)

    # ✅ Obter stream base URL (apenas servidor:porta)
    print(Fore.YELLOW + "  🔍 Obtendo URL base do stream (servidor:porta)...")
    stream_base = obter_stream_base(server, username, password)
    if stream_base:
        print(Fore.GREEN + f"  🔰 URL BASE: {stream_base}")
        salvar_url_base_estrutura(stream_base)
    else:
        print(Fore.RED + "  ⚠️ Não foi possível obter a URL base do stream")

    # ----------------- CONSOLE ORIGINAL -----------------
    print(Fore.CYAN + "▬▬▬▬▬ஜ۩ INFORMAÇÕES DO SERVIDOR ۩ஜ▬▬▬▬▬")
    print(Fore.GREEN + f"🟢 Status: {safe(userinfo.get('status')).upper()}")
    print(Fore.WHITE + "┌─────────────────────────────────────────────┐")
    print(Fore.YELLOW + f"│ 👤 Usuário: {safe(userinfo.get('username')):<27} │")
    print(Fore.YELLOW + f"│ 🔑 Senha: {safe(userinfo.get('password')):<29} │")
    print(Fore.CYAN + f"│ 📅 Criação: {criado:<25} │")
    print(Fore.CYAN + f"│ ⏰ Expiração: {expira:<23} │")
    print(Fore.GREEN + f"│ 🔗 Conexões Max: {safe(userinfo.get('max_connections')):<19} │")
    print(Fore.RED + f"│ 📡 Conexões Ativas: {safe(userinfo.get('active_cons')):<15} │")
    print(Fore.WHITE + "├─────────────────────────────────────────────┤")
    print(Fore.MAGENTA + f"│ 🌐 Host: {server:<31} │")
    print(Fore.YELLOW + f"│ 🔎 URL: {safe(url_server):<32} │")
    print(Fore.BLUE + f"│ 🌍 Timezone: {safe(serverinfo.get('timezone')):<25} │")
    print(Fore.BLUE + f"│ 🕒 Hora Atual: {safe(serverinfo.get('time_now')):<23} │")
    print(Fore.CYAN + f"│ 🔒 Porta HTTPS: {safe(serverinfo.get('https_port')):<21} │")
    print(Fore.CYAN + f"│ 📺 Porta RTMP: {safe(serverinfo.get('rtmp_port')):<22} │")
    print(Fore.GREEN + f"│ 🎯 Protocolo: {safe(serverinfo.get('server_protocol')):<23} │")
    print(Fore.YELLOW + f"│ 🎬 Formato: {safe(serverinfo.get('allowed_output_formats')):<27} │")
    print(Fore.WHITE + "├─────────────────────────────────────────────┤")
    print(Fore.GREEN + f"│ 📺 Canais ao Vivo: {live:<19} │")
    print(Fore.BLUE + f"│ 🎬 Filmes (VOD): {vod:<21} │")
    print(Fore.MAGENTA + f"│ 📺 Séries: {series:<27} │")
    print(Fore.WHITE + "└─────────────────────────────────────────────┘")

    # ✅ Exibir stream base no console
    if stream_base:
        print(Fore.GREEN + f"│ 🔗 URL Base: {stream_base}")

    print(Fore.CYAN + "\n📋 LINK M3U:")
    print(Fore.WHITE + f"🔗 {m3u_link}")

    sys.stdout.flush()

    # Texto para salvar no arquivo principal (formato original preservado)
    texto_resultado = f"""
🟢STATUS: ATIVO
👤USUÁRIO: {username}
🔑SENHA: {password}
📅CRIADO: {criado}
⏰EXPIRA: {expira}
🔗CONEXÕES MAX: {safe(userinfo.get('max_connections'))}
📡CONEXÕES ATIVAS: {safe(userinfo.get('active_cons'))}
📺CANAIS: {live}
🎬FILMES: {vod}
📺SÉRIES: {series}
🌍TIMEZONE: {safe(serverinfo.get('timezone'))}
🕒HORA ATUAL: {safe(serverinfo.get('time_now'))}
🌐HOST: {server}
🔎URL: {url_server}
🔗M3U: {m3u_link}"""

    # ✅ Adicionar stream base ao texto de resultado
    if stream_base:
        texto_resultado += f"\n🔰 URL BASE: {stream_base}"

    texto_resultado += "\n▬▬▬ஜ۩𝑬𝒅𝒊𝒗𝒂𝒍𝒅𝒐۩ஜ▬▬▬\n"

    # Salvar no arquivo principal (original)
    salvar_resultado(texto_resultado)

# ----------------------------------------------------------------------
# WORKER
# ----------------------------------------------------------------------
def worker(lista, user, pwd):
    for srv in lista:
        testar_servidor(srv, user, pwd)

# ----------------------------------------------------------------------
# INICIAR
# ----------------------------------------------------------------------
def iniciar():
    try:
        os.system("clear")
    except Exception:
        pass

    print(Fore.CYAN + "Digite user:pass")
    cred = input("➤ ").strip()
    if ":" not in cred:
        print(Fore.RED + "Formato inválido.")
        return

    user, pwd = cred.split(":", 1)

    hosts = carregar_hosts()
    if not hosts:
        return

    partes = 10
    tamanho = max(1, len(hosts) // partes)
    threads = []
    for i in range(partes):
        bloco = hosts[i * tamanho:(i + 1) * tamanho]
        if bloco:
            t = threading.Thread(target=worker, args=(bloco, user, pwd))
            t.start()
            threads.append(t)

    resto = hosts[partes * tamanho:]
    if resto:
        t = threading.Thread(target=worker, args=(resto, user, pwd))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print(Fore.GREEN + "\nMIGRAÇÃO FINALIZADA!")
    print(Fore.YELLOW + f"TOTAL HITS: {hits}")
    print(Fore.RED + f"TOTAL OFF: {fails}")
    print(Fore.CYAN + f"Resultados salvos em: {SAVE_FILE}")
    print(Fore.CYAN + f"Estrutura + URLs salvas em: {URLS_FILE}")

if __name__ == "__main__":
    iniciar()
