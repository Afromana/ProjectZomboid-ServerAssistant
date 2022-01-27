import json
import subprocess
import discord
from discord.ext import commands
from discord.ext.tasks import loop
import glob
import os
import re
import requests

bot = commands.Bot(command_prefix='?', case_insensitive=True)

with open('config.json') as f:
    config = json.load(f)

path = config["zomboidPath"] + "/ProjectZomboidServer.bat"  # Not currently used, planned for handling server management
dPath = config["docPath"]
sName = config["serverName"]
nChannel = config["notifyChannel"]
cChannel = config["chatChannel"]
nUser = config["notifyUser"]
botToken = config["botToken"]
joinNotif = config["joinNotif"]
deathNotif = config["deathNotif"]


with open(dPath+"Server/"+sName) as file:
    configfile = file.read().splitlines()
    for entry in configfile:
        if entry.startswith('WorkshopItems'):
            workshopIDs = entry[14:].split(";")  # Extracts the IDs from the config

@loop(minutes=30)  # Runs every 30 minutes
async def modcheck():
    print("ModCheck")
    data = {}
    data["itemcount"] = str(len(workshopIDs)) # The list of workshop IDs retrieved from the server config previously
    counter = 0

    for entry in workshopIDs: # Adds the workshop entries to an array
        data[f"publishedfileids[{counter}]"] = str(entry)
        counter += 1


    xcheck = requests.post("https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/", data).json()  # Sends the data to steam, recieving all workshop pages and its info back
    checkresults = {}
    for entry in xcheck["response"]["publishedfiledetails"]: # Fetches the specific workshop data we care about into "dictionaries"
        id = entry["publishedfileid"]
        checkresults[id] = {}  # The ID of the workshop mod, as the base of the "dictionary"
        checkresults[id]["title"] = entry["title"]  # The name of the workshop mod
        checkresults[id]["time_updated"] = entry["time_updated"]  # The last time the mod was updated, in UNIX Epoch time.
    if os.path.isfile("moddata.json") == False:
        print("No moddata.json found, creating file")
        with open("moddata.json", "w+") as f:
            print("Populating file with workshop data")
            json.dump(checkresults, f) # Populate the list by default

    with open ("moddata.json", "r+") as f:  # Loads previously fetched workshop data for comparison
        cacheresult = json.load(f)
        print("Loaded moddata.json")

    for key, value in checkresults.items():  # Run this code for every workshop entry in our "dictionary"

        try:  # Weird method for me to detect if this entry exists or not, if not, probably a new mod
            print(f"""{value["time_updated"]} vs {cacheresult[key]["time_updated"]}""")
        except KeyError:
            print(f'Mod {value["title"]} was not found in cache, new mod?')
            with open("moddata.json", "w+") as f:
                json.dump(checkresults, f)
            break

        if value["time_updated"] > cacheresult[key]["time_updated"]:  # If that value is higher then the one we cached, the mod on the workshop is newer, and has been updated
            print("Detected mod update!")
            with open("moddata.json", "w") as f:  # Save the updated workshop data to our file for later comparison
                json.dump(checkresults, f)
            ch = bot.get_channel(nChannel)  # Yell in this Discord channel
            await ch.send(f"""<@{nUser}> Mod updated! {value["title"]}""")

@bot.command()
async def modlist(ctx):
    data = {}
    data["itemcount"] = str(len(workshopIDs))
    counter = 0
    for entry in workshopIDs:
        data[f"publishedfileids[{counter}]"] = str(entry)
        counter += 1

    x = requests.post("https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/", data).json()

    results = {}
    for entry in x["response"]["publishedfiledetails"]:
        id = entry["publishedfileid"]
        results[id] = {}
        results[id]["title"] = entry["title"]
        results[id]["time_updated"] = entry["time_updated"]

    mainstring = ""
    for key, value in results.items():
        mainstring += f"""**[{value["title"]}](https://steamcommunity.com/sharedfiles/filedetails/?id={key})**\nLast updated: <t:{value["time_updated"]}:R>\n"""
    embed = discord.Embed(title="Zomboid Server mod status", colour=discord.Colour(0x768ac4),
                          description=mainstring)
    await ctx.send(embed=embed)

rfile = None
latest_file = None

none = "\n"
reapeatcount = 0
lastmessage = None

@bot.command()
async def deaths(ctx):
    if os.path.isfile("deaths.json") == False:
        await ctx.send("There is no Death file present, has anyone died yet?")
        return
    with open("deaths.json", "r") as f:
        x = json.load(f)
        xsorted = {k: v for k, v in sorted(x.items(), key=lambda item: item[1])}
        deathstring = ""
        for entry in reversed(xsorted):
            deathstring += f"{entry}: {x[entry]}\n"
        embed = discord.Embed(title="~Zomboid Death Leaderboard~", description=deathstring)
        #embed.set_image(url="https://cdn.discordapp.com/attachments/390989307680391168/925506790001606667/scrungo.png")  # Scrungo
        await ctx.send(embed=embed)

@loop(seconds=1)
async def connectioncheck():
    global rfile
    global openedFile
    if rfile == None:
        try:
            list_of_files = glob.glob(dPath+r'Logs/*.txt')
            filter_object = filter(lambda a: 'user.txt' in a, list_of_files)
            latest_file = max(list(filter_object), key=os.path.getctime)
            rfile = open(latest_file, 'r', encoding="UTF-8")
            openedFile = latest_file
            rfile.seek(0, 2)
            print("Loaded User log file")
        except Exception as e:
            print(f"Failed to load User log file!\n{e}")
            return
    else:
        list_of_files = glob.glob(dPath + r'Logs/*.txt')
        filter_object = filter(lambda a: 'user.txt' in a, list_of_files)
        latest_file = max(list(filter_object), key=os.path.getctime)
        if os.path.getctime(openedFile) < os.path.getctime(latest_file):
            rfile.close()
            rfile = open(latest_file, 'r', encoding="UTF-8")
            rfile.seek(0, 2)
            openedFile = latest_file
            print("Loaded new User file")
    fileLine = rfile.readline()
    message = fileLine
    if not fileLine:
        return
    if fileLine == none:
        return
    else:
        zomboidch = bot.get_channel(cChannel)
        if "fully connected" in message:
            if joinNotif:
                playername = message.split('"')[1]
                await zomboidch.send(f"{playername} joined the server")
                print(f"{playername} joined the server")
            else:
                print("Join message ignored, disabled in config")
                return
        elif "disconnected player" in message:
            if joinNotif:
                playername = message.split('"')[1]
                await zomboidch.send(f"{playername} left the server")
                print(f"{playername} left the server")
            else:
                print("Leave message ignored, disabled in config")
                return
        elif "died at" in message:
            if deathNotif:
                if os.path.isfile("deaths.json") == False:
                    print("No deaths.json found, creating file")
                    with open("deaths.json", "w+") as f:
                        print("Inserting dummy data")
                        defaultdata = {}
                        json.dump(defaultdata, f)  # Populate the list by default
                f = open("deaths.json", "r+")
                y = re.search('user (.*) died', message)
                deathname = y.group(1)
                deathboard = json.load(f)
                try:
                    deathboard[deathname] += 1
                except:
                    deathboard[deathname] = 1
                playerdeath = deathboard[deathname]
                f.seek(0)
                json.dump(deathboard, f)
                f.close()
                await zomboidch.send(f"**{deathname} died!** *[{playerdeath} deaths]*")
                print(f"{deathname} died! [{playerdeath} deaths]")
            else:
                print("Death message ignored, disabled in config")
                return
        else:
            print(f"No match for string:\n{message}")

@bot.event
async def on_ready():
    connectioncheck.start()
    modcheck.start()

bot.run(botToken)