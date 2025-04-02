import discord
import os
import random
from discord.ext import commands

from keep_alive import keep_alive

keep_alive()

# Създаване на бота
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Глобален списък за съхранение на играчите и силите им
players = []
team_a = []
team_b = []

# Команда за добавяне на играч (сега се въвежда само общата сила)
@bot.command()
async def join(ctx, name: str, total_power: int):
    # Проверка дали играчът вече съществува
    for player in players:
        if player['name'].lower() == name.lower():
            await ctx.send(f"⚠️ Player **{name}** is already registered!")
            return

    # Запазване на данните на играча
    players.append({
        'name': name,
        'total_power': total_power
    })

    await ctx.send(f"✅ **{name}** successfully registered with **{total_power}M**!")

# Команда за формиране на отборите
@bot.command()
async def teams(ctx):
    global team_a, team_b

    if len(players) < 2:
        await ctx.send("📭 Not enough players to form teams.")
        return

    # Сортиране по обща сила (от най-силен към най-слаб)
    players_sorted = sorted(players, key=lambda x: x['total_power'], reverse=True)

    team_a, team_b = [], []
    total_a, total_b = 0, 0

    # Разпределение на играчите по два отбора
    for player in players_sorted:
        if total_a < total_b:
            team_a.append(player)
            total_a += player['total_power']
        else:
            team_b.append(player)
            total_b += player['total_power']

    # Вътрешно сортиране
    team_a_sorted = sorted(team_a, key=lambda x: x['total_power'], reverse=True)
    team_b_sorted = sorted(team_b, key=lambda x: x['total_power'], reverse=True)

    # Основен състав и резерви
    main_a = team_a_sorted[:20]  
    substitutes_a = team_a_sorted[20:30]

    main_b = team_b_sorted[:20]  
    substitutes_b = team_b_sorted[20:30]

    # Изпращане на отборите
    await ctx.send("🏆 **Team distribution:**")

    await ctx.send(f"🟦 **Team A** (Total power: {total_a}M):")
    await ctx.send(f"**Main (20 Players):**\n" + "\n".join([f"{p['name']} - {p['total_power']}M" for p in main_a]))
    await ctx.send(f"**Subs (10 players):**\n" + "\n".join([f"{p['name']} - {p['total_power']}M" for p in substitutes_a]))

    await ctx.send(f"\n🟥 **Team B** (Total power: {total_b}M):")
    await ctx.send(f"**Main (20 Players):**\n" + "\n".join([f"{p['name']} - {p['total_power']}M" for p in main_b]))
    await ctx.send(f"**Subs (10 Players):**\n" + "\n".join([f"{p['name']} - {p['total_power']}M" for p in substitutes_b]))

    await ctx.send(f"✅ Teams have been formed! Use !teamas1, !teamas2, !teamas3, !teambs1, !teambs2, !teambs3 to view them.")

# Функция за създаване на вътрешни отбори
def create_team_variations(team, team_name):
    variations = {}

    # Взимаме двамата най-силни в един вътрешен отбор
    top_two = team[:2]
    remaining_players = team[2:]

    # Разпределение на останалите 18 играчи в 9 отборa с балансирана сила
    sub_teams = [[] for _ in range(9)]
    sorted_remaining = sorted(remaining_players, key=lambda x: x['total_power'], reverse=True)

    for i, player in enumerate(sorted_remaining):
        sub_teams[i % 9].append(player)

    # Балансиране на отборите така, че да имат сходна обща сила
    for sub_team in sub_teams:
        sub_team.sort(key=lambda x: x['total_power'], reverse=True)

    # Разбъркване за различните вариации
    for i in range(1, 4):
        random.shuffle(sub_teams)
        variations[f"{team_name.lower()}s{i}"] = [top_two] + sub_teams

    return variations

# Команди за показване на вътрешните отбори
@bot.command()
async def teamas1(ctx):
    await show_team(ctx, "teama", 1)

@bot.command()
async def teamas2(ctx):
    await show_team(ctx, "teama", 2)

@bot.command()
async def teamas3(ctx):
    await show_team(ctx, "teama", 3)

@bot.command()
async def teambs1(ctx):
    await show_team(ctx, "teamb", 1)

@bot.command()
async def teambs2(ctx):
    await show_team(ctx, "teamb", 2)

@bot.command()
async def teambs3(ctx):
    await show_team(ctx, "teamb", 3)

# Функция за показване на дадена вариация на отбор
async def show_team(ctx, team_name, variation_number):
    global team_a, team_b

    team = team_a if team_name == "teama" else team_b
    if not team:
        await ctx.send(f"❌ {team_name.upper()} has not been formed yet. Use !teams first!")
        return

    team_variation = create_team_variations(team, team_name.upper())[f"{team_name}s{variation_number}"]

    team_message = f"### {team_name.upper()} Strategy {variation_number}\n"
    for i, sub_team in enumerate(team_variation):
        members = ", ".join([f"{p['name']} ({p['total_power']}M)" for p in sub_team])
        team_message += f"**Team {i+1}:** {members}\n"

    await ctx.send(team_message)

# Команда за изтриване на играч
@bot.command()
async def remove(ctx, name: str):
    global players
    new_players = [player for player in players if player['name'].lower() != name.lower()]

    if len(new_players) == len(players):
        await ctx.send(f"⚠️ Player **{name}** not found!")
    else:
        players = new_players
        await ctx.send(f"🗑️ Player **{name}** has been removed!")

# Команда за показване на текущите играчи
@bot.command()
async def status(ctx):
    if not players:
        await ctx.send("📭 No players added.")
        return

    status_message = "### 📋 Players:\n"
    for player in players:
        status_message += f"🔹 **{player['name']}** - {player['total_power']}M Main Squad\n"

    await ctx.send(status_message)

# Стартиране на бота
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if TOKEN is None:
    raise ValueError("DISCORD_BOT_TOKEN environment variable is not set.")

bot.run(TOKEN)