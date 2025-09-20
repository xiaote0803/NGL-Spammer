# NGL-Spammer

## Support

Join our Discord server for support and updates: [Discord Link](https://discord.gg/ZBXepTXj)

A Python tool to spam messages to NGL.link using proxies.

## Features

- Multi-threaded sending with proxy
- Rate limit bypass
- User agent rotation

## Requirements

- Python 3.6+
- `requests` and `urllib3` libraries

## Installation

```bash
pip install requests urllib3
```

## Configuration

- **`message.txt`**: Contains messages to send, one message per line
- **`proxy.txt`**: Contains proxy servers in `ip:port` format, one proxy per line  

## Proxy Collection

You can use [Proxy-Scraper-And-Checker](https://github.com/iamthebestm85/Proxy-Scraper-And-Checker-) to collect fresh proxies for `proxy.txt`.

## Usage

```bash
python main.py
```

## Disclaimer

Use responsibly. Sending unsolicited messages may violate terms of service.
