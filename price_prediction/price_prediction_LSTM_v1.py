import math
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import Dense, LSTM
from sklearn.metrics import mean_squared_error

df = pd.read_excel("path/nifty_data.xlsx")
df['diff_h_l'] = df['high'] - df['low'] #df['close'].rolling(360).mean()
df = df.iloc[80000:len(df), :]
df.index = range(len(df))

data = df.filter(['close', 'diff_h_l'])
dataset = data.values
training_data_len = math.ceil(len(dataset)*0.7)

scaler = MinMaxScaler(feature_range=(0,1))
scaled_data = scaler.fit_transform(dataset)

train_data = scaled_data[0:training_data_len, : ]
x_train = []
y_train = []
window = 50
for i in range(window, training_data_len):
    x_train.append(train_data[i-window:i, 0:2])
    y_train.append(train_data[i, 0])
    
x_train, y_train = np.array(x_train), np.array(y_train)
x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 2)) #third arg - number of features

model = Sequential()
model.add(LSTM(50, return_sequences=True, input_shape=(x_train.shape[1], 2)))
model.add(LSTM(50, return_sequences=False))
model.add(Dense(25))
model.add(Dense(1))

model.compile(optimizer='adam', loss='mean_squared_error')
model.fit(x_train, y_train, batch_size=1, epochs=70)

test_data = scaled_data[training_data_len-window: , :]
x_test = []
y_test = dataset[training_data_len: , 0]
for i in range(window, len(test_data)):
    x_test.append(test_data[i-window:i, 0:2])
    
x_test = np.array(x_test)
x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 2))
predictions = model.predict(x_test)

z = np.zeros((len(predictions),1))
predictions = np.append(predictions, z, axis=1)
predictions = scaler.inverse_transform(predictions)
predictions = predictions[ :,0].reshape(-1, 1)

print("RMSE: ")
print(mean_squared_error(y_test, predictions, squared=False))
