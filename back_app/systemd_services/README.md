### Install Unit files

```
sudo cp *.service *.target /etc/systemd/system/

sudo sed -i 's/User=analytics_user/User=yourusername/' /etc/systemd/system/analytics*.service

sed -i 's|ANALYTICS_PATH|path to the back_app folder|g' /etc/systemd/system/analytics*.service

sudo systemctl daemon-reload
```

### Restart all services

```
sudo systemctl restart analytics.target
```

### Get info
```
sudo systemctl status analytics*
sudo systemctl status analytics*|grep active|nl
```
