# Correção de Detecção de Fone - Lenovo Thinkpad E14

## Problema Identificado
No Lenovo Thinkpad E14, o sistema reconhecia um fone de ouvido conectado mesmo sem estar fisicamente conectado. Isso causava:
1. Teste de fone sendo realizado sem fone conectado
2. Sistema pedindo para remover o fone mesmo quando já não estava lá
3. Teste não passava ao conectar e remover o fone

## Causa Raiz
- O driver Realtek ou o subsistema PulseAudio reportava uma porta de fone "fantasma" como conectada
- A função `headphone_connected()` apenas verificava o estado via PulseAudio, sem confirmação do usuário
- Não havia forma de resolver conflitos de detecção automática

## Solução Implementada

### Alterações em `src/alltests.py`

1. **Função `headphone_connected()` - Melhorada**
   - Tenta detectar via PulseAudio
   - Se detecta algo, pede confirmação manual ao usuário
   - Retorna `True` apenas se confirmado pelo usuário
   - Fallback: retorna `False` se não conseguir detectar

2. **Função `wait_for_headphone_connect()`** - Nova
   - Substitui o `draw_text()` por um diálogo
   - Pede explicitamente ao usuário conectar o fone
   - Retorna confirmação manual do usuário

3. **Função `wait_for_headphone_disconnect()`** - Nova
   - Substitui o `draw_text()` por um diálogo
   - Pede explicitamente ao usuário remover o fone
   - Retorna confirmação manual do usuário

### Alterações no Fluxo de Estados

#### Estado HEADPHONE_STEP
- **Antes**: `draw_text()` + espera passiva por detecção
- **Depois**: `wait_for_headphone_connect()` com confirmação ativa do usuário

#### Estado HEADPHONE_REMOVE
- **Antes**: `draw_text()` + espera passiva por detecção
- **Depois**: `wait_for_headphone_disconnect()` com confirmação ativa do usuário

### Alterações em `src/functions/audio.py`

- Descomentou a função `headphone_connected()` original
- Adicionou tratamento robusto de exceções
- Adicionou comentário de aviso sobre limitações em ThinkPads

## Benefícios

✅ **Confiabilidade**: Confirmação manual do usuário elimina falsos positivos  
✅ **UX**: Diálogos claros em vez de telas de espera ambíguas  
✅ **Flexibilidade**: Permite ao usuário cancelar o teste se necessário  
✅ **Compatibilidade**: Funciona mesmo com detectores defeituosos  

## Testes Recomendados

1. Executar teste SEM fone conectado:
   - Sistema deve pedir para conectar
   - Clique "NÃO" para pular (ou "SIM" se conectou)

2. Executar teste COM fone conectado:
   - Sistema pede para conectar
   - Clique "SIM" após conectar
   - Toque de som nos dois canais
   - Sistema pede para remover
   - Clique "SIM" após remover
   - Passe para próximo teste

3. Conectar/Remover durante o teste:
   - Deve funcionar normalmente
   - Diálogos permitem retomar a qualquer momento

## Notas de Implementação

- Usa `ask_yes_no()` existente em alltests.py
- Mantém integração com log de dados (`add_log()`)
- Estado pode retornar a `SPEAKER_STEP` se usuário cancelar
- Compatível com ambos PulseAudio e ALSA
