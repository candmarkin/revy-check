"""Login do técnico na bancada.

O agente não carrega chave nenhuma: quem autoriza a rodar o checklist é a
credencial do próprio técnico, a mesma do Revy web. A API troca e-mail + senha
pela `key` do usuário (`POST /revy-check/login`), e o agente usa essa chave nas
chamadas seguintes, só em memória.

Isso resolve dois problemas de uma vez: o executável que fica numa pasta
pública deixa de ter segredo dentro, e o log do checklist passa a ter autor --
que importa porque o modo DEV permite aprovar teste na mão.
"""

import sys

import pygame

from src import api_client, app_state


CAMPOS = ("email", "senha")


def _desenhar(campos, ativo, aviso, cor_aviso):
    tela = app_state.SCREEN
    tela.fill((20, 24, 32))

    fonte_titulo = pygame.font.SysFont("Arial", 30, bold=True)
    fonte = pygame.font.SysFont("Arial", 22)
    fonte_dica = pygame.font.SysFont("Arial", 16)

    centro_x = app_state.WIDTH // 2
    y = app_state.HEIGHT // 3 - 80

    titulo = fonte_titulo.render("RevyCheck - identificacao do tecnico", True, (255, 255, 255))
    tela.blit(titulo, titulo.get_rect(center=(centro_x, y)))

    dica = fonte_dica.render(
        "Use o mesmo e-mail e senha do Revy. TAB troca de campo, ENTER confirma.",
        True, (150, 160, 175),
    )
    tela.blit(dica, dica.get_rect(center=(centro_x, y + 36)))

    y += 100
    largura = min(560, app_state.WIDTH - 80)
    for nome in CAMPOS:
        rotulo = fonte.render("E-mail:" if nome == "email" else "Senha:", True, (200, 210, 225))
        tela.blit(rotulo, (centro_x - largura // 2, y - 30))

        caixa = pygame.Rect(centro_x - largura // 2, y, largura, 44)
        cor_borda = (90, 170, 255) if nome == ativo else (70, 78, 92)
        pygame.draw.rect(tela, (32, 38, 50), caixa, border_radius=6)
        pygame.draw.rect(tela, cor_borda, caixa, width=2, border_radius=6)

        # A senha não aparece em tela: a bancada é um lugar público, e o
        # supervisor passa atrás do técnico o dia todo.
        conteudo = campos[nome] if nome == "email" else "*" * len(campos[nome])
        texto = fonte.render(conteudo, True, (255, 255, 255))
        tela.blit(texto, (caixa.x + 12, caixa.y + 10))

        if nome == ativo and pygame.time.get_ticks() % 1000 < 500:
            cursor_x = caixa.x + 14 + texto.get_width()
            pygame.draw.line(tela, (255, 255, 255), (cursor_x, caixa.y + 10),
                             (cursor_x, caixa.y + 34), 2)
        y += 100

    if aviso:
        for i, linha in enumerate(aviso.split("\n")[:3]):
            render = fonte_dica.render(linha, True, cor_aviso)
            tela.blit(render, render.get_rect(center=(centro_x, y + 10 + i * 24)))

    pygame.display.flip()


def _digitar(evento, campos, ativo):
    """Aplica uma tecla ao campo ativo. Devolve o campo ativo depois dela."""
    if evento.key == pygame.K_TAB:
        return CAMPOS[(CAMPOS.index(ativo) + 1) % len(CAMPOS)]
    if evento.key == pygame.K_BACKSPACE:
        campos[ativo] = campos[ativo][:-1]
        return ativo
    if evento.unicode and evento.unicode.isprintable():
        # 200 chars é folga para e-mail e senha; o limite só evita que segurar
        # uma tecla encha a memória.
        if len(campos[ativo]) < 200:
            campos[ativo] += evento.unicode
    return ativo


def tela_de_login():
    """Pede credencial até autenticar. Devolve o usuário logado.

    Só sai daqui autenticado, ou por ESC no modo DEV -- em produção não há
    saída, porque sem login não há checklist para rodar.
    """
    campos = {"email": "", "senha": ""}
    ativo = "email"
    aviso = ""
    cor_aviso = (240, 180, 90)

    while True:
        _desenhar(campos, ativo, aviso, cor_aviso)

        for evento in pygame.event.get():
            if evento.type == pygame.QUIT and app_state.MODE == "DEV":
                pygame.quit()
                sys.exit()
            if evento.type != pygame.KEYDOWN:
                continue
            if evento.key == pygame.K_ESCAPE and app_state.MODE == "DEV":
                pygame.quit()
                sys.exit()

            if evento.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if ativo == "email" and not campos["senha"]:
                    ativo = "senha"
                    continue
                if not campos["email"] or not campos["senha"]:
                    aviso, cor_aviso = "Preencha e-mail e senha.", (240, 180, 90)
                    continue

                aviso, cor_aviso = "Verificando...", (150, 200, 255)
                _desenhar(campos, ativo, aviso, cor_aviso)
                try:
                    usuario = api_client.login(campos["email"], campos["senha"])
                except api_client.CredenciaisInvalidas:
                    campos["senha"] = ""
                    ativo = "senha"
                    aviso, cor_aviso = "E-mail ou senha invalidos.", (255, 110, 110)
                except api_client.LoginBloqueado as exc:
                    campos["senha"] = ""
                    aviso, cor_aviso = str(exc), (255, 110, 110)
                except api_client.ApiError as exc:
                    # Rede fora, API fora, URL errada: mostra o motivo em vez
                    # de fingir que a senha está errada.
                    aviso, cor_aviso = f"Sem resposta da API.\n{exc}", (255, 160, 90)
                else:
                    app_state.USER = usuario
                    app_state.add_log({
                        "step": "LOGIN",
                        "time": app_state.now_iso(),
                        "result": "APROVADO",
                        "detalhe": f"{usuario['name']} ({usuario['role']})",
                    })
                    return usuario
            else:
                ativo = _digitar(evento, campos, ativo)

        app_state.CLOCK.tick(30)


def reautenticar(motivo=""):
    """Sessão recusada no meio do fluxo (chave revogada). Pede login de novo.

    Mantém o log do checklist: o equipamento já foi testado, o que falta é
    alguém autorizado para assinar o envio.
    """
    api_client.encerrar_sessao()
    app_state.USER = None
    if motivo:
        print(f"Sessao invalida: {motivo}")
    return tela_de_login()
