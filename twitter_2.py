import tweepy
import json
import pandas as pd
import nltk
import csv
from collections import defaultdict
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from tweepy import OAuthHandler

def retrieve_keyword_dataframe():
    #read suicide-related keywords in csv
    df = pd.read_csv("suicide_keywords.csv", 
                    header=None,
			        dtype=str,
                    usecols=[i for i in range(1)],
			        sep='+',
			        encoding='latin-1')

    #dropping null value columns to avoid errors 
    df.dropna(inplace=True) 

    return df

def process_dataframe(words):
    """
    Prepare suicide keywords dataframe
    """
    words[0] = words[0].astype(str)
    words[0] = words[0].str.strip()
    words[0] = words.apply(get_keywords, axis=1)
    words[0].apply(word_tokenize)
    df2 = pd.DataFrame(words[0].str.split(',').tolist()).stack()
    return df2.reset_index()

def get_keywords(row):
    lowered = row[0].lower()
    tokens = nltk.tokenize.word_tokenize(lowered)
    keywords = [keyword for keyword in tokens if keyword.isalpha() and not keyword in stopwords.words('english')]
    keywords_string = ','.join(keywords)
    return keywords_string

def get_api_authentication():
     # Open json file with credentials (predetermined)
    with open("twitter_credentials.json", "r") as file:
        creds = json.load(file)
        assert creds

    # Declare credentials
    auth = OAuthHandler(creds['CONSUMER_KEY'], creds['CONSUMER_SECRET'])
    auth.set_access_token(creds['ACCESS_TOKEN'], creds['ACCESS_SECRET'])

    # Auth
    return tweepy.API(auth, wait_on_rate_limit=True)

def main():
    """
    Test
    """

    # Authentication
    api = get_api_authentication()
    assert api

    # ----- Data storing -----

    # User's tweets with keyword and the timing
    user_tweets = {"User_ID": [],     # .user.id
                    "Tweet_ID": [],   # .id
                    "Created": [],    # .created_at
                    "Keyword": []     # Affiliated keyword found in tweet
                    }    

    # Users and their information
    users = {"User_ID": [],         # .id
                "Username": [],     # .screen_name
                "Location": [],     # .location
                "Created": [],      # .created_at
                "Followers": [],    # .followers
                "Following": [],    # .following
                "Tweets": []        # .statuses_count
                }

    # Tweets and its information
    tweets = {"Tweet_ID": [],       # .id
                "Tweet": [],        # .text/.full_text (normal/extended tweet)
                "Created": [],      # .created_at
                "Retweets": [],     # .retweets
                "Likes": []         # .favourites
                }

    tweet_keyword_counter = defaultdict()
    user_ids = []

    # Get dataframe with keywords
    df = retrieve_keyword_dataframe()

    # Process dataframe to be a list of keywords
    df2 = process_dataframe(df)

    # Keywords with only unique values
    keywords = list(filter(None, set(df2[0].astype(str).values.flatten().tolist())))

    # main algorithm (getting users from initial search)
    # tweepy.Cursor object methods include: author, 
    for word in keywords:
        for status in tweepy.Cursor(api.search, 
                                    q=word,
                                    tweet_mode='extended', lang="en").items(10):

            # Add to user account list to then iterate through
            if status.user.id not in user_ids:
                user_ids.append(status.user.id)

            # User information
            if status.user.id not in users["User_ID"]:
                users["User_ID"].append(status.user.id)
                users["Username"].append(status.user.screen_name)
                users["Location"].append(status.user.location)
                users["Created"].append(status.user.created_at)
                users["Followers"].append(status.user.followers_count)
                users["Following"].append(status.user.friends_count)
                users["Tweets"].append(status.user.statuses_count)
            
            # Tweet information
            if status.id not in tweets["Tweet_ID"]:
                tweets["Tweet_ID"].append(status.id)
                tweets["Tweet"].append(status.full_text)
                tweets["Created"].append(status.created_at)
                tweets["Retweets"].append(status.retweet_count)
                tweets["Likes"].append(status.favorite_count)
            
    # Check all users tweets
    # TODO
        ## User and tweet information
        #user_tweets["User_ID"].append(status.user.id)
        #user_tweets["Tweet_ID"].append(status.id)
        #user_tweets["Created"].append(status.created_at)
        #user_tweets["Keyword"].append(word)
        # TODO: Polarity score column

    # SENTIMENT ANALYSIS
    # TODO

    # PANDAS AND CSV WRITING

    user_tweet_df = pd.DataFrame(user_tweets)
    users_df = pd.DataFrame(users)
    tweets_df = pd.DataFrame(tweets)

    user_tweet_df.sort_values(by=['User_ID', 'Tweet_ID']) # TODO: Not working

    # Users and tweets
    #with open(f'tweets/twitter_user_submissions.csv', 'w+', encoding="utf-8", newline='') as file:
    #    user_tweet_df.to_csv(file, index=False)

    # Users
    with open(f'tweets/twitter_users.csv', 'w+', encoding="utf-8", newline='') as file:
        users_df.to_csv(file, index=False)

    # Tweets
    with open(f'tweets/twitter_tweets.csv', 'w+', encoding="utf-8", newline='') as file:
        tweets_df.to_csv(file, index=False)

if __name__ == "__main__":
    main()