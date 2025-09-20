# NGL-Spammer

A Python tool to send anonymous messages to NGL.link using proxies.

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

Prepare these files in the same directory:

- `message.txt`: Messages to send (one per line)
- `proxy.txt`: Proxies in `ip:port` format
- `user_agents.txt`: User agent strings

## Proxy Collection

You can use [Proxy-Scraper-And-Checker](https://github.com/iamthebestm85/Proxy-Scraper-And-Checker-) to collect fresh proxies for `proxy.txt`.

## Usage

```bash
python main.py
```

Enter the target username when prompted.

## Disclaimer

Use responsibly. Sending unsolicited messages may violate terms of service.
