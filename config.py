##
# General configuration and Presets

config = {
    
    ## File configuration
    
    "files": {
        
        ## State file, keep the posting status over cron cycles
        "state": "state.yaml",
        
        ## Global fundamental hashtag replacement file
        "global_hashtags": "hashtags"
    },
    
    # ## Identification of original articles (backling - boosting)
    
    ## Fake user agent when crawling for original article links on orf.at
    "user_agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/119.0",
    
    ## div class to look for in news pages when searching for original article links
    "crawl_class_story": "story-story",
    
    # Debug and test flags
    
    ## Set True to enable actual mastodon postings (otherwise dryrun with output)
    "enable_mastodon": False,
    
    ## Default posting format
    "template": "{title}\n\n{text}\n\n{url}\n\n{hashtags}",
    
    ## Max message size
    "message_size": 496,
    
}
