import random
import time
import threading
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.93 Safari/537.36",
    # "Add More User-Agents"
]

MESSAGES = [
    "Your Message",
    # "Add More Messages"
]

PROXY_FILE = "proxy.txt"
INVALID_PROXIES = []
COUNTER_LOCK = threading.Lock()

URL = "https://ngl.link/api/submit"

def load_proxies(filename):
    with open(filename, "r") as f:
        return [line.strip() for line in f if line.strip()]

def proxy_worker(proxy, username, messages, counter, stop_event):
    session = requests.Session()
    base_headers = {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Referer": f"https://ngl.link/{username}",
        "Origin": "https://ngl.link",
    }
    px = {"http": f"http://{proxy}", "https": f"http://{proxy}"}

    min_interval = 0.9
    last_sent = 0.0
    backoff = 0.0
    max_backoff = 30.0

    consecutive_timeouts = 0
    max_timeouts_before_drop = 3

    while not stop_event.is_set():
        now = time.monotonic()
        sleep_for = (last_sent + min_interval + backoff) - now
        if sleep_for > 0:
            time.sleep(sleep_for)

        headers = dict(base_headers)
        headers["User-Agent"] = random.choice(USER_AGENTS)

        device_id = "".join(random.choices("0123456789abcdef", k=42))
        data = {
            "username": username,
            "question": random.choice(messages),
            "deviceId": device_id,
            "gameSlug": "",
            "referrer": "",
        }

        try:
            resp = session.post(
                URL,
                headers=headers,
                data=data,
                proxies=px,
                timeout=(3, 7),
            )
            status = resp.status_code
            last_sent = time.monotonic()

            if status == 429:
                backoff = min(max_backoff, max(1.0, (backoff * 2) or 1.0) + random.uniform(0.2, 0.8))
                continue
            elif 500 <= status < 600:
                backoff = min(max_backoff, max(1.0, (backoff * 1.5) or 1.0) + random.uniform(0.2, 0.8))
                continue
            elif status != 200:
                with COUNTER_LOCK:
                    if proxy not in INVALID_PROXIES:
                        INVALID_PROXIES.append(proxy)
                print(f"\033[0m\033[1;31m[Error]\033[0m \033[0;31m{status} | drop {proxy}")
                break
            else:
                backoff = 0.0
                consecutive_timeouts = 0
                with COUNTER_LOCK:
                    counter[0] += 1
                    print(f"\033[0m\033[1;32m[Successful]\033[0m \033[0;32mMessage Total: {counter[0]}")

        except requests.exceptions.Timeout:
            consecutive_timeouts += 1
            backoff = min(max_backoff, max(0.5, (backoff * 1.3) or 0.7) + random.uniform(0.1, 0.4))
            if consecutive_timeouts >= max_timeouts_before_drop:
                with COUNTER_LOCK:
                    if proxy not in INVALID_PROXIES:
                        INVALID_PROXIES.append(proxy)
                print(f"\033[0m\033[1;31m[Error]\033[0m \033[0;31mTimeout x{consecutive_timeouts} | drop {proxy}")
                break
            continue
        except (requests.exceptions.ProxyError,
                requests.exceptions.SSLError,
                requests.exceptions.ConnectionError) as e:
            with COUNTER_LOCK:
                if proxy not in INVALID_PROXIES:
                    INVALID_PROXIES.append(proxy)
            print(f"\033[0m\033[1;31m[Error]\033[0m \033[0;31mProxy fail | {proxy} | {type(e).__name__}")
            break
        except Exception as e:
            with COUNTER_LOCK:
                if proxy not in INVALID_PROXIES:
                    INVALID_PROXIES.append(proxy)
            print(f"\033[0m\033[1;31m[Error]\033[0m \033[0;31mUnexpected | {proxy} | {type(e).__name__}")
            break

def send_messages(username, messages, proxies):
    counter = [0]
    threads = []
    stop_event = threading.Event()

    for proxy in proxies:
        if proxy in INVALID_PROXIES:
            continue

        t = threading.Thread(target=proxy_worker, args=(proxy, username, messages, counter, stop_event), daemon=True)
        threads.append(t)
        t.start()

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        stop_event.set()
        print("\nStopping...")

def main():
    username = input("\033[0m\033[93mUser => \033[0m").strip()
    proxies = load_proxies("proxy.txt")
    send_messages(username, MESSAGES, proxies)

if __name__ == "__main__":
    main()
