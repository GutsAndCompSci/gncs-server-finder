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

activity = discord.Activity(
    type=discord.ActivityType.watching, 
    name="server waves"
)
client = discord.Client(intents=discord.Intents.none(), activity=activity)
tree = CommandTree(client)

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

@find_servers.error
async def on_servers_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    print(str(error))
    await interaction.response.send_message(str(error), ephemeral=True)

client.run(os.getenv("BOT_TOKEN"))
