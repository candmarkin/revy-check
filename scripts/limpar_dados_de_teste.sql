-- Remove os dados que o teste de integração dos endpoints /revy-check/* criou
-- no banco de produção em 2026-08-26.
--
-- Precisa de um usuário com DELETE: o `drack` que a API usa tem só
-- SELECT/INSERT/UPDATE em `revycheck.*`, então a limpeza não pôde ser feita
-- pela mesma credencial que criou as linhas.
--
-- São 6 linhas ao todo: 1 device de teste, 1 porta USB, 1 porta de vídeo e
-- 3 entradas de log. Os nomes foram marcados de propósito para não haver
-- dúvida sobre o que é descartável.

SELECT id, name, cpu_vendor, platform
  FROM devices
 WHERE name = 'ZZZ-TESTE-CLAUDE-APAGAR';   -- confirme que devolve só o id 107

DELETE FROM device_usb_ports
 WHERE device_id IN (SELECT id FROM (
       SELECT id FROM devices WHERE name = 'ZZZ-TESTE-CLAUDE-APAGAR') AS t);

DELETE FROM device_video_ports
 WHERE device_id IN (SELECT id FROM (
       SELECT id FROM devices WHERE name = 'ZZZ-TESTE-CLAUDE-APAGAR') AS t);

DELETE FROM devices
 WHERE name = 'ZZZ-TESTE-CLAUDE-APAGAR';

DELETE FROM logs
 WHERE device_serial = 'ZZZTESTECLAUDE';

-- Conferência: as duas contagens devem voltar a 89 devices e 180095 logs.
SELECT (SELECT COUNT(*) FROM devices) AS devices,
       (SELECT COUNT(*) FROM logs)    AS logs;
