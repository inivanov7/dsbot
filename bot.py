from dotenv import load_dotenv
import os
import json
import discord
from discord.ext import commands

# Зареждане на .env файла
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if TOKEN is None:
    raise ValueError("❌ DISCORD_BOT_TOKEN environment variable is not set!")

# Създаване на бота
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Файл за съхранение на данните
DATA_FILE = "players.json"

# Глобални списъци
players = []
team_a = []
team_b = []

# Функция за зареждане на играчите от файла
def load_players():
    global players
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            try:
                players = json.load(file)
            except json.JSONDecodeError:
                players = []

# Функция за записване на играчите във файла
def save_players():
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(players, file, ensure_ascii=False, indent=4)

# Зареждане на съхранените играчи при стартиране
load_players()

# Команда за добавяне на играч
@bot.command()
async def join(ctx, name: str, total_power: int):
    for player in players:
        if player['name'].lower() == name.lower():
            await ctx.send(f"⚠️ Player **{name}** is already registered!")
            return

    players.append({'name': name, 'total_power': total_power})
    save_players()  # Запазване на новия играч в JSON файла
    await ctx.send(f"✅ **{name}** successfully registered with **{total_power}M**!")

# Команда за премахване на играч
@bot.command()
async def remove(ctx, name: str):
    global players
    new_players = [player for player in players if player['name'].lower() != name.lower()]

    if len(new_players) == len(players):
        await ctx.send(f"⚠️ Player **{name}** not found!")
    else:
        players = new_players
        save_players()  # Запазване на промените
        await ctx.send(f"🗑️ Player **{name}** has been removed!")

# Команда за показване на текущите играчи
@bot.command()
async def status(ctx):
    if not players:
        await ctx.send("📭 No players added.")
        return

    status_message = "### 📋 Players:\n"
    for player in players:
        status_message += f"🔹 **{player['name']}** - {player['total_power']}M\n"

    await ctx.send(status_message)

# Команда за изчистване на всички играчи
@bot.command()
async def clear1(ctx):
    global players
    players = []
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)  # Изтриваме файла, ако съществува
    await ctx.send("🧹 All player data has been cleared!")

# Стартиране на бота
bot.run(TOKEN)
