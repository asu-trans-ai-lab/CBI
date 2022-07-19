import pandas as pd
import time

start_time = time.process_time()

df_reading = pd.read_csv('Reading.csv',encoding='utf-8')

df_reading['year'] = df_reading['measurement_tstamp'].apply(lambda x:x.split(' ')[0].split('/')[2])
df_reading['month'] = df_reading['measurement_tstamp'].apply(lambda x:x.split(' ')[0].split('/')[0])
df_reading['day'] = df_reading['measurement_tstamp'].apply(lambda x:x.split(' ')[0].split('/')[1])
df_reading['hour'] = df_reading['measurement_tstamp'].apply(lambda x:x.split(' ')[1].split(':')[0])
df_reading['minute'] = df_reading['measurement_tstamp'].apply(lambda x:x.split(' ')[1].split(':')[1])

df_reading['month'] = df_reading['month'].apply(lambda x:'0'+x if int(x)<10 else x)
df_reading['day'] = df_reading['day'].apply(lambda x:'0'+x if int(x)<10 else x)
df_reading['hour'] = df_reading['hour'].apply(lambda x:'0'+x if int(x)<10 else x)

df_reading['measurement_tstamp'] = df_reading.apply(lambda x:x.year+'-'+x.month+'-'+x.day+'T'+x.hour+':'+x.minute+':00',axis=1)
df_reading = df_reading.drop(['year','month','day','hour','minute'],axis=1,inplace=False)
df_reading.to_csv('Reading1.csv',index=False)
end_time = time.process_time()

print('Total running time:%d seconds'%(end_time-start_time))