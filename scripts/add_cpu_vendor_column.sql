-- Script SQL para adicionar a coluna cpu_vendor na tabela devices
--
-- Motivo: o DMI nao separa as variantes Intel e AMD do mesmo modelo comercial.
-- Um ThinkPad T14 Gen 1 se identifica como "ThinkPad T14 Gen 1" nas duas, mas a
-- topologia USB (numeros de bus, BDF do controlador xHCI) e os connectors DRM
-- sao diferentes, entao cada variante precisa do seu proprio cadastro de portas.
--
-- Linhas antigas ficam com cpu_vendor NULL e seguem sendo usadas como fallback
-- ate' serem recadastradas -- veja _find_device em src/functions/device_info.py.

-- Adicionar coluna cpu_vendor
ALTER TABLE devices
ADD COLUMN cpu_vendor VARCHAR(16) NULL COMMENT 'Fabricante da CPU: intel ou amd' AFTER name;

-- O par (name, cpu_vendor) passa a ser a chave logica do modelo
CREATE INDEX idx_devices_name_cpu ON devices (name, cpu_vendor);

-- Opcional: se voce sabe que um cadastro existente foi feito numa maquina Intel,
-- marque-o para que a variante AMD possa ser cadastrada em separado.
-- UPDATE devices SET cpu_vendor = 'intel' WHERE id = <id>;

-- Opcional: normaliza as entradas de video antigas removendo o prefixo 'cardN-'.
-- Nao e' obrigatorio (o codigo ja compara so' o nome do connector), mas deixa a
-- tabela consistente com o que o cadastro grava agora.
-- UPDATE device_video_ports
--    SET entry = SUBSTRING(entry, LOCATE('-', entry) + 1)
--  WHERE entry LIKE 'card%-%';

-- Verificar a coluna adicionada
DESCRIBE devices;
