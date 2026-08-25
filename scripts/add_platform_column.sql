-- Separa os cadastros por sistema operacional.
--
-- A mesma porta fisica tem nomes diferentes em cada SO. USB:
--
--     Linux    0000:00:14.0        / 3.2
--     Windows  PCIROOT(0)#PCI(1400) / 3.2
--
-- Video, pior ainda: o nome do connector do DRM ('HDMI-A-1') e o
-- `connectorInstance` do Windows ('HDMI-0#198219') nao tem correspondencia
-- garantida nem entre maquinas do mesmo modelo.
--
-- Sem esta coluna, um equipamento cadastrado no Linux e testado no Windows
-- encontra o registro do modelo e reprova todas as portas, porque nenhuma
-- string casa. O mesmo modelo precisa de um cadastro por SO.
--
-- As linhas antigas ficam com platform = 'linux': todo cadastro existente foi
-- feito na linha Debian.

ALTER TABLE devices
    ADD COLUMN platform VARCHAR(16) NULL AFTER cpu_vendor;

UPDATE devices SET platform = 'linux' WHERE platform IS NULL OR platform = '';

-- O par (nome, cpu_vendor, platform) e' o que identifica um cadastro.
-- Descomente se quiser que o banco imponha a unicidade:
-- ALTER TABLE devices
--     ADD UNIQUE KEY uk_device_variant (name, cpu_vendor, platform);
