


sudo systemctl edit getty@tty1
    [Service]
        ExecStart=
        ExecStart=-/sbin/agetty --autologin vistoria --noclear %I - ${TERM}

sudo systemctl daemon-reload
sudo systemctl restart getty@tty1




