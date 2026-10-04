import discord
from discord.ext import commands, tasks
import logging.handlers
from dotenv import load_dotenv
import os
import json
import datetime
from zoneinfo import ZoneInfo
from dateutil import parser

#Load env variables
load_dotenv()

#Discord linking
token = os.getenv('DISCORD_TOKEN')
channel_id = int(os.getenv('CHANNEL_ID'))

#Roles
turmy_id = os.getenv('TURMAC_ROLE_ID')
snowy_id = os.getenv('SNOWAGER_ROLE_ID')
obelisk_id = os.getenv('OBELISK_ROLE_ID')
soup_id = os.getenv('SOUP_FAE_ROLE_ID')

date_format = os.getenv('DATE_FORMAT')

#Handle logging 
handler = logging.handlers.TimedRotatingFileHandler(filename='discord.log', encoding='utf-8', when='D', interval=1, backupCount=3)

#timezone
pst = ZoneInfo("America/Los_Angeles")

snowy_times = [datetime.datetime(year=2000, month=1, day=1, hour=6+8*i, minute=0, tzinfo=pst).timetz() for i in range(3)]#"look at me i use list comprehension im so smart" eat shit asshole, fall off your horse

turmac_times = [datetime.datetime(year=2000, month=1, day=1, hour=0, minute=0, tzinfo=pst).timetz()] #just a placeholder i should make this run off of a file and the snowy times too tbh

# obelisk stuff
obelisk_seed_day = datetime.date(2026, 9, 2) #known obelisk deadline to make your picks
obelisk_battle_start = datetime.date(2026, 9, 3) #known obelisk deadline to start battles
obelisk_battle_deadline = datetime.date(2026, 9, 6) #known obelisk deadline to finish battles
obelisk_boon_deadline = datetime.date(2026, 9, 7) #known obelisk deadline to choose your boon
obelisk_pick_file = "obelisk_pick.json" #so the pick survives restarts

def load_obelisk_pick():
    try:
        with open(obelisk_pick_file, encoding="utf-8") as f:
            data = json.load(f)
        return data["pick"], data["user_id"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return "", 0

def save_obelisk_pick(pick, user_id):
    with open(obelisk_pick_file, "w", encoding="utf-8") as f:
        json.dump({"pick": pick, "user_id": user_id}, f)

current_obelisk_pick, current_obelisk_picker = load_obelisk_pick() #the faction the guild picked this round and the id of who picked it, cleared at the boon ping

# --------------- BOT STARTS HERE ---------------

#Set bots intents, what it's allowed to see
intents = discord.Intents.default()
intents.message_content = True

#Initialize bot
bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)

#this pops up when the bot starts, its neat
@bot.event
async def on_ready():
    print(f"Hiya! {bot.user.name}")
    for loop in (snowy_messages, turmy_messages, obelisk_messages, soup_messages):
        if not loop.is_running():
            loop.start()

    #channel = bot.get_channel(channel_id)
    #await channel.send("Hi guys, I'm online!")
    
#func to parse brownhownd times
def brown_to_time(datesString):
    
    datesList = [date for date in datesString.split("\n") if date]
    datesToReturn = []
    
    print(datesList)
    
    for date in datesList:

        if "Awake" in date: #kill "awake" times
            continue

        IsANewDate = False

        dateSplat = date.split(": ")

        if "or" not in dateSplat[0]:#this way the date is only overwritten if its new
            IsANewDate = True
            day = dateSplat[0] #just year, month and day data, no time

        if IsANewDate:#if its a new date, do the thing to the second element of dateSplat
            times = [i for i in dateSplat[1].strip(" NST").split(" ") if i not in ("or", "OR")] #readable code is for CHUMPS

        elif not IsANewDate:#if its not new, do the thing to the first element
            times = [i for i in dateSplat[0].strip(" NST").split(" ") if i not in ("or", "OR")]
        
        for time in times:
            dateandtime = day + " " + time

            dateobject = parser.parse(dateandtime)
            dateobject = dateobject.replace(tzinfo=pst)
            
            datesToReturn.append(dateobject)
            
    if datesToReturn: return datesToReturn
    else: return -1

def times_print(times):
    returned = ""
    for time in times:
        returned += "\n* "
        returned += time.strftime("%b-%d %H:%M")
        returned += ".\n"
    return returned

@bot.command(aliases=["tt"])
async def turmytimes(ctx, *, arg):

    global turmac_times

    turmac_times = brown_to_time(arg)
    turmy_messages.restart()
    print("New turmy times list: ", turmac_times)
    print("Printing current loop after changing times and restarting: ", turmy_messages.current_loop)
    channel = bot.get_channel(channel_id)
    
    embedding = discord.Embed(
    title="New Turmaculus Times Uploaded!", 
    url="https://www.neopets.com/~Brownhownd",
    description=f"new turmy times are the following:\n\n{times_print(turmac_times)}\n\nI'll format this nicer eventually, promise!",
    color=0x996699
    )
    embedding.set_image(url="https://images.neopets.com/new_shopkeepers/939.gif")
    
    await channel.send(embed=embedding)

@bot.command(aliases=["tw"])
async def turmywhen(command):
    await command.send(f"Hi There!\n\nThe Currently Stored Turmy Times Are:{times_print(turmac_times)}")

@bot.command(aliases=["turmy", "t"])
async def turmac(command):
    await command.send(f"Wow {command.author.mention}, you sure he's awake?\nOh well, not my problem\n<@&{int(turmy_id)}> !")

@bot.command(aliases=["i"])#oh gosh i sure am being nice with this one aw shucks aw hope they use it and that uhhhhhhhh they give me a quadrillion dallas texas cowboys
async def igloo(command):
    await command.send(f"Hi there {command.author.mention}!\nIgloo is here: https://www.neopets.com/winter/igloo.phtml?stock=1 :)")

@tasks.loop(time=datetime.time(hour=0, minute=0, tzinfo=pst))
async def soup_messages():
    channel = bot.get_channel(channel_id)
    
    embedding = discord.Embed(
    title="Soup Time Y'all! 🍲🥄", 
    url="https://www.neopets.com/soupkitchen.phtml", 
    description=f"Remember! Minimum of 25k if you're cheap like me :^)",
    color=0xffe92a
    )
    embedding.set_image(url="https://images.neopets.com/soupkitchen/images/soup-kitchen-banner.png")

    await channel.send(f"<@&{int(soup_id)}>", embed=embedding)


@tasks.loop(time=snowy_times)
async def snowy_messages():
    channel = bot.get_channel(channel_id)
    
    embedding = discord.Embed(
    title="The Snowager is Asleep! 🐍❄️", 
    url="https://www.neopets.com/winter/snowager.phtml", 
    description=f"Come get blasted everybody!!",
    color=0x009dff
    )
    embedding.set_image(url="https://images.neopets.com/winter/iceworm_sleep.gif")

    await channel.send(f"<@&{int(snowy_id)}>", embed=embedding)

@tasks.loop(time=turmac_times)
async def turmy_messages():

    global turmac_times

    channel = bot.get_channel(channel_id)    

    embedding = discord.Embed(
    title="The Turmaculus Could Be Asleep! ༘ 🦕𖦹⋆｡˚", 
    url="https://www.neopets.com/medieval/turmaculus.phtml", 
    description="NOW LISTEN HERE YOU ROLY POLY MOTHERFUCKER",
    color=0x996699
    )
    embedding.set_image(url="https://images.neopets.com/new_shopkeepers/939.gif")

    print("Pinging turmy role at what should be: ", turmac_times[0].strftime("%b-%d %H:%M"))
    print("The current time is actually: ", datetime.datetime.now(pst).strftime("%b-%d %H:%M"))
    print("The current turmy times list is: ", turmac_times)
    print("Printing current loop before changing times: ", turmy_messages.current_loop)

    turmac_times = [time for time in turmac_times if time > datetime.datetime.now(pst)] #i think this should work....? keeps only times bigger than now? eh i can just .tw to check, surely its fine :clueless:
    turmy_messages.restart()
    print("New turmy times list: ", turmac_times)
    print("Printing current loop after changing times and restarting: ", turmy_messages.current_loop)

    await channel.send(f"<@&{int(turmy_id)}>", embed=embedding)

# selector for pinging when the guild picks an obelisk faction
class SelectView(discord.ui.View):
    @discord.ui.select(
        placeholder="Who did the guild pick?",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="Awakened", description="Awakened"),
            discord.SelectOption(label="Brutes", description="Brute Squad"),
            discord.SelectOption(label="Order", description="Order of the Red Erisim"),
            discord.SelectOption(label="Seekers", description="Seekers"),
            discord.SelectOption(label="Sway", description="Sway"),
            discord.SelectOption(label="Thieves", description="Thieves Guild")
        ]
    )
    async def select_callback(self, interaction, select):
        global current_obelisk_pick, current_obelisk_picker

        current_obelisk_pick = select.values[0]
        current_obelisk_picker = interaction.user.id
        save_obelisk_pick(current_obelisk_pick, current_obelisk_picker)

        embedding = discord.Embed(
            title=f"The guild picked {current_obelisk_pick}!",
            url="https://www.neopets.com/prehistoric/battleground/",
            description=f"Picked by <@{current_obelisk_picker}>",
            color=0xf3f1d4
            )
        embedding.set_image(url="https://images.neopets.com/items/weap_shard_obelisk.gif")

        await interaction.response.send_message(f"<@&{int(obelisk_id)}>", embed=embedding)

class ChangePickView(discord.ui.View):
    @discord.ui.button(label="Change pick", style=discord.ButtonStyle.primary)
    async def change_callback(self, interaction, button):
        await interaction.response.send_message("Who did the guild pick?", view=SelectView(), ephemeral=True)

@bot.command(aliases=["obelisk"])
async def obelisk_pick(ctx):
    if current_obelisk_pick:
        await ctx.send(f"The guild's pick is **{current_obelisk_pick}**, picked by <@{current_obelisk_picker}>.", view=ChangePickView())
    else:
        await ctx.send("Who did the guild pick?", view=SelectView())

@tasks.loop(time=datetime.time(hour=0, minute=0, tzinfo=pst))
async def obelisk_messages():
    global current_obelisk_pick, current_obelisk_picker

    channel = bot.get_channel(channel_id)

    # pick faction
    if (datetime.datetime.now(pst).date() - obelisk_seed_day).days % 14 == 0:
        embedding = discord.Embed(
        title="Time to pick a faction!!", 
        url="https://www.neopets.com/prehistoric/battleground/", 
        description=f"Do we even know who the pick is <:Clueless:1534993720372625539>",
        color=0xf3f1d4
        )
        embedding.set_image(url="https://images.neopets.com/items/weap_shard_obelisk.gif")
    
        await channel.send(f"<@&{int(obelisk_id)}>",embed=embedding)
    # start battles
    elif (datetime.datetime.now(pst).date() - obelisk_battle_start).days % 14 == 0:
        embedding = discord.Embed(
        title="Time to battle!!", 
        url="https://www.neopets.com/prehistoric/battleground/", 
        description=f"You can start battling now!",
        color=0xf3f1d4
        )
        embedding.set_image(url="https://images.neopets.com/items/weap_shard_obelisk.gif")
    
        await channel.send(f"<@&{int(obelisk_id)}>",embed=embedding)
    # finish battles
    elif (datetime.datetime.now(pst).date() - obelisk_battle_deadline).days % 14 == 0:
        embedding = discord.Embed(
        title="Last day to battle!!", 
        url="https://www.neopets.com/prehistoric/battleground/", 
        description=f"Did you finish your battles? Last day!",
        color=0xf3f1d4
        )
        embedding.set_image(url="https://images.neopets.com/items/weap_shard_obelisk.gif")
    
        await channel.send(f"<@&{int(obelisk_id)}>",embed=embedding)
    # choose boon
    elif (datetime.datetime.now(pst).date() - obelisk_boon_deadline).days % 14 == 0:
        current_obelisk_pick, current_obelisk_picker = "", 0 # new round coming, clear the old pick
        save_obelisk_pick(current_obelisk_pick, current_obelisk_picker)

        embedding = discord.Embed(
        title="Time to choose your boon!!", 
        url="https://www.neopets.com/prehistoric/battleground/", 
        description=f"Make sure you choose your boon before doing your dailies!",
        color=0xf3f1d4
        )
        embedding.set_image(url="https://images.neopets.com/items/weap_shard_obelisk.gif")
    
        await channel.send(f"<@&{int(obelisk_id)}>",embed=embedding)
    else:
        return
        
    

@bot.command()
async def help(command):
    embedding = discord.Embed(
    title="Here are the things that i can do!", 
    description="""* **help**: You already know this one! A handy shorthand is using **.h**!
    # \n* **turmytimes**: This one's used to send the turmaculus times in the same format as [Brownhownd](https://www.neopets.com/~Brownhownd) (you can also use .tt)
    # \n* **turmywhen**: You can use this one to know how many wake-up times are left in the queue! (you can also use .tw)
    \n* **turmac**: This one pings everyone with the turmac role! (you can also use .turmy or .t)
    \n* **igloo**: This ones doesn't ping anyone atm, but it links to igloo! Useful to anounce it's stocked! (yadda yadda .i)
    \n* **ping**: It's a ping! You know, [A Ping](https://en.wikipedia.org/wiki/Ping_(networking_utility))
    \n* **mpic**: Links to Mystery Pic! Because why not.
    \n* **artgallery**: Links to the Neopets Art Gallery! (also .ag)
    \n* Also, there may be a couple secrets (but it's a secret!).""",
    color=0xFA903E
    )
    await command.send(embed=embedding)

@bot.command()
async def ping(command):
    await command.send("Pong")

@bot.command()
async def gura(command):
    await command.send("gura is so cool, some say she's goated.")

@bot.command()
async def dale(command):
    await command.send("Dale only gets better with age. 👴 🦖")

@bot.command()
async def carol(command):
    await command.send("YAY SPORTS! 🏈 🏒 ⚾️")

@bot.command()
async def hero(command):
    await command.send("Rich")

@bot.command()
async def connie(command):
    await command.send("Pro")

@bot.command()
async def sweet(command):
    await command.send("Goat")

@bot.command()
async def liz(command):
    await command.send("Pro")

@bot.command()
async def lupana(command):
    await command.send("Certified Pharmacy Pro")

@bot.command()
async def lee(command):
    await command.send("Expert at www.neopets.com")

@bot.command()
async def toto(command):
    await command.send("Most Readable Code Writer")

@bot.command()
async def sharkie(command):
    await command.send("90 percent of gamblers....")

@bot.command()
async def justin(command):
    await command.send("STAMPS")

@bot.command()
async def charlene(command):
    await command.send("NEW MAMA!!")

@bot.command()
async def tami(command):
    await command.send("RUN TAMI RUN")

@bot.command()
async def ash(command):
    await command.send("Thunder from down under")

@bot.command()
async def maddie(command):
    await command.send("NT Story Pro")

@bot.command()
async def coco(command):
    await command.send("rich lois griffin")

@bot.command()
async def amii(command):
    await command.send("r99 queen")

@bot.command()
async def mpic(command):
    await command.send('https://www.neopets.com/games/mysterypic.phtml, this should ping maybe idk <:carol:1419684583766622259>')

@bot.command(aliases=["ag"])
async def artgallery(command):
    await command.send("https://www.neopets.com/art/gallery.phtml")


bot.run(token, log_handler=handler, log_level=logging.DEBUG)