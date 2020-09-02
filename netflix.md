# Leeching Netflix

This is a small howto showing how to download movies and series from Netflix, which we can then watch offline.
This can be useful, for example, to get content not available in your country.

## Get a Netflix account
In principle, you could use your own Netflix account - but it's probably better to create a new account, in case Netflix decides we've violated their fair-use rules.

### Get a Netflix gift card
We don't want to use our credit card for the same reason.
Instead, we can create a Netflix account and pay for it with a gift card. There are many services which let you buy gift cards online. eGifter (https://www.egifter.com/) for example is an easy to use service which even accepts Bitcoin.

## Hide our IP
We may want to watch content which is not available in our country. VPNs (e.g. NordVPN - https://nordvpn.com/) can help.
However, note that Netflix is actively trying to detect (and block) VPNs and proxies.

Alternatively, SmartDNS (https://www.smartdnsproxy.com/) is a simple solution that can allow us to access content as if we're in a different country. 

### Starting a Windows machine in the cloud
We will need Windows for the actual ripping. If you don't want to run it on your own machine, you can easily run it in the cloud.
For example, BitLaunch (https://bitlaunch.io) and BitHost (https://bithost.io) even accept Bitcoin.

## Get a Netflix downloader
Netflix is using DRM to encrypt its content. This means it's quite hard (and also illegal in some places) to download an "untouched" movie.
Fortunately, there are multiple applications that can download Netflix content - the way they work is by "playing" the movie - which they then reencode when saving to disk. FlixiCam (https://flixicam.com/) for example, works quite well - and can even download an entire season, organizing the downloaded files. This app can "play" the video in the background (it doesn't appear on screen), taking minutes to download an episode (depending on CPU).

FlixGrab and FlixGrab+ are two other options (there are many others).

## Get a list of URLs to download
FlixiCam (and other downloaders) need a URL to start downloading from. This can be a link to the episode - or (at least with FlixiCam) a link to the series (e.g. http://www.netflix.com/title/...).
uNoGS offer an API (via RapidAPI. https://rapidapi.com/unogs/api/unogsng) which can be used to create a list of URLs that can be imported into the Netflix downloader.
Note that you will need a credit card to use the API. If you don't have a credit card, you can buy a Visa gift card from eGifter (note you may need to use a VPN to appear to be in the US)

