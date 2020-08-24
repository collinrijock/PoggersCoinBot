import os
import json
import discord
from discord.ext import commands

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
    if not author in data:
        await deposit_coins(author, 5000)
    await add_player_to_event(author, for_win, coins)
    new_coins = data[author]['coins'] - coins
    data[author]['coins'] = new_coins
    await write_json(data, coin_filename)
    return new_coins

async def add_player_to_event(name, for_win, coins):
    event = await get_json(event_filename)
    data = {'name': name, 'for_win': for_win, 'bet': coins}
    event['players'].append(data)
    await write_json(event, event_filename)

async def deposit_coins(author, coins):
    data = await get_json(coin_filename)
    data[author] = {
            'coins': coins,
            'misc': None
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
        author = ctx.message.author.name
        await start_event(odds, author)
        await ctx.send("Event created and is active")
    except Exception as e:
        print(e)
        return

@bot.command()
async def end(ctx, win):
    try:
        author = ctx.message.author.name
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
        author = ctx.message.author.nick
        coins = int(arg)
        for_win = True if arg2 == 'win' else False
        assert 0 < coins <= 50000
        balance = await bet_coins(author, coins, for_win)
        await ctx.send(F"{author} bet {coins} coins. New balance for account is: {balance}")
    except Exception as e:
        print(e)
        return

token = os.environ['DISCORD_BOT_TOKEN']
bot.run(token)
