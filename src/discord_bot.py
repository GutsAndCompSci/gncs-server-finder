import discord
from discord.app_commands import CommandTree
from typing import Literal
from heapq import nlargest, nsmallest
import orjson
import os
import asyncio
import logging
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)

PLATFORM_ICON = {
    "VC": "🔊",
    "PC": "🖥️",
    "Hardcore": "👿",
    "Mobile": "📱"
}

REGION_ICONS = {
    "Asia": ":earth_asia:",
    "US East": "🇺🇸 **E**",
    "US Central": "🇺🇸 **C**",
    "US West": "🇺🇸 **W**",
    "EU": "🇪🇺",
    "Australia": "🇦🇺",
    "Germany": "🇩🇪",
    "France": "🇫🇷",
    "Netherlands": "🇳🇱",
    "Singapore": "🇸🇬",
    "Japan": "🇯🇵",
    "India": "🇮🇳",
    "Poland": ":flag_pl:",
    "Egypt": ":flag_eg:",
    "United Kingdom": "🇬🇧",
    "Null": ":flag_white:",
}

def read_servers():
    if os.path.exists("servers.json"):
        with open("servers.json", "rb") as file:
            return orjson.loads(file.read())
    return []

def read_reminders():
    if os.path.exists("reminders.json"):
        with open("reminders.json", "rb") as file:
            return orjson.loads(file.read())
    return []

def save_reminders(reminders):
    with open("reminders.json", "wb") as file:
        file.write(orjson.dumps(reminders))

activity = discord.Activity(
    type=discord.ActivityType.watching, 
    name="server waves"
)

client = discord.Client(intents=discord.Intents.none(), activity=activity)
tree = CommandTree(client)

async def check_reminders():
    while True:
        servers = read_servers()
        reminders = read_reminders()
        updated_reminders = []
        
        for reminder in reminders:
            matching_servers = [
                s for s in servers
                if (not reminder["map"] or reminder["map"] in s["map"]) and
                   (not reminder["platform"] or reminder["platform"] == s["platform"]) and
                   (not reminder["region"] or reminder["region"] in s["region"]) and
                   s["wave"] >= reminder["target_wave"]
            ]
            
            if matching_servers:
                try:
                    user = await client.fetch_user(reminder["user_id"])
                    for server in matching_servers:
                        await user.send(
                            f"🌊 Wave {reminder['target_wave']} reached!\n" +
                            f"Server: {server['name']}\n" +
                            f"Current wave: {server['wave']}\n" +
                            f"Map: {server['map']}\n" +
                            f"Platform: {PLATFORM_ICON[server['platform']]}\n" +
                            f"Region: {REGION_ICONS[server.get('location', server['region'])]}"
                        )
                except discord.NotFound:
                    # crashed the bot last time someone got banned off discord 🤌
                    pass
            else:
                updated_reminders.append(reminder)
        
        save_reminders(updated_reminders)
        await asyncio.sleep(60)

async def update_status():
    while True:
        servers = read_servers()
        if not servers:
            await client.change_presence(activity=None)
            await asyncio.sleep(30)
            continue
        
        server = max(servers, key=lambda x: x["wave"])
        await client.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching, 
            name=f"Wave {server['wave']} {' '.join(server['map'].split()[:2])} {server['name']}", 
        ))
        await asyncio.sleep(180)

@client.event
async def on_ready():
    await tree.sync()
    logging.info(f'Logged in as {client.user}!')
    client.loop.create_task(update_status())
    client.loop.create_task(check_reminders())

@tree.command(name="rm", description="Set a reminder for when a server reaches a specific wave")
async def remind_me(
    interaction: discord.Interaction,
    wave: int,
    map: Literal["La ferme d'En-Haut", "Hougoumont", "Tyrolean Village", "La Haye Sainte"] | None = None,
    region: Literal["US", "EU", "Asia", "Australia"] | None = None,
    platform: Literal["PC", "VC", "Mobile", "Hardcore"] | None = None,
):
    if wave < 1:
        return await interaction.response.send_message(
            "Wave number must be positive!",
            ephemeral=True
        )
    
    reminders = read_reminders()
    existing = any(
        r["user_id"] == interaction.user.id and
        r["target_wave"] == wave and
        r["map"] == map and
        r["platform"] == platform and
        r["region"] == region
        for r in reminders
    )
    
    if existing:
        return await interaction.response.send_message(
            "You already have this reminder set!",
            ephemeral=True
        )
    
    reminders.append({
        "user_id": interaction.user.id,
        "target_wave": wave,
        "map": map,
        "platform": platform,
        "region": region,
        "created_at": int(interaction.created_at.timestamp())
    })
    
    save_reminders(reminders)
    
    filters = []
    if map:
        filters.append(f"Map: {map}")
    if platform:
        filters.append(f"Platform: {PLATFORM_ICON[platform]}")
    if region:
        filters.append(f"Region: {region}")
    
    response = f"I'll notify you when a server reaches wave {wave}"
    if filters:
        response += f" with these filters:\n" + "\n".join(f"• {f}" for f in filters)
    
    await interaction.response.send_message(response, ephemeral=True)

@tree.command(name="findserver", description="Finds G&B high wave endless servers")
async def find_servers(
    interaction: discord.Interaction, 
    map: Literal["La ferme d'En-Haut", "Hougoumont", "Tyrolean Village", "La Haye Sainte"] | None,
    region: Literal["US", "EU", "Asia", "Australia"] | None,
    platform: Literal["PC", "VC", "Mobile", "Hardcore"] | None,
    ordering: Literal["Ascending", "Descending"] = "Descending",
):
    print(f"Received interaction from {interaction.user}")
    match = list(filter(lambda x: x[1], (("map", map), ("region", region), ("platform", platform))))
    servers = read_servers()
    
    if not servers:
        return await interaction.response.send_message(
            "The bot just started. Give it a second to get the servers.",
            ephemeral=True
        )
    
    updated = max(s["updated"] for s in servers)
    sort = nlargest if ordering == "Descending" else nsmallest
    servers = sort(5, (s for s in servers if all(v in s[k] for k, v in match)), key=lambda x: x["wave"])
    
    if not servers:
        return await interaction.response.send_message(
            f"No servers matching your criteria were found.\n-# Last updated <t:{updated}:R>",
            ephemeral=True
        )
    
    output = "# "
    if map:
        output += " ".join(map.split()[:2]) + " "
    output += "Servers:\n"
    
    for server in servers:
        output += "- " + ' | '.join((
            f"*[{server['name']}]({server['link']})*" if "link" in server else f"*{server['name']}*",
            f"{server['players']}/20",
            f"w**{server['wave']}**",
            f"***{server['map']}***",
            PLATFORM_ICON[server["platform"]],
            REGION_ICONS[server.get("location", server["region"])],
        )) + "\n"
    
    output += f"-# Last updated <t:{updated}:R>"
    await interaction.response.send_message(output)

@tree.command(name="myreminders", description="List your active wave reminders")
async def list_reminders(interaction: discord.Interaction):
    reminders = read_reminders()
    user_reminders = [r for r in reminders if r["user_id"] == interaction.user.id]
    
    if not user_reminders:
        return await interaction.response.send_message(
            "You don't have any active reminders.",
            ephemeral=True
        )
    
    output = "Your active reminders:\n"
    for r in user_reminders:
        filters = [f"Wave {r['target_wave']}"]
        if r["map"]:
            filters.append(f"Map: {r['map']}")
        if r["platform"]:
            filters.append(f"Platform: {PLATFORM_ICON[r['platform']]}")
        if r["region"]:
            filters.append(f"Region: {r['region']}")
        output += "• " + " | ".join(filters) + f" (Set <t:{r['created_at']}:R>)\n"
    
    await interaction.response.send_message(output, ephemeral=True)

@find_servers.error
@remind_me.error
@list_reminders.error
async def on_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    print(str(error))
    await interaction.response.send_message(str(error), ephemeral=True)

client.run(os.getenv("BOT_TOKEN"))
