# Turning your AmpliPi into a Plexamp Player
This guide will detail multiple ways to setup Plexamp on the AmpliPi system.

## Prerequisites
Regardless of which setup path you take, a few requirements must be met. First, Plexamp must be installed on the Pi. This should come standard with our AmpliPi install. If you find yourself needing to install it, we use a modified copy of Plexamp v1.0.5 for the Pi. Our version can be found here ####WHERE CAN IT BE FOUND?####

You will also need a Plex Pass subscription to be able to discover the device (Plexamp is a subscription-only service).

Finally, Node 9 is required since this is an older version of the Plexamp software ####IS THIS STILL NECESSARY???????####

## Option 1 - Using the AmpliPi API
This is the simplest option available. Simply navigate to the Settings pane on 'amplipi.local/' and select "Connect Plex Account"
# (INCLUDE PICTURE ONCE THE SITE SUPPORTS THIS. POTENTIALLY EDIT NAMES AND WHATNOT AS WELL)
Connecting your Plex account is as simple as clicking a button, then entering your username/password. Upon entering the information for an account with a Plex Pass subscription, a unique identifier/token pair will be generated for your AmpliPi. This information will be used to create a Plexamp stream in a similar fashion to Pandora, Spotify, etc.

## Option 2 - Manual ID/Token creation
If you would like to do some development of your own, or want access to the token generation process for any other reason, this is the way to go.

### Step 1
To start, request a pin from Plex. This is most easily done on a Linux-based system, or by using SSH to connect to AmpliPi. To do this, put the following command into your terminal:
```
curl -X POST https://plex.tv/api/v2/pins \
-H 'accept: application/json' \
-d 'strong=true' \
-d 'X-Plex-Product=AmpliPi' \
-d 'X-Plex-Client-Identifier=<clientIdentifier>'
```
Where "\<clientIdentifier>" should be replaced with a unique string/number sequence. Using 'uuidgen' is pretty simple, and it provides a reasonably unique entry for clientIdentifier. Once you have replaced the text with your UUID, hit Enter.

The system should respond with a block of information that it fetched. The important information here is "id":##########, "code":"xxxxxxxxxxxxxxxxxxxxxxxxx", and our clientIdentifier/UUID from before.

### Step 2
Next, generate a URL from the information you received. A sample looks something like this:
```
https://app.plex.tv/auth#?clientID=<clientIdentifier>&code=<pinCode>&context%5Bdevice%5D%5Bproduct%5D=AmpliPi
```
Replace \<pinCode> and \<clientIdentifier> with the "code" and UUID from the previous steps. This should create a functional link that requests a Plex sign-in. Give your Plex Pass account information and feel free to close the window when prompted. This should have generated a Plexamp token.

### Step 3
Retrieve the token with another command line input:
```
curl -X GET 'https://plex.tv/api/v2/pins/<pinID>' \
-H 'accept: application/json' \
-d 'code=<pinCode>' \
-d 'X-Plex-Client-Identifier=<clientIdentifier>'
```
Using the information from Step 1, replace \<pinID> with your "id", \<pinCode> with "code", and \<clientIdentifier> with your UUID.

This request returns a similar block of information to that received in Step 1, though "authToken" should no longer be null. This is your new Plexamp token! It should be a 20-character string. Copy this over to 'server.json' along with your clientIdentifier - you should now have a working Plexamp device!
```
SERVER.JSON snippet:

"player": {
  "name": "AmpliPi-Template",    <--- Can be whatever you choose
  "identifier": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" <--- clientID
},
"user": {
  "token": "_" <--- authToken
},
```

## Option 3 - Getting a server.json file from an existing install
This option requires an install of an older version of the Plexamp desktop application on a different computer.

The install links can be found here:

for windows - https://plexamp.plex.tv/plexamp.plex.tv/Plexamp%20Setup%201.1.0.exe

for MacOS - https://plexamp.plex.tv/plexamp.plex.tv/Plexamp-1.1.0.dmg


Follow the steps to install Plexamp, then sign in with your account. This should generate a server.json with a working token/id pair. Navigate to the file on your system and copy it over to /home/pi/amplipi-dev/streams on AmpliPi. You can find server.json here:

for windows - c:\Users\USER_\AppData\Local\Plexamp\server.json

for MacOS - /System/Volumes/Data/Users/USER_/Library/Application Support/Plexamp/server.json

Where USER_ is replaced with you username on that system. Once you've placed this file in the accurate AmpliPi directory, create a Plexamp stream source in the Settings pane on the WebApp!
# INCLUDE PICTURE OF A PLEXAMP STREAM GENERATOR (USE THE SITE TO FIND SERVER.JSON AND THEN USE IT)
