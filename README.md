# WatchDog
This project was created by a group of vampires at Voorivex Academy to improve bug hunting progress :)

## Installation
 1. Move `config.py.example` to `config.py` using this command.
``` bash
 mv config.py.example config.py
 ```
 2. Change `discord_webhook`, `database`, `telegram_token` and `telegram_chatid` variable to your own values.
 3. Run the program using this command.
 
## Examples

Help:
```bash
 python3 watch_dog.py -h
 ```

Monitoring all platforms and sending changes to the Discord server:
```bash
 python3 watch_dog.py -d --token "<discord_webhook>"
 ```
 
Monitoring all platforms and sending changes to the Telegram channel:
```bash
 python3 watch_dog.py -t --token "<telegram bot token>" -cid "<chatid>"
 ```
 
 Monitoring single or multiple platforms:
 ```bash
 python3 watch_dog.py -p "hackerone" # Single platform
 python3 watch_dog.py -p "hackerone,bugcrowd" # Multiple platform
 ```
 
 Change database name:
```bash
 python3 watch_dog.py --database "<Your database name>"
 ```
 
  Change MongoDB connection:
```bash
 python3 watch_dog.py --mongo "mongodb://localhost:27017" # Default: mongodb://mongo:27017/
 ```
