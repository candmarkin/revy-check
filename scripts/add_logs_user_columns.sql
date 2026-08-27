-- Autoria do checklist: quem estava logado no agente quando o log foi gravado.
--
-- O agente pede login (POST /revy-check/login) e a API passa o usuario para
-- `gravar_teste_final`. Sem estas colunas o log grava como antes, sem autor, e
-- a API loga um aviso -- entao a migracao pode entrar depois do deploy, sem
-- parar bancada.
--
-- Importa porque o modo DEV do agente permite aprovar teste na mao: log sem
-- autor nao responde "quem aprovou este equipamento".
--
-- Rodar no banco do RevyCheck (o mesmo de `revycheck_connection`):
--   mysql -h <host> -u <user> -p <base> < scripts/add_logs_user_columns.sql

ALTER TABLE logs
  ADD COLUMN user_id INT NULL COMMENT 'users.id do Neon (Revy web)',
  ADD COLUMN user_name VARCHAR(120) NULL COMMENT 'nome do tecnico no login do agente';

-- Consulta de quem aprovou o que, para conferencia depois:
--
--   SELECT device_serial, user_name, MIN(time) AS inicio,
--          SUM(approved = 0) AS reprovados
--     FROM logs
--    WHERE user_name IS NOT NULL
--    GROUP BY device_serial, user_name
--    ORDER BY inicio DESC;
