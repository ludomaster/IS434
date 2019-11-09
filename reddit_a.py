import json
import sys
from datetime import datetime, timedelta
from statistics import median
import pandas as pd
import praw
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from nltk.sentiment.vader import SentimentIntensityAnalyzer as SIA


def get_table(subreddit):
    """
    Returns values from a .csv file.

    Parameters: 
    subreddit: Name of subreddit to fetch data from.

    Returns:
    DataFrame: pandas DataFrame from csv file

    """

    with open(f'subreddits/{subreddit}/reddit_{subreddit}_submissions.csv', encoding="utf8") as file:
        df = pd.read_csv(file)
    return df

def authentication():
    """
    Connects to the reddit API (PRAW).

    Returns:
    Reddit: Reddit API authentication

    """
    with open("reddit_credentials.json", "r") as file:
        creds = json.load(file)

    # Initiate with credentials (you may have to comment this out when first initializing your json file)
    reddit = praw.Reddit(client_id=creds["CLIENT_ID"],
                         client_secret=creds["CLIENT_SECRET"],
                         user_agent=creds["USER_AGENT"],
                         username=creds["USERNAME"],
                         password=creds["PASSWORD"])
    
    return reddit

def main(arg):

    r = authentication()
    ps = PorterStemmer()

    _submissions = {'user_id': [],
                    'sub_id': [],
                    'throwaway': [],
                    'percentage': [],
                    'created': [],
                    'sentiment': [],
                    'comments': [],
                    'score': []
                    }

    _users_scored = {'user_id': [],
                    'username': [],
                    'throwaway': [],
                    'percentage': [],
                    'score': []
                    }

    time_scoring = {'01': -1, '02': -1, '03': -1, '04': -1, '05': -0.8, '06': -0.8, '07': -0.6, '08': -0.6,
                    '09': -0.4, '10': -0.4, '11': -0.2, '12': -0.2, '13': 0, '14': 0, '15': 0, '16': 0,
                    '17': -0.2, '18': -0.2, '19': -0.4, '20': -0.4, '21': -0.6, '22': -0.6, '23': -0.8, '24': -0.8, '00': -0.8}


    with open('analysis/keyword_sentiment_reddit.json', 'r') as f:
        k_s = json.load(f)

    k_s_scoring = {'kill': [],
                    'hate': [],
                    'depress': [],
                    'die': [],
                    'suicid': [],
                    'anxieti': []
                    }

    # Keywords
    keywords = ['kill', 'hate', 'depress', 'die', 'suicid', 'anxieti']

    sia = SIA()

    table = get_table(arg)
    for index, row in table.iterrows():

        # Setting base values for each submission
        is_affected = False
        k_count = 0
        k_values = []

        # Current submission
        _submission = r.submission(row['sub_id'])

        # Stemming
        tok_word = word_tokenize(row['submission'])
        stem_words = [ps.stem(w) for w in tok_word if w.isalpha()]

        # Check number of keywords (if any) in title
        for word in keywords:
            # Append value to later score
            if word in stem_words:

                # If keyword exist in sub, make affected and append counter
                is_affected = True
                k_count += 1
                k_values.append(word)
                
        # Go on if affected
        if is_affected:

            # TIME SCORING
            time_score = time_scoring[row['timestamp'][11:13]]
            
            # SENTIMENT SCORING
            pol_score = sia.polarity_scores(row['submission'])
            sa_scoring = pol_score['compound']

            # KEYWORD SCORING
            if len(k_values) > 1:
                for k in k_values:
                    k_s_scoring[k].append(sa_scoring)
                    k_s[k] = median(k_s_scoring[k])
            else:
                k = k_values[0]
                k_s_scoring[k].append(sa_scoring)
                k_s[k] = median(k_s_scoring[k])

            comments = row['comments']

            # THROWAWAY SCORING (-1 if throwaway, -0.5 if not)
            _user = r.redditor(str(_submission.author))
            _created = _user.created_utc
            result_s = str(pd.to_datetime(_created, unit='s'))

            is_throwaway = -0.25
            margin = timedelta(days=30)
            today = datetime.today().date()
            date = f'{result_s[5:7]}-{result_s[8:10]}-{result_s[:4]}'
            acc_date = datetime.strptime(date, '%m-%d-%Y').date()

            if (today - margin <= acc_date <= today + margin):
                is_throwaway = -1

            # USER SUBMISSIONS SCORING
            user_submissions = _user.submissions.new(limit=50)

            count = 0
            for user_sub in user_submissions:
                #for k in keywords:
                for k in keywords:

                    # If title or body of sub include any keyword
                    if k in user_sub.title or k in user_sub.selftext:
                        count += 1
            # PERCENTAGE SCORING
            try:
                percentage = count / len(list(_user.submissions.new()))
            except ZeroDivisionError:
                percentage = 0
            perc_2dm = round(percentage, 2)

            # Scoring of percentage
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

            # MEDIAN SUBMISSION SCORING
            score = median([time_score, sa_scoring, is_throwaway, perc_score]) # Comments excluded

            # Submission scoring
            if _submission.id not in _submissions['sub_id']:
                _submissions['user_id'].append(_user.id)                    # No score (used to see user score)
                _submissions['sub_id'].append(_submission.id)               # No score    
                _submissions['throwaway'].append(is_throwaway)              # -1 or 1
                _submissions['percentage'].append(perc_score)               # -1 to 1
                _submissions['sentiment'].append(sa_scoring)                # -1 to 1
                _submissions['comments'].append(comments)                   # No score   
                _submissions['created'].append(time_score)                  # -1 to 0
                _submissions['score'].append(score)                         # -1 to 1   


    # USE BELOW ONLY WHEN SAVING DATA

    # Save json
    #with open('analysis/keyword_sentiment_reddit.json', 'w+') as f:
    #    json.dump(k_s, f)

    #with open('analysis/keyword_sentiment_list_reddit.json', 'w+') as f:
    #    json.dump(k_s_scoring, f)

    # Load data from json keyword sentiment list
    #with open('analysis/keyword_sentiment_reddit.json', 'r') as f:
    #    data = json.loads(f.read())
    
    # Prepare data for csv conversion
    #ks_df = json_normalize(data)

    #with open('analysis/keyword_sentiment_reddit.csv', 'w+', encoding='utf-8', newline='') as file:
    #    ks_df.to_csv(file, index=False)

    #sub_data = pd.DataFrame(_submissions)

    # Write submission data
    #with open(f'analysis/subreddits/{chosen_sub}_submissions.csv', 'w+', encoding="utf-8", newline='') as file:
    #    sub_data.to_csv(file, index=False)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Error: Please include an existing subreddit. (ie, 'python.exe reddit_a.py <subreddit>'")
        print("     List of available subreddits:")
        print("     - 'drepression'")
        print("     - 'foreveralone'")
        print("     - 'offmychest'")
        print("     - 'suicidewatch'")
        print("     - 'singapore'")
    else:
        main(sys.argv[1])