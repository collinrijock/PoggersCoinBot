#!/usr/bin/python3.8
import os
import json
import random
import csv
import time
import typing
import discord
from discord.ext import commands
from discord.utils import get


bot = commands.Bot(command_prefix='=')

class PhraseGenerator:
    def __init__(self, filename):
        verbs = []
        nouns = []
        subjects = []
        words_list = [verbs, nouns, subjects]
        with open(filename, 'r') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                for i in range(3):
                    if (word := row[i]):
                        words_list[i].append(word)
        self.verbs = verbs
        self.nouns = nouns
        self.subjects = subjects

    def _get_verb(self) -> str:
        return random.choice(self.verbs)

    def _get_noun(self) -> str:
        return random.choice(self.nouns)

    def _get_subject(self) -> str:
        return random.choice(self.subjects)

    def generate(self) -> str:
        calls = [self.generate_original, self.generate_alt, self.generate_war]
        method = random.choice(calls)
        return method()

    def generate_original(self) -> str:
        verb = self._get_verb()
        noun = self._get_noun()
        subject = self._get_subject()
        return f"I will {verb} {subject}'s {noun}"

    def generate_alt(self) -> str:
        verb = self._get_verb()
        noun = self._get_noun()
        subject = self._get_subject()
        return f"hey {subject} i can't wait to {verb} your {noun}"

    def generate_war(self) -> str:
        verb = self._get_verb()
        noun = self._get_noun()
        subject = self._get_subject()
        war = self._get_war_name()
        return f"hey {subject} did you know that they used to {verb} {noun} during the {war}"

    def _get_war_name(self) -> str:
        wars = ["Boxer Rebellion",
        "Boer War",
        "Russo-Japanese War",
        "Mexican Revolution",
        "First and Second Balkan Wars",
        "World War I",
        "Armenian Genocide",
        "Russian Revolution",
        "Russian Civil War",
        "Irish War of Independence",
        "Holocaust",
        "Second Italo-Abyssinian War",
        "Spanish Civil War",
        "World War II",
        "Cold War",
        "Chinese Civil War",
        "First Indochina War",
        "Israel War of Independence",
        "Korean War",
        "French-Algerian War",
        "First Sudanese Civil War",
        "Suez Crisis",
        "Cuban Revolution",
        "Vietnam War",
        "Six-Day War",
        "Soviet-Afghan War",
        "Iran-Iraq War",
        "Persian Gulf War",
        "Third Balkan War",
        "Rwandan Genocide",
        ]
        return random.choice(wars)



# make the filestorage
coin_filename = 'out_file.json'
event_filename = 'event_file.json'
blacklist_filename = "blacklist.txt"
black_list = None

@bot.event
async def on_ready():
    print("bot online")

async def write_json(data, filename=coin_filename):
    with open(filename, 'w') as f:
        json.dump(data, f)

async def get_json(filename):
    with open(filename, 'r') as f:
        data = json.load(f)
    return data

async def bet_coins(author, coins, for_win):
    data = await get_json(coin_filename)
    if not author.id in data:
        await deposit_coins(author, 10)
    await add_player_to_event(author, for_win, coins)
    new_coins = data[author.id]['coins'] - coins
    data[author.id]['coins'] = new_coins
    await write_json(data, filename=coin_filename)
    return new_coins

async def add_player_to_event(name, for_win, coins):
    event = await get_json(event_filename)
    data = {'name': name, 'for_win': for_win, 'bet': coins}
    event['players'].append(data)
    await write_json(event, event_filename)

async def deposit_coins(author_id, coins):
    data = await get_json(coin_filename)
    data[author_id] = {
            'coins': coins,
            'daily_pog': True,
            'daily_antipog': True
            }
    await write_json(data, filename=coin_filename)

async def start_event(odds, author):
    event = {'odds': odds, 'author': author, 'players': [], 'done': False}
    await write_json(event, event_filename)

async def end_event(author, win):
    event = await get_json(event_filename)
    payouts = {}
    for player in event['players']:
        name = player['name']
        if player['for_win'] == win:
            payouts[name] = player['bet'] * event['odds']
    event['done'] = True
    await write_json(event, event_filename)
    return await make_payouts(payouts)

async def make_payouts(payouts):
    purse = await get_json(coin_filename)
    top_amount = 0
    top_name = None
    for player, amount in payouts.items():
        purse[player] += amount
        if top_amount < amount:
            top_name = player
            top_amount = amount
    return F"The top winner is: {top_name}! Winning a total of {top_amount} PoggersCoins"

async def is_event_finished():
    try:
        event = await get_json(event_filename)
        return event['done']
    except:
        return True

@bot.command()
async def start(ctx, odds):
    try:
        author = ctx.message.author
        await start_event(odds, author)
        await ctx.send("Event created and is active")
    except Exception as e:
        print(e)
        return

@bot.command()
async def end(ctx, win):
    try:
        author = ctx.message.author
        try:
            win = True if win.lower() == 'win' else False
        except:
            await ctx.send("ERROR!: the command needs to have the win status for the event (\"win\" or \"loss\")")
            return
        response = await end_event(author, win)
        await ctx.send(response)
        return
    except Exception as e:
        print(e)
        return

@bot.command()
async def bet(ctx, arg, arg2):
    """
    Bet coins from your PoggersPurse on the event
    """
    if await is_event_finished():
        await ctx.send("ERROR!: There are no ongoing events")
        return
    try:
        author = ctx.message.author
        coins = int(arg)
        for_win = True if arg2 == 'win' else False
        assert 0 < coins <= 50000
        balance = await bet_coins(author, coins, for_win)
        await ctx.send(F"{author.name} bet {coins} coins. New balance for account is: {balance}")
    except Exception as e:
        print(e)
        return

@bot.command()
async def bal(ctx):
    data = await get_json(coin_filename)
    author = ctx.message.author
    if ctx.message.mentions:
        author = ctx.message.mentions[0]
        print(ctx.message.mentions[0].id)

    if not str(author.id) in data:
        await deposit_coins(author.id, 10)
        data = await get_json(coin_filename)

    guild = ctx.message.guild
    emoji = get(guild.emojis, name='poggers')
    balance = data[str(author.id)]['coins']
    if author.nick:
        await ctx.message.channel.send(f"{author.nick} has {balance} {emoji}")
    else:
        await ctx.message.channel.send(f"{author.name} has {balance} {emoji}")
    return

#On message, 1/20 chance of gaining 1 pog

async def check_author_meets_coin_cutoff(author, cutoff):
    """
    Returns true if author has enough balance
    to meet the cutoff, else false
    """
    balance = await get_author_balance(author)
    return balance >= cutoff

async def get_author_balance(author):
    data = await get_json(coin_filename)
    balance = data[str(author.id)]['coins']
    return balance

@bot.command()
async def blacklist(ctx, blacklist_token):
    author = ctx.message.author
    cutoff = 1
    if not await check_author_meets_coin_cutoff(author, cutoff):
        balance = await get_author_balance(author)
        await ctx.message.channel.send(f"@{author.nick} not enough balance. (Needs {cutoff} has {balance})")
    else:
        await add_token_to_song_blacklist(blacklist_token)
        await subtract_from_balance(author, 1)
        balance = await get_author_balance(author)
        await ctx.message.channel.send(f"added {blacklist_token} to blacklist. new balance for {author.nick} is: {balance}")

async def add_token_to_song_blacklist(blacklist_token):
    global black_list
    black_list = None
    with open(blacklist_filename, 'w') as f:
        f.write(blacklist_token + "\n")

async def subtract_from_balance(author, amount):
    data = await get_json(coin_filename)
    new_balance = max(data[str(author.id)]['coins'] - amount, 0)
    data[str(author.id)]['coins'] = new_balance
    write_json(data)

async def message_is_blacklisted(message):
    if not message.embeds:
        return
    message_content = message.embeds[0].to_dict()["description"].lower()
    global black_list
    if not black_list:
        with open(blacklist_filename, 'r') as f:
            black_list = f.readlines()
    for word in black_list:
        trim_word = word.replace("\n", "")
        if trim_word.lower() in message_content:
            return True
    return False


@bot.event
async def on_message(message):
    if message.author.bot and await message_is_blacklisted(message):
        time.sleep(0.5)
        await message.channel.send("-skip")
        return

    random_chance = random.random() < (1 / 500)
    if random_chance:

        if message.author.bot:
            return

        #Pog emote reaction
        guild = message.guild
        emoji = get(guild.emojis, name='poggers')
        await message.add_reaction(emoji)

        author = message.author
        author_id = str(message.author.id)
        pog_gained = 1
        data = await get_json(coin_filename)

        if not author_id in data:
            await deposit_coins(author_id, 10)
            data = await get_json(coin_filename)

        new_coins = data[author_id]['coins'] + pog_gained
        data[author_id]['coins'] = new_coins
        await write_json(data, filename=coin_filename)

        if author.nick:
            await message.channel.send(f"{author.nick} now has {new_coins} {emoji}")
        else:
            await message.channel.send(f"{author.name} now has {new_coins} {emoji}")


        await bot.process_commands(message)
    else:
        await bot.process_commands(message)

csv_filename = "sheet.csv"
israel_generator = PhraseGenerator(csv_filename)

@bot.command()
async def israel_says(ctx):
    await ctx.message.channel.send(israel_generator.generate_original())

@bot.command()
async def israel_rand(ctx):
    await ctx.message.channel.send(israel_generator.generate())

@bot.command()
async def israel_war(ctx):
    await ctx.message.channel.send(israel_generator.generate_war())

# Pog ( Plus PoggersCoin to someone )
@bot.command()
async def pog(ctx, user_pogged,amount:typing.Optional[int]=1):

     amount = int(amount)
     if amount < 1:
         return
     data = await get_json(coin_filename)
     author = ctx.message.author
     author_id = str(author.id)
     user_pogged_id = ctx.message.mentions[0]
     # check users exist
     if not author in data:
         await deposit_coins(author_id, 10)
     if not target_user_id in data:
         await deposit_coins(target_user_id, 10)

     # make transaction
     user_balance = data[author_id]['coins']
     target_balance = data[target_user_id]['coins']
     if user_balance > amount:
         user_balance -= amount
         target_balance += amount
         data[author_id]['coins'] = user_balance
         data[target_user_id]['coins'] = user_balance

token = os.environ['DISCORD_BOT_TOKEN']
bot.run(token)

