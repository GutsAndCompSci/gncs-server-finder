import pydirectinput
import tesserocr
import string
import orjson
from PIL import Image
import dxcam
import pygetwindow as gw
from time import time, sleep
import os
import pyperclip
from math import floor
import requests
from threading import Thread
import json
import subprocess
pydirectinput.PAUSE = 0

MAPS = {
    "fer": "La ferme d'En-Haut",
    "erm": "La ferme d'En-Haut",
    "aut": "La ferme d'En-Haut",
    "mme": "La ferme d'En-Haut",
    "laf": "La ferme d'En-Haut",
    "tyro": "Tyrolean Village",
    "age": "Tyrolean Village",
    "tro": "Tyrolean Village",
    "hou": "Hougoumont",
    "oug": "Hougoumont",
    "mont": "Hougoumont",
    "var": "Vardohus Fortress",
    "haye": "La Haye Sainte",
    "sai": "La Haye Sainte",
    "ros": "Roscloff",
    "san": "San Sebastian",
    "Kauby": "Kaub",
}
REGIONS = {
    "east": "US East",
    "west": "US West",
    "cen": "US Central",
    "ect": "US West",
    "kin": "EU",
    "ger": "EU",
    "many": "EU",
    "fra": "EU",
    "net": "EU",
    "pol": "EU",
    "ether": "EU",
    "sin": "Asia",
    "ing": "Asia",
    "por": "Asia",
    "pere": "Asia",
    "pece": "Asia",
    "hon": "Asia",
    "jap": "Asia",
    "ind": "Asia",
    "pndia": "Asia",
    "alla": "Australia",
    "aus": "Australia",
    "alia": "Australia",
    "ustra": "Australia",
    "nul": "Null",
    "ull": "Null",
}
LOCATIONS = {
    "Cali": "US West",
    "Angel": "US West",
    "Seattle": "US West",
    "Flor": "US East",
    "Ashburn": "US East",
    "Secaucus": "US East",
    "Jersey": "US East",
    "Virginia": "US East",
    "Chicago": "US Central",
    "Texas": "US Central",
    "Frank": "Germany",
    "Paris": "France",
    "France": "France",
    "Amster": "Netherlands",
    "Flevoland": "Netherlands",
    "Warsaw": "Poland",
    "Singa": "Singapore",
    "Tokyo": "Japan",
    "Mumba": "India",
    "Sydney": "Australia",
    "Ubir": "Egypt",
    "London": "United Kingdom"
}
LOCATION_TO_REGION = {
    "Germany": "EU",
    "France": "EU",
    "Netherlands": "EU",
    "Poland": "EU",
    "Egypt": "EU",
    "Singapore": "Asia",
    "Japan": "Asia",
    "India": "Asia",
}
PLATFORMS = {
    "vc": "VC",
    "only": "VC",
    "pc": "PC",
    "con": "PC",
    "mo": "Mobile",
    "ha": "Hardcore",
    "core": "Hardcore",
}
NAMES = {
    "Gruz": "Cruz",
    "Gcruz": "Cruz",
    "Tsaiah": "Isaiah",
    "Tisaiah": "Isaiah",
    "Gay": "Cay",
    "Gcay": "Cay",
    "Cgay": "Cay",
    "Gape": "Cape",
    "Gatalina": "Catalina",
    "Cgatalina": "Catalina",
    "Gcatalina": "Catalina",
    "Lackbeard": "Blackbeard",
    "Artholomew": "Bartholomew",
    "Lutch": "Dutch",
    "Wwaterloo": "Waterloo",
    "Izoratio": "Horatio",
    "Hvratio": "Horatio",
    "Eortuga": "Tortuga",
    "Demingo": "Domingo",
    "Ruyal": "Royal",
    "Vecra": "Vera",
    "Gquebec": "Quebec",
}
LINK_EXPIRATION = 60*60*3 #three hours

x, y = 391, 155 #top left of server list
w, h = 566, 68 #width and height of a server
press = pydirectinput.press

if not os.path.exists("ids.json"):
    with open("ids.json", "w") as file:
        file.write("{}")
with open("ids.json", "rb") as file:
    ids = orjson.loads(file.read().strip() or "{}")
with open("servers.json", "w") as file:
    file.write("[]")
with open("names.json", "rb") as file:
    names = set(orjson.loads(file.read()))

default_api = tesserocr.PyTessBaseAPI(path="traineddata", psm=tesserocr.PSM.SINGLE_BLOCK)
number_api = tesserocr.PyTessBaseAPI(path="traineddata", psm=tesserocr.PSM.SINGLE_BLOCK)
number_api.SetVariable('tessedit_char_whitelist', '0123456789')
default_api.SetVariable(
    'tessedit_char_whitelist',
    string.ascii_letters + string.digits + "|/-"
)

# BEGGINING OF MY BULLSHIT 
api_key = '.BFWAikwu_m+xwN$2=Ht;j9E'



def send_data(data, api_key):
    url = 'http://ec2-18-188-94-75.us-east-2.compute.amazonaws.com:5000/submit'
    headers = {
        'Content-Type': 'application/json',
        'X-API-Key': api_key,
    }
    try:
        response = requests.post(url, data=json.dumps(data), headers=headers)
        response.raise_for_status()
        print('Data sent successfully')
    except requests.exceptions.RequestException as e:
        print(f'Failed to send data: {e}')

# THAT'S ALL FOLKS!

def get_text(image, number=False, replace_newlines=True):
    api = number_api if number else default_api
    api.SetImage(image)
    text = api.GetUTF8Text().strip()
    if replace_newlines:
        text = text.replace("\n", " ")
    api.ClearPersistentCache()
    return text

camera = dxcam.create(max_buffer_len=1)
camera.start(video_mode=True)
def grab(region=None):
    array = camera.get_latest_frame()
    x1, y1, x2, y2 = region
    return Image.fromarray(array[y1:y2, x1:x2])

def grab_text(region, number=False, replace_newlines=True):
    return get_text(grab(region), number, replace_newlines)

def log(*args):
    text = " ".join(map(str, list(args)))
    print(text)
    with open("output.txt", "a") as file:
        file.write(text + "\n")

def match(dictionary, word):
    word = word.lower()
    for key, value in dictionary.items():
        if key.lower() in word:
            return value
        
def get_number(text):
    if text.isdigit():
        return int(text)
    
def click(x, y):
    pydirectinput.moveTo(x, y)
    pydirectinput.moveRel(-10, -10)
    pydirectinput.click()

def wait_for_word(region, word, to_disappear=False, timeout=5, number=False, wait=0):
    #Wait for a word in a specific region of the screen
    sleep(wait)
    start = time()
    while (word in grab_text(region, number=number).lower()) == to_disappear and (time() - start) <= timeout:
        pass
    return (time() - start) <= timeout

def exit_server():
    click(500, 630)
    #Wait until the "exit" button disappears. Thats how you know the wave screen is gone
    return wait_for_word((440, 614, 552, 640), "exit", to_disappear=True)

def get_server(region):
    x1, y1, x2, y2 = region
    stats_region = (x1 + 71, y1 + 35, x1 + 339, y1 + 54)
    stats = [s.strip() for s in grab_text(stats_region).split("|") if s.strip()]
    #This grabs the "US West | Latency: 0 | Mobile | 14/20"
    if len(stats) == 3:
        latency = stats[1]
        for sep in ("/", "-", "cy"):
            if sep in latency:
                del stats[1]
                stats.insert(1, latency.split(sep)[0])
                stats.insert(2, latency.split(sep)[1])
                break
    if len(stats) != 4:
        return log("Stats:", stats)
    if (country := match(REGIONS, stats[0])) is None:
        return log("Country:", stats[0])
    if (platform := match(PLATFORMS, stats[2])) is None:
        return log("Platform:", stats[2])
    if (players := get_number(stats[3].split("/")[0].replace("-", ""))) is None:
        return log("Players:", stats[3].split("/")[0])
    if not players:
        return
    if players >= 100:
        players /= 100

    server = {
        "region": country,
        "platform": platform,
        "players": players,
    }
    click((x1 + x2) // 2, (y1 + y2) // 2) #Click on the server
    #Wait until wave screen shows up(the word "exit" should be in the bottom left)
    wait_for_word((440, 614, 552, 640), "exit")
    name = grab_text((438, 152, 687, 175))
    if name and name[-1] == "-":
        name = name[:-1]
    if not name:
        exit_server()
        return log("Name")
    if "-" not in name:
        name = "-".join(w.strip() for w in name.split())
    if name.count("-") != 1:
        exit_server()
        return log("Name:", name)
    name = "-".join(w.strip().capitalize() for w in name.split("-", 1))
    name = "".join(c for c in name if c.isalpha() or c == "-")
    for key, value in NAMES.items():
        name = name.replace(key, value)
    first, second = name.split("-")
    if not (first in names and second in names):
        exit_server()
        return log("Name:", name)
    map_text = grab_text((448, 184, 656, 205))
    if not (map := match(MAPS, map_text)):
        exit_server()
        return log("Map:", map_text)
    if map in ("San Sebastian", "Roscloff", "Kaub"):
        log("Map:", map)
        return False
    wave_text = grab_text((805, 358, 879, 374), number=True)
    if not wave_text:
        exit_server()
        return log("Wave")
    if (wave := get_number(wave_text)) is None:
        exit_server()
        return log("Wave:", name, map, wave_text)
    if wave >= 200:
        wave %= 100
    server["name"] = name
    server["map"] = map
    server["wave"] = wave
    if id := ids.get(server["name"]):
        server["link"] = id["link"]
        if "location" in id:
            server["location"] = id["location"]
            server["region"] = LOCATION_TO_REGION.get(id["location"], id["location"])
    exit_server()
    server["updated"] = floor(time())
    return server

def open_roblox():
    while True:
        try:
            windows = gw.getWindowsWithTitle("Roblox")
            windows += gw.getWindowsWithTitle("Bloxstrap")
            if windows:
                for window in windows:
                    window.close()
            else:
                break
        except Exception:
            pass
    sleep(2)
    try:
        subprocess.call("TASKKILL /F /IM RobloxPlayerBeta.exe", shell=True)
        sleep(2)
    except:
        pass
    try:
        subprocess.call("TASKKILL /F /IM Bloxstrap.exe", shell=True)
        sleep(2)
    except:
        pass
    sleep(0.3)
    press(" ")                                                                                                                    
    os.system("start \"\" roblox://placeId=12334109280")
    # if wait_for_word((728, 387, 758, 403), "yes", timeout=10):
    #     click(744, 395)
    #     sleep(5)
    start = time()
    while not gw.getWindowsWithTitle("Roblox") and time() - start < 30:
        pass
    if time() - start > 30:
        open_roblox()
    else:
        focus()
    sleep(0.3)

def focus():
    try:
        if windows := gw.getWindowsWithTitle("Roblox"):
            windows[0].activate()
    except Exception:
        pass

def go_to_server_list():
    start = time()
    canskip = None
    while True:
        if "ser" in (text := grab_text((567, 419, 792, 453)).lower()) or "ver" in text:
            #find server button has appeared, means its done loading
            sleep(1)
            break
        elif time() - start > 150:
            open_roblox()
            start = time()
        if "skip" in grab_text((597, 626, 655, 649)).lower():
            if not canskip:
                start = time()
                canskip = time()
            elif time() - canskip > 30:
                click(677, 648) #skip loading
                canskip = time()

    click(679, 437) #find server
    if wait_for_word((419, 439, 683, 464), "browse", timeout=1):
        click(536, 462) #browse
    else:
        click(682, 451) #browse
    wait_for_word((409, 572, 502, 596), "return")
    click(571, 582) #filter
    wait_for_word((397, 610, 442, 636), "map")
    click(770, 663) #filter for endless
    wait_for_word((680, 650, 734, 666), "end")

def check_if_in_roblox():
    # if gw.getActiveWindowTitle() != "Roblox":
    #     print("Tabbed out")
    #     sys.exit()
    pass

session = requests.Session()
def get_all_servers(place_id):
    all_servers = set()
    cursor = ""
    while True:
        url = f"https://games.roblox.com/v1/games/{place_id}/servers/Public?sortOrder=Asc&limit=100&cursor={cursor}"
        try:
            response = session.get(url)
            if response.status_code != 200:
                print(f"Failed to fetch servers for place {place_id}. Status code: {response.status_code}")
                log(response.json())
                return
        except Exception as e:
            print(e)
            return

        data = response.json()
        for server in data['data']:
            all_servers.add(server['id'])

        cursor = data.get('nextPageCursor')
        if not cursor:
            break
        sleep(20)

    return all_servers

def cleanup_servers():
    place_ids = ['12334109280', '14218103727', '14216737767', '15010218068']

    print("Fetching active servers for all places...")
    active_job_ids = set()
    for place_id in place_ids:
        print(f"Fetching servers for place ID: {place_id}")
        place_servers = get_all_servers(place_id)
        if not place_servers:
            return
        active_job_ids.update(place_servers)
        print(f"Found {len(place_servers)} active servers for place ID: {place_id}")
        sleep(60)

    print(f"Total unique active servers across all places: {len(active_job_ids)}")

    updated_ids_data = {}
    removed_count = 0

    global ids
    for server_name, server_info in ids.items():
        link = server_info['link']
        job_id = link.split('gameInstanceId=')[-1]

        if job_id in active_job_ids:
            updated_ids_data[server_name] = server_info
        else:
            # print(f"Removing inactive server: {server_name}")
            removed_count += 1

    ids = updated_ids_data

    print(f"Server cleanup completed. Removed {removed_count} inactive servers.")

def loop_cleanup():
    while True:
        cleanup_servers()
        sleep(600)
Thread(target=loop_cleanup).start()

if not gw.getWindowsWithTitle("Roblox"):
    open_roblox()
    go_to_server_list()
focus()
server_name = None

while True:
    # click(544, 592) # Refresh
    # sleep(5)
    click(544, 592) # Refresh
    if not wait_for_word((700, 154, 944, 223), "end", timeout=20, wait=1):
        server_name = None
        open_roblox()
        go_to_server_list()
        continue

    servers = []
    press("\\", 1)
    errored = 0
    check = 0
    previous = None
    seen = set()
    while True:
        press("down", 6)
        sleep(0.5)
        current = []
        for i in range(6):
            server = get_server((x, y+(i*h), x+w, y+(i*h)+h))
            if server:
                current.append(server["name"])
                values = (server["name"], server["map"], server["wave"])
                if values not in seen:
                    servers.append(server)
                    seen.add(values)
            elif server == False:
                current.append(None)
            else:
                errored += 1
                current.append(None)
            if not gw.getWindowsWithTitle("Roblox"):
                errored = 10
                break
            check_if_in_roblox()
        if errored >= 10:
            break
        if previous == current:
            if check == 1:
                break
            check += 1
        previous = current

    if len(servers) < 30 or errored >= 20:
        log(f"Servers: {len(servers)}, Errors: {errored}")
        open_roblox()
        go_to_server_list()
        server_name = None
        continue

    with open("servers.json", "wb") as file:
        file.write(orjson.dumps(
            servers,
            option=orjson.OPT_INDENT_2
        ))

    if server_name and any(server["name"] == server_name for server in servers):
        roblox = gw.getWindowsWithTitle("Roblox")[0]
        roblox.minimize()
        wait_for_word((1258, 744, 1324, 762), "202", timeout=20, number=True)
        #taskbar has appeared because the date is showing
        start = time()
        while time() - start < 60:
            pydirectinput.moveTo(1149, 745)
            pydirectinput.moveRel(-10, -10)
            pydirectinput.rightClick()
            if wait_for_word((1150, 557, 1314, 619), "deep", timeout=1):
                break
        else:
            server_name = None
            open_roblox()
            go_to_server_list()
            continue
        click(1232, 601)
        sleep(1)
        link = pyperclip.paste()
        if not (link and link.startswith("roblox")):
            log("Link:", link)
            server_name = None
            open_roblox()
            go_to_server_list()
            continue
        link = "https://knightofeden.github.io/?" + link.split("?")[-1]
        start = time()
        while time() - start < 60:
            pydirectinput.moveTo(1149, 745)
            pydirectinput.moveRel(-10, -10)
            pydirectinput.rightClick()
            if wait_for_word((1150, 557, 1314, 619), "deep", timeout=1):
                break
        else:
            server_name = None
            open_roblox()
            go_to_server_list()
            continue
        click(1233, 631)
        wait_for_word((777, 399, 876, 431), "close")
        location_text = grab_text((564, 337, 874, 362))
        location = match(LOCATIONS, location_text)
        if not location:
            log("Location:", location_text)
        for server in servers:
            if server["name"] == server_name:
                server["link"] = link
                if location:
                    server["location"] = location 
        ids[server_name] = {
            "link": link,
        }
        if location:
            ids[server_name]["location"] = location
        with open("ids.json", "wb") as file:
            file.write(orjson.dumps(ids, option=orjson.OPT_INDENT_2))
        roblox.maximize()

    with open("servers.json", "wb") as file:
        file.write(orjson.dumps(
            servers,
            option=orjson.OPT_INDENT_2
        ))

    start = time()
    while gw.getActiveWindowTitle() != "Roblox" and time() - start < 10:
        pass
    if time() - start > 10:
        open_roblox()
        go_to_server_list()
        server_name = None

    press("\\", 2)
    sleep(0.5)
    for server in sorted(servers, key=lambda x: x["wave"], reverse=True):
        if "link" in server:
            continue
        click(691, 586)
        sleep(0.5)
        pydirectinput.write(server["name"].lower().replace("-", "--", 1))
        sleep(0.5)
        click(691, 191 + [s for s in servers if s["name"] == server["name"]].index(server) * h)
        if not wait_for_word((440, 614, 552, 640), "exit", timeout=1):
            continue
        click(833, 628)
        new_server = False
        start = time()
        while True:
            if "load" in (text := grab_text((837, 720, 1360, 768)).lower()) or "await" in text:
                server_name = server["name"]
                go_to_server_list()
                new_server = True
                break
            elif "fail" in grab_text((608, 272, 754, 298)).lower():
                click(682, 472)
                sleep(0.5)
                exit_server()
                break
            elif "yes" in grab_text((516, 518, 674, 542)).lower():
                click(594, 531)
            elif not gw.getWindowsWithTitle("Roblox"):
                open_roblox()
                go_to_server_list()
                new_server = True
                server_name = None
                break
            elif time() - start > 60:
                open_roblox()
                go_to_server_list()
                new_server = True
                server_name = None
                break
            check_if_in_roblox()
        if new_server:
            break
        sleep(0.5)
    else:
        open_roblox()
        go_to_server_list()
        server_name = None
