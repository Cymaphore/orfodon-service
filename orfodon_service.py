##
# @mainpage ORFodon service script
# 
# Quick and dirty solution to turn ORF.at into a Mastodon-site
#
# @Warning this is tailormade for ORF.at and will not work without modification
# with other RSS based news sites!
#
# Inspired by feediverse from Ed Summers
#
# Process configuration, fetch news entries and post them to different accounts
# 
# Dependencies:
# - bs4
# - feedparser
# - yaml
# - mastodon
#
# License: The MIT License (MIT)
# Copyright: Martin Eitzenberger <x@cymaphore.net>
# @cymaphore@i.cymaphore.net
# https://cymaphore.net
#
# @todo Secondary urls like https://vorarlberg.orf.at/radio/stories/3231551/ https://steiermark.orf.at/magazin/stories/3232156/
# @todo Sort news in descending order by date when bulk processing <-- low prio, usually not an issue
# @todo Account mentioner ("der Standard" --> @derStandard)?
# @todo extract top hashtags from current posts and add them to profile
# @todo ORF_Topos as channel
#

#############################################################################

# External components

import re
import yaml
import copy
import feedparser
from datetime import datetime
import time

import requests
from bs4 import BeautifulSoup
from mastodon import Mastodon

from pprint import pprint

#############################################################################

# Configuration

from config import config
from credentials import credentials
from feeds import feeds
from hashtag_modification import hashtag_replace
from hashtag_modification import hashtag_blacklist

#############################################################################

# Current fetched articles / state
global state

# State from previous run cycle
global oldState

# Global hashtag wordlist
global hashtag_wordlist

state = {}
oldState = {}
hashtag_wordlist = []

#############################################################################

##
# Main function
# Call all the stages in correct order
def main():
    
    # Load hashtag wordlists
    load_hashtags()
    
    # Load previous state, initialize new state
    load_state()
    
    # Load the configured feeds and preprocess text
    load_feeds()
    
    # Grab post references from other channels for boosting, keep id from oldState
    grab_posts()
    
    # Post newly generated articles to the channels
    post_feeds()
    
    # Save state for next cycle
    save_state()

#############################################################################

##
# Load hashtag wordlists
def load_hashtags():
    hashtags_filename = config["files"]["global_hashtags"]
    if True:
        hashtags_file = open(hashtags_filename, "r")
        global hashtag_wordlist
        hashtag_wordlist = hashtags_file.read().splitlines()

#############################################################################

##
# Load the configured feeds and preprocess text
def load_state():
    global state
    global oldState
    global hashtag_wordlist
    
    try:
        with open(config["files"]["state"]) as fh:
            oldState = yaml.load(fh, yaml.SafeLoader)
    except:
        oldState = {}
    
    for feed in feeds:
        
        if not feed["id"] in state:
            state[feed["id"]] = {}
        if not feed["id"] in oldState:
            oldState[feed["id"]] = {}
            

#############################################################################

##
# Save state for next cycle
def save_state():
    with open(config["files"]["state"], 'w') as fh:
        fh.write(yaml.dump(state, default_flow_style=False))

#############################################################################

##
# Load the configured feeds and preprocess text
def load_feeds():
    global state
    global oldState
    
    for feed in feeds:
        
        feedStateOld = oldState[feed["id"]]
        feedState = state[feed["id"]]
        
        if "url" in feed:
            entries = feedparser.parse(feed["url"]).entries
            
            if len(entries) < 1:
                raise RuntimeError("No elements in feed " + feed["url"])
            
            for entry in entries:
                title = entry.get('title')
                text = entry.get('summary')
                url = entry.get('link')
                raw_posting = ""
                post_type_text = False
                hashtags = []
                updated = entry.get('updated')
                boost_target = ""
                edited = False
                exists = False
                oldPosting = {}
                status_id = 0
                posted = False
                post_text = ""
                boosted = False
                ref = ""
                
                if url in feedStateOld:
                    exists = True
                    oldPosting = feedStateOld[url]
                    if "status_id" in oldPosting:
                        status_id = oldPosting["status_id"]
                    if "posted" in oldPosting:
                        posted = oldPosting["posted"]
                    if "boosted" in oldPosting:
                        boosted = oldPosting["boosted"]
                
                try:
                    ttags = entry.get('orfon_oewacategory', {}).get("rdf:resource", '')
                    if not ttags is None and not ttags == "":
                        ttags = ttags.split(":")[3].split("/")
                        if not ttags[0] is None:
                            hashtags.append('#{}'.format(ttags[0]))
                            #pprint(ttags[1])
                except:
                    ()
                
                ttags = entry.get('tags')
                
                if not ttags is None:
                    for tag1 in entry.get('tags'):
                        for tag2 in tag1["term"].split(" "):
                            tag = tag2 \
                                    .replace(".", "") \
                                    .replace("-", "") \
                                    .replace("&", "") \
                                    .replace("/", "") \
                                    .replace(":", "")
                            hashtags.append('#{}'.format(tag))

                if "additional_hashtags" in feed:
                    hashtags.extend(feed["additional_hashtags"])

                try:
                    for ht in hashtag_wordlist:
                        if re.search(r"\b" + re.escape(ht) + r"\b", title):
                            hashtags.append("#" + ht)
                except:
                    ()
                
                for tagi in range(len(hashtags)):
                    if hashtags[tagi] in hashtag_replace:
                        hashtags[tagi] = copy.copy(hashtag_replace[hashtags[tagi]])
                
                hashtags = list(dict.fromkeys(hashtags))
                try:
                    hashtags.remove("#")
                except:
                    ()
                
                for bt in hashtag_blacklist:
                    try:
                        hashtags.remove(bt)
                    except:
                        ()
                
                #pprint(hashtags)
                
                ts_story_details = 0
                if "ts_story_details" in oldPosting:
                    ts_story_details = oldPosting["ts_story_details"]
                
                if text and len(text) > 0:
                    raw_posting = text
                    post_type_text = True
                else:
                    if "boost_target" in oldPosting and len(oldPosting["boost_target"]) > 0:
                        boost_target = oldPosting["boost_target"]
                        if "ts_story_details" in oldPosting:
                            if ts_story_details < ts() - 600:
                                story_details = get_story_details(url)
                                ts_story_details = ts()
                                if len(story_details["text"]) >= len(title):
                                    raw_posting = story_details["text"]
                                else:
                                    raw_posting = title
                            else:
                                raw_posting = oldPosting["text"]
                        elif "text" in oldPosting and len(oldPosting["text"]) > 0:
                            raw_posting = oldPosting["text"]
                        else:
                            raw_posting = title
                    else:
                        story_details = get_story_details(url)
                        ts_story_details = ts()
                        boost_target = story_details["url"]
                        if len(story_details["text"]) >= len(title):
                            raw_posting = story_details["text"]
                        else:
                            raw_posting = title
                    post_type_text = False
                    
                if "text" in oldPosting and raw_posting != oldPosting["text"]:
                    edited = True
                
                if edited or not posted:
                    cu_posting = cleanup(raw_posting, hashtags)
                    
                    hashlist = " ".join(hashtags)
                    post_text = limit_text(cu_posting.strip(), 495 - (len(" " + url + " " + hashlist)), ' (…)') + ' ' + url + " " + hashlist
                
                posting = {
                    'text': raw_posting,
                    'post_text': post_text.strip(),
                    'url': url,
                    'post_type_text': post_type_text,
                    'hashtags': hashtags,
                    'updated': updated,
                    'boost_target': boost_target,
                    'edited': edited,
                    'posted': posted,
                    'status_id': status_id,
                    'boosted': boosted,
                    'ts_story_details': ts_story_details
                    }
                
                feedState[url] = posting
        
#############################################################################

##
# Grab post references from other channels for boosting, keep id from oldState
def grab_posts():
    global state
    global oldState
    
    try:
        for feed in feeds:
            if "prefix" in feed and len(feed["prefix"]) > 0:
                for feed2 in feeds:
                    if feed["id"] == feed2["id"]:
                        continue
                    for postu in oldState[feed2["id"]]:
                        post = oldState[feed2["id"]][postu]
                        if post["url"][:len(feed["prefix"])] == feed["prefix"]:
                            if not postu in state[feed["id"]]:
                                state[feed["id"]][postu] = copy.deepcopy(oldState[feed["id"]][postu])
                            else:
                                if not "status_id" in state[feed["id"]][postu] or state[feed["id"]][postu]["status_id"] < 1:
                                    if "status_id" in oldState[feed["id"]][postu]:
                                        if not state[feed["id"]][postu]["posted"] and oldState[feed["id"]][postu]["posted"]:
                                            state[feed["id"]][postu]["edited"] = True
                                        state[feed["id"]][postu]["status_id"] = oldState[feed["id"]][postu]["status_id"]
                                        state[feed["id"]][postu]["posted"] = oldState[feed["id"]][postu]["posted"]
                                        state[feed["id"]][postu]["boosted"] = oldState[feed["id"]][postu]["boosted"]
    except:
        print(timestamp() + " Exception: grab_posts() Stage 1 failed")
    
    try:
        for feed in feeds:
            if "prefix" in feed and len(feed["prefix"]) > 0:
                for feed2 in feeds:
                    if feed["id"] == feed2["id"]:
                        continue
                    for postu in state[feed2["id"]]:
                        post = state[feed2["id"]][postu]
                        if post["url"][:len(feed["prefix"])] == feed["prefix"]:
                            if not postu in state[feed["id"]]:
                                state[feed["id"]][postu] = copy.deepcopy(post)
    except:
        print(timestamp() + " Exception: grab_posts() Stage 2 failed")
        
#############################################################################

##
# Post newly generated articles to the channels
def post_feeds():
    global state
    global oldState
    
    for feed in feeds:
        cred = credentials[feed["id"]]
        
        instance = Mastodon(
            api_base_url=cred['instance'],
            client_id=cred['client_id'],
            client_secret=cred['client_secret'],
            access_token=cred['access_token']
        )
        
        filterbots = {}
        
        if "filterbots" in feed:
            for filterbot in feed["filterbots"].keys():
                filterbots[filterbot] = []
        
        for posting_id in state[feed["id"]]:
            posting = state[feed["id"]][posting_id]
            boosted = False
            
            if not posting["posted"]:
                if "boost_target" in posting and len(posting["boost_target"]) > 0:
                    original_posting = get_canon_posting(posting["boost_target"])
                    
                    if not original_posting is None:
                        print("==============================================================================")
                        if "post_text" in original_posting and len(original_posting["post_text"])>0:
                            dbg_text = original_posting["post_text"]
                        else:
                            dbg_text = original_posting["text"] + " (no post_text)"
                        print(timestamp() + " -> BOOST to " + feed["id"] + ": " + dbg_text)
                        
                        if "status_id" in original_posting:
                            try:
                                if config["enable_mastodon"]:
                                    status = instance.status_reblog(original_posting["status_id"])
                                else:
                                    print("DRYRUN: not executing: instance.status_reblog() ID \"" + original_posting["status_id"] + "\"")
                            except:
                                print(timestamp() + " EXCEPTION wile instance.status_reblog()")
                                print(original_posting)
                            for filterbot in filterbots:
                                for fb_prefix in feed["filterbots"][filterbot]:
                                    if fb_prefix == original_posting["url"][:len(fb_prefix)]:
                                        filterbots[filterbot].append(original_posting["status_id"])
                        else:
                            print(timestamp() + " ERROR Missing status_id")
                            print(original_posting)
                        
                        posting["posted"] = True
                        boosted = True
                        posting["boosted"] = True
                        
                backref_posting = get_canon_posting(posting["url"])
                if not backref_posting is None and backref_posting != posting:
                    print("==============================================================================")
                    if "post_text" in backref_posting and len(backref_posting["post_text"])>0:
                        dbg_text = backref_posting["post_text"]
                    else:
                        dbg_text = backref_posting["text"] + " (no post_text)"
                    print(timestamp() + " -> BOOST backref to " + feed["id"] + ": " + dbg_text)
                        
                    if "status_id" in backref_posting:
                        try:
                            if config["enable_mastodon"]:
                                status = instance.status_reblog(backref_posting["status_id"])
                            else:
                                print("DRYRUN: not executing: instance.status_reblog() ID \"" + backref_posting["status_id"] + "\"")
                                
                        except:
                            print(timestamp() + " EXCEPTION while instance.status_reblog()")
                            print(backref_posting)
                        for filterbot in filterbots:
                            for fb_prefix in feed["filterbots"][filterbot]:
                                if fb_prefix == backref_posting["url"][:len(fb_prefix)]:
                                    filterbots[filterbot].append(backref_posting["status_id"])
                    else:
                        print(timestamp() + " ERROR Missing status_id")
                        print(backref_posting)
                        
                    posting["posted"] = True
                    boosted = True
                    posting["boosted"] = True

                if not boosted:
                    print("==============================================================================")
                    print(timestamp() + " ++ POST to " + feed["id"] + ": " + posting["post_text"])
                    print(" (~>" + posting["boost_target"] + ")")
                    
                    try:
                        if config["enable_mastodon"]:
                            status = instance.status_post(posting["post_text"])
                        else:
                            print("DRYRUN: not executing: instance.status_post()")
                            status = {"id": 0}
                        posting["status_id"] = status["id"]
                        for filterbot in filterbots:
                            filterbots[filterbot].append(status["id"])
                    except:
                        print(timestamp() + " EXCEPTION while instance.status_post()")
                        print(posting)
                        #posting["status_id"] = 0;
                    
                    posting["boosted"] = False
                    posting["posted"] = True
                    
            if posting["edited"] and not posting["boosted"]:
                print("==============================================================================")
                print(timestamp() + " ** EDIT on " + feed["id"] + ": " + posting["post_text"])
                
                if "status_id" in posting and posting["status_id"] > 0:
                    try:
                        if config["enable_mastodon"]:
                            status = instance.status_update(posting["status_id"], posting["post_text"])
                        else:
                            print("DRYRUN: not executing: instance.status_update() ID \"" + posting["status_id"] + "\"")
                            status = {"id": 0}
                        posting["status_id"] = status["id"]
                    except:
                        print(timestamp() + " EXCEPTION while instance.status_update()")
                        print(posting)
                    
                posting["edited"] = False
        
        if "filterbots" in feed:
            for filterbot in feed["filterbots"].keys():
                if len(filterbots[filterbot]) > 0:
                    cred = credentials[filterbot]
                    
                    instance = Mastodon(
                        api_base_url=cred['instance'],
                        client_id=cred['client_id'],
                        client_secret=cred['client_secret'],
                        access_token=cred['access_token']
                    )
                    for status_id in filterbots[filterbot]:
                        print("==============================================================================")
                        print(timestamp() + " -> BOOST filterbot to " + filterbot + ": " + str(status_id))
                        
                        try:
                            if config["enable_mastodon"]:
                                status = instance.status_reblog(status_id)
                            else:
                                print("DRYRUN: not executing: instance.status_reblog(\"" + str(status_id) + "\")")
                        except:
                            print(timestamp() + " EXCEPTION while instance.status_reblog()")
                            print(str(status_id))
                        


#############################################################################

##
# Search state for canonical posting
# used for boosting other postings
def get_canon_posting(posting):
    global state
    global oldState
    
    for state_id in state:
        sta = state[state_id]
        if posting in sta:
            return sta[posting]
        if posting + "/" in sta:
            return sta[posting + "/"]
    
    return None

#############################################################################

##
# Load news-article, search for article in the page and identify
# a possible link to another article. Used to transform
# Postings that are only referencing another article without adding
# own news into boosts of the linked article.
def get_story_details(url):
    
    retr = {
        "url": "",
        "text": ""
    }
    
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '3600',
        'User-Agent': config["user_agent"]
    }

    if url is None:
        return retr
    
    req = requests.get(url, headers)
    soup = BeautifulSoup(req.content, 'html.parser')
    story = soup.find("div", {"class": config["crawl_class_story"]})
    
    if story is None:
        return retr
    
    try:
        retr["text"] = story.find("p").get_text()
    except:
        ()
    
    try:
        retr["url"] = story.find("a").attrs["href"]
    except:
        ()
    
    return retr

#############################################################################

##
# Limit post text to length, automatic shortening with proper suffix
# will not cut words in half
def limit_text(text, max_len=500, suffix='...'):
    if len(text) <= max_len:
        return text
    else:
        return ' '.join(text[:max_len + 1].split(' ')[0:-1]) + suffix

#############################################################################

##
# Cleanup rss feed article, remove HTML, fix whitespaces
# and add hashtags
def cleanup(text, hashtags):
    html = BeautifulSoup(text, 'html.parser')
    text = html.get_text()
    text = re.sub('\xa0+', ' ', text)
    text = re.sub('  +', ' ', text)
    text = re.sub(' +\n', '\n', text)
    text = re.sub('\n\n\n+', '\n\n', text, flags=re.M)
    
    global hashtag_wordlist
    
    for wrd in hashtag_wordlist:
        wrd = wrd.strip()
        if wrd != "" and wrd[0] != '#':
            text = re.sub(r'\b' + wrd + r'\b(?!@)', '#' + wrd, text, 1)
    
    ht_bl2 = []
    
    for ht in hashtags:
        if re.search(r"\b" + re.escape(ht[1:]) + r"\b", text):
            ht_bl2.append(ht)
    for ht in ht_bl2:
        hashtags.remove(ht)
    
    return text.strip()

#############################################################################

##
# Generate a timestamp for use in output/logging
def timestamp():
    return datetime.now().strftime("[%Y-%m-%d_%H:%M:%S]")

#############################################################################

##
# Generate unix timestamp
def ts():
    return int(time.time())

#############################################################################

##
# Redirect to main() function when running the script
if __name__ == "__main__":
    main()
