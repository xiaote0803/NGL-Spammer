import random
import time
import threading
import requests
import urllib3
from typing import List, Dict, Iterable

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

MAX_TIMEOUTS_BEFORE_DROP = 3
TIMEOUT_SLEEP = 10
REQUEST_TIMEOUT = (3, 7)
DEVICE_ID_LENGTH = 42
URL = "https://ngl.link/api/submit"

PRINT_LOCK = threading.Lock()
COUNTER_LOCK = threading.Lock()

INVALID_PROXIES: List[str] = []
USER_AGENTS: List[str] = []
MESSAGES: List[str] = []
PROXIES: List[str] = []


def print_sync(msg: str) -> None:
    with PRINT_LOCK:
        print(msg, flush=True)


def print_colored(msg_type: str, message: str) -> None:
    colors = {
        "ERROR": "\033[1;31m",
        "SUCCESS": "\033[1;32m",
        "WARN": "\033[33m",
        "ABORT": "\033[31m",
        "MISSING": "\033[31m",
        "INFO": "\033[34m"
    }
    color = colors.get(msg_type.upper(), "")
    reset = "\033[0m"
    with PRINT_LOCK:
        print(f"{color}[{msg_type.upper()}]{reset} {message}", flush=True)


def load_file_lines(filename: str) -> List[str]:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            if not lines:
                print_colored("WARN", f"Empty file: {filename}")
            return lines
    except FileNotFoundError:
        print_colored("MISSING", f"File not found: {filename}")
        return []


def build_headers(username: str, user_agents: Iterable[str]) -> Dict[str, str]:
    ua_list = list(user_agents)
    if not ua_list:
        raise ValueError("No user agents available")
    return {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Referer": f"https://ngl.link/{username}",
        "Origin": "https://ngl.link",
        "User-Agent": random.choice(ua_list),
    }


def proxy_worker(proxy: str, username: str, messages: List[str], user_agents: List[str], counter: List[int], stop_event: threading.Event) -> None:
    session = requests.Session()
    px = {"http": f"http://{proxy}", "https": f"http://{proxy}"}
    consecutive_timeouts = 0
    while not stop_event.is_set():
        headers = build_headers(username, user_agents)
        data = {
            "username": username,
            "question": random.choice(messages),
            "deviceId": "".join(random.choices("0123456789abcdef", k=DEVICE_ID_LENGTH)),
            "gameSlug": "",
            "referrer": "",
        }
        try:
            resp = session.post(URL, headers=headers, data=data, proxies=px, timeout=REQUEST_TIMEOUT)
            status = resp.status_code
            if status == 429:
                time.sleep(TIMEOUT_SLEEP)
                continue
            if 500 <= status < 600:
                continue
            if status != 200:
                print_colored("ERROR", f"{status} | drop {proxy}")
                break
            consecutive_timeouts = 0
            with COUNTER_LOCK:
                counter[0] += 1
                print_colored("SUCCESS", f"Message Total: {counter[0]}")
        except requests.exceptions.Timeout:
            consecutive_timeouts += 1
            if consecutive_timeouts >= MAX_TIMEOUTS_BEFORE_DROP:
                break
            continue
        except (requests.exceptions.ProxyError, requests.exceptions.SSLError, requests.exceptions.ConnectionError):
            with COUNTER_LOCK:
                if proxy not in INVALID_PROXIES:
                    INVALID_PROXIES.append(proxy)
            break
        except Exception as e:
            print_colored("ERROR", f"Unexpected | {proxy} | {type(e).__name__}")
            break


def send_messages(username: str, messages: List[str], proxies: List[str], user_agents: List[str]) -> None:
    counter = [0]
    stop_event = threading.Event()
    threads: List[threading.Thread] = []
    for proxy in proxies:
        if proxy in INVALID_PROXIES:
            continue
        t = threading.Thread(
            target=proxy_worker,
            args=(proxy, username, messages, user_agents, counter, stop_event),
            daemon=True,
        )
        threads.append(t)
        t.start()
    for t in threads:
        t.join()


def get_username() -> str:
    while True:
        try:
            print_colored("INFO", "Enter the target username:")
            username = input().strip()
            if not username:
                print_colored("WARN", "Username cannot be empty.")
                continue
            return username
        except KeyboardInterrupt:
            print_colored("ABORT", "Input interrupted.")
            raise


def main() -> None:
    global USER_AGENTS, MESSAGES, PROXIES
    USER_AGENTS = load_file_lines("user_agents.txt")
    MESSAGES = load_file_lines("message.txt")
    PROXIES = load_file_lines("proxy.txt")
    if not USER_AGENTS or not MESSAGES or not PROXIES:
        print_colored("ABORT", "Required files missing or empty.")
        return
    try:
        username = get_username()
    except KeyboardInterrupt:
        return
    send_messages(username, MESSAGES, PROXIES, USER_AGENTS)


if __name__ == "__main__":
    main()
