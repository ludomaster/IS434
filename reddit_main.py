import datetime as dt
import json
from collections import defaultdict
import praw
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from nltk.sentiment.vader import SentimentIntensityAnalyzer as SIA

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

def get_date(created):
    """
    Converts into correct datetime format
    """
    return dt.datetime.fromtimestamp(created)

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

    # Use this after initializing your credentials
    with open("reddit_credentials.json", "r") as file:
        creds = json.load(file)

    # Initiate with credentials (you may have to comment this out when first initializing your json file)
    reddit = praw.Reddit(client_id=creds["CLIENT_ID"], \
                        client_secret=creds["CLIENT_SECRET"], \
                        user_agent=creds["USER_AGENT"], \
                        username=creds["USERNAME"], \
                        password=creds["PASSWORD"])

    
    # SUBREDDIT(S)
    subreddit = reddit.subreddit('depression+suicidewatch+singapore+SGExams')

    #TODO: Put in correct keywords
    keywords = ['suicidal', 'suicide', 'stress', 'depressed', 'depression', 'sad', 'hate']

    # Getting top up-voted topics of all time
    top_submissions = subreddit.top(limit=25) 

    
    #############################################
    # TABLE DEFINITIONS (Users, Submissions) 3NF    # TODO: Keyword-submission table (many-to-many)
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
                            "subreddit": [],        # Subreddit of submission
                            "created": []}          # Daytime/Nighttime

    keyword_subs = defaultdict(list)                # Sub ID and Keywords

    top_post_users = [] #Each user (author) from the top posts saved to check their other submissions/replies
    riskzone_users = []

    # Sentiment analysis variables
    results = []
    headlines = set()
    sia = SIA()

    #############################################
    # EVALUATION SUBMISSIONS
    #############################################

    for submission in top_submissions:
        for word in keywords:

            # Include posts where title has any of keywords in it
            if word in submission.selftext or word in submission.title:     # Either .selftext (body) or .title (title of post)
                # Adding for sentiment analysis on initial submissions
                #headlines.add(submission.title)

                # Adds each user to a list
                if submission.author not in top_post_users:
                    top_post_users.append(submission.author)


    
    #############################################
    # EVALUATING USERS & THEIR SUBMISSIONS
    #############################################

    for account in top_post_users:
        user = reddit.redditor(str(account))
        user_submissions = user.submissions.new() # Add limit

        # Check every submission that user has made.
        for submission in user_submissions:
            #TODO: Add evaluation constraints (frequency, number of keywords, comments, minimum submissions/comments/replies etc)
            #TODO: SentimentAnalysis
            
            # If keyword is in any of users submissions, they will be printed out.
            for keyword in keywords:
                if keyword in submission.title or keyword in submission.selftext:

                    # Only include unique submissions
                    if submission.id not in user_submissions_dict.get("sub_id"):

                        # Add submission in preparation for sentiment analysis 
                        headlines.add(submission.title)

                        user_submissions_dict["sub_id"].append(submission.id)
                        user_submissions_dict["author_id"].append(user.id)
                        user_submissions_dict["submission"].append(submission.title)
                        user_submissions_dict["subreddit"].append(submission.subreddit)
                        user_submissions_dict["created"].append(submission.created_utc)
                    
                    # If user checks all flags: FLAG ACCOUNT AS RISKY
                    if user not in riskzone_users:
                        riskzone_users.append(user)

                    # Add keywords found in specific sub
                    keyword_subs["sub_id"].append(submission.id)
                    keyword_subs["keyword"].append(keyword)

    # ADD SCORES FOR EACH HEADLINE (in preparation for sentiment analysis)
    for line in headlines:
        pol_score = sia.polarity_scores(line)
        pol_score['title'] = line
        results.append(pol_score)
    
    # ADDS UNIQUE ACCOUNTS AND THEIR DATA
    for user in riskzone_users:
        users_dict["author_id"].append(user.id)
        users_dict["author"].append(user)
        users_dict["submissions"].append(len(list(user.submissions.new())))
        users_dict["comment_karma"].append(user.comment_karma)
        users_dict["link_karma"].append(user.link_karma)
        users_dict["created"].append(user.created_utc)

    #############################################
    # BELOW IS CODE TO RUN WHEN DATA IS COMPLETE
    #############################################

    # Convert dictionary to dataframe to make data more easily readable
    users_data = pd.DataFrame(users_dict)
    users_submissions_data = pd.DataFrame(user_submissions_dict)
    subs_keywords_data = pd.DataFrame(dict(keyword_subs))

    # Fixing column date for users (unix time to actual time)
    _timestamp_users = users_data["created"].apply(get_date)
    users_data = users_data.assign(timestamp=_timestamp_users)

    _timestamp_users_submissions_data = users_submissions_data["created"].apply(get_date)
    users_submissions_data = users_submissions_data.assign(timestamp=_timestamp_users_submissions_data)

    with open('reddit_riskzone_table.csv', 'w+', encoding="utf-8") as file:
        users_data.to_csv(file, index=False)

    with open('reddit_riskzone_submissions_table.csv', 'w+', encoding="utf-8") as file:
        users_submissions_data.to_csv(file, index=False)

    with open('reddit_riskzone_keywords_table.csv', 'w+', encoding="utf-8") as file:
        subs_keywords_data.to_csv(file, index=False)

    ########################################################
    ################## SENTIMENT ANALYSIS ##################
    ########################################################

    ################## PLOTTING BAR CHART ##################

    df = pd.DataFrame.from_records(results)

    fig, ax = plt.subplots(figsize=(8, 8))

    counts = df.risk.value_counts(normalize=True) * 100

    sns.barplot(x=counts.index, y=counts, ax=ax)

    ax.set_xticklabels(['Negative', 'Neutral', 'Positive'])
    ax.set_ylabel("Percentage")

    plt.show()

    #################### DONE PLOTTING  ####################

if __name__ == "__main__":
    main()
