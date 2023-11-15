##
# Feed configuration
# Important: Order matters!
# Will be processed in order to allow instant boost of referenced articles!
#
# Feed-Settings:
# id: internal feed/channel-id
# url: URL of RSS feed to read
# prefix: Prefix of news urls for backref-boosting

feeds = [
    
    # Bundesländer
    
    {
        'id': 'burgenland',
        'url': 'https://rss.orf.at/burgenland.xml',
        'prefix': 'https://burgenland.orf.at/stories/'
    },
    {
        'id': 'kaernten',
        'url': 'https://rss.orf.at/kaernten.xml',
        'prefix': 'https://kaernten.orf.at/stories/'
    },
    {
        'id': 'niederoesterreich',
        'url': 'https://rss.orf.at/noe.xml',
        'prefix': 'https://noe.orf.at/stories/'
    },
    {
        'id': 'oberoesterreich',
        'url': 'https://rss.orf.at/ooe.xml',
        'prefix': 'https://ooe.orf.at/stories/'
    },
    {
        'id': 'salzburg',
        'url': 'https://rss.orf.at/salzburg.xml',
        'prefix': 'https://salzburg.orf.at/stories/'
    },
    {
        'id': 'steiermark',
        'url': 'https://rss.orf.at/steiermark.xml',
        'prefix': 'https://steiermark.orf.at/stories/'
    },
    {
        'id': 'tirol',
        'url': 'https://rss.orf.at/tirol.xml',
        'prefix': 'https://tirol.orf.at/stories/'
    },
    {
        'id': 'vorarlberg',
        'url': 'https://rss.orf.at/vorarlberg.xml',
        'prefix': 'https://vorarlberg.orf.at/stories/'
    },
    {
        'id': 'wien',
        'url': 'https://rss.orf.at/wien.xml',
        'prefix': 'https://wien.orf.at/stories/'
    },
    
    # Sparten
    
    {
        'id': 'help',
        'url': 'https://rss.orf.at/help.xml',
        'prefix': 'https://help.orf.at/stories/'
    },
    {
        'id': 'science',
        'url': 'https://rss.orf.at/science.xml',
        'prefix': 'https://science.orf.at/stories/',
        'additional_hashtags': [ "#Wissenschaft" ]
    },
    {
        'id': 'religion',
        'url': 'https://rss.orf.at/religion.xml',
        'prefix': 'https://religion.orf.at/stories/',
        'additional_hashtags': [ "#Religion" ]
    },
    {
        'id': 'sport',
        'url': 'https://rss.orf.at/sport.xml',
        'prefix': 'https://sport.orf.at/stories/',
        'additional_hashtags': [ "#Sport" ]
    },
    
    # Hauptfeeds
    
    {
        'id': 'oesterreich',
        'url': 'https://rss.orf.at/oesterreich.xml'
    },
    {
        'id': 'news',
        'url': 'https://rss.orf.at/news.xml',
        'filterbots': {
            'news_lite': [
                'https://oesterreich.orf.at/stories/'
            ],
            'news_liteplus': [
                'https://burgenland.orf.at/stories/',
                'https://kaernten.orf.at/stories/',
                'https://noe.orf.at/stories/',
                'https://ooe.orf.at/stories/',
                'https://salzburg.orf.at/stories/',
                'https://steiermark.orf.at/stories/',
                'https://tirol.orf.at/stories/',
                'https://vorarlberg.orf.at/stories/',
                'https://wien.orf.at/stories/',
                'https://oesterreich.orf.at/stories/'
            ]
        }
    }
]
