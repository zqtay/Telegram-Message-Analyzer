# This is a Telegram message analyzer.
# Please go to https://telegram.org/blog/export-and-more for instruction on how to export chat history.
VERSION = '21.9.1'

from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
import imageio
import matplotlib
import matplotlib.pyplot as plt
import os
from math import ceil
from statistics import mean, stdev, median
from datetime import datetime as dt

plt.ioff()
matplotlib.use("Agg")
    
# Process preparation
if True:  
    print(f'Telegram Message Analyzer {VERSION}. Developed by Tay Zong Qing: https://github.com/zqtay/.\n'
          'Please go to https://telegram.org/blog/export-and-more for instruction on how to export chat history.\n')
    data_path = input('Please enter the directory path where all the messages#.html are located:\n')
    os.chdir(data_path)
    html_pages = [i for i in os.listdir(data_path) if i.startswith('message') and i.endswith('.html')]
    assert len(html_pages) > 0, 'No chat history files are found in this directory!'
    print(f'{len(html_pages)} chat history files found.')

    stopwords_path = input('Please enter the directory path where all the stopwords_{language}.txt are located:\n')
    stopwords = []
    if os.path.isdir(stopwords_path) == False:
        input("No path entered. Press any key to continue.")
    else:
        stopwords_files = [i for i in os.listdir(stopwords_path) if i.startswith('stopwords') and i.endswith('.txt')]
        if len(stopwords_files) == 0:
            input('No stopwords files are found in this directory! Press any key to continue.')
        else:
            input(f'{len(stopwords_files)} stopwords files found. Press any key to continue.')
            for stopwords_file in stopwords_files:
                stopwords += open(os.path.join(stopwords_path,stopwords_file), 'r').read().split('\n')
            stopwords = set(stopwords)
        
    # Create result folder
    result_folder = str(dt.now()).replace(':', '.')
    os.mkdir(result_folder)
    
# Empty variables creation
if True:
    msg_count = {}  # {name_0: {(date_0, hr_0): count, (date_0, hr_1): count}, name_1: {(date_0, hr_0): count ... }}
    msg_text = {}  # {name_0: 'string of concatenated texts', name_1: ... }
    word_count = {}  # {name_0: {word_0: count, word_1: count, ... }, name_1: {word_0: ... }}
    most_used = {}  # {name_0: [word_0, word_1, word_2, ... ], name_1: [word_0 ... ]}
    most_used_filtered = {}  # Stopwords filtered
    char_count = {}  # {name_0: [count, count, ... ], name_1: [count ...]}

# HTML parsing
if True:
    for html_page in tqdm(html_pages):
        soup = BeautifulSoup(open(html_page, encoding='utf8'), 'html.parser')
        msgs = soup.find_all(class_=lambda x: x and x.startswith('message default'))
        for msg in msgs:
            # HTML element selection
            time = msg.find('div', class_="pull_right date details").get('title')
            date = dt.strptime(time.split()[0], '%d.%m.%Y').strftime('%Y-%m-%d')
            hr = int(time.split()[1][:2])
            name = msg.find('div', class_="from_name")
            text = msg.find('div', class_="text")

            if name is not None:
                name = name.text.strip()
                name_prev = name
            else:
                name = name_prev

            if text is not None:
                text = text.text.strip().lower()
            else:
                text = ''

            # Data aggregation
            if True:
                try:
                    msg_count[name][(date, hr)] += 1
                except Exception as KeyError:
                    try:
                        for h in range(24):
                            msg_count[name][(date, h)] = 0
                    except Exception as KeyError:
                        msg_count[name] = {}
                        for h in range(24):
                            msg_count[name][(date, h)] = 0
                    msg_count[name][(date, hr)] = 1

                try:
                    msg_text[name] += text + ' '
                except Exception as KeyError:
                    msg_text[name] = text + ' '

                try:
                    char_count[name].append(len(text.replace(' ', '')))
                except:
                    char_count[name] = [len(text.replace(' ', ''))]

# Data frame preparation
if True:
    # Message count by date and time of day
    msg_count_df = pd.DataFrame(msg_count)
    msg_count_df.fillna(0, inplace=True)
    msg_count_df.sort_index(level=[0, 1], inplace=True)
    msg_count_df = msg_count_df.astype('int').iloc[:, :2]

    # Names
    names = list(msg_count_df.columns)
    name_0, name_1 = names

# Data analysis
if True:
    # Message count calculation
    chat_stats = {}
    for name in names:
        chat_stats[name] = {}
        chat_stats[name]['Total message count'] = msg_count_df[name].sum()
        chat_stats[name]['Total message ratio'] = round(msg_count_df[name].sum() / msg_count_df.sum().sum(), 3)
        chat_stats[name][
            'Average message count per day'] = f'{round(msg_count_df[name].groupby(level=0).sum().mean(), 3)} +- {round(msg_count_df[name].groupby(level=0).sum().std(), 3)}'
        chat_stats[name]['Median message count per day'] = msg_count_df[name].groupby(level=0).sum().median()
        chat_stats[name]['Total character count'] = sum(char_count[name])
        chat_stats[name]['Total character ratio'] = round(
            sum(char_count[name]) / sum([sum(i) for i in char_count.values()]), 3)
        chat_stats[name][
            'Average character count per message'] = f'{round(mean(char_count[name]), 3)} +- {round(stdev(char_count[name]), 3)}'
        chat_stats[name]['Median character count per message'] = median(char_count[name])

    # Word count & most used words calculation
    for name in names:
        wcount = {}
        for word in msg_text[name].split():
            try:
                wcount[word] += 1
            except Exception as KeyError:
                wcount[word] = 1
        word_count[name] = wcount
        most_used[name] = sorted(word_count[name],
                                 key=word_count[name].get,
                                 reverse=True)

    # Stopwords filtering
    most_used_filtered = most_used.copy()
    for name in names:
        for stopword in stopwords:
            if stopword in most_used_filtered[name]:
                most_used_filtered[name].remove(stopword)

    # Results in dataframes
    chat_stats_report = pd.DataFrame(chat_stats)
    most_used_df_0 = pd.DataFrame(data=[word_count[name_0][x] for x in most_used_filtered[name_0][0:100]],
                                  index=most_used_filtered[name_0][0:100],
                                  columns=[name_0])
    most_used_df_1 = pd.DataFrame(data=[word_count[name_1][x] for x in most_used_filtered[name_1][0:100]],
                                  index=most_used_filtered[name_1][0:100],
                                  columns=[name_1])

# Graph plotting
if True:
    # Message count vs. date
    graph_date = plt.figure(1, figsize=(30, 10))
    date_list = [dt.strptime(date,'%Y-%m-%d') for date in msg_count_df.index.levels[0]]
    plt.bar(date_list,
            msg_count_df[name_0].groupby(level=0).sum(),
            label=name_0)
    plt.bar(date_list,
            msg_count_df[name_1].groupby(level=0).sum(),
            label=name_1,
            bottom=msg_count_df[name_0].groupby(level=0).sum())
    plt.title(f'{name_0} & {name_1}\nTelegram Message Count by Date')
    plt.xlabel('Date')
    plt.ylabel('No. of messages')
    plt.legend()

    # Message count vs. time of day
    graph_hr = plt.figure(2)
    plt.xlim((-1, 24))
    plt.bar(msg_count_df.index.levels[1],
            msg_count_df[name_0].groupby(level=1).sum(),
            label=name_0)
    plt.bar(msg_count_df.index.levels[1],
            msg_count_df[name_0].groupby(level=1).sum(),
            label=name_1,
            bottom=msg_count_df[name_0].groupby(level=1).sum())
    plt.title(f'{name_0} & {name_1}\nTelegram Message Count by Time of Day')
    plt.xlabel('Time of day')
    plt.ylabel('No. of messages')
    plt.legend()

# Result and graph saving
if True:
    with open(f'{result_folder}\\msg_analysis.txt', 'w', encoding='utf8') as f:
        f.writelines("%s\n\n" % line for line in
                     [f'{name_0} & {name_1} Telegram Message Analysis Report\n' +
                      f'From {msg_count_df.index[0][0]} To {msg_count_df.index[-1][0]}:',
                      f'(This analysis report is generated in {result_folder})',
                      'Summary:',
                      chat_stats_report.to_string(),
                      'Message count by date:',
                      msg_count_df.groupby(level=0).sum().sort_index().to_string(),
                      'Message count by time of day:',
                      msg_count_df.groupby(level=1).sum().sort_index().to_string(),
                      'Words with the highest occurrence:',
                      most_used_df_0.to_string(),
                      most_used_df_1.to_string()])
        f.close()
    graph_date.savefig(f'{result_folder}\graph_date')
    graph_hr.savefig(f'{result_folder}\graph_hr')
    msg_count_df.to_csv(f'{result_folder}\msg_count_df.csv')

# Cumulative message count GIF creation
if True:
    os.mkdir(f'{result_folder}\\cum_graph_hr')
    cum = {}
    for name in names:
        cum[name] = {}
        for h in range(24):
            cum[name][h] = 0
    cum_df = pd.DataFrame(cum).fillna(value=0).astype('int')

    for date in tqdm(msg_count_df.index.levels[0]):
        cum_df += msg_count_df.loc[date]
        cum_graph_hr = plt.figure(3)
        plt.xlim((-1, 24))
        ylim_max = int(ceil(msg_count_df.groupby(level=1).sum().sum(axis=1).max() / 1000) * 1000)
        plt.ylim((0, ylim_max))
        plt.bar(cum_df[name_0].index,
                cum_df[name_0],
                label=name_0)
        plt.bar(cum_df[name_1].index,
                cum_df[name_1],
                label=name_1,
                bottom=cum_df[name_0])
        plt.title(f'{name_0} & {name_1}\nCumulative Telegram Message Count by Time of Day\nby {date}')
        plt.xlabel('Time of day')
        plt.ylabel('No. of messages')
        plt.legend()
        cum_graph_hr.savefig(f'{result_folder}\\cum_graph_hr\{date}.png')
        plt.close()
    
    print("Generating GIF...")
    
    with imageio.get_writer(f'{result_folder}\\cum_graph_hr.gif', mode='I') as writer:
        for filename in os.listdir(f'{result_folder}\\cum_graph_hr'):
            image = imageio.imread(f'{result_folder}\\cum_graph_hr\\{filename}')
            writer.append_data(image)
        writer.close()

print(f"Result and graphs are saved in '{os.getcwd()}\\{result_folder}'.")
input('Press any key to exit the program.\n')
