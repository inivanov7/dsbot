import discord
import os
import json
import math
from datetime import datetime
from discord.ext import commands
from dotenv import load_dotenv

# Loading the .env file
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if TOKEN is None:
    raise ValueError("❌ DISCORD_BOT_TOKEN environment variable is not set!")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Запазваме текущите и оригиналните стратегии по ключ (1a, 2a, ..., 4b)
# Запазваме текущите и оригиналните стратегии по ключ (1a, 2a, ..., 4b)
current_strategies = {
    "1a": [], "2a": [], "3a": [], "4a": [],
    "1b": [], "2b": [], "3b": [], "4b": []
}
original_strategies = {
    "1a": [], "2a": [], "3a": [], "4a": [],
    "1b": [], "2b": [], "3b": [], "4b": []
}
current_subs = {
    "1a": [], "2a": [], "3a": [], "4a": [],
    "1b": [], "2b": [], "3b": [], "4b": []
}


# Saving data in JSON
data_file = "players_data.json"

# Checking if data already exists
def load_data():
    if os.path.exists(data_file):
        with open(data_file, "r") as f:
            return json.load(f)
    else:
        return {"team_a": [], "team_b": [], "sub_a": [], "sub_b": [], "unassigned": []}

def save_data(data):
    with open(data_file, "w") as f:
        json.dump(data, f, indent=4)

# Задаваме файл за съхранение на състоянието на записването
status_file = "registration_status.json"

# Проверяваме дали съществува файл за състоянието на записването
def load_registration_status():
    if os.path.exists(status_file):
        with open(status_file, "r") as f:
            return json.load(f)
    else:
        # Ако няма файл, създаваме нов със стойност за активирано записване
        return {"registration_active": True}

def save_registration_status(status):
    with open(status_file, "w") as f:
        json.dump(status, f, indent=4)

def convert_players_to_tuples(data):
    for key in data:
        data[key] = [tuple(player) for player in data[key]]
    return data

NOTES_FILE = "notes.json"

def load_notes():
    try:
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_notes(notes):
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)

STRATEGIES_FILE = "strategies.json"

def load_strategies():
    if os.path.exists(STRATEGIES_FILE):
        with open(STRATEGIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {}

def save_strategies(data):
    with open(STRATEGIES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ✅ След като са дефинирани, тогава зареждаме от файл:
persisted_strategies = load_strategies()
for key in persisted_strategies:
    current_strategies[key] = [list(map(tuple, team)) for team in persisted_strategies[key]["current"]]
    original_strategies[key] = [list(map(tuple, team)) for team in persisted_strategies[key]["original"]]
    current_subs[key] = [tuple(sub) for sub in persisted_strategies[key]["subs"]]

@bot.command()
async def note(ctx, *, message):
    if not any(role.name in ["R4", "R5"] for role in ctx.author.roles):
        await ctx.send("❌ You do not have permission to use this command.")
        return
    notes = load_notes()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    notes.append({
        "author": ctx.author.display_name,
        "message": message,
        "time": now
    })
    save_notes(notes)
    await ctx.send(f"📝 Note added by **{ctx.author.display_name}** at {now}.")

@bot.command()
async def notes(ctx):
    if not any(role.name in ["R4", "R5"] for role in ctx.author.roles):
        await ctx.send("❌ You do not have permission to use this command.")
        return
    notes = load_notes()
    if not notes:
        await ctx.send("📭 No notes saved.")
        return

    note_lines = [f"• [{n['time']}] {n['author']}: {n['message']}" for n in notes]
    output = "\n".join(note_lines)
    
    if len(output) > 2000:
        await ctx.send("📋 Notes too long to display.")
    else:
        await ctx.send(f"📒 **DS Notes:**\n{output}")

@bot.command()
async def clearnotes(ctx):
    if not any(role.name in ["R4", "R5"] for role in ctx.author.roles):
        await ctx.send("❌ You do not have permission to use this command.")
        return
    save_notes([])
    await ctx.send("🧹 All notes have been cleared.")


@bot.command()
async def start(ctx):
    if not any(role.name in ["R4", "R5"] for role in ctx.author.roles):
        await ctx.send("⚠️ You do not have the required role to use this command.")
        return

    # Променяме състоянието на записването на активно
    status = load_registration_status()
    status["registration_active"] = True
    save_registration_status(status)

    await ctx.send("✅ Registration for Desert Storm has been opened. Players can now join.")

@bot.command()
async def end(ctx):
    if not any(role.name in ["R4", "R5"] for role in ctx.author.roles):
        await ctx.send("⚠️ You do not have the required role to use this command.")
        return

    # Променяме състоянието на записването на неактивно
    status = load_registration_status()
    status["registration_active"] = False
    save_registration_status(status)

    await ctx.send("🚫 Registration and Update power for Desert Storm has been closed. No new players can join.")

@bot.command()
async def join(ctx, *args):
    # Проверка за празен или твърде кратък вход
    if len(args) < 2:
        await ctx.send("⚠️ Please provide a name and a strength. Example: `!join INIv 23`")
        return

    # Последният елемент е силата, останалите са името
    *name_parts, strength = args
    name = " ".join(name_parts)

    # Проверяваме дали записването е активно
    status = load_registration_status()
    if not status["registration_active"]:
        await ctx.send("⚠️ Registration is closed. You cannot join at this moment.")
        return

    strength = strength.replace(',', '.')

    try:
        strength = float(strength)
    except ValueError:
        await ctx.send(f"⚠️ Invalid strength value for **{name}**. Please provide a valid number.")
        return

    data = convert_players_to_tuples(load_data())
    all_players = data["unassigned"] + data["team_a"] + data["team_b"] + data["sub_a"] + data["sub_b"]
    
    if any(name.lower() == player[0].lower() for player in all_players):
        await ctx.send(f"⚠️ A player named **{name}** is already registered.")
        return

    data["unassigned"].append((name, strength))
    data["unassigned"].sort(key=lambda x: x[1], reverse=True)
    save_data(data)
    await ctx.send(f"{name} with strength {strength:.2f} has been added to the player pool.")

@bot.command()
async def update(ctx, *args):

    # 🛑 Проверка дали регистрацията е активна
    status = load_registration_status()
    if not status.get("registration_active", True):
        await ctx.send("🚫 Registration is closed. You cannot update strength at this moment.")
        return

    if len(args) < 2:
        await ctx.send("⚠️ Please provide a name and a strength. Example: !update INIv 24.5")
        return

    *name_parts, strength = args
    name = " ".join(name_parts)

    strength = strength.replace(',', '.')

    try:
        strength = float(strength)
    except ValueError:
        await ctx.send(f"⚠️ Invalid strength value for **{name}**. Please provide a valid number.")
        return

    data = convert_players_to_tuples(load_data())

    player_found = False
    for team in ["team_a", "team_b", "sub_a", "sub_b", "unassigned"]:
        for idx, player in enumerate(data[team]):
            if player[0].lower() == name.lower():
                data[team][idx] = (name, strength)
                player_found = True
                break
        if player_found:
            break

    if player_found:
        data["unassigned"].sort(key=lambda x: x[1], reverse=True)
        save_data(data)
        await ctx.send(f"✅ The strength of **{name}** has been updated to **{strength:.2f}**.")
    else:
        await ctx.send(f"⚠️ Player **{name}** not found.")

@bot.command()
async def status(ctx):
    if not any(role.name in ["R4", "R5"] for role in ctx.author.roles):
        await ctx.send("❌ You don't have access to moderator commands.")
        return
    data = convert_players_to_tuples(load_data())

    def format_players(players):
        if not players:
            return "—"
        return "\n".join([f"• {name} ({strength:.2f})" for name, strength in players])

    players_text = format_players(data["unassigned"])
    header = f"🧾 Unassigned Players ({len(data['unassigned'])})"

    full_text = f"{header}\n\n{players_text}"

    # Discord позволява максимум 2000 символа в едно съобщение
    if len(full_text) > 2000:
        parts = [full_text[i:i + 1900] for i in range(0, len(full_text), 1900)]
        for part in parts:
            await ctx.send(part)
    else:
        await ctx.send(full_text)


@bot.command()
async def teams(ctx):
    if not any(role.name in ["R4", "R5"] for role in ctx.author.roles):
        await ctx.send("⚠️ You do not have the required role to use this command.")
        return
    data = convert_players_to_tuples(load_data())

    # Format the players in each team and substitute list
    def format_players(players):
        if not players:
            return "_no players_"
        return "\n".join([f"{p[0]} - {p[1]:.2f}" for p in players])

    message = (
        f"⚔️ **Team A ({len(data['team_a'])}) | Total Power: {sum(p[1] for p in data['team_a']):.2f}**\n"
        f"{format_players(data['team_a'])}\n\n"
        f"🔁 **Substitutes A ({len(data['sub_a'])})**\n"
        f"{format_players(data['sub_a'])}\n\n"
        f"⚔️ **Team B ({len(data['team_b'])}) | Total Power: {sum(p[1] for p in data['team_b']):.2f}**\n"
        f"{format_players(data['team_b'])}\n\n"
        f"🔁 **Substitutes B ({len(data['sub_b'])})**\n"
        f"{format_players(data['sub_b'])}"
    )

    await ctx.send(message)

@bot.command()
async def balance(ctx):
    if not any(role.name in ["R4", "R5"] for role in ctx.author.roles):
        await ctx.send("You do not have the required role to use this command.")
        return

    data = convert_players_to_tuples(load_data())

    # Collecting all players from all places
    all_players = (
        data.get("team_a", []) +
        data.get("team_b", []) +
        data.get("sub_a", []) +
        data.get("sub_b", []) +
        data.get("unassigned", [])
    )

    # Sorting by strength
    all_players = sorted(all_players, key=lambda x: x[1], reverse=True)

    # New empty teams
    team_a, team_b = [], []
    strength_a, strength_b = 0, 0

    # Distribute players evenly
    for player in all_players:
        if strength_a <= strength_b:
            team_a.append(player)
            strength_a += player[1]
        else:
            team_b.append(player)
            strength_b += player[1]

    # Splitting into starters and substitutes
    sorted_a = sorted(team_a, key=lambda x: x[1], reverse=True)
    sorted_b = sorted(team_b, key=lambda x: x[1], reverse=True)

    data["team_a"] = sorted_a[:20]
    data["sub_a"] = sorted_a[20:30]
    data["team_b"] = sorted_b[:20]
    data["sub_b"] = sorted_b[20:30]
    data["unassigned"] = []

    save_data(data)

    def format_team(team, name):
        if not team:
            return f"**{name}:** _empty_"
        total_strength = sum(p[1] for p in team)
        return f"**{name} ({len(team)}) | Total Strength: {total_strength:.2f}**\n" + "\n".join([f"{p[0]} - {p[1]:.2f}" for p in team])

    msg = (
        f"**⚖️ The teams have been balanced!**\n\n"
        f"{format_team(data['team_a'], 'Team A')}\n\n"
        f"{format_team(data['sub_a'], 'Sub A')}\n\n"
        f"{format_team(data['team_b'], 'Team B')}\n\n"
        f"{format_team(data['sub_b'], 'Sub B')}"
    )

    await ctx.send(msg)

@bot.command()
async def remove(ctx, *, name: str):
    if not any(role.name in ["R4", "R5"] for role in ctx.author.roles):
        await ctx.send("You do not have the required role to use this command.")
        return

    data = convert_players_to_tuples(load_data())
    
    # Премахване на играч от всички отбори, резерви и неназначени
    removed = False
    for team in ["team_a", "team_b", "sub_a", "sub_b", "unassigned"]:
        new_team = [player for player in data[team] if player[0].lower() != name.lower()]
        if len(new_team) != len(data[team]):
            removed = True  # Играчът е премахнат
            data[team] = new_team
    
    if removed:
        save_data(data)
        await ctx.send(f"{name} has been removed from all teams and the unassigned pool.")
    else:
        await ctx.send(f"Could not find player {name} in any team or in the unassigned pool.")


@bot.command()
async def move(ctx, to_team: str, *, name: str):
    if not any(role.name in ["R4", "R5"] for role in ctx.author.roles):
        await ctx.send("You do not have the required role to use this command.")
        return

    data = convert_players_to_tuples(load_data())

    team_map = {
        "a": "team_a",
        "b": "team_b",
        "asub": "sub_a",
        "bsub": "sub_b",
        "un": "unassigned"
    }

    if to_team not in team_map:
        await ctx.send("Invalid destination team. Use: a, b, asub, bsub, un.")
        return

    # Намери и премахни играча от всичко
    player_to_move = None
    for team in data:
        for player in data[team]:
            if player[0].lower() == name.lower():
                player_to_move = player
                data[team] = [p for p in data[team] if p[0].lower() != name.lower()]
                break
        if player_to_move:
            break

    if not player_to_move:
        await ctx.send(f"⚠️ Player **{name}** not found in any team.")
        return

    # Добави към новия отбор
    data[team_map[to_team]].append(player_to_move)
    data[team_map[to_team]].sort(key=lambda x: x[1], reverse=True)
    save_data(data)

    await ctx.send(f"✅ **{name}** has been moved to **{to_team.upper()}**.")

def generate_strategy(team_name, team_players, substitutes, strategy_type):
    team_players_sorted = sorted(team_players, key=lambda x: x[1], reverse=True)
    num_players = len(team_players_sorted)

    if strategy_type == 1:
        num_teams = 4
        intro = """⚔️ **Strategy 1: Only Hospitals**
For the substitutes (those who can join only if there is space: 20 people maximum in the battlefield)
You risk being called at any time if someone from the participants cannot be present and if those present have no longer soldiers and can't fight so please stay tuned and ready to join the battle field at any time (even at the start). 
""" 
        outro = """
🧭 **Hospital Distribution**
Team 1 → OUR North Hospital  
Team 2 → OUR South Hospital  
Team 3 → ENEMY North Hospital  
Team 4 → ENEMY South Hospital

For the participants : Please join the battle field 5 minutes before the start. 
In addition, you will be in a team in order to keep the hospitals as long as possible
Please follow your team leaders if any question, or strategy.

When building in middle will be open : our 3 big hitters will take one each, the other stay on your hospital."""
        # Default distribution by strength
        team_groups = [[] for _ in range(num_teams)]
        team_strengths = [0] * num_teams
        for player in team_players_sorted:
            idx = team_strengths.index(min(team_strengths))
            team_groups[idx].append(player)
            team_strengths[idx] += player[1]

    elif strategy_type == 2:
        num_teams = 3
        intro = """⚔️ **Strategy 2: 3 Teams**
"""
        outro = """
We split into 3 teams:

Team 1 - You plunder the buildings that are NOT hospitals. Your job is to capture and defend the buildings throughout the game. Have an equal split defending each building.

Team 2 - Your job is to defend the hospitals on OUR side of the map, even split 3/3 and +1 to defend each hospital.

Team 3 - First 10min : 2 on Enemy Hospital North, 2 on Enemy Hospital South. And the last 2 aid in defending our hospitals if they are under pressure. One to each hospital to burn any attackers.

When the time hits 10 min, one of Team Gamma hold the Nuclear plant (central building) / Another one holds the northern central building and last one holds the southern. 
If one of our hospitals is under attack and the team there is struggling, 1 will stay to defend / assist in capturing back our hospitals, and the last 2 of team Gamma will try to keep the enemy hospital.

For the substitutes (those who can join only if there is space: 20 people maximum in the battlefield)
You risk being called at any time if someone from the participants cannot be present and if those present have no longer soldiers and can't fight so please stay tuned and ready to join the battlefield at any time (even at the start).
"""

        team_groups = [[] for _ in range(num_teams)]
        
        if num_players >= 6:
            top_3 = team_players_sorted[:3]
            bottom_3 = team_players_sorted[-3:]
            rest = team_players_sorted[3:-3]

            team_groups[2].extend(top_3 + bottom_3)

            # Balance the remaining between Team 1 and 2
            team_strengths = [0, 0]
            for player in rest:
                idx = team_strengths.index(min(team_strengths))
                team_groups[idx].append(player)
                team_strengths[idx] += player[1]
        else:
            # If there are less than 6 players, just distribute them evenly
            team_strengths = [0, 0, 0]
            for player in team_players_sorted:
                idx = team_strengths.index(min(team_strengths))
                team_groups[idx].append(player)
                team_strengths[idx] += player[1]

    elif strategy_type == 3:
        num_teams = 10
        intro = """⚔️ **Strategy 3: ALL buildings: in DUO**
"""
        outro = """
"""
        team_groups = [[] for _ in range(num_teams)]

        top_4 = team_players_sorted[:4]
        next_8 = team_players_sorted[4:12]
        rest = team_players_sorted[12:]

        # Team 5 & 6
        team_groups[4].extend(top_4[:2])  # Team 5
        team_groups[5].extend(top_4[2:])  # Team 6

        # Team 1,2,9,10
        positions_1_2_9_10 = [0, 1, 8, 9]
        for i, player in enumerate(next_8):
            team_groups[positions_1_2_9_10[i % 4]].append(player)

        # Remaining → Team 3,4,7,8
        positions_3_4_7_8 = [2, 3, 6, 7]
        for i, player in enumerate(rest):
            team_groups[positions_3_4_7_8[i % 4]].append(player)

    elif strategy_type == 4:
        num_teams = 10
        intro = """⚔️ **Strategy 4: 10 Teams**
We will be divided into 10 teams

🧭 **Teams Distribution**
Team 1 - Hospital 1
Team 2 - Hospital 2
Team 3 - Info Center
Team 4 - Science Hub
Team 5 - Nuclear Silo (free movement to help)
Team 6 -  Mercenary Factory/ Arsenal (free movement to help)
Team 7 - Oil Refinery I
Team 8 - Oil Refinery II
Team 9 - Hospital 3
Team 10 - Hospital 4
"""
        outro = """
"""
        team_groups = [[] for _ in range(num_teams)]

        # Step 1: Най-силните 4 играча → балансирано в отбори 5 и 6
        top_4 = team_players_sorted[:4]
        team_5_6 = [[], []]
        strengths_5_6 = [0, 0]
        for player in top_4:
            idx = strengths_5_6.index(min(strengths_5_6))
            team_5_6[idx].append(player)
            strengths_5_6[idx] += player[1]
        team_groups[4].extend(team_5_6[0])  # Team 5
        team_groups[5].extend(team_5_6[1])  # Team 6

        # Step 2: Следващите двама най-силни → отбор 3 и 4
        if len(team_players_sorted) >= 6:
            team_groups[2].append(team_players_sorted[4])  # Team 3
            team_groups[3].append(team_players_sorted[5])  # Team 4

        # Step 3: Следващи 12 играча → 4 отбора с по 3 човека (1, 2, 9, 10)
        remaining_players = team_players_sorted[6:]
        team_ids_balanced = [0, 1, 8, 9]
        team_balances = [[], [], [], []]
        team_strengths = [0] * 4
        for player in remaining_players[:12]:
            idx = team_strengths.index(min(team_strengths))
            team_balances[idx].append(player)
            team_strengths[idx] += player[1]
        for i, team in enumerate(team_balances):
            team_groups[team_ids_balanced[i]].extend(team)

        # Step 4: Последните 2 играча → отбори 7 и 8
        for i, player in enumerate(remaining_players[12:14]):
            team_groups[6 + i].append(player)
    else:
        return "Invalid strategy type."

    # 📝 Генериране на текста
    strategy_text = f"{intro}\n"
    strategy_text += "\n📋 **Substitutes** (in case someone can't play):\n"
    strategy_text += "➤ " + ' / '.join([sub[0] for sub in substitutes]) + "\n" if substitutes else "None.\n"
    strategy_text += "\n🛡️ **Teams**\n"

    for i, group in enumerate(team_groups, 1):
        group_sorted = sorted(group, key=lambda x: x[1], reverse=True)
        members = ' / '.join([f'{name} ({strength})' for name, strength in group_sorted])
        strategy_text += f"Team {i}: {members}\n"

    strategy_text += f"\n{outro}"
    return strategy_text

def generate_strategy_groups(team_players, strategy_type):
    team_players_sorted = sorted(team_players, key=lambda x: x[1], reverse=True)
    num_players = len(team_players_sorted)

    if strategy_type == 1:
        num_teams = 4
        team_groups = [[] for _ in range(num_teams)]
        team_strengths = [0] * num_teams
        for player in team_players_sorted:
            idx = team_strengths.index(min(team_strengths))
            team_groups[idx].append(player)
            team_strengths[idx] += player[1]

    elif strategy_type == 2:
        num_teams = 3
        team_groups = [[] for _ in range(num_teams)]
        if num_players >= 6:
            top_3 = team_players_sorted[:3]
            bottom_3 = team_players_sorted[-3:]
            rest = team_players_sorted[3:-3]
            team_groups[2].extend(top_3 + bottom_3)
            team_strengths = [0, 0]
            for player in rest:
                idx = team_strengths.index(min(team_strengths))
                team_groups[idx].append(player)
                team_strengths[idx] += player[1]
        else:
            team_strengths = [0, 0, 0]
            for player in team_players_sorted:
                idx = team_strengths.index(min(team_strengths))
                team_groups[idx].append(player)
                team_strengths[idx] += player[1]

    elif strategy_type == 3 or strategy_type == 4:
        num_teams = 10
        team_groups = [[] for _ in range(num_teams)]
        top_4 = team_players_sorted[:4]
        team_groups[4].extend(top_4[:2])
        team_groups[5].extend(top_4[2:])

        if strategy_type == 3:
            next_8 = team_players_sorted[4:12]
            rest = team_players_sorted[12:]
            positions_1_2_9_10 = [0, 1, 8, 9]
            for i, player in enumerate(next_8):
                team_groups[positions_1_2_9_10[i % 4]].append(player)
            positions_3_4_7_8 = [2, 3, 6, 7]
            for i, player in enumerate(rest):
                team_groups[positions_3_4_7_8[i % 4]].append(player)
        else:
            if len(team_players_sorted) >= 6:
                team_groups[2].append(team_players_sorted[4])
                team_groups[3].append(team_players_sorted[5])
            remaining_players = team_players_sorted[6:]
            team_ids_balanced = [0, 1, 8, 9]
            team_balances = [[] for _ in range(4)]
            team_strengths = [0] * 4
            for player in remaining_players[:12]:
                idx = team_strengths.index(min(team_strengths))
                team_balances[idx].append(player)
                team_strengths[idx] += player[1]
            for i, team in enumerate(team_balances):
                team_groups[team_ids_balanced[i]].extend(team)
            for i, player in enumerate(remaining_players[12:14]):
                team_groups[6 + i].append(player)

    return team_groups

def render_strategy_from_groups(strategy_type, team_name, team_groups, subs):
    intro_texts = {
        1: """⚔️ **Strategy 1: Only Hospitals**
For the substitutes (those who can join only if there is space: 20 people maximum in the battlefield)
You risk being called at any time if someone from the participants cannot be present and if those present have no longer soldiers and can't fight so please stay tuned and ready to join the battle field at any time (even at the start). 
🧭 **Hospital Distribution**
Team 1 → OUR North Hospital  
Team 2 → OUR South Hospital  
Team 3 → ENEMY North Hospital  
Team 4 → ENEMY South Hospital

Please join the battlefield 5 minutes before the start. Stay with your team and follow your leaders.""",

        2: """⚔️ **Strategy 2: 3 Teams**
Team 1 - Non-hospital buildings (plunder/defend)  
Team 2 - Defend OUR hospitals  
Team 3 - Attack ENEMY hospitals, then central buildings after 10 min""",

        3: """⚔️ **Strategy 3: 10 Squads**

""",

        4: """⚔️ **Strategy 4: 10 Teams**
Same as Strategy 3 with different distribution priorities."""
    }

    strategy_text = f"{intro_texts.get(strategy_type, '')}\n\n"

    # Substitutes
    strategy_text += "📋 **Substitutes** (in case someone can't play):\n"
    strategy_text += "➤ " + ' / '.join([sub[0] for sub in subs]) + "\n\n" if subs else "None\n\n"

    # Teams
    strategy_text += f"🛡️ **{team_name} Teams**\n"
    for i, team in enumerate(team_groups, 1):
        if not team:
            strategy_text += f"Team {i}: _empty_\n"
        else:
            players = " / ".join(f"{name} ({strength:.2f})" for name, strength in team)
            strategy_text += f"Team {i}: {players}\n"

    return strategy_text

# Генериране на стратегия
@bot.command()
async def strategy1a(ctx):
    data = convert_players_to_tuples(load_data())
    key = "1a"
    groups = generate_strategy_groups(data["team_a"], 1)
    strategy_text = generate_strategy("Team A", data["team_a"], data["sub_a"], 1)
    current_strategies[key] = groups
    original_strategies[key] = [list(team) for team in groups]
    current_subs[key] = data["sub_a"]

    save_strategies({
        key: {
            "current": current_strategies[key],
            "original": original_strategies[key],
            "subs": current_subs[key]
        } for key in current_strategies
    })

    await ctx.send(strategy_text)

@bot.command()
async def strategy2a(ctx):
    data = convert_players_to_tuples(load_data())
    key = "2a"
    groups = generate_strategy_groups(data["team_a"], 2)
    strategy_text = generate_strategy("Team A", data["team_a"], data["sub_a"], 2)
    current_strategies[key] = groups
    original_strategies[key] = [list(team) for team in groups]
    current_subs[key] = data["sub_a"]

    save_strategies({
        key: {
            "current": current_strategies[key],
            "original": original_strategies[key],
            "subs": current_subs[key]
        } for key in current_strategies
    })

    await ctx.send(strategy_text)

@bot.command()
async def strategy3a(ctx):
    data = convert_players_to_tuples(load_data())
    key = "3a"
    groups = generate_strategy_groups(data["team_a"], 3)
    strategy_text = generate_strategy("Team A", data["team_a"], data["sub_a"], 3)
    current_strategies[key] = groups
    original_strategies[key] = [list(team) for team in groups]
    current_subs[key] = data["sub_a"]

    save_strategies({
        key: {
            "current": current_strategies[key],
            "original": original_strategies[key],
            "subs": current_subs[key]
        } for key in current_strategies
    })

    await ctx.send(strategy_text)

@bot.command()
async def strategy4a(ctx):
    data = convert_players_to_tuples(load_data())
    key = "4a"
    groups = generate_strategy_groups(data["team_a"], 4)
    strategy_text = generate_strategy("Team A", data["team_a"], data["sub_a"], 4)
    current_strategies[key] = groups
    original_strategies[key] = [list(team) for team in groups]
    current_subs[key] = data["sub_a"]

    save_strategies({
        key: {
            "current": current_strategies[key],
            "original": original_strategies[key],
            "subs": current_subs[key]
        } for key in current_strategies
    })

    await ctx.send(strategy_text)

@bot.command()
async def strategy1b(ctx):
    data = convert_players_to_tuples(load_data())
    key = "1b"
    groups = generate_strategy_groups(data["team_b"], 1)
    strategy_text = generate_strategy("Team B", data["team_b"], data["sub_b"], 1)
    current_strategies[key] = groups
    original_strategies[key] = [list(team) for team in groups]
    current_subs[key] = data["sub_b"]

    save_strategies({
        key: {
            "current": current_strategies[key],
            "original": original_strategies[key],
            "subs": current_subs[key]
        } for key in current_strategies
    })

    await ctx.send(strategy_text)

@bot.command()
async def strategy2b(ctx):
    data = convert_players_to_tuples(load_data())
    key = "2b"
    groups = generate_strategy_groups(data["team_b"], 2)
    strategy_text = generate_strategy("Team B", data["team_b"], data["sub_b"], 2)
    current_strategies[key] = groups
    original_strategies[key] = [list(team) for team in groups]
    current_subs[key] = data["sub_b"]

    save_strategies({
        key: {
            "current": current_strategies[key],
            "original": original_strategies[key],
            "subs": current_subs[key]
        } for key in current_strategies
    })

    await ctx.send(strategy_text)

@bot.command()
async def strategy3b(ctx):
    data = convert_players_to_tuples(load_data())
    key = "3b"
    groups = generate_strategy_groups(data["team_b"], 3)
    strategy_text = generate_strategy("Team B", data["team_b"], data["sub_b"], 3)
    current_strategies[key] = groups
    original_strategies[key] = [list(team) for team in groups]
    current_subs[key] = data["sub_b"]

    save_strategies({
        key: {
            "current": current_strategies[key],
            "original": original_strategies[key],
            "subs": current_subs[key]
        } for key in current_strategies
    })

    await ctx.send(strategy_text)

@bot.command()
async def strategy4b(ctx):
    data = convert_players_to_tuples(load_data())
    key = "4b"
    groups = generate_strategy_groups(data["team_b"], 4)
    strategy_text = generate_strategy("Team B", data["team_b"], data["sub_b"], 4)
    current_strategies[key] = groups
    original_strategies[key] = [list(team) for team in groups]
    current_subs[key] = data["sub_b"]

    save_strategies({
        key: {
            "current": current_strategies[key],
            "original": original_strategies[key],
            "subs": current_subs[key]
        } for key in current_strategies
    })

    await ctx.send(strategy_text)

@bot.command()
async def clear(ctx):
    # Проверка дали потребителят има роля R4 или R5
    if not any(role.name in ["R4", "R5"] for role in ctx.author.roles):
        await ctx.send("You do not have the required role to use this command.")
        return
    
    # Зареждаме данните
    data = convert_players_to_tuples(load_data())

    # Изчистваме всички играчи от всички отбори и резерви
    data["team_a"] = []
    data["team_b"] = []
    data["sub_a"] = []
    data["sub_b"] = []
    
    # Изчистваме списъка с неразпределените играчи
    data["unassigned"] = []  # Това е правилният ключ според текущия код

    # Записваме промените в JSON файла
    save_data(data)

    for key in current_strategies:
        current_strategies[key] = []
        original_strategies[key] = []
        current_subs[key] = []
    save_strategies({})    

    await ctx.send("All players have been cleared.")

@bot.command()
async def count(ctx):
    data = load_data()

    total_signed = sum(len(data.get(key, [])) for key in [
        "team_a", "team_b", "sub_a", "sub_b", "unassigned"
    ])

    max_slots = data.get("max_players", 60)  # или твърдо число

    await ctx.send(f"👥 People sign in: {total_signed}/{max_slots}")

def swap_players(strategy_key, name1, name2):
    teams = current_strategies.get(strategy_key, [])
    found1 = found2 = False
    for team in teams:
        for i, player in enumerate(team):
            if player[0].lower() == name1.lower():
                team1, idx1 = team, i
                found1 = True
            elif player[0].lower() == name2.lower():
                team2, idx2 = team, i
                found2 = True
    if found1 and found2:
        team1[idx1], team2[idx2] = team2[idx2], team1[idx1]
        return True
    return False

@bot.command()
async def info(ctx):
    help_text = """
📘 **Available Commands (R1/R2/R3)**

`!join <name> <power>` – Register a player  
`!update <name> <new_power>` – Update your power  
`!count` – Show how many people have registered  
"""
    await ctx.send(help_text)

@bot.command()
async def rmenu(ctx):
    if not any(role.name in ["R4", "R5"] for role in ctx.author.roles):
        await ctx.send("❌ You don't have access to moderator commands.")
        return

    mod_text = """
🛠️ **Moderator Commands (R4/R5 only)**

**Player Management**
`!start` / `!end` – Open/close registration  
`!balance` – Auto balance all players  
`!move <team> <name>` – Move player manually  
`!remove <name>` – Remove player  
`!clear` – Clear everything

**Strategy Management**
`!strategy1a` to `!strategy4b` – Generate strategy  
`!swap3a <p1> <p2>` / `!reset3a` / `!show3a` – Swap, reset or view  
`!text3` – Show first part of the in game mail for strategy 3  
`!text3a` – Show second part of the in game mail for strategy 3 Team A
`!text3b` – Show second part of the in game mail for strategy 3 Team B
`!i` – Setup Teams and Strategies

**Note System**
`!note <text>` – Add internal note  
`!notes` – View notes  
`!clearnotes` – Clear notes  
"""
    await ctx.send(mod_text)

def swap_players(strategy_key, name1, name2):
    teams = current_strategies.get(strategy_key, [])
    found1 = found2 = False
    for team in teams:
        for i, player in enumerate(team):
            if player[0].lower() == name1.lower():
                team1, idx1 = team, i
                found1 = True
            elif player[0].lower() == name2.lower():
                team2, idx2 = team, i
                found2 = True
    if found1 and found2:
        team1[idx1], team2[idx2] = team2[idx2], team1[idx1]
        return True
    return False

def create_strategy_commands(key):
    # Команда за swap
    @bot.command(name="swap" + key)
    async def _swap(ctx, name1: str, name2: str):
        if not any(role.name in ["R4", "R5"] for role in ctx.author.roles):
            await ctx.send("You do not have the required role to use this command.")
            return

        if swap_players(key, name1, name2):
            save_strategies({
                key: {
                    "current": current_strategies[key],
                    "original": original_strategies[key],
                    "subs": current_subs[key]
                } for key in current_strategies
            })
            await ctx.send(f"🔁 Swapped {name1} and {name2} in strategy {key.upper()}")
        else:
            await ctx.send("⚠️ One or both players not found in strategy.")

    # Команда за reset
    @bot.command(name="reset" + key)
    async def _reset(ctx):
        if not any(role.name in ["R4", "R5"] for role in ctx.author.roles):
            await ctx.send("You do not have the required role to use this command.")
            return

        current_strategies[key] = [list(team) for team in original_strategies[key]]

        save_strategies({
            key: {
                "current": current_strategies[key],
                "original": original_strategies[key],
                "subs": current_subs[key]
            } for key in current_strategies
        })

        await ctx.send(f"🔄 Strategy {key.upper()} has been reset.")

    # Команда за show
    @bot.command(name="show" + key)
    async def _show(ctx):
        if not any(role.name in ["R4", "R5"] for role in ctx.author.roles):
            await ctx.send("You do not have the required role to use this command.")
            return

        strategy_type = int(key[0])
        team_name = "Team A" if key[1] == "a" else "Team B"
        groups = current_strategies[key]
        subs = current_subs[key]

        strategy_text = render_strategy_from_groups(strategy_type, team_name, groups, subs)
        await ctx.send(strategy_text)

@bot.command()
async def crossswap3(ctx, name1: str, name2: str):
    if not any(role.name in ["R4", "R5"] for role in ctx.author.roles):
        await ctx.send("You do not have the required role to use this command.")
        return

    key_a = "3a"
    key_b = "3b"
    team1_found = team2_found = False

    for team in current_strategies[key_a]:
        for i, player in enumerate(team):
            if player[0].lower() == name1.lower():
                team1 = team
                idx1 = i
                team1_found = True
                break
    for team in current_strategies[key_b]:
        for i, player in enumerate(team):
            if player[0].lower() == name2.lower():
                team2 = team
                idx2 = i
                team2_found = True
                break

    if team1_found and team2_found:
        # Размяна
        team1[idx1], team2[idx2] = team2[idx2], team1[idx1]

        # Записване
        save_strategies({
            key: {
                "current": current_strategies[key],
                "original": original_strategies[key],
                "subs": current_subs[key]
            } for key in current_strategies
        })

        await ctx.send(f"🔁 Swapped **{name1}** (3A) with **{name2}** (3B).")
    else:
        await ctx.send("⚠️ One or both players not found in strategy 3a or 3b.")

@bot.command()
async def text3a(ctx):
    if not any(role.name in ["R4", "R5"] for role in ctx.author.roles):
        await ctx.send("❌ You do not have the required role.")
        return

    key = "3a"
    groups = current_strategies.get(key, [])
    subs = current_subs.get(key, [])

    if not groups:
        await ctx.send("⚠️ Strategy 3A has not been generated yet. Please use !strategy3a first.")
        return

    message = (
        "For the substitutes (those who can join only if there is space: 20 people maximum in the battlefield)\n"
        "You risk being called at any time if someone from the participants cannot be present and if those present have no longer soldiers and can't fight so please stay tuned and ready to join the battle field at any time (even at the start).\n\n"
        "🗒️**Substitutes (in case someone can't play):**\n"
    )

    if subs:
        message += "➤ " + ' / '.join(name for name, _ in subs) + "\n\n"
    else:
        message += "_No substitutes assigned._\n\n"

    message += (
        "‼️ In this strategy you are a duo: 2 people by team: So STAY with your partner! "
        "If he left or didn't join the battlefield ask for a sub to join and stick TOGETHER AT ALL COST: i will look at you if you don't 😉\n\n"
        "Participants will be divided into 10 teams: for the 8 buildings available at the beginning of the game and after 10 min the 3 central buildings. "
        "We will have 2 \"floating\" teams (our strongest players) during the first 10 minutes of the battle.\n\n"
        "🛡️**Teams:**\n"
    )

    for i, team in enumerate(groups, 1):
        if not team:
            message += f"Team {i}: _empty_\n"
        else:
            members = " / ".join(name for name, _ in team)
            message += f"Team {i}: {members}\n"

    message += (
        "\n🌟please let me know if you read that mail by pressing the heart 🌟\n"
        "Thanks for reading that mail, and please don't hesitate and ask if you have any question💙"
    )

    await ctx.send(message)


@bot.command()
async def text3b(ctx):
    if not any(role.name in ["R4", "R5"] for role in ctx.author.roles):
        await ctx.send("❌ You do not have the required role.")
        return

    key = "3b"
    groups = current_strategies.get(key, [])
    subs = current_subs.get(key, [])

    if not groups:
        await ctx.send("⚠️ Strategy 3B has not been generated yet. Please use !strategy3b first.")
        return

    message = (
        "For the substitutes (those who can join only if there is space: 20 people maximum in the battlefield)\n"
        "You risk being called at any time if someone from the participants cannot be present and if those present have no longer soldiers and can't fight so please stay tuned and ready to join the battle field at any time (even at the start).\n\n"
        "🗒️**Substitutes (in case someone can't play):**\n"
    )

    if subs:
        message += "➤ " + ' / '.join(name for name, _ in subs) + "\n\n"
    else:
        message += "_No substitutes assigned._\n\n"

    message += (
        "‼️ In this strategy you are a duo: 2 people by team: So STAY with your partner! "
        "If he left or didn't join the battlefield ask for a sub to join and stick TOGETHER AT ALL COST: i will look at you if you don't 😉\n\n"
        "Participants will be divided into 10 teams: for the 8 buildings available at the beginning of the game and after 10 min the 3 central buildings. "
        "We will have 2 \"floating\" teams (our strongest players) during the first 10 minutes of the battle.\n\n"
        "🛡️**Teams:**\n"
    )

    for i, team in enumerate(groups, 1):
        if not team:
            message += f"Team {i}: _empty_\n"
        else:
            members = " / ".join(name for name, _ in team)
            message += f"Team {i}: {members}\n"

    message += (
        "\n🌟please let me know if you read that mail by pressing the heart 🌟\n"
        "Thanks for reading that mail, and please don't hesitate and ask if you have any question💙"
    )

    await ctx.send(message)

@bot.command()
async def text3(ctx):
    if not any(role.name in ["R4", "R5"] for role in ctx.author.roles):
        await ctx.send("You do not have the required role to use this command.")
        return

    message = (
        "**Hello all!**\n"
        "DS will start at **06:00pm (18:00)** Server time (you can join 5min before the start).\n"
        "In the meantime, I ask all the people who are not participating **to not talk in the alliance chat**, and **not to dig**.\n"
        "Even if we have an event chat for the communication and we will be in a Discord vocal (you can join even if it's only to listen).\n\n"
        "‼️ In both teams you have one **strategist**; his messages are the most important:\n"
        "please read it! Or come in the Discord call to get it faster, but **focus only on his message and the one from your partner!**\n\n"
        "**Strategist**\n"
        "Team A: Snowdreil / Erido / SnowmAndy\n"
        "Team B: AngelDevilorigin / INIv\n\n"
        "**Strategy 3: ALL buildings: in DUO**\n\n"
        "🧭 **Teams Distribution**\n"
        "Team 1 - Hospital 1\n"
        "Team 2 - Hospital 2\n"
        "Team 3 - Info Center\n"
        "Team 4 - Science Hub\n"
        "Team 5 - Nuclear Silo\n"
        "Team 6 - Arsenal\n"
        "Team 7 - Oil Refinery I\n"
        "Team 8 - Oil Refinery II\n"
        "Team 9 - Hospital 3\n"
        "Team 10 - Hospital 4\n\n"
    )

    await ctx.send(message)

@bot.command()
async def i(ctx):
    if not any(role.name in ["R4", "R5"] for role in ctx.author.roles):
        await ctx.send("❌ You don't have permission to use this command.")
        return

    info_text = """
📌 **Strategy Setup Commands (R4/R5 only)**

`!strategy1a` to `!strategy4b` – Generate teams (A or B) for selected strategy  
`!swap1a` to `!swap4b` <name1> <name2> – Swap two players in current strategy  
`!reset1a` to `!reset4b` – Reset strategy to original version  
`!show1a` to `!show4b` – Show current team distribution  
`!text3` – Send full message for in-game mail (Strategy 3)  
`!crossswap3 <name1> <name2>` – Swap players between Strategy 3A and 3B
"""
    await ctx.send(info_text)


    @bot.command(name="sub" + key)
    async def _subs(ctx):
        subs = current_subs[key]
        if not subs:
            await ctx.send(f"📋 No substitutes assigned for Strategy {key.upper()}.")
        else:
            subs_text = "\n".join([f"• {name} ({strength:.2f})" for name, strength in subs])
            await ctx.send(f"📋 Substitutes for Strategy {key.upper()}:\n{subs_text}")

for key in current_strategies.keys():
    create_strategy_commands(key)

# Стартиране на бота
bot.run(TOKEN)
