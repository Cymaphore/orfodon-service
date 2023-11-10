## ORFodon Service

*orfodon_service* is the service scripted used on https://orfodon.org
to read news from https://orf.at and turn them into Mastodon postings.

See this for more informations on ORFodon: https://orfodon.org/about

This script is tailormade for orfodon.org and orf.at and will not
work out of the box with other news outlets!

## Install

Put it on a GNU/Linux-System with python3

Dependencies:
- bs4
- feedparser
- yaml
- mastodon

Copy credentials.py.example to credentials.py
Add credentials to the file, must be generated manually
Configure feeds.py and config.py as needed

Also check run_service.sh if paths are correct

## Run

Once configured, you must set up a cronjob to run the thing:

    * * * * * /usr/local/orfodon-service/run_service.sh &>/dev/null
