import random
import time
import threading
import requests
import urllib3
from typing import List, Dict, Iterable

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

PRINT_LOCK = threading.Lock()
COUNTER_LOCK = threading.Lock()
INVALID_PROXIES: List[str] = []

USER_AGENTS: List[str] = []
MESSAGES: List[str] = []
PROXIES: List[str] = []

URL = "https://ngl.link/api/submit"
DEFAULT_UA = "Mozilla/5.0"


def print_sync(msg: str) -> None:
    with PRINT_LOCK:
        print(msg, flush=True)


def load_file_lines(filename: str) -> List[str]:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            if not lines:
                print_sync(f"\033[33m[WARN]\033[0m Empty file: {filename}")
            return lines
    except FileNotFoundError:
        print_sync(f"\033[31m[MISSING]\033[0m File not found: {filename}")
        return []


def build_headers(username: str, user_agents: Iterable[str]) -> Dict[str, str]:
    ua_list = list(user_agents) or [DEFAULT_UA]
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
    max_timeouts_before_drop = 3
    while not stop_event.is_set():
        time.sleep(random.uniform(0.8, 1.5))
        headers = build_headers(username, user_agents)
        data = {
            "username": username,
            "question": random.choice(messages),
            "deviceId": "".join(random.choices("0123456789abcdef", k=42)),
            "gameSlug": "",
            "referrer": "",
        }
        try:
            resp = session.post(URL, headers=headers, data=data, proxies=px, timeout=(3, 7))
            status = resp.status_code
            if status == 429:
                time.sleep(random.uniform(5.0, 10.0))
                continue
            if 500 <= status < 600:
                time.sleep(random.uniform(1.0, 2.0))
                continue
            if status != 200:
                print_sync(f"\033[1;31m[Error]\033[0m \033[31m{status} | drop {proxy}\033[0m")
                break
            consecutive_timeouts = 0
            with COUNTER_LOCK:
                counter[0] += 1
                print_sync(f"\033[1;32m[Successful]\033[0m \033[32mMessage Total: {counter[0]}\033[0m")
        except requests.exceptions.Timeout:
            consecutive_timeouts += 1
            if consecutive_timeouts >= max_timeouts_before_drop:
                break
            time.sleep(random.uniform(1.0, 2.0))
            continue
        except (requests.exceptions.ProxyError, requests.exceptions.SSLError, requests.exceptions.ConnectionError):
            with COUNTER_LOCK:
                if proxy not in INVALID_PROXIES:
                    INVALID_PROXIES.append(proxy)
            break
        except Exception as e:
            print_sync(f"\033[1;31m[Error]\033[0m \033[31mUnexpected | {proxy} | {type(e).__name__}\033[0m")
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
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        stop_event.set()
        print_sync("\nStopping...")


def main() -> None:
    global USER_AGENTS, MESSAGES, PROXIES
    USER_AGENTS = load_file_lines("user_agents.txt")
    MESSAGES = load_file_lines("message.txt")
    PROXIES = load_file_lines("proxy.txt")
    if not MESSAGES or not PROXIES:
        print_sync("\033[31m[ABORT]\033[0m Required files missing or empty.")
        return
    username = input("\033[33mUser Name=> \033[0m").strip()
    if not username:
        print_sync("\033[31m[ABORT]\033[0m Empty username")
        return
    send_messages(username, MESSAGES, PROXIES, USER_AGENTS)


if __name__ == "__main__":
    main()
