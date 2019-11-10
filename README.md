# Programmatic Suicide Prevention 

The project focuses on understanding suicide signs through social media analysis, crawling data from Twitter and Reddit using their respective API's (Tweepy and PRAW).

## Abstract

Crawling code base for a social analytics project part of the IS434: Social Analytics and Applications course at [Singapore Management University](https://www.smu.edu.sg/) (fall 2019).

## Usage

This application is used by executing different scripts in a sequence. First of all, you need to crawl your data from either Reddit or Twitter:

```shell
# Reddit
$ python3 reddit_main.py <insert subreddit> # ie 'askreddit'

# Twitter
# Twitter script will need a DataFrame of desired keywords to look through 
# before running.
$ python3 twitter_main.py
```

Secondly, when data is crawled and saved into your csv files, you will want to analyse this data to score each submission/tweet to acknowledge the level of proneness the user has of committing suicide. This is done by applying our analyzing scripts to our recently crawled data:

```shell
# Reddit
$ python3 reddit_a.py <name of one of the subreddits crawled> # ie 'depression'

# Twitter
# This script has a 'keyword' variable with hardcoded elements that it will
# use to iterate through. Change this to whatever you want before usage.
$ python3 twitter_a.py
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)
