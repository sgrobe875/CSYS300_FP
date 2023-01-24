import pandas as pd
from labMTsimple.storyLab import emotionFileReader, emotion, stopper, emotionV
import datetime
from string import punctuation
import nltk
from nltk.corpus import stopwords
from collections import Counter
import warnings
warnings.filterwarnings("ignore")
nltk.download('stopwords')
stops = set(stopwords.words('english'))



# load in the preprocessed tweet data
geotagged_tweets = pd.read_csv('data/tweets_processed.csv', dtype=str)

# rename some columns
geotagged_tweets.rename(columns={'tweet_text': 'text'}, inplace=True)
geotagged_tweets.rename(columns={'tweet_created_at': 'created_at'}, inplace=True)



# set up the analyzer
labMT,labMTvector,labMTwordList = emotionFileReader(stopval=0.0,lang='english', returnVector=True)









#### Declare functions ####

# takes in a string, performs preprocessing functions, and returns list of all words in the string
def words_of_tweet(tweet):
  exclude = set(punctuation)  # Keep a set of "bad" characters.
  list_letters_noPunct = [char for char in tweet if char not in exclude]
  text_noPunct = "".join(list_letters_noPunct)
  list_words = text_noPunct.strip().split()
  list_words = [word.lower() for word in list_words]
  return list_words  



# takes in the concatenated string of all tweets in the group
# returns dictionary of word frequencies for that mega string
def get_frequencies(mega_string):
    # get list of individual words
    words = words_of_tweet(mega_string)
    # count how many times each word appears
    word_frequencies = Counter(words)   
    return word_frequencies
            


# takes in a dataframe including state, year, tweet data
# returns the average sentiment for all tweets in each combination of state and year
def group_by_both(df):
    # print update
    print('Beginning grouping by both')
    e = datetime.datetime.now()
    print ("The current time is %s:%s:%s" % (e.hour, e.minute, e.second))
    
    # get list of all unique states and years in the data set
    states = df['state'].unique()
    years = df['year'].unique()
    
    # initialize columns for the final dataframe
    states_col = []
    years_col = []
    sentiment_column = []
    raw_sent_column = []
    
    
    # loop through all states
    for st in states:
        # filter dataframe by the current state
        temp_st = df[df['state'] == st]

        # loop through all years within states
        for yr in years:
            # record the current state and year to the column lists
            states_col.append(st)
            years_col.append(yr)
            
            # get df of all tweets from that state and year
            temp_tweets = temp_st[temp_st['year'] == yr]
            
            # concatenate all these tweets into one large string
            year_tweets = ''
            for index in range(0, len(temp_tweets)):
                year_tweets += str(temp_tweets.iloc[index]['text'])
                year_tweets += ' '  # add a space onto the end to avoid tweets merging together
            
            # garbage collection
            del(temp_tweets)
            
            # get word frequency dictionary
            freqs = get_frequencies(year_tweets)
                        
            del(year_tweets)
            
            # lists to hold sentiments for this group (to be averaged later)
            this_group_sent = []
            this_group_raw = []
            
            # need this line to avoid a ValueError in the for loop 
            keys = list(freqs.keys())
            
            # loop through all keys in the dict (unique words in the group tweets)
            for key in keys:
                # run the sentiment analysis on each of these wrods
                raw_sent, vec = emotion(key, labMT, shift=True, happsList=labMTvector)
                temp = stopper(vec,labMTvector,labMTwordList,stopVal=1.0)
                sentiment = emotionV(temp,labMTvector)
                
                # negative sentiment means cannot be sentimentized, so let's remove it
                if raw_sent < 0 or sentiment < 0:
                    freqs.pop(key)
                
                # if it was successfully sentimentized, append to the list so we can calc the avg
                else:
                    # when appending, multiply the sentiment by how many times that word appears
                    this_group_sent.append(sentiment * freqs[key])
                    this_group_raw.append(raw_sent * freqs[key]) 
            
            # get the total number of words in the mega_sting (must be done after the for loop!)
            num_words = sum(freqs.values())
            
            # divide total sentiment by number of words in the mega string
            try:
                sentiment = sum(this_group_sent)/num_words
                raw_sent = sum(this_group_raw)/num_words
            except ZeroDivisionError:
                sentiment = 0
                raw_sent = 0
            
            # add these averages to the dataframe column lists
            sentiment_column.append(sentiment)
            raw_sent_column.append(raw_sent)
            
            # print an update
            # print('Completed:', st, yr)
            # e = datetime.datetime.now()
            # print ("The current time is %s:%s:%s" % (e.hour, e.minute, e.second))
            # print()
                
    del(temp_st)
    
    # convert to dictionary and then to dataframe
    state_years_grouped = {'state':states_col, 'year': years_col, 'sentiment':sentiment_column, 'raw_sent':raw_sent_column}
    state_years_grouped = pd.DataFrame(state_years_grouped)

    
    # save the results to a file to move to R
    # state_years_grouped.to_csv('data/sentiment/state_year_sentiment.csv', index = False)
    
    # del(state_years_grouped)
    
    print('Completed sentiment analysis for grouping by both')
    e = datetime.datetime.now()
    print ("The current time is %s:%s:%s" % (e.hour, e.minute, e.second))
    print()
    
    return state_years_grouped



# takes in a dataframe including state and tweet data
# returns the average sentiment (across all years) for each state
def group_by_state(df):
    # print update
    print('Beginning grouping by state')
    e = datetime.datetime.now()
    print ("The current time is %s:%s:%s" % (e.hour, e.minute, e.second))
    
    # get list of all unique states in the data set
    states = df['state'].unique()

    # initialize dataframe column lists
    sentiment_column = []
    raw_sent_column = []
    
    # loop through all states
    for st in states:
        # filter by the current state
        temp_tweets = df[df['state'] == st]
            
        # concatenate all these tweets into one large string
        state_tweets = ''
        for index in range(0, len(temp_tweets)):
            state_tweets += str(temp_tweets.iloc[index]['text'])
            state_tweets += ' '  # add a space onto the end to avoid tweets merging together

        # garbage collection
        del(temp_tweets)
        
        # get dictionary of frequency for each word in the mega string
        freqs = get_frequencies(state_tweets)
        
        del(state_tweets)
        
        # lists to hold the sentiments of each word (which will be averaged over)
        this_group_sent = []
        this_group_raw = []
        
        # need this line to avoid a ValueError in the for loop 
        keys = list(freqs.keys())
        
        # loop through all unique words in the mega string
        for key in keys:
            # perform the sentiment analysis on each word
            raw_sent, vec = emotion(key, labMT, shift=True, happsList=labMTvector)
            temp = stopper(vec,labMTvector,labMTwordList,stopVal=1.0)
            sentiment = emotionV(temp,labMTvector)
            
            # negative sentiment means cannot be sentimentized, so let's remove it
            if raw_sent < 0 or sentiment < 0:
                freqs.pop(key)
            
            # if it was successfully sentimentized, append to the list so we can calc the avg
            else:
                # multiply sentiment by how many times that word appears
                this_group_sent.append(sentiment * freqs[key])
                this_group_raw.append(raw_sent * freqs[key]) 
        
        # get the total number of words in the mega_sting (must be done after the for loop!)
        num_words = sum(freqs.values())
        
        # calculate the average sentiment per word
        try:
            sentiment = sum(this_group_sent)/num_words
            raw_sent = sum(this_group_raw)/num_words
        except ZeroDivisionError:
            sentiment = 0
            raw_sent = 0
        
        # add to the dataframe sentiment columns
        sentiment_column.append(sentiment)
        raw_sent_column.append(raw_sent)
        
        # print update
        # print('Completed:', st)
        # e = datetime.datetime.now()
        # print ("The current time is %s:%s:%s" % (e.hour, e.minute, e.second))
        # print()
    
    # convert to dictionary and then to dataframe
    state_grouped = {'state':states, 'sentiment':sentiment_column, 'raw_sent':raw_sent_column}
    state_grouped = pd.DataFrame(state_grouped)

    
    # save the results to a file to move to R
    # state_grouped.to_csv('data/sentiment/state_sentiment.csv', index = False)
    
    # del(state_grouped)
    
    print('Completed sentiment analysis for grouping by state')
    e = datetime.datetime.now()
    print ("The current time is %s:%s:%s" % (e.hour, e.minute, e.second))
    print()
    
    return state_grouped



# takes in a dataframe including year and tweet data
# returns the average sentiment (across all states) for each year
def group_by_year(df):
    # print update
    print('Beginning grouping by year')
    e = datetime.datetime.now()
    print ("The current time is %s:%s:%s" % (e.hour, e.minute, e.second))
    
    # get list of all unique years 
    years = df['year'].unique()

    # initialize dataframe column lists
    sentiment_column = []
    raw_sent_column = []
    
    # loop through all years
    for yr in years:
        # filter by the current year
        temp_tweets = df[df['year'] == yr]
            
        # concatenate all these tweets into one large string
        year_tweets = ''
        for index in range(0, len(temp_tweets)):
            year_tweets += str(temp_tweets.iloc[index]['text'])
            year_tweets += ' '  # add a space onto the end to avoid tweets merging together

        # garbage collection
        del(temp_tweets)
        
        # get the frequency of each word in the mega string
        freqs = get_frequencies(year_tweets)
        
        del(year_tweets)
        
        # lists to hold the sentiments to be averaged
        this_group_sent = []
        this_group_raw = []
        
        # need this line to avoid a ValueError in the for loop 
        keys = list(freqs.keys())
        
        # loop through each unique word in the mega string
        for key in keys:
            # perform the sentiment analysis on the individual word
            raw_sent, vec = emotion(key, labMT, shift=True, happsList=labMTvector)
            temp = stopper(vec,labMTvector,labMTwordList,stopVal=1.0)
            sentiment = emotionV(temp,labMTvector)
            
            # negative sentiment means cannot be sentimentized, so let's remove it
            if raw_sent < 0 or sentiment < 0:
                freqs.pop(key)
            
            # if it was successfully sentimentized, append to the list so we can calc the avg
            else:
                # multiply the sentiment by the number of times the word appears
                this_group_sent.append(sentiment * freqs[key])
                this_group_raw.append(raw_sent * freqs[key]) 

        
        # get the total number of words in the mega_sting (must be done after the for loop!)
        num_words = sum(freqs.values())
        
        # calculate average sentiment per word
        try:
            sentiment = sum(this_group_sent)/num_words
            raw_sent = sum(this_group_raw)/num_words
        except ZeroDivisionError:
            sentiment = 0
            raw_sent = 0
    
        # add to the column list
        sentiment_column.append(sentiment)
        raw_sent_column.append(raw_sent)
        
        # print update
        # print('Completed:', yr)
        # e = datetime.datetime.now()
        # print ("The current time is %s:%s:%s" % (e.hour, e.minute, e.second))
        # print()
    
    # convert to dictionary and then to dataframe using column lists
    year_grouped = {'year':years, 'sentiment':sentiment_column, 'raw_sent':raw_sent_column}
    year_grouped = pd.DataFrame(year_grouped)

    # save the results to a file to move to R
    # year_grouped.to_csv('data/sentiment/year_sentiment.csv', index = False)
    
    # del(year_grouped)
    
    print('Completed sentiment analysis for grouping by year')
    e = datetime.datetime.now()
    print ("The current time is %s:%s:%s" % (e.hour, e.minute, e.second))
    print()
    
    return year_grouped



# takes in a list of strings giving the date and time tweets were posted
# returns a list of months the tweets were posted in the format: YYYY-MM
def get_months(date_time_list):
    return_list = []
    for string in date_time_list:
        try:
            # split string into date and time
            date_time_split = string.split('T')
            # extract just the date
            date = date_time_split[0]
            # year-month = first 7 characters in string
            return_list.append(date[0:7])
        except:
            return_list.append('NA')
        
    return return_list



# takes in a list of strings giving the date and time tweets were posted
# returns a list of days the tweets were posted in the format: YYYY-MM-DD
def get_days(date_time_list):
    return_list = []
    for string in date_time_list:
        try:
            # split string into date and time
            date_time_split = string.split('T')
            # extract just the date
            date = date_time_split[0]
            return_list.append(date)
        except:
            return_list.append('NA')
        
    return return_list



# takes in a dataframe including tweet text and when the tweet was posted
# returns the average sentiment for each month of each year
def group_by_month(df):
    # begin by building the month column with the get_months function
    # print('Building month column')        
    # print()
    
    # call get_months with the entire 'created_at' column
    df['month'] = get_months(list(df['created_at']))
    
    # print update
    print('Beginning grouping by month')
    e = datetime.datetime.now()
    print ("The current time is %s:%s:%s" % (e.hour, e.minute, e.second))

    # get list of all unique year-month combos
    months = df['month'].unique()

    # initialize dataframe column lsits
    sentiment_column = []
    raw_sent_column = []
    
    # loop through all months
    for m in months:
        # filter by the current month
        temp_tweets = df[df['month'] == m]
            
        # concatenate all these tweets into one large string
        month_tweets = ''
        for index in range(0, len(temp_tweets)):
            month_tweets += str(temp_tweets.iloc[index]['text'])
            month_tweets += ' '  # add a space onto the end to avoid tweets merging together

        # garbage collection
        del(temp_tweets)
        
        # get the frequency of each word in the mega string
        freqs = get_frequencies(month_tweets)
        
        del(month_tweets)
        
        # lists of sentiments to be averaged over
        this_group_sent = []
        this_group_raw = []
        
        # need this line to avoid a ValueError in the for loop 
        keys = list(freqs.keys())
        
        # loop through each unique word in the mega string
        for key in keys:
            # calculate the sentiment for the individual word
            raw_sent, vec = emotion(key, labMT, shift=True, happsList=labMTvector)
            temp = stopper(vec,labMTvector,labMTwordList,stopVal=1.0)
            sentiment = emotionV(temp,labMTvector)
            
            # negative sentiment means cannot be sentimentized, so let's remove it
            if raw_sent < 0 or sentiment < 0:
                freqs.pop(key)
            
            # if it was successfully sentimentized, append to the list so we can calc the avg
            else:
                # multiply sentiment by how many times the word appears
                this_group_sent.append(sentiment * freqs[key])
                this_group_raw.append(raw_sent * freqs[key]) 

        
        # get the total number of words in the mega_sting (must be done after the for loop!)
        num_words = sum(freqs.values())
        
        # calculate the average sentiment per word
        try:
            sentiment = sum(this_group_sent)/num_words
            raw_sent = sum(this_group_raw)/num_words
        except ZeroDivisionError:
            sentiment = 0
            raw_sent = 0
        
        # add to the dataframe column list
        sentiment_column.append(sentiment)
        raw_sent_column.append(raw_sent)
        
        # print('Completed:', m)
        # e = datetime.datetime.now()
        # print ("The current time is %s:%s:%s" % (e.hour, e.minute, e.second))
        # print()
    
    # convert to dictionary and then to dataframe
    month_grouped = {'month':months, 'sentiment':sentiment_column, 'raw_sent':raw_sent_column}
    month_grouped = pd.DataFrame(month_grouped)

    
    # save the results to a file to move to R
    # month_grouped.to_csv('data/sentiment/month_sentiment.csv', index = False)
    
    # del(month_grouped)
    
    print('Completed sentiment analysis for grouping by month')
    e = datetime.datetime.now()
    print ("The current time is %s:%s:%s" % (e.hour, e.minute, e.second))
    print()
    
    return month_grouped



# takes in a dataframe including tweet text and when the tweet was posted
# returns the average sentiment for each day of each year
def group_by_day(df):
    # begin by building the day column
    # print('Building day column')
    # print()
    
    # call the get_days function with the entire 'created_at' column
    df['day'] = get_days(list(df['created_at']))
    
    # print update
    print('Beginning grouping by day')
    e = datetime.datetime.now()
    print ("The current time is %s:%s:%s" % (e.hour, e.minute, e.second))
    
    # get the list of all unique days
    days = df['day'].unique()
    
    # initialize lists to use as columns in the final dataframe
    sentiment_column = []
    raw_sent_column = []
    
    # loop through all days
    for d in days:
        # filter by the current day
        temp_tweets = df[df['day'] == d]
            
        # concatenate all these tweets into one large string
        day_tweets = ''
        for index in range(0, len(temp_tweets)):
            day_tweets += str(temp_tweets.iloc[index]['text'])
            day_tweets += ' '  # add a space onto the end to avoid tweets merging together

        # garbage collection
        del(temp_tweets)
        
        # get the frequency for each unique word
        freqs = get_frequencies(day_tweets)
        
        del(day_tweets)
        
        # initialize lists for averaging the sentiment
        this_group_sent = []
        this_group_raw = []
        
        # need this line to avoid a ValueError in the for loop 
        keys = list(freqs.keys())
        
        # loop through each unique word in the mega string
        for key in keys:
            # calculate the sentiment for the individual word
            raw_sent, vec = emotion(key, labMT, shift=True, happsList=labMTvector)
            temp = stopper(vec,labMTvector,labMTwordList,stopVal=1.0)
            sentiment = emotionV(temp,labMTvector)
            
            # negative sentiment means cannot be sentimentized, so let's remove it
            if raw_sent < 0 or sentiment < 0:
                freqs.pop(key)
            
            # if it was successfully sentimentized, append to the list so we can calc the avg
            else:
                # multiply the sentiment by the number of times the word appears
                this_group_sent.append(sentiment * freqs[key])
                this_group_raw.append(raw_sent * freqs[key]) 

        
        # get the total number of words in the mega_sting (must be done after the for loop!)
        num_words = sum(freqs.values())
        
        # calculate the average sentiment per word
        try:
            sentiment = sum(this_group_sent)/num_words
            raw_sent = sum(this_group_raw)/num_words
        except ZeroDivisionError:
            sentiment = 0
            raw_sent = 0
        
        # add to the dataframe column list
        sentiment_column.append(sentiment)
        raw_sent_column.append(raw_sent)
        
        # print('Completed:', d)
        # e = datetime.datetime.now()
        # print ("The current time is %s:%s:%s" % (e.hour, e.minute, e.second))
        # print()
    
    # convert to dictionary and then to dataframe
    day_grouped = {'day':days, 'sentiment':sentiment_column, 'raw_sent':raw_sent_column}
    day_grouped = pd.DataFrame(day_grouped)

    
    # save the results to a file to move to R
    # day_grouped.to_csv('data/sentiment/day_sentiment.csv', index = False)
    
    # del(day_grouped)
    
    print('Completed sentiment analysis for grouping by day')
    e = datetime.datetime.now()
    print ("The current time is %s:%s:%s" % (e.hour, e.minute, e.second))
    print()
    
    return day_grouped






####################################






# filter out some unneeded values 
df = pd.DataFrame(geotagged_tweets.loc[(geotagged_tweets["state"]!= "GU") & 
                                       (geotagged_tweets["state"]!= "AS") & 
                                       (geotagged_tweets["state"] != "PR") & 
                                       (geotagged_tweets["state"] != "Unknown") & 
                                       (geotagged_tweets['year'] != "Unknown")])

# filter by retweet type
unique = df[df['tweet_type'] == 'unique']           # only unique tweets
qrts = df[df['tweet_type'] == 'quoted']             # only quote retweets
replies = df[df['tweet_type'] == 'replied_to']      # only reply tweets


print()



## Comment/uncomment the following lines as needed!



# # First do for total data set
# print('Beginning total data set\n')

# month_grouped = group_by_month(df)
# month_grouped.to_csv('data/sentiment/month_sentiment.csv', index = False)
# del(month_grouped)

# # day_grouped = group_by_day(df)
# # day_grouped.to_csv('data/sentiment/day_sentiment.csv', index = False)
# # del(day_grouped)

# state_years_grouped = group_by_both(df)
# state_years_grouped.to_csv('data/sentiment/state_year_sentiment.csv', index = False)
# del(state_years_grouped)

# year_grouped = group_by_year(df)
# year_grouped.to_csv('data/sentiment/year_sentiment.csv', index = False)
# del(year_grouped)

# state_grouped = group_by_state(df)
# state_grouped.to_csv('data/sentiment/state_sentiment.csv', index = False)
# del(state_grouped)

    
    
    
# # For QRTs only:
# print('Beginning QRTs\n')
    
# month_grouped = group_by_month(qrts)
# month_grouped.to_csv('data/sentiment/month_sentiment_qrt.csv', index = False)
# del(month_grouped)

# # day_grouped = group_by_day(qrts)
# # day_grouped.to_csv('data/sentiment/day_sentiment_qrt.csv', index = False)
# # del(day_grouped)

# state_years_grouped = group_by_both(qrts)
# state_years_grouped.to_csv('data/sentiment/state_year_sentiment_qrt.csv', index = False)
# del(state_years_grouped)

# year_grouped = group_by_year(qrts)
# year_grouped.to_csv('data/sentiment/year_sentiment_qrt.csv', index = False)
# del(year_grouped)

# state_grouped = group_by_state(qrts)
# state_grouped.to_csv('data/sentiment/state_sentiment_qrt.csv', index = False)
# del(state_grouped)
    

    
    
# # For RTs only:
# print('Beginning replies\n')
    
# month_grouped = group_by_month(replies)
# month_grouped.to_csv('data/sentiment/month_sentiment_replies.csv', index = False)
# del(month_grouped)

# # day_grouped = group_by_day(replies)
# # day_grouped.to_csv('data/sentiment/day_sentiment_replies.csv', index = False)
# # del(day_grouped)

# state_years_grouped = group_by_both(replies)
# state_years_grouped.to_csv('data/sentiment/state_year_sentiment_replies.csv', index = False)
# del(state_years_grouped)

# year_grouped = group_by_year(replies)
# year_grouped.to_csv('data/sentiment/year_sentiment_replies.csv', index = False)
# del(year_grouped)

# state_grouped = group_by_state(replies)
# state_grouped.to_csv('data/sentiment/state_sentiment_replies.csv', index = False)
# del(state_grouped)




# For unique tweets:
print('Beginning unique tweets only\n')
    
month_grouped = group_by_month(unique)
month_grouped.to_csv('data/sentiment/month_sentiment_unique.csv', index = False)
del(month_grouped)

# day_grouped = group_by_day(unique)
# day_grouped.to_csv('data/sentiment/day_sentiment_unique.csv', index = False)
# del(day_grouped)

state_years_grouped = group_by_both(unique)
state_years_grouped.to_csv('data/sentiment/state_year_sentiment_unique.csv', index = False)
del(state_years_grouped)

year_grouped = group_by_year(unique)
year_grouped.to_csv('data/sentiment/year_sentiment_unique.csv', index = False)
del(year_grouped)

state_grouped = group_by_state(unique)
state_grouped.to_csv('data/sentiment/state_sentiment_unique.csv', index = False)
del(state_grouped)


