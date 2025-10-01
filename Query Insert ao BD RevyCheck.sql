use revycheck;

INSERT INTO devices (
    name, type, has_embedded_screen, has_embedded_keyboard,
    has_ethernet, eth_interface, has_speaker, has_headphone_jack, has_microphone
) VALUES (
    'Optiplex 3060', 'CPU',
    FALSE, FALSE, TRUE, 'enp1s0', TRUE, TRUE, TRUE
);

SET @dev_id = LAST_INSERT_ID();

INSERT INTO device_usb_ports (device_id, bus, port, label) VALUES
(@dev_id, 'Bus 001.Port 001', 'Port 001:', 'USB-A Frontal 2'),
(@dev_id, 'Bus 001.Port 001', 'Port 002:', 'USB-A Frontal 1'),
(@dev_id, 'Bus 001.Port 001', 'Port 007:', 'USB-A 2.0 Traseiro 1'),
(@dev_id, 'Bus 001.Port 001', 'Port 008:', 'USB-A 2.0 Traseiro 2'),
(@dev_id, 'Bus 001.Port 001', 'Port 003:', 'USB-A 3.0 Traseiro 1'),
(@dev_id, 'Bus 001.Port 001', 'Port 004:', 'USB-A 3.0 Traseiro 2');

INSERT INTO device_video_ports (device_id, label, entry) VALUES
(@dev_id, 'HDMI', 'card0-HDMI-A-1'),
(@dev_id, 'DisplayPort ', 'card0-DP-1');
