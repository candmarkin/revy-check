-- Script SQL para adicionar as colunas has_wifi, has_touchpad e has_camera na tabela devices

-- Adicionar coluna has_wifi
ALTER TABLE devices 
ADD COLUMN has_wifi TINYINT(1) DEFAULT 0 COMMENT 'Indica se o dispositivo possui WiFi';

-- Adicionar coluna has_touchpad
ALTER TABLE devices 
ADD COLUMN has_touchpad TINYINT(1) DEFAULT 0 COMMENT 'Indica se o dispositivo possui touchpad';

-- Adicionar coluna has_camera
ALTER TABLE devices 
ADD COLUMN has_camera TINYINT(1) DEFAULT 0 COMMENT 'Indica se o dispositivo possui câmera/webcam';

-- Verificar as colunas adicionadas
DESCRIBE devices;
