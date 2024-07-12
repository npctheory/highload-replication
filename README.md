## Начало работы
Создать docker-сеть:
```bash
docker network create pg_net
```
Находясь в папке highload запустить docker-compose:
```bash
docker compose up -d --build
```
## Настройка репликации
Репликация настраивается через плейбуки ansible. Ansible находится в отдельном контейнере.
```bash
docker exec -it ansible bash
```
Выполнить один из плейбуков:  

1. Контейнер pg_master становится primary. Контейнеры pg_slave и pg_asyncslave в режиме standby (async)
```bash
ansible-playbook playbooks/pg_master_is_primary.yml
```
2. Контейнер pg_slave становится primary.
```bash
ansible-playbook playbooks/pg_slave_is_primary.yml
```
