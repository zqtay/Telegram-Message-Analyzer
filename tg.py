# This is a Telegram message analyzer.
# Please go to https://telegram.org/blog/export-and-more for instruction on how to export chat history.

# Process preparation
if True:
    from bs4 import BeautifulSoup
    import pandas as pd
    import matplotlib.pyplot as plt
    import os
    from datetime import datetime as dt

    filepath='C:\\Users\\User\\Desktop\\ChatExport_30_12_2018' # Change to the path where all the messages#.html are located
    os.chdir(filepath)

# Empty variables creation
if True:
    msgcount={}     # {name0:{date0:count,date1:count}, name1:{date0:count ... }}
    msgtext={}      # {name0:'string of concatenated texts', name1: ... }
    wordcount={}    # {name0:{word0:count0,word1:count1, ... }, name1:{word0: ... }}
    topwords={}     # {name0:[topword0,topword1,topword2, ... ], name1:[topword0 ... ]}
    msgcounthr={}   # {name0:{hour0:count,hour1:count}, name1:{hour0:count ... }}

# HTML parsing
if True:
    pgind=['']+[str(i) for i in range(2,1+len([i for i in os.listdir(filepath) if i.startswith('message') and i.endswith('.html')]))]
    for n in pgind:
        page=open('.\\messages'+n+'.html',encoding='utf8')
        soup = BeautifulSoup(page,'html.parser')
        allmsg = soup.find_all(class_=lambda x: x and x.startswith(('message default')))

        for msg in allmsg:
            #Element selection
            time=msg.find('div',class_="pull_right date details").get('title')
            date=time.split()[0]
            hr=int(time.split()[1][:2])
            name=msg.find('div',class_="from_name")
            text=msg.find('div',class_="text")

            if name is not None:
                name=name.text.strip()
                prevname=name
            else:
                name=prevname

            if text is not None:
                text=text.text.strip().lower()
            else:
                text=''

            # Data aggregation
            if True:
                try:
                    msgcount[name][date] += 1
                except Exception as KeyError:
                    try:
                        msgcount[name][date] = 1
                    except Exception as KeyError:
                        msgcount[name]=dict([(date,1)])

                try:
                    msgcounthr[name][hr] += 1
                except Exception as KeyError:
                    try:
                        msgcounthr[name][hr] = 1
                    except Exception as KeyError:
                        msgcounthr[name]=dict([(hr,1)])

                try:
                    msgtext[name]+=text+' '
                except Exception as KeyError:
                    msgtext[name]=text+' '

# Data frame preparation
if True:
    #Message count by date
    msgcountdf=pd.DataFrame(msgcount)
    msgcountdf.fillna(0,inplace=True)
    msgcountdf.index = pd.to_datetime(msgcountdf.index,format='%d.%m.%Y')
    msgcountdf.sort_index(inplace=True)
    msgcountdf=msgcountdf.astype(int)
    mcdf=msgcountdf[msgcountdf.columns[0:2]]

    # Message count by time of day
    msgcounthrdf=pd.DataFrame(msgcounthr)
    msgcounthrdf.fillna(0,inplace=True)
    msgcounthrdf.sort_index(inplace=True)
    msgcounthrdf=msgcounthrdf.astype(int)
    mchdf=msgcounthrdf[msgcounthrdf.columns[0:2]]

    #Names
    names=list(mcdf.columns)
    name0,name1=names

# Data analysis
if True:
    # Message count
    stat0=[]
    msgcount0=sum(mcdf[name0])
    msgcount1=sum(mcdf[name1])
    msgcounttot=msgcount0+msgcount1
    msgratio0=round(msgcount0/msgcounttot, 3)
    msgratio1=round(msgcount1/msgcounttot, 3)
    avgmsgday0=round(msgcount0/len(mcdf.index), 3)
    avgmsgday1=round(msgcount1/len(mcdf.index), 3)

    # Character count
    charcount0=len(msgtext[name0].replace(' ',''))
    charcount1=len(msgtext[name1].replace(' ',''))
    charcounttot=charcount0+charcount1
    charratio0=round(charcount0/charcounttot,3)
    charratio1=round(charcount1/charcounttot,3)
    charmsg0=round(charcount0/msgcount0, 3)
    charmsg1=round(charcount1/msgcount1, 3)

    # Word count & most used words
    for name in list(mcdf.columns):
        wcount={}
        for word in msgtext[name].split():
            try:
                wcount[word] += 1
            except Exception as KeyError:
                wcount[word] = 1
        wordcount[name]=wcount
        topwords[name]=sorted(wordcount[name],key=wordcount[name].get, reverse=True)

    # Summary in dataframes
    textrep=pd.DataFrame(data=[[msgcount0, msgratio0, charcount0, charratio0, avgmsgday0, charmsg0],
                               [msgcount1, msgratio1, charcount1, charratio1, avgmsgday1, charmsg1]],
                         index=[name0,name1],
                         columns=['Total message count',
                                  'Total message ratio',
                                  'Total character count',
                                  'Total character ratio',
                                  'Average message count per day',
                                  'Average character count per message']).T.astype(str)
    topwords0=pd.DataFrame(data=[wordcount[name0][x] for x in topwords[name0][0:100]],
                        index=topwords[name0][0:100],
                        columns=[name0])
    topwords1=pd.DataFrame(data=[wordcount[name1][x] for x in topwords[name1][0:100]],
                        index=topwords[name1][0:100],
                        columns=[name1])

# Graph plotting
if True:
    # Message count vs. date
    graphdate=plt.figure(1)
    plt.plot([date for date in mcdf.index], mcdf[name0], label=name0)
    plt.plot([date for date in mcdf.index], mcdf[name1], label=name1)
    plt.title(names[0]+' & '+names[1]+' Telegram Message Frequency by Date')
    plt.xlabel('Date')
    plt.ylabel('No. of messages')
    plt.legend()

    # Message count vs. hour of day
    graphhr=plt.figure(2)
    plt.plot([hr for hr in mchdf.index],mchdf[name0],label=name0)
    plt.plot([hr for hr in mchdf.index],mchdf[name1],label=name1)
    plt.title(names[0]+' & '+names[1]+' Telegram Message Frequency by Time of Day')
    plt.xlabel('Time of day')
    plt.ylabel('No. of messages')
    plt.legend()

# Result and graph display. Switch on to display.
if False:
    graphhr.show()
    graphdate.show()
    display(textrep,mcdf,mchdf,topwords0,topwords1)

# Result and graph saving
if True:
    newfolder=str(dt.now()).replace(':','.')
    os.makedirs(newfolder)
    with open(newfolder+'\\tganalysis.txt','w',encoding='utf8') as f:
        f.writelines("%s\n\n" % line for line in
                     [names[0] +' & ' + names[1] +' Telegram Message Analysis Report\n'+
                      'From ' + str(mcdf.index[0]).split()[0] + ' To ' + str(mcdf.index[-1]).split()[0]+':',
                      '(This analysis report is generated on '+newfolder+')',
                      'Summary:',
                      textrep.to_string(),
                      'Message frequency by date:',
                      mcdf.to_string(),
                     'Message frequency by time of day:',
                      mchdf.to_string(),
                      'Words with the highest occurrence:',
                      topwords0.to_string(),
                      topwords1.to_string()])
        f.close()
    graphdate.savefig(newfolder+'\\graphdate')
    graphhr.savefig(newfolder+'\\graphhr')
    print('Result and graphs are saved in',filepath+'\\'+newfolder)
