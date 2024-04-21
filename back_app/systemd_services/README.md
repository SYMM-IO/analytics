### Setup

```
sudo ./set_services user
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
