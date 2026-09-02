# -*- coding: utf-8 -*-
"""URL da API embutida no build onefile.

O PyInstaller NAO herda variavel de ambiente do momento do build: o
`os.environ` do executavel e' o da maquina onde ele roda, nao o do
`pyinstaller` que o gerou. Entao, para fixar o endereco da API dentro do
.exe, este hook roda no boot do binario -- antes do app -- e define a
variavel que o `src/config.py` le.

`setdefault`, e nao atribuicao: uma variavel de ambiente real definida na
bancada continua vencendo (precedencia documentada em config.py). Mas o
arquivo `revycheck.env` ao lado do .exe NAO vence mais este valor: por ser
embutido como variavel, ele fica acima do arquivo na precedencia -- que e'
exatamente o que se quer quando o .exe mora numa pasta de acesso amplo,
onde um `revycheck.env` plantado redirecionaria o agente para outra API.

Para re-apontar um build: edite a URL abaixo e rode `pyinstaller main.spec`.
"""

import os

os.environ.setdefault("REVYCHECK_API_URL", "http://revy.selbetti.com.br:8000/revy-check")
