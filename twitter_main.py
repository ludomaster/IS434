import ast
import json
import csv
from collections import Counter
import chardet
import pandas as pd
from tweepy import Stream
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from twython import Twython
from twython import TwythonStreamer

CONSUMER_KEY = 'PUT KEY HERE'
CONSUMER_SECRET = 'PUT SECRET HERE'
ACCESS_TOKEN = 'PUT TOKEN HERE'
ACCESS_SECRET = 'PUT SECRET HERE'

def main():
    """
    Initiation #TODO
    """
    credentials = {}
    credentials['CONSUMER_KEY'] = CONSUMER_KEY
    credentials['CONSUMER_SECRET'] = CONSUMER_SECRET
    credentials['ACCESS_TOKEN'] = ACCESS_TOKEN
    credentials['ACCESS_SECRET'] = ACCESS_SECRET

    # (1) If you haven't saved your json file, use this template first!
    #with open("twitter_credentials.json", "w") as file:
    #    json.dump(credentials, file)

    # (2) After you saved your json file using your above stated credentials, use this template.
    with open("twitter_credentials.json", "r") as file:
        creds = json.load(file)

    python_tweets = Twython(creds['CONSUMER_KEY'], creds['CONSUMER_SECRET'])

    # Create our query
    query = {'q': 'HongKong',
            'result_type': 'popular',
            'count': 10,
            'lang': 'en',
            }

    # Search tweets
    dict_ = {
            'user': [],
            'date': [],
            'text': [],
            'favorite_count': []
            }

    for status in python_tweets.search(**query)['statuses']:
        dict_['user'].append(status['user']['screen_name'])
        dict_['date'].append(status['created_at'])
        dict_['text'].append(status['text'])
        dict_['favorite_count'].append(status['favorite_count'])

    # Structure data in a pandas DataFrame for easier manipulation
    df = pd.DataFrame(dict_)
    df.sort_values(by='favorite_count', inplace=True, ascending=False)
    df.head(5)

    # Filter out unwanted data
    def process_tweet(tweet):

        # TODO: Add wanted data
        d = {}
        d['hashtags'] = [hashtag['text'] for hashtag in tweet['entities']['hashtags']]
        d['text'] = tweet['text'].encode('utf-8')
        d['user'] = tweet['user']['screen_name'].encode('utf-8')
        
        if tweet['user']['location'] != None:
            d['user_loc'] = tweet['user']['location'].encode('utf-8')
        else:
            d['user_loc'] = ''
        
        return d
        
    def find_encoding(fname):
        r_file = open(fname, 'rb').read()
        result = chardet.detect(r_file)
        charenc = result['encoding']
        return charenc

    # Create a class that inherits TwythonStreamer
    class MyStreamer(TwythonStreamer):
        """
        Initiates TwythonStreamer object
        """
        # Received data
        def on_success(self, data):

            # Only collect tweets in English
            if data['lang'] == 'en':
                tweet_data = process_tweet(data)
                self.save_to_csv(tweet_data)

        # Problem with the API
        def on_error(self, status_code, data):
            print(status_code, data)
            self.disconnect()
            
        # Save each tweet to csv file
        def save_to_csv(self, tweet):
            with open(r'twitter_table.csv', 'a') as f:
                writer = csv.writer(f)
                writer.writerow(list(tweet.values()))

    # Instantiate from our streaming class
    stream = MyStreamer(creds['CONSUMER_KEY'], creds['CONSUMER_SECRET'], 
                        creds['ACCESS_TOKEN'], creds['ACCESS_SECRET'])

    # Start the stream
    # TODO: Add our keywords
    query_terms = ['stress', 'depressed', 'tired', 'sad', 'hate']
    stream.statuses.filter(track=query_terms)

    my_encoding = find_encoding('twitter_table.csv')
    tweets = pd.read_csv('twitter_table.csv', encoding=my_encoding, names=['hashtags', 'text', 'user', 'location'])

    tweets.head()

if __name__ == "__main__": 
    main()