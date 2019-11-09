import json
import tweepy
import pandas as pd
from datetime import datetime, timedelta
from tweepy import OAuthHandler, TweepError
from pandas.io.json import json_normalize
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from statistics import median
from nltk.sentiment.vader import SentimentIntensityAnalyzer as SIA

def get_table():
    # Get appropriate table depending on subreddit

    with open(f'tweets/twitter_tweets.csv', encoding="utf8") as file:
        df = pd.read_csv(file)
    return df

def get_api_authentication():
     # Open json file with credentials (predetermined)
    with open("twitter_credentials.json", "r") as file:
        creds = json.load(file)

    # Declare credentials
    auth = OAuthHandler(creds['CONSUMER_KEY'], creds['CONSUMER_SECRET'])
    auth.set_access_token(creds['ACCESS_TOKEN'], creds['ACCESS_SECRET'])

    # Auth
    return tweepy.API(auth, wait_on_rate_limit=True)

def main():

    # Authenticate (Tweepy)
    api = get_api_authentication()

    # Instantiation
    ps = PorterStemmer()
    sia = SIA()

    # Scoring
    time_scoring = {'01': -1, '02': -1, '03': -1, '04': -1, '05': -0.8, '06': -0.8, '07': -0.6, '08': -0.6,
                '09': -0.4, '10': -0.4, '11': -0.2, '12': -0.2, '13': 0, '14': 0, '15': 0, '16': 0,
                '17': -0.2, '18': -0.2, '19': -0.4, '20': -0.4, '21': -0.6, '22': -0.6, '23': -0.8, '24': -0.8, '00': -0.8}

    # Tables
    _tweets = {'user_id': [],
                'tweet_id': [],
                'throwaway': [],
                'percentage': [],
                'retweet': [],
                'created': [],
                'sentiment': [],
                'likes': [],
                'score': []
                }


    with open('analysis/keyword_sentiment_twitter.json', 'r') as f:
        k_s = json.load(f)

    k_s_scoring = {'kill': [],
                    'hate': [],
                    'depress': [],
                    'die': [],
                    'suicid': [],
                    'anxieti': []
                    }

    keywords = ['kill', 'hate', 'depress', 'die', 'suicid', 'anxieti']
    table = get_table()

    hashtags = {}

    for index, row in table.iterrows():

        is_affected = False
        k_count = 0
        k_values = []

        try:
            current_tweet = api.get_status(row['tweet_id'])
        except TweepError:
            print('Error: Account not found.')
            continue

        tok_tweet = word_tokenize(current_tweet.text)
        stem_tweet = [ps.stem(w) for w in tok_tweet if w.isalpha()]

        for word in keywords:
            if word in stem_tweet:
                is_affected = True
                k_count += 1
                k_values.append(word)
        
        if is_affected:

            # Time
            time = row['created'][11:16]
            time_score = time_scoring[row['created'][11:13]]

            # TODO Hashtags
            if hasattr(current_tweet, "entities"):
                if "hashtags" in current_tweet.entities:
                    tags = [ent["text"] for ent in current_tweet.entities["hashtags"] if "text" in ent and ent is not None]
                    if tags is not None:
                        for h in tags:
                            if h in hashtags:
                                hashtags[h] += 1
                            else:
                                hashtags[h] = 1

            # Sentiment
            pol_score = sia.polarity_scores(row['tweet'])
            sa_scoring = pol_score['compound']
            print(f'    SENTIMENT: {sa_scoring}')

            # KEYWORD SCORING
            if len(k_values) > 1:
                for k in k_values:
                    k_s_scoring[k].append(sa_scoring)
                    k_s[k] = median(k_s_scoring[k])
            else:
                k = k_values[0]
                k_s_scoring[k].append(sa_scoring)
                k_s[k] = median(k_s_scoring[k])

            # Retweet
            is_retweet = -0.2
            retweets = 0
            if hasattr(current_tweet, 'retweeted_status'):
                is_retweet = -0.6
                retweets = current_tweet.retweet_count
                print(f'    RT: True (# of RT\'s: {retweets})')

            likes = current_tweet.favorite_count

            # Throwaway
            tweet_user = api.get_user(row['user_id'])
            tweet_user_created = str(tweet_user.created_at)

            is_throwaway = -0.25
            margin = timedelta(days=30)
            today = datetime.today().date()
            date = f'{tweet_user_created[5:7]}-{tweet_user_created[8:10]}-{tweet_user_created[:4]}'
            acc_date = datetime.strptime(date, '%m-%d-%Y').date()
            diff = today - acc_date

            if (today - margin <= acc_date <= today + margin):
                is_throwaway = -1

            # User submissions
            count = 0
            _user_tweets = tweepy.Cursor(api.user_timeline, screen_name=tweet_user.screen_name, tweet_mode='extended').items(100)
            _user_tweets_total = 0
            for status in _user_tweets:
                _user_tweets_total += 1
                for k in keywords:
                    if k in status.full_text:
                        count += 1

            # Percentage (replies) 
            try:
                percentage = count / _user_tweets_total
            except ZeroDivisionError:
                percentage = 0
                print("Error: User hasn't made any submissions.")
            perc_2dm = round(percentage, 2)

            perc_score = 0
            if round(perc_2dm, 1) > 0.8:
                perc_score = -1
            elif perc_2dm > 0.6 and perc_2dm < 0.8:
                perc_score = -0.8
            elif perc_2dm > 0.4 and perc_2dm < 0.6:
                perc_score = -0.6
            elif perc_2dm > 0.2 and perc_2dm < 0.4:
                perc_score = -0.4
            elif perc_2dm < 0.2:
                perc_score = -0.1

            # Median scoring
            score = median([time_score, sa_scoring, is_retweet, is_throwaway, perc_score])

            # Tweets saved to table
            if current_tweet.id not in _tweets['tweet_id']:
                _tweets['user_id'].append(tweet_user.id)                # -
                _tweets['tweet_id'].append(current_tweet.id)            # -    
                _tweets['throwaway'].append(is_throwaway)               # DONE
                _tweets['percentage'].append(perc_score)                # DONE
                _tweets['retweet'].append(is_retweet)                   # DONE
                _tweets['created'].append(time_score)                   # DONE
                _tweets['sentiment'].append(sa_scoring)                 # DONE
                _tweets['likes'].append(likes)                          # TODO
                _tweets['score'].append(score)                          # DONE
        

    # Save json
    with open('analysis/keyword_sentiment_twitter.json', 'w+') as f:
        json.dump(k_s, f)

    with open('analysis/keyword_sentiment_list_twitter.json', 'w+') as f:
        json.dump(k_s_scoring, f)

    # Load data from json keyword sentiment list
    with open('analysis/keyword_sentiment_twitter.json', 'r') as f:
        data = json.loads(f.read())
    
    # Prepare data for csv conversion
    ks_df = json_normalize(data)

    with open('analysis/keyword_sentiment_twitter.csv', 'w+', encoding='utf-8', newline='') as file:
        ks_df.to_csv(file, index=False)

    # Plot dataframe
    tweet_data = pd.DataFrame(_tweets)

    # Write entry to csv
    with open(f'analysis/tweets/twitter_submissions.csv', 'w+', encoding="utf-8", newline='') as file:
        tweet_data.to_csv(file, index=False)

    print(hashtags)

if __name__ == "__main__":
    main()