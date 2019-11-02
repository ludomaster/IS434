import datetime as dt
import json
from collections import defaultdict
import praw
import os
import pandas as pd
import seaborn as sns
import nltk
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer as SIA
nltk.download('stopwords')
from nltk.tokenize import word_tokenize

sns.set(style='darkgrid', context='talk', palette='Dark2')

#TODO: Affected vs. Not affected subreddits piechart (from users)
#TODO: Keywords piechart (frequency)
#TODO: Subreddits piechart (frequency)

# General docs: https://praw.readthedocs.io/en/latest/code_overview/models/subreddit.html
# Submissions docs: https://praw.readthedocs.io/en/latest/code_overview/models/submission.html
# Redditor object docs: https://praw.readthedocs.io/en/latest/code_overview/models/redditor.html
# Comments docs: https://praw.readthedocs.io/en/latest/code_overview/models/comment.html

CLIENT_ID = 'YOUR PERSONAL USE SCRIPT (14 CHARS)'
CLIENT_SECRET = 'YOUR SECRET KEY (27 CHARS)'
USER_AGENT = 'YOUR APP NAME'
USERNAME = 'YOUR REDDIT USERNAME'
PASSWORD = 'YOUR REDDIT PASSWORD'

def get_keyword_frequency(k_list):
    freq = {}
    for item in k_list: 
        if item in freq: 
            freq[item] += 1
        else: 
            freq[item] = 1
    return freq

def get_date(created):
    """
    Converts into correct datetime format
    """
    return dt.datetime.fromtimestamp(created)

# This function will be applied to each row in our Pandas Dataframe
def get_keywords(row):
    lowered = row[0].lower()
    tokens = nltk.tokenize.word_tokenize(lowered)
    keywords = [keyword for keyword in tokens if keyword.isalpha() and not keyword in stopwords.words('english')]
    keywords_string = ','.join(keywords)
    return keywords_string

# Instantiation
def main():
    """
    Initiation docstring
    """
    credentials = {}
    credentials['CLIENT_ID'] = CLIENT_ID
    credentials['CLIENT_SECRET'] = CLIENT_SECRET
    credentials['USER_AGENT'] = USER_AGENT
    credentials['USERNAME'] = USERNAME
    credentials['PASSWORD'] = PASSWORD

    # (1) If you haven't saved your json file, use this template first!
    #with open("reddit_credentials.json", "w") as file:
    #    json.dump(credentials, file)

    # (2) Use this after initializing your credentials
    with open("reddit_credentials.json", "r") as file:
        creds = json.load(file)

    # Initiate with credentials (you may have to comment this out when first initializing your json file)
    reddit = praw.Reddit(client_id=creds["CLIENT_ID"], \
                        client_secret=creds["CLIENT_SECRET"], \
                        user_agent=creds["USER_AGENT"], \
                        username=creds["USERNAME"], \
                        password=creds["PASSWORD"])
	
	#read suicide-related keywords in csv
    df = pd.read_csv("suicide_keywords.csv", 
                    header=None,
			        dtype=str,
                    usecols = [i for i in range(1)],
			        sep='+',
			        encoding='latin-1')

    #dropping null value columns to avoid errors 
    df.dropna(inplace=True) 

	#process dataframe to be a list of keywords
    df[0] = df[0].astype(str)
    df[0] = df[0].str.strip()
    df[0] = df.apply(get_keywords, axis=1)
    df[0].apply(word_tokenize)
    df2 = pd.DataFrame(df[0].str.split(',').tolist()).stack()
    df2 = df2.reset_index()


    # SUBREDDIT(S)
    # Subreddit used: 'depression', 'suicidewatch', 'offmychest' TODO: singapore
    chosen_sub = "depression"
    subreddit = reddit.subreddit(chosen_sub)

    # Keywords with only unique values
    keywords = list(filter(None, set(df2[0].astype(str).values.flatten().tolist()))) #remove empty values

    # Getting top up-voted topics of all time (can be any amount from .hot, .top, etc)
    top_submissions = subreddit.top(limit=100)
    
    #############################################
    # TABLE DEFINITIONS (Users, User Submissions) 3NF
    #############################################

    users_dict = {"author_id": [],                  # UserID
                "author": [],                       # User
                "submissions": [],                  # Title of submission
                "comment_karma": [],                # Number of comment karma
                "link_karma": [],                   # Number of link karma
                "created": []}                      # Creation date and time

    user_submissions_dict = {"author_id": [],       # User ID
                            "sub_id": [],           # Sub ID
                            "submission": [],       # Title of submission
                            "comments": [],         # Comments of post
                            "subreddit": [],        # Subreddit of submission
                            "created": []}          # Daytime/Nighttime

    keyword_subs = defaultdict(list)                # Sub ID and Keywords
    keyword_freq = defaultdict(list)                # Keywords and Counter

    # Scraping variables
    top_post_users = [] #Each user (author) from the top posts saved to check their other submissions/replies
    riskzone_users = []

    # Sentiment analysis variables
    results = []
    sia = SIA()

    #############################################
    ########## EVALUATION SUBMISSIONS ###########
    #############################################

    # Check each submission from row 68 to get users
    for submission in top_submissions:
        # Iterate through all our keywords
        for word in keywords:
            # Include posts where title any of keywords in it
            if word in submission.title:

                # Adds each user to a list if not already in list
                if submission.author not in top_post_users:
                    top_post_users.append(submission.author)
    
    #############################################
    ####### EVALUATING USERS & SUBMISSIONS ######
    #############################################

    # Iterate through every account from our users
    for account in top_post_users:
        user = reddit.redditor(str(account))            # Redditor object
        user_submissions = user.submissions.new()       # ListingGenerator object containing submissions

        # Iterate through every submission that user has made.
        for submission in user_submissions:
            for keyword in keywords:

                # Check if keyword exists in either title or body
                if keyword in submission.title or keyword in submission.selftext:

                    # Only include unique submissions (if id from submission already exist, ignore)
                    if submission.id not in user_submissions_dict.get("sub_id"):

                        # Sentiment analysis for each submission title
                        pol_score = sia.polarity_scores(submission.title)
                        pol_score['title'] = submission.title
                        results.append(pol_score)

                        # Add data to dictionary (in preparation for pandas to do its thing)
                        user_submissions_dict["sub_id"].append(submission.id)
                        user_submissions_dict["author_id"].append(user.id)
                        user_submissions_dict["submission"].append(submission.title)
                        user_submissions_dict["comments"].append(submission.num_comments)
                        user_submissions_dict["subreddit"].append(submission.subreddit)
                        user_submissions_dict["created"].append(submission.created_utc)
                    
                    # If user checks all flags: FLAG ACCOUNT AS RISKY
                    # TODO: Add constraints to flag user (thresholds for minimum amount of subs with keywords etc)
                    # TODO: Now it adds everyone as long as they have submissions containing keywords
                    if user not in riskzone_users:
                        riskzone_users.append(user)

                    # Add keywords found in specific sub
                    keyword_subs["sub_id"].append(submission.id)
                    keyword_subs["keyword"].append(keyword)

    # Prepare keyword data frequency
    k_count_freq = get_keyword_frequency(keyword_subs["keyword"])
    for k, val in k_count_freq.items():
        keyword_freq["keyword"].append(k)
        keyword_freq["counter"].append(val)


    # ADDS UNIQUE ACCOUNTS AND THEIR DATA
    for user in riskzone_users:
        users_dict["author_id"].append(user.id)
        users_dict["author"].append(user)
        users_dict["submissions"].append(len(list(user.submissions.new())))
        users_dict["comment_karma"].append(user.comment_karma)
        users_dict["link_karma"].append(user.link_karma)
        users_dict["created"].append(user.created_utc)

    # Convert dictionary to dataframe to make data more easily readable
    users_data = pd.DataFrame(users_dict)
    users_submissions_data = pd.DataFrame(user_submissions_dict)
    subs_keywords_data = pd.DataFrame(dict(keyword_freq))

    # Fixing column date for users (unix time to actual time)
    _timestamp_users = users_data["created"].apply(get_date)
    users_data = users_data.assign(timestamp=_timestamp_users)

    _timestamp_users_submissions_data = users_submissions_data["created"].apply(get_date)
    users_submissions_data = users_submissions_data.assign(timestamp=_timestamp_users_submissions_data)

    # Adds column to see wether or not title is risky or not
    df = pd.DataFrame.from_records(results)

    users_submissions_data['risk'] = 0
    users_submissions_data.loc[df['compound'] > 0.2, 'risk'] = 1
    users_submissions_data.loc[df['compound'] < -0.2, 'risk'] = -1

    # Check if directory exists
    directory = f'subreddits/{chosen_sub}/'
    if not os.path.exists(directory):
        os.makedirs(directory)

    with open(f'subreddits/{chosen_sub}/reddit_{chosen_sub}_users.csv', 'w+', encoding="utf-8", newline='') as file:
        users_data.to_csv(file, index=False)

    with open(f'subreddits/{chosen_sub}/reddit_{chosen_sub}_submissions.csv', 'w+', encoding="utf-8", newline='') as file:
        users_submissions_data.to_csv(file, index=False)

    with open(f'subreddits/{chosen_sub}/reddit_{chosen_sub}_keywords.csv', 'w+', encoding="utf-8", newline='') as file:
        subs_keywords_data.to_csv(file, index=False)

if __name__ == "__main__":
    main()
