# NOTE! Not done at all. Just testing things to later implement in reddit_main.py

import datetime as dt
import json
from collections import defaultdict
import math
import praw
import pandas as pd
import numpy as np
import nltk
import matplotlib.pyplot as plt
import seaborn as sns
from pprint import pprint
from IPython import display
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer as SIA

sns.set(style='darkgrid', context='talk', palette='Dark2')

def main():
    """
    Initiation docstring
    """
    
    # Use this after initializing your credentials
    with open("reddit_credentials.json", "r") as file:
        creds = json.load(file)

    # Initiate with credentials (you may have to comment this out when first initializing your json file)
    reddit = praw.Reddit(client_id=creds["CLIENT_ID"], \
                        client_secret=creds["CLIENT_SECRET"], \
                        user_agent=creds["USER_AGENT"], \
                        username=creds["USERNAME"], \
                        password=creds["PASSWORD"])

    titles = set()
    sia = SIA()
    results = []

    subreddit = reddit.subreddit('depression+suicidewatch+singapore+SGExams')

    # Add submissions from other page
    top_submissions = subreddit.top(limit=100)

    for submission in top_submissions:
        titles.add(submission.title)
        display.clear_output()
    
    for line in titles:
        pol_score = sia.polarity_scores(line)
        pol_score['title'] = line
        results.append(pol_score)

    #pprint(results[:10], width=100)
    
    # Creating a DataFrame from our sentiment analysis results.
    df = pd.DataFrame.from_records(results)
    
    # Add column showing negative/positive by -1/1
    df['risk'] = 0
    df.loc[df['compound'] > 0.2, 'risk'] = 1
    df.loc[df['compound'] < -0.2, 'risk'] = -1
    #print(df.head())

    # # # PRINT TO CSV FILE
    #df2 = df[['title', 'risk']]
    #df2.to_csv('reddit_sentiment_analysis.csv', mode='a', encoding='utf-8', index=False)  

    # # # PRINTING POSITIVE/NEGATIVE TITLES
    #print("Positive titles:\n")
    #pprint(list(df[df['risk'] == 1].title)[:5], width=200)
    #print("\nNegative titles:\n")
    #pprint(list(df[df['risk'] == -1].title)[:5], width=200)

    # # # PRINTING NUMBER AND PERCENTAGE OF TOPICS
    #print(df.risk.value_counts())
    #print(df.risk.value_counts(normalize=True) * 100)

    ########################################################
    ################## PLOTTING BAR CHART ##################
    ########################################################

    fig, ax = plt.subplots(figsize=(8, 8))

    counts = df.risk.value_counts(normalize=True) * 100

    sns.barplot(x=counts.index, y=counts, ax=ax)

    ax.set_xticklabels(['Negative', 'Neutral', 'Positive'])
    ax.set_ylabel("Percentage")

    plt.show()

    ########################################################
    #################### DONE PLOTTING  ####################
    ########################################################









if __name__ == "__main__":
    main()