# Cherris-PC-info

# Getting Started:

Creating the bot:
1. Go to https://discord.com/developers/applications
2. Create a new application
3. If not already there, click on the application.
4. On the left side click on the "Bot" tab
5. Scroll down and enable "Message Content Intent"
6. On the left side click on the "OAuth2" tab
7. Scroll down to the URL generator and check the "bot" option then in the second list check the "Administrator" option
8. Copy the link and add it to one of your servers

Setting up the app:
1. Install python: https://www.python.org/ftp/python/3.14.2/python-3.14.2-amd64.exe
2. Open up cmd and run this command: pip install psutil discord.py pystray Pillow GPUtil wmi tk
3. Open the EXE file
4. Enter your bot token (This is found by going into the bot tab, resetting the token, and then copy and pasting it into the window.)
5. Enter your user ID (Go into discord settings, scroll down to the Advanced tab, turn on developer mode, turn off settings, right click on your profile and click "Copy User ID")
6. And then your done!

After setting it up the first time it will store the token and User ID in the "pcinfosettings.txt" file. There is currently a bug that'll give u the three day warning on boot, ignore it, after boot it will wait three days before sending it again. I can't fix it, if you have luck dm me on discord "wtvcherrii".

Adding it to the bootup:
1. In the folder with the exe, right click and click "Create Shortcut"
2. Press Win+R and type in "shell:startup"
3. Put the shortcut into the Startup folder
4. And now it will boot at start up!
