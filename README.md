# ProjectZomboid-ServerAssistant
Notifies server owners of mod updates, also notifies of player deaths and player joins through Discord.
A Python based Discord bot made for my own private server with friends, which is why the code is a bit haphazard in places, but people wanted it.

This is probably not the most user friendly at the moment, and will go through some iterations, but this first release is in an attempt to get it out to those who seem to particularly need it at the moment.

Library dependencies:
```
discord.py
requests
```

# Setup:
The included config.json needs to be set up by filling in the fields accordingly:
```
{
  "zomboidPath": "",    // Currently unused, will manage server restarts later on.
  "docPath": "",        // Your Zomboid path in Documents, where your logs and server config sits, usually: "C:\Users\(USERNAME HERE)\Zomboid\".
  "serverName": "",     // Your server's config name under the \Server\ Directory of docPath, likely "servertest.ini" or such.
  "notifyUser": 0,      // Your Discord ID, or whoever should be pinged when a mod update occurs.
  "notifyChannel": 0,   // The discord channel ID that the mod notification should occur in, probably best to keep it to the same as chatChannel
  "chatChannel": 0,     // General chat channel ID, where join, leave and death messages will be sent.
  "joinNotif": true,    // If to enable notifications about joining or leaving, true / false.
  "deathNotif": true,   // If to enable notifications and logging of player deaths, true / false.
  "botToken": ""        // Your Discord bot token, https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token
}
```
