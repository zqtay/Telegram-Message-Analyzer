# This is a Telegram message analyzer.
# Please go to https://telegram.org/blog/export-and-more for instruction on how to export chat history.

# Process preparation
if True:
    from bs4 import BeautifulSoup
    import pandas as pd
    from tqdm import tqdm
    import imageio
    import matplotlib.pyplot as plt
    plt.ioff()
    import os
    import math
    from datetime import datetime as dt

    print('Telegram Message Analyzer 19.6.7a. Developed by Tay Zong Qing: https://github.com/zqtay/.\n'
          'Please go to https://telegram.org/blog/export-and-more for instruction on how to export chat history.\n')
    data_path = input('Please enter the directory path where all the messages#.html are located:\n')
    os.chdir(data_path)

    stopwords_path = input('Please enter the directory path where all the stopwords_{language}.txt are located:\n')
    stopwords = []
    for stopword_txt in [i for i in os.listdir(stopwords_path) if i.startswith('stopwords') and i.endswith('.txt')]:
        stopwords += open(stopword_txt,'r').read().split('\n')
    stopwords = set(stopwords)

# Empty variables creation
if True:
    msg_count = {}              # {name_0: {date0: count, date1: count}, name_1: {date0: count ... }}
    msg_text = {}               # {name_0: 'string of concatenated texts', name_1: ... }
    word_count = {}             # {name_0: {word0: count0, word1: count1, ... }, name_1: {word0: ... }}
    most_used = {}              # {name_0: [topword0, topword1, topword2, ... ], name_1: [topword0 ... ]}
    most_used_filtered = {}     # Stopwords filtered
    msg_count_hr = {}           # {name_0: {hour0: count, hour1: count}, name_1: {hour0: count ... }}

# HTML parsing
if True:
    html_pages = [i for i in os.listdir(data_path) if i.startswith('message') and i.endswith('.html')]
    for html_page in tqdm(html_pages):
        soup = BeautifulSoup(open(html_page, encoding ='utf8'), 'html.parser')
        msgs = soup.find_all(class_ = lambda x: x and x.startswith('message default'))
        for msg in msgs:
            # HTML element selection
            time = msg.find('div', class_ = "pull_right date details").get('title')
            date = dt.strptime(time.split()[0], '%d.%m.%Y').strftime('%Y-%m-%d')
            hr = int(time.split()[1][:2])
            name = msg.find('div', class_ = "from_name")
            text = msg.find('div', class_ = "text")

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

# Data frame preparation
if True:
    # Message count by date and time of day
    msg_count_df = pd.DataFrame(msg_count)
    msg_count_df.fillna(0, inplace = True)
    msg_count_df.sort_index(level = [0, 1], inplace = True)
    msg_count_df = msg_count_df.astype('int').iloc[:,:2]

    # Names
    names = list(msg_count_df.columns)
    name_0, name_1 = names

# Data analysis
if True:
    # Message count
    chat_stats = {}
    both_total_char = 0
    for name in names:
        chat_stats[name] = {}
        chat_stats[name]['total_msg'] = msg_count_df[name].sum()
        chat_stats[name]['msg_ratio'] = round(msg_count_df[name].sum() / msg_count_df.sum().sum(), 3)
        chat_stats[name]['median_msg_per_day'] = msg_count_df[name].median()
        chat_stats[name]['avg_msg_per_day'] = f'{round(msg_count_df[name].mean(), 3)} +- {round(msg_count_df[name].std(), 3)}'
        chat_stats[name]['total_char'] = len(msg_text[name].replace(' ', ''))
        chat_stats[name]['avg_char_per_msg'] = round(chat_stats[name]['total_char'] / chat_stats[name]['total_msg'], 3)
        both_total_char += chat_stats[name]['total_char']

    for name in names:
        chat_stats[name]['char_ratio'] = round(chat_stats[name]['total_char'] / both_total_char,3)

    # Word count & most used words
    for name in names:
        wcount={}
        for word in msg_text[name].split():
            try:
                wcount[word] += 1
            except Exception as KeyError:
                wcount[word] = 1
        word_count[name] = wcount
        most_used[name] = sorted(word_count[name],
                                 key = word_count[name].get,
                                 reverse = True)

    most_used_filtered = most_used.copy()
    for name in names:
        for stopword in stopwords:
            if stopword in most_used_filtered[name]:
                most_used_filtered[name].remove(stopword)

    # Results in dataframes
    chat_stats_report = pd.DataFrame(chat_stats).rename(
                         index={'total_msg':'Total message count',
                                'msg_ratio':'Total message ratio',
                                'total_char':'Total character count',
                                'char_ratio':'Total character ratio',
                                'avg_char_per_msg':'Average character count per message',
                                'avg_msg_per_day':'Average message count per day',
                                'median_msg_per_day':'Median message count per day'})
    most_used_df_0 = pd.DataFrame(data = [word_count[name_0][x] for x in most_used_filtered[name_0][0:100]],
                                  index = most_used_filtered[name_0][0:100],
                                  columns = [name_0])
    most_used_df_1 = pd.DataFrame(data = [word_count[name_1][x] for x in most_used_filtered[name_1][0:100]],
                                  index = most_used_filtered[name_1][0:100],
                                  columns = [name_1])

# Graph plotting
if True:
    # Message count vs. date
    graph_date = plt.figure(1, figsize = (30, 10))
    plt.bar(msg_count_df.index.levels[0],
            msg_count_df[name_0].sum(level = 0),
            label = name_0)
    plt.bar(msg_count_df.index.levels[0],
            msg_count_df[name_1].sum(level = 0),
            label = name_1,
            bottom = msg_count_df[name_0].sum(level = 0))
    plt.title(f'{name_0} & {name_1}\nTelegram Message Count by Date')
    plt.xlabel('Date')
    plt.ylabel('No. of messages')
    plt.legend()

    # Message count vs. time of day
    graph_hr = plt.figure(2)
    plt.xlim((-1,24))
    plt.bar(msg_count_df.index.levels[1],
            msg_count_df[name_0].sum(level = 1),
            label=name_0)
    plt.bar(msg_count_df.index.levels[1],
            msg_count_df[name_0].sum(level = 1),
            label=name_1,
            bottom = msg_count_df[name_0].sum(level = 1))
    plt.title(f'{name_0} & {name_1}\nTelegram Message Count by Time of Day')
    plt.xlabel('Time of day')
    plt.ylabel('No. of messages')
    plt.legend()

# Result and graph saving
if True:
    result_folder = str(dt.now()).replace(':', '.')
    os.mkdir(result_folder)
    with open(f'{result_folder}\\tganalysis.txt', 'w', encoding='utf8') as f:
        f.writelines("%s\n\n" % line for line in
                     [f'{name_0} & {name_1} Telegram Message Analysis Report\n' +
                      f'From {str(msg_count_df.index[0]).split()[0]} To {str(msg_count_df.index[-1]).split()[0]}:',
                      f'(This analysis report is generated in {result_folder})',
                      'Summary:',
                      chat_stats_report.to_string(),
                      'Message frequency by date:',
                      msg_count_df.sum(level = 0).sort_index().to_string(),
                     'Message frequency by time of day:',
                      msg_count_df.sum(level = 1).sort_index().to_string(),
                      'Words with the highest occurrence:',
                      most_used_df_0.to_string(),
                      most_used_df_1.to_string()])
        f.close()
    graph_date.savefig(f'{result_folder}\graph_date')
    graph_hr.savefig(f'{result_folder}\graph_hr')
    msg_count_df.to_csv(f'{result_folder}\msg_count_df.csv')
    print(f"Result and graphs are saved in '{os.getcwd()}\\{result_folder}'.")

# Aggregated message count GIF creation
if True:
    os.mkdir(f'{result_folder}\\agg_graph_hr')
    agg = {}
    for name in names:
        agg[name] = {}
        for h in range(24):
            agg[name][h] = 0
    agg_df = pd.DataFrame(agg).fillna(value = 0).astype('int')

    for date in tqdm(msg_count_df.index.levels[0]):
        agg_df += msg_count_df.loc[date]
        agg_graph_hr = plt.figure(3)
        plt.xlim((-1,24))
        ylim_max = int(math.ceil(msg_count_df.sum(level=1).sum(axis=1).max() / 1000) * 1000)
        plt.ylim((0,ylim_max))
        plt.bar(agg_df[name_0].index,
                agg_df[name_0],
                label=name_0)
        plt.bar(agg_df[name_1].index,
                agg_df[name_1],
                label=name_1,
                bottom = agg_df[name_0])
        plt.title(f'{name_0} & {name_1}\nTelegram Message Count by Time of Day\nby {date}')
        plt.xlabel('Time of day')
        plt.ylabel('No. of messages')
        plt.legend()
        agg_graph_hr.savefig(f'{result_folder}\\agg_graph_hr\{date}.png')
        plt.close()

    with imageio.get_writer(f'{result_folder}\\agg_graph_hr.gif', mode='I') as writer:
        for filename in os.listdir(f'{result_folder}\\agg_graph_hr'):
            image = imageio.imread(f'{result_folder}\\agg_graph_hr\\{filename}')
            writer.append_data(image)
    writer.close()

input('Please press ENTER to exit the program.\n')
