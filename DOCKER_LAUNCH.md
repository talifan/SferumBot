# Docker Launch Guide

## Prerequisites
- Docker Engine must be installed with access to `/var/run/docker.sock`.
- This repository should be checked out locally with the `.env` file populated.

## Environment Variables
Create or update `.env` in the project root with your own secrets:
```
AUTH_COOKIE=<vk_remixdsid_cookie>
BOT_TOKEN=<telegram_bot_token>
TG_USER_ID=<telegram_user_id>
TG_CHAT_ID=-100<telegram_chat_id>
VK_CHAT_ID=<comma_separated_vk_chat_ids>
```
Replace placeholders with актуальными значениями. Никогда не коммитьте `.env`.

**Note:** Для супергрупп/каналов Telegram id в `.env` должен начинаться с `-100`. Значения без префикса приведут к ошибке `Bad Request: chat not found`.

## Build Image
From the project root run:
```
docker build -t sferum-bot .
```
The provided `dockerfile` installs dependencies inside a virtual environment and sets `startup.py` as the entrypoint.

## Run Container
Launch the bot in detached mode:
```
docker run --env-file .env --name sferum-bot --restart unless-stopped -d sferum-bot
```
- `--env-file` shares the Telegram and VK credentials with the container.
- `--restart unless-stopped` makes Docker respawn the bot on host reboot.

## Rebuild & Restart
After updating the code, rebuild the image and relaunch the container:
```
docker build -t sferum-bot .
docker stop sferum-bot || true
docker rm sferum-bot || true
docker run --env-file .env --name sferum-bot --restart unless-stopped -d sferum-bot
```

## Monitoring
Tail the runtime logs:
```
docker logs -f sferum-bot
```
The application also writes to `sferum.log` inside the container at `/app/sferum.log`.

## Maintenance
- Stop the bot: `docker stop sferum-bot`
- Start again: `docker start sferum-bot`
- Remove after stopping: `docker rm sferum-bot`
- Rebuild after code updates: rerun the build command and restart the container.
