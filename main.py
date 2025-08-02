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

def load_proxies(filename):
    try:
        with open(filename, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        print("\033[0m\033[1;31m[Error] \033[0m\033[0;31mproxy.txt file not found")
        exit(1)

def send_single_message(proxy, username, messages, counter):
    while True:
        try:
            px = {"http": proxy, "https": proxy}
            device_id = "".join(random.choices("0123456789abcdef", k=42))
            url = "https://ngl.link/api/submit"
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
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
            data = {
                "username": username,
                "question": random.choice(messages),
                "deviceId": device_id,
                "gameSlug": "",
                "referrer": "",
            }
            response = requests.post(url, headers=headers, data=data, proxies=px, timeout=10, verify=False)

            if response.status_code == 429:
                print("\033[0m\033[1;31m[Error] \033[0m\033[0;31m429 | Rate Limit")
                time.sleep(10)
            elif response.status_code != 200:
                print(f"\033[0m\033[1;31m[Error] \033[0m\033[0;31m{response.status_code} | {proxy}")
                with COUNTER_LOCK:
                    if proxy not in INVALID_PROXIES:
                        INVALID_PROXIES.append(proxy)
                break
            else:
                with COUNTER_LOCK:
                    counter[0] += 1
                    print(f"\033[0m\033[1;32m[Successful] \033[0m\033[0;32mMessage Total: {counter[0]}")
        except Exception:
            with COUNTER_LOCK:
                if proxy not in INVALID_PROXIES:
                    INVALID_PROXIES.append(proxy)
            break

def send_messages(username, messages, proxies):
    counter = [0]
    threads = []
    for proxy in proxies:
        for _ in range(5):
            t = threading.Thread(target=send_single_message, args=(proxy, username, messages, counter))
            threads.append(t)
            t.start()
    for t in threads:
        t.join()

def main():
    username = input("\033[0m\033[93mUser => \033[0m")
    proxies = load_proxies(PROXY_FILE)
    send_messages(username, MESSAGES, proxies)

if __name__ == "__main__":
    main()
