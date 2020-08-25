import os
import json
import random
import time
import discord
from discord.ext import commands
from discord.utils import get


bot = commands.Bot(command_prefix='=')

# make the filestorage
coin_filename = 'out_file.json'
event_filename = 'event_file.json'

@bot.event
async def on_ready():
    print("bot online")

async def write_json(data, filename):
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
    await write_json(data, coin_filename)
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
    await write_json(data, coin_filename)

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

@bot.event
async def on_message(message):
    random_chance = random.random()
    if random_chance < 0.05:

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
        await write_json(data, coin_filename)

        if author.nick:
            await message.channel.send(f"{author.nick} now has {new_coins} {emoji}")
        else:
            await message.channel.send(f"{author.name} now has {new_coins} {emoji}")


        await bot.process_commands(message)
    else:
        await bot.process_commands(message)

# Pog ( Plus PoggersCoin to someone )
@bot.command()
async def pog(ctx, user_pogged,amount='1'):

     amount = int(amount)
     if amount < 1:
         return
     data = await get_json(coin_filename)
     author = ctx.message.author
     author_id = str(author.id)

     # validate target
     if ctx.message.guild.get_member(user_pogged):
         target_user_id = ctx.message.server.get_member(user_pogged).id
     else:
         return

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

