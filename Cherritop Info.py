import os
import sys
import time
import threading
import asyncio
import discord
import pystray
from PIL import Image, ImageDraw
import psutil
import GPUtil
import winreg
import tkinter as tk
from tkinter import simpledialog, messagebox

# ================= CONFIG =================
CONFIG_FILE = "pcinfosettings.txt"

def get_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            lines = f.read().splitlines()
            if len(lines) >= 2:
                token = lines[0].strip()
                user_id = int(lines[1].strip())
                return token, user_id

    # First launch → ask using Tkinter windows
    root = tk.Tk()
    root.withdraw()  # Hide the main root window

    # Ask for bot token
    token = simpledialog.askstring("Discord Bot Token", "Enter your Discord Bot Token:", parent=root)
    if not token:
        messagebox.showerror("Error", "Bot token is required!")
        sys.exit()

    # Ask for user ID
    user_id_str = simpledialog.askstring("Discord User ID", "Enter your Discord User ID:", parent=root)
    if not user_id_str or not user_id_str.isdigit():
        messagebox.showerror("Error", "A valid numeric User ID is required!")
        sys.exit()
    user_id = int(user_id_str)

    # Save to pcinfosettings.txt
    with open(CONFIG_FILE, "w") as f:
        f.write(f"{token}\n{user_id}\n")

    return token, user_id

DISCORD_BOT_TOKEN, DISCORD_USER_ID = get_config()
CHECK_INTERVAL = 5  # safe battery check interval (seconds)
LOW_BATTERY = 20

# ================= DISCORD SETUP =================
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
loop = asyncio.new_event_loop()

async def send_dm(message):
    try:
        user = await client.fetch_user(DISCORD_USER_ID)
        await user.send(message)
    except Exception as e:
        print("DM FAILED:", repr(e))

def start_discord():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(client.start(DISCORD_BOT_TOKEN))

# ================= BATTERY MONITOR =================
def monitor_battery():
    battery = psutil.sensors_battery()
    if battery is None:
        print("No battery detected")
        return

    last_plugged = battery.power_plugged
    low_alert_sent = battery.percent <= LOW_BATTERY

    # Immediate startup alert
    if last_plugged:
        asyncio.run_coroutine_threadsafe(
            send_dm(f"⚡ Laptop plugged in ({battery.percent}%)"),
            loop
        )
    else:
        asyncio.run_coroutine_threadsafe(
            send_dm(f"🔌 Laptop unplugged ({battery.percent}%)"),
            loop
        )

    while True:
        battery = psutil.sensors_battery()
        if battery is None:
            time.sleep(CHECK_INTERVAL)
            continue

        plugged = battery.power_plugged
        percent = battery.percent

        if last_plugged and not plugged:
            asyncio.run_coroutine_threadsafe(
                send_dm(f"🔌 Laptop unplugged ({percent}%)"),
                loop
            )

        if not last_plugged and plugged:
            asyncio.run_coroutine_threadsafe(
                send_dm(f"⚡ Laptop plugged in ({percent}%)"),
                loop
            )
            low_alert_sent = False

        if percent <= LOW_BATTERY and not low_alert_sent:
            asyncio.run_coroutine_threadsafe(
                send_dm(f"🪫 Battery low ({percent}%)"),
                loop
            )
            low_alert_sent = True

        last_plugged = plugged
        time.sleep(CHECK_INTERVAL)

# ================= HELPER: CPU NAME =================
def get_cpu_name():
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
        cpu_name, _ = winreg.QueryValueEx(key, "ProcessorNameString")
        winreg.CloseKey(key)
        return cpu_name.strip()
    except Exception:
        return "Unknown CPU"

# ================= DISCORD COMMANDS =================
@client.event
async def on_message(message):
    if message.author.id != DISCORD_USER_ID:
        return

    content = message.content.lower().strip()

    if content == "!cpu":
        cpu = psutil.cpu_percent(interval=1)
        await message.channel.send(f"🖥️ CPU usage: {cpu}%")

    elif content == "!ram":
        mem = psutil.virtual_memory()
        used = mem.used / (1024 ** 3)
        total = mem.total / (1024 ** 3)
        free = mem.available / (1024 ** 3)
        await message.channel.send(
            f"🧠 RAM usage:\nUsed: {used:.1f} GB\nFree: {free:.1f} GB\nTotal: {total:.1f} GB"
        )

    elif content == "!pcinfo":
        cpu_name = get_cpu_name()
        response = f"🖥️ CPU: {cpu_name}\n"
        gpus = GPUtil.getGPUs()
        if not gpus:
            response += "No GPUs detected."
        else:
            for i, gpu in enumerate(gpus, start=1):
                response += (
                    f"GPU{i} - {gpu.name} | "
                    f"Usage: {gpu.load*100:.1f}% | "
                    f"Memory: {gpu.memoryUsed:.1f}/{gpu.memoryTotal:.1f} MB\n"
                )
        await message.channel.send(response)

    elif content == "!battery":
        battery = psutil.sensors_battery()
        if battery is None:
            await message.channel.send("No battery detected.")
        else:
            plugged = "plugged in ⚡" if battery.power_plugged else "unplugged 🔌"
            await message.channel.send(
                f"🔋 Battery: {battery.percent:.0f}% ({plugged})"
            )

@client.event
async def on_ready():
    print(f"Bot logged in as {client.user}")

# ================= TRAY ICON =================
def create_image():
    img = Image.new("RGB", (64, 64), "black")
    draw = ImageDraw.Draw(img)
    draw.rectangle((16, 16, 48, 48), outline="white", width=3)
    draw.rectangle((48, 26, 56, 38), fill="white")
    return img

def on_exit(icon, item):
    icon.stop()
    loop.call_soon_threadsafe(loop.stop)
    asyncio.run_coroutine_threadsafe(client.close(), loop)
    raise SystemExit

def tray_icon():
    icon = pystray.Icon(
        "BatteryMonitor",
        create_image(),
        "Cherri's PC Info Bot",
        menu=pystray.Menu(
            pystray.MenuItem("Exit", on_exit)
        )
    )
    icon.run()

# ================= RESTART REMINDER =================
def restart_reminder():
    REMINDER_INTERVAL = 3 * 24 * 60 * 60  # 3 days in seconds
    while True:
        asyncio.run_coroutine_threadsafe(
            send_dm("⏰ Reminder: It's been 3 days! Consider restarting your PC."),
            loop
        )
        time.sleep(REMINDER_INTERVAL)

# ================= START EVERYTHING =================
threading.Thread(target=start_discord, daemon=True).start()
threading.Thread(target=monitor_battery, daemon=True).start()
threading.Thread(target=restart_reminder, daemon=True).start()
tray_icon()