import json
from collections import defaultdict
import tweepy
from tweepy import OAuthHandler
import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer as SIA

def calculate_frequency(k_list):
    freq = {}
    for item in k_list: 
        if item in freq: 
            freq[item] += 1
        else: 
            freq[item] = 1
    return freq

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
    # Authentication
    api = get_api_authentication()
    assert api

    # ----- Data storing -----

    # Users and their information
    users = {"user_id": [],         # .id
                "username": [],     # .screen_name
                "location": [],     # .location
                "created": [],      # .created_at
                "followers": [],    # .followers_count
                "following": [],    # .friends_count
                "tweets": []        # .statuses_count
                }

    # Tweets and its information
    tweets = {"user_id": [],        # .user.id
                "tweet_id": [],     # .id
                "tweet": [],        # .text/.full_text (normal/extended tweet)
                "is_retweet": [],   #  True/False
                "created": [],      # .created_at
                "retweets": [],     # .retweet_count
                "likes": []         # .favorite_count
                }

    tweet_keyword_counter = defaultdict(list)
    tweet_keyword_freq = defaultdict(list)



    # List definitions
    user_ids = []
    hashtags = []
    results = []

    # SIA Initializer
    sia = SIA()

    # Get dataframe with keywords
    df = retrieve_keyword_dataframe()

    # Process dataframe to be a list of keywords
    df2 = process_dataframe(df)

    # Keywords with only unique values
    keywords = list(filter(None, set(df2[0].astype(str).values.flatten().tolist())))

    # main algorithm (getting users from initial search) (2 tweets per keyword)
    for word in keywords:
        for status in tweepy.Cursor(api.search, 
                                    q=word,
                                    tweet_mode='extended', lang="en").items(2):

            # Add to user account list to then iterate through
            if status.user.id not in user_ids:
                user_ids.append(status.user.id)

    # Check all users tweets
    # 1. For every account id that we've saved from initial search, add user
    # 2. For every tweet in that account (with a limit), add tweet
    # 3. For every keyword in our wordlist
    # 4. If that keyword exist in the current tweet: save information.
    for acc_id in user_ids:
        user = api.get_user(acc_id)

        # Add user information
        if user.id not in users["user_id"]:
            users["user_id"].append(user.id)
            users["username"].append(user.screen_name)
            users["location"].append(user.location)     #TODO: Check if correct location before adding
            users["created"].append(user.created_at)
            users["followers"].append(user.followers_count)
            users["following"].append(user.friends_count)
            users["tweets"].append(user.statuses_count)

        ret = 0
        for status in tweepy.Cursor(api.user_timeline, screen_name=user.screen_name, tweet_mode='extended').items(500):
            for word in keywords:
                if word in status.full_text:

                    # Polarity score
                    pol_score = sia.polarity_scores(status.full_text)
                    pol_score['tweet'] = status.full_text
                    results.append(pol_score)

                    # Add tweet information
                    if status.id not in tweets["tweet_id"]:
                        tweets["user_id"].append(status.user.id)
                        tweets["tweet_id"].append(status.id)
                        tweets["tweet"].append(status.full_text)
                        if hasattr(status, 'retweeted_status'):
                            tweets["is_retweet"].append(True)
                            ret += 1
                        else:
                            tweets["is_retweet"].append(False)
                        tweets["created"].append(status.created_at)
                        tweets["retweets"].append(status.retweet_count)
                        tweets["likes"].append(status.favorite_count)                    

                    # Add hashtags if exists
                    if hasattr(status, "entities"):
                        if "hashtags" in status.entities:
                            hashtag = [ent["text"] for ent in status.entities["hashtags"] if "text" in ent and ent is not None]
                            if hashtag is not None:
                                hashtags.append(hashtag)

                    # Add keywords and their counters
                    tweet_keyword_counter["tweet_id"].append(status.id)
                    tweet_keyword_counter["keyword"].append(word)
                    tweet_keyword_counter["tweet_time"].append(status.created_at)
        acc += 1
    
    # Get keyword and each frequency
    k_count_freq = calculate_frequency(tweet_keyword_counter["keyword"])
    for k, val in k_count_freq.items():
        tweet_keyword_freq["keyword"].append(k)
        tweet_keyword_freq["counter"].append(val)
    
    # PANDAS AND CSV WRITING
    users_df = pd.DataFrame(users)
    tweets_df = pd.DataFrame(tweets)
    keys_df = pd.DataFrame(tweet_keyword_freq)

    # Adds column to see wether or not title is risky or not
    df = pd.DataFrame.from_records(results)
    tweets_df['risk'] = 0
    tweets_df.loc[df['compound'] > 0.2, 'risk'] = 1
    tweets_df.loc[df['compound'] < -0.2, 'risk'] = -1

    # Users
    with open(f'tweets/twitter_users.csv', 'w+', encoding="utf-8", newline='') as file:
        users_df.to_csv(file, index=False)

    # Tweets
    with open(f'tweets/twitter_tweets.csv', 'w+', encoding="utf-8", newline='') as file:
        tweets_df.to_csv(file, index=False)

    # Keywords with datetime
    with open(f'tweets/twitter_keywords.csv', 'w+', encoding='utf-8', newline='') as file:
        keys_df.to_csv(file, index=False)

if __name__ == "__main__":
    main()