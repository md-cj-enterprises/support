import pandas as pd


class StrategyImplementation:
    def __init__(self, df):
        self.df = df
        df.index = range(len(df))

        self.entry_point = 0
        self.exit_point = 0
        self.profit = 0
        self.trades = 0
        self.signal = 0
        self.signal_type = 0
        self.stop_loss = 0
        self.p3_switch = 'on'



    def get_df(self):
        return self.df




# Heikin Ashi
    def calculate_heiken_values(self, df):
        df["h_close"] = (df["close"]+df["open"]+df["high"]+df["low"])/4.0
        if not 'h_open' in df.columns:
            df.insert(6,'h_open','')
        df.at[0, "h_open"] = df.at[0, 'open']

        for i in range(1, len(df)):
            df.at[i, 'h_open'] = (df.at[i - 1, 'h_open'] + df.at[i - 1, 'h_close'])/2.0

        if not 'h_high' in df.columns:
            df.insert(7,'h_high','')
        df['h_high'] = df[['high', 'h_open', 'h_close']].max(axis=1)
        if not 'h_low' in df.columns:
            df.insert(8,'h_low','')
        df['h_low'] = df[['low', 'h_open', 'h_close']].min(axis=1)
        return df


    # Ichimoku Cloud (a,b,c,d, index)
    # a is the Conversion Line Periods, b is the Baseline Periods, c is the Lagging Span 2 Periods or Leading Span B periods, d is the Displacement
    # index is name or index of the Ichimoku cloud. It'll be suffxed at the name of columns. It is recommended to use numbers.

    def ichimoku_cloud(self, df, a, b, c, d, index):
        # Conversion Line (TenkanSen)
        period_a_high = df['h_high'].rolling(window=a).max()
        period_a_low = df['h_low'].rolling(window=a).min()
        df['conversion_line'  + str(index)] = (period_a_high + period_a_low) / 2
            
        # Base Line (KijunSen)
        period_b_high = df['h_high'].rolling(window=b).max()
        period_b_low = df['h_low'].rolling(window=b).min()
        df['base_line' + str(index)] = (period_b_high + period_b_low) / 2
        
        # Lagging Span (Chiku Span)
        df['lagging_span' + str(index)] = df['h_close'].shift(-(d-1))
        
        #Leading Span A (Senkou A)
        df['leading_span_a' + str(index)] = ((df['conversion_line' + str(index)] + df['base_line' + str(index)]) / 2).shift((d-1))
        
        #Leading Span B (Senkou B)
        df['leading_span_b' + str(index)] = ((df['h_high'].rolling(window=c).max() + df['h_low'].rolling(window=c).min()) / 2).shift((d-1))
        
        #Top leading line of the cloud
        df['top_leading_line' + str(index)] = df[['leading_span_a' + str(index), 'leading_span_b' + str(index)]].max(axis=1, skipna=False)    
        
        #Bottom leading line of the cloud
        df['bottom_leading_line' + str(index)] = df[['leading_span_a' + str(index), 'leading_span_b' + str(index)]].min(axis=1, skipna=False) 
        
        return df

    # Green bar and Red bar
    def green_bar(self, df, i):
        if df.at[i,'h_close'] > df.at[i,'h_open']:
            return 1
        else:
            return 0

    def red_bar(self, df, i):
        if df.at[i,'h_close'] < df.at[i,'h_open']:
            return 1
        else:
            return 0



    # Breakout is Cross with respect to the Heikin Open and the Heikin Close higher or lower than the Leading Line in question.
    # Index indicates the index of the Ichimoku Cloud compared with


    def breakout(self, df, i, index):
        if df.at[i,'h_close'] > df.at[i,'top_leading_line' + str(index)] > df.at[i,'h_open']:
            return 1
            
        elif df.at[i,'h_close'] < df.at[i,'bottom_leading_line' + str(index)] < df.at[i,'h_open']:
            return -1
            
        else:
            return 0
    
    
    def signal_1(self, df, index, i):
        if df.at[i,'top_leading_line' + str(index)] != df.at[i,'bottom_leading_line' + str(index)]:
            if ((df.at[i, 'h_close'] >= df.at[i,'top_leading_line' + str(index)]) and (df.at[i-1, 'h_close'] >= df.at[i-1,'top_leading_line' + str(index)])
                and (df.at[i-2, 'h_close'] >= df.at[i-2,'top_leading_line' + str(index)]) and (df.at[i-3, 'h_close'] > df.at[i-3,'top_leading_line' + str(index)])
                and (df.at[i-3, 'h_open'] < df.at[i-3,'top_leading_line' + str(index)]) and
                max(df.at[i, 'h_high'], df.at[i-1, 'h_high'], df.at[i-2, 'h_high'], df.at[i-3, 'h_high']) <= 1.0045*df.at[i-3,'top_leading_line' + str(index)]):
                return 1
            elif ((df.at[i, 'h_close'] <= df.at[i,'bottom_leading_line' + str(index)]) and (df.at[i-1, 'h_close'] <= df.at[i-1,'bottom_leading_line' + str(index)])
                and (df.at[i-2, 'h_close'] <= df.at[i-2,'bottom_leading_line' + str(index)]) and (df.at[i-3, 'h_close'] < df.at[i-3,'bottom_leading_line' + str(index)])
                and (df.at[i-3, 'h_open'] > df.at[i-3,'bottom_leading_line' + str(index)]) and
                min(df.at[i, 'h_low'], df.at[i-1, 'h_low'], df.at[i-2, 'h_low'], df.at[i-3, 'h_low']) >= 0.9955*df.at[i-3,'bottom_leading_line' + str(index)]):
                return -1
        else:
            return 0
        
    def signal_2(self, df, index, i):
        if df.at[i,'top_leading_line' + str(index)] != df.at[i,'bottom_leading_line' + str(index)]:
            if ((df.at[i-3, 'h_open'] > df.at[i-3,'top_leading_line' + str(index)] >= df.at[i-3, 'h_low']) and (df.at[i-3, 'h_close'] >= df.at[i-3,'top_leading_line' + str(index)]) and
                (df.at[i-2, 'h_close'] > df.at[i-2,'top_leading_line' + str(index)]) and (df.at[i-1, 'h_close'] > df.at[i-1,'top_leading_line' + str(index)]) and
                (df.at[i, 'h_close'] > df.at[i,'top_leading_line' + str(index)]) and
                max(df.at[i, 'h_high'], df.at[i-1, 'h_high'], df.at[i-2, 'h_high'], df.at[i-3, 'h_high']) <= 1.0043*df.at[i-3,'top_leading_line' + str(index)]):
                return 1
            elif ((df.at[i-3, 'h_open'] < df.at[i-3,'bottom_leading_line' + str(index)] <= df.at[i-3, 'h_high']) and (df.at[i-3, 'h_close'] <= df.at[i-3,'bottom_leading_line' + str(index)]) and
                (df.at[i-2, 'h_close'] < df.at[i-2,'bottom_leading_line' + str(index)]) and (df.at[i-1, 'h_close'] < df.at[i-1,'bottom_leading_line' + str(index)]) and
                (df.at[i, 'h_close'] < df.at[i,'bottom_leading_line' + str(index)]) and
                min(df.at[i, 'h_low'], df.at[i-1, 'h_low'], df.at[i-2, 'h_low'], df.at[i-3, 'h_low']) >= 0.9957*df.at[i-3,'bottom_leading_line' + str(index)]):
                return -1
        else:
            return 0
    
    def signal_3(self, df, index, i):
        if df.at[i,'top_leading_line' + str(index)] != df.at[i,'bottom_leading_line' + str(index)]:
            if ((df.at[i-2, 'h_close'] > df.at[i-2,'top_leading_line' + str(index)]) and (df.at[i-1, 'h_close'] > df.at[i-1,'top_leading_line' + str(index)])
                and (df.at[i-2, 'h_open'] < df.at[i-2,'top_leading_line' + str(index)])
                and (df.at[i-2, 'h_high'] < 1.004*df.at[i-2,'top_leading_line' + str(index)]) and (df.at[i-1, 'h_high'] < 1.004*df.at[i-1,'top_leading_line' + str(index)])):
                # and (df.at[i-2, 'h_open'] == df.at[i-2, 'h_low']) and (df.at[i-1, 'h_open'] == df.at[i-1, 'h_low'])):
                return 1
            elif ((df.at[i-2, 'h_close'] < df.at[i-2,'bottom_leading_line' + str(index)]) and (df.at[i-1, 'h_close'] < df.at[i-1,'bottom_leading_line' + str(index)])
                and (df.at[i-2, 'h_open'] > df.at[i-2,'bottom_leading_line' + str(index)])
                and (df.at[i-2, 'h_low'] > 0.996*df.at[i-2,'bottom_leading_line' + str(index)]) and (df.at[i-1, 'h_low'] > 0.996*df.at[i-1,'bottom_leading_line' + str(index)])):
                # and (df.at[i-2, 'h_open'] == df.at[i-2, 'h_high']) and (df.at[i-1, 'h_open'] == df.at[i-1, 'h_high'])):
                return -1
        else:
            return 0
    

    def signal_4(self, df, index, i):
        if df.at[i,'top_leading_line' + str(index)] != df.at[i,'bottom_leading_line' + str(index)]:
            if ((df.at[i-2, 'h_close'] > df.at[i-2,'top_leading_line' + str(index)]) and (df.at[i-1, 'h_close'] > df.at[i-1,'top_leading_line' + str(index)])
                and (df.at[i-2, 'h_open'] < df.at[i-2,'top_leading_line' + str(index)])
                and (df.at[i-2, 'h_high'] < 1.003*df.at[i-2,'top_leading_line' + str(index)]) and (df.at[i-1, 'h_high'] < 1.003*df.at[i-1,'top_leading_line' + str(index)])
                and (df.at[i-2, 'h_open'] == df.at[i-2, 'h_low']) and (df.at[i-1, 'h_open'] == df.at[i-1, 'h_low'])):
                return 1
            elif ((df.at[i-2, 'h_close'] < df.at[i-2,'bottom_leading_line' + str(index)]) and (df.at[i-1, 'h_close'] < df.at[i-1,'bottom_leading_line' + str(index)])
                and (df.at[i-2, 'h_open'] > df.at[i-2,'bottom_leading_line' + str(index)])
                and (df.at[i-2, 'h_low'] > 0.997*df.at[i-2,'bottom_leading_line' + str(index)]) and (df.at[i-1, 'h_low'] > 0.997*df.at[i-1,'bottom_leading_line' + str(index)])
                and (df.at[i-2, 'h_open'] == df.at[i-2, 'h_high']) and (df.at[i-1, 'h_open'] == df.at[i-1, 'h_high'])):
                return -1
        else:
            return 0
    
    def save_values_to_df(self, df, i):
        df.at[i, 'signal_type'] = self.signal_type
        df.at[i, 'exit_point'] = self.exit_point
        df.at[i, 'entry_point'] = self.entry_point
        df.at[i, 'stop_loss'] = self.stop_loss
        df.at[i, 'signal'] = self.signal
        df.at[i, 'p3_switch'] = self.p3_switch

        return df
    
    def cj_strategy_base_line(self, df, i, index):
        
    
        
        #df = ichimoku_cloud(df, p, q, r, s, index)
            
        if (self.signal != 2) and (self.signal != -2):
            if self.p3_switch == 'on':
                if (self.signal_3(df, index, i) == 1) and (df.at[i, 'high'] >= 1.004*df.at[i,'top_leading_line' + str(index)]): #and (ltp < 1.001*df.at[i,'top_leading_line' + str(index)]):
                    self.signal = 2
                    df.at[i, 'final_signal'] = 2
                    self.entry_point = 1.004*df.at[i,'top_leading_line' + str(index)]
                    self.signal_type = 0
                    df = self.save_values_to_df(df, i)
                elif (self.signal_3(df, index, i) == -1) and (df.at[i, 'low'] <= 0.996*df.at[i,'bottom_leading_line' + str(index)]): #and (ltp > 0.99*df.at[i,'bottom_leading_line' + str(index)]):
                    self.signal = -2
                    df.at[i, 'final_signal'] = -2

                    self.entry_point = 0.996*df.at[i-1,'bottom_leading_line' + str(index)]
                    self.signal_type = 0
                    df = self.save_values_to_df(df, i)

                elif (self.signal_3(df, index, i) == 1) or (self.signal_3(df, index, i) == -1):
                    self.p3_switch = 'off'
            elif self.p3_switch == 'off':
                if (df.at[i, 'h_close'] < df.at[i,'top_leading_line' + str(index)]) or (df.at[i, 'h_close'] > df.at[i,'bottom_leading_line' + str(index)]):
                    self.p3_switch = 'on'
                    
            
                    
                    
        if self.signal == 0:
            
            if self.signal_1(df, index, i) == 1:
                self.entry_point = 1.0005 * max(df.at[i, 'h_high'], df.at[i-1, 'h_high'], df.at[i-2, 'h_high'], df.at[i-3, 'h_high'])
                #stop_loss = 0.996 * entry_point
                df.at[i, 'final_signal'] = 1
                #df.at[i, 'stop_loss'] = stop_loss
                self.signal = 1
                self.signal_type = 'p1'
                df = self.save_values_to_df(df, i)

                
            elif self.signal_1(df, index, i) == -1:
                self.entry_point = 0.9995 * min(df.at[i, 'h_low'], df.at[i-1, 'h_low'], df.at[i-2, 'h_low'], df.at[i-3, 'h_low'])
                #stop_loss = 1.004 * entry_point
                df.at[i, 'final_signal'] = -1
                #df.at[i, 'stop_loss'] = stop_loss
                self.signal = -1
                self.signal_type = 'p1'
                df = self.save_values_to_df(df, i)

            
            elif self.signal_2(df, index, i) == 1:
                self.entry_point = 1.0005 * max(df.at[i, 'h_high'], df.at[i-1, 'h_high'], df.at[i-2, 'h_high'], df.at[i-3, 'h_high'])
                #stop_loss = 0.996 * entry_point

                df.at[i, 'final_signal'] = 1
                #df.at[i, 'stop_loss'] = stop_loss
                self.signal = 1
                self.signal_type = 'p2'
                df = self.save_values_to_df(df, i)

                
            elif self.signal_2(df, index, i) == -1:
                self.entry_point = 0.9995 * min(df.at[i, 'h_low'], df.at[i-1, 'h_low'], df.at[i-2, 'h_low'], df.at[i-3, 'h_low'])
                #stop_loss = 1.004 * entry_point
                df.at[i, 'final_signal'] = -1
                #df.at[i, 'stop_loss'] = stop_loss
                self.signal = -1
                self.signal_type = 'p2'
                df = self.save_values_to_df(df, i)

                
        elif self.signal == 1:
            if df.at[i, 'high']  >= self.entry_point: #and ltp < 1.001*self.entry_point:
                self.signal = 2
                df.at[i, 'final_signal'] = 2

                self.signal_type = 0
                df = self.save_values_to_df(df, i)

            elif df.at[i, 'h_close'] < df.at[i,'top_leading_line' + str(index)]:
                self.signal = 0
                df.at[i, 'final_signal'] = 0
                df.at[i, 'turn_to0'] = 1
                self.signal_type = 0
                df = self.save_values_to_df(df, i)
            elif (self.signal_type == 'p1') and (self.signal_2(df, index, i) == 1):
                self.entry_point = 1.0005 * max(df.at[i, 'h_high'], df.at[i-1, 'h_high'], df.at[i-2, 'h_high'], df.at[i-3, 'h_high'])
                #stop_loss = 0.996 * entry_point
                df.at[i, 'final_signal'] = 1
                #df.at[i, 'stop_loss'] = stop_loss
                self.signal = 1
                self.signal_type = 'p2'
                df = self.save_values_to_df(df, i)
            elif (self.signal_type == 'p2') and (self.signal_1(df, index, i) == 1):
                self.entry_point = 1.0005 * max(df.at[i, 'h_high'], df.at[i-1, 'h_high'], df.at[i-2, 'h_high'], df.at[i-3, 'h_high'])
                #stop_loss = 0.996 * entry_point

                df.at[i, 'final_signal'] = 1
                #df.at[i, 'stop_loss'] = stop_loss
                self.signal = 1
                self.signal_type = 'p1'
                df = self.save_values_to_df(df, i)
                
            
        elif self.signal == -1:
            if df.at[i, 'low'] <= self.entry_point: # and ltp > 0.99*self.entry_point:
                self.signal = -2
                df.at[i, 'final_signal'] = -2

                self.signal_type = 0
                df = self.save_values_to_df(df, i)

            elif df.at[i, 'h_close'] > df.at[i,'bottom_leading_line' + str(index)]:
                self.signal = 0
                df.at[i, 'final_signal'] = 0
                df.at[i, 'turn_to0'] = 1
                self.signal_type = 0
                df = self.save_values_to_df(df, i)
            elif (self.signal_type == 'p1') and (self.signal_2(df, index, i) == -1):
                self.entry_point = 0.9995 * min(df.at[i, 'h_low'], df.at[i-1, 'h_low'], df.at[i-2, 'h_low'], df.at[i-3, 'h_low'])
                #stop_loss = 1.004 * entry_point
                df.at[i, 'final_signal'] = -1
                #df.at[i, 'stop_loss'] = stop_loss
                self.signal = -1
                self.signal_type = 'p2'
                df = self.save_values_to_df(df, i)
            elif (self.signal_type == 'p2') and (self.signal_1(df, index, i) == -1):
                self.entry_point = 0.9995 * min(df.at[i, 'h_low'], df.at[i-1, 'h_low'], df.at[i-2, 'h_low'], df.at[i-3, 'h_low'])
                #stop_loss = 1.004 * entry_point
                df.at[i, 'final_signal'] = -1
                #df.at[i, 'stop_loss'] = stop_loss
                self.signal = -1
                self.signal_type = 'p1'
                df = self.save_values_to_df(df, i)
        
        #LTP!!!
        elif self.signal == 2:
            if (self.stop_loss != 0) and (df.at[i, 'low'] <= self.stop_loss):
                df.at[i, 'profit'] = self.stop_loss - self.entry_point
                self.profit += df.at[i, 'profit']
                self.trades += 1
                self.entry_point = 0
                self.exit_point = 0
                self.stop_loss = 0
                self.signal = 0
                df.at[i, 'final_signal'] = 3
                df = self.save_values_to_df(df, i)
                
            elif (self.exit_point != 0) and (df.at[i, 'low'] <= self.exit_point):
                df.at[i, 'profit'] = self.exit_point - self.entry_point
                self.profit += df.at[i, 'profit']
                self.trades += 1
                self.entry_point = 0
                self.stop_loss = 0
                self.signal = 0
                self.exit_point = 0
                df.at[i, 'final_signal'] = 3
                df = self.save_values_to_df(df, i)
                                        
            elif ((df.at[i, 'h_open'] > df.at[i ,'base_line' + str(index)]) and (df.at[i, 'low'] <= 0.9929*df.at[i, 'h_open']) and
                (df.at[i, 'low'] <= 0.9997*df.at[i ,'base_line' + str(index)])):
                df.at[i, 'profit'] = 0.9993*df.at[i ,'base_line' + str(index)] - self.entry_point
                self.profit += df.at[i, 'profit']
                self.trades += 1
                self.entry_point = 0
                self.exit_point = 0
                self.stop_loss = 0
                self.signal = 0
                df.at[i, 'final_signal'] = 3
                df = self.save_values_to_df(df, i)
                
            elif (df.at[i, 'h_open'] > df.at[i ,'top_leading_line' + str(index)] > df.at[i, 'h_close']) and (df.at[i, 'low'] <= 0.9995*df.at[i ,'bottom_leading_line' + str(index)]):
                df.at[i, 'profit'] = 0.9995*df.at[i ,'bottom_leading_line' + str(index)] - self.entry_point
                self.profit += df.at[i, 'profit']
                self.trades += 1
                self.entry_point = 0
                self.exit_point = 0
                self.stop_loss = 0
                self.signal = 0
                df.at[i, 'final_signal'] = 3
                df = self.save_values_to_df(df, i)
                
            if df.at[i, 'final_signal'] != 3:
                if self.exit_point == 0 and (df.at[i-1, 'h_close'] < df.at[i-1, 'base_line' + str(index)] < df.at[i-1, 'h_open']) and (df.at[i, 'h_close'] < df.at[i ,'base_line' + str(index)]):
                    self.exit_point = 0.9997 * min(df.at[i, 'h_low'], df.at[i-1, 'h_low'])
                    df.at[i, 'exit_point'] = self.exit_point
                elif (self.exit_point != 0) and (df.at[i, 'h_close'] >= df.at[i ,'base_line' + str(index)]):
                    self.exit_point = 0
                if self.stop_loss == 0:
                    if df.at[i, 'h_close'] < df.at[i,'top_leading_line' + str(index)]:
                        self.stop_loss = df.at[i, 'h_close']
                        df.at[i, 'stop_loss'] = self.stop_loss
                elif self.stop_loss != 0:
                    if df.at[i, 'h_close'] > df.at[i, 'top_leading_line' + str(index)]:
                        self.stop_loss = 0

        #LTP!!!
        elif self.signal == -2:
            
            if (self.stop_loss != 0) and (df.at[i, 'high'] >= self.stop_loss):
                df.at[i, 'profit'] = self.entry_point - self.stop_loss 
                self.profit += df.at[i, 'profit']
                self.trades += 1
                self.entry_point = 0
                self.exit_point = 0
                self.stop_loss = 0
                self.signal = 0
                df.at[i, 'final_signal'] = -3
                df = self.save_values_to_df(df, i)
                
            elif (self.exit_point != 0) and (df.at[i, 'high'] >= self.exit_point):
                df.at[i, 'profit'] = self.entry_point - self.exit_point
                self.profit += df.at[i, 'profit']
                self.trades += 1
                self.entry_point = 0
                self.stop_loss = 0
                self.signal = 0
                self.exit_point = 0
                df.at[i, 'final_signal'] = -3
                df = self.save_values_to_df(df, i)
                                        
            elif ((df.at[i, 'h_open'] < df.at[i ,'base_line' + str(index)]) and (df.at[i, 'high'] >= 1.0071*df.at[i, 'h_open']) and
                (df.at[i, 'high'] >= 1.0003*df.at[i ,'base_line' + str(index)])):
                df.at[i, 'profit'] = self.entry_point - 1.0003*df.at[i ,'base_line' + str(index)]
                self.profit += df.at[i, 'profit']
                self.trades += 1
                self.entry_point = 0
                self.exit_point = 0
                self.stop_loss = 0
                self.signal = 0
                df.at[i, 'final_signal'] = -3
                df = self.save_values_to_df(df, i)
                
            elif (df.at[i, 'h_open'] < df.at[i ,'bottom_leading_line' + str(index)] < df.at[i, 'h_close']) and (df.at[i, 'high'] >= 1.0005*df.at[i ,'top_leading_line' + str(index)]):
                df.at[i, 'profit'] = self.entry_point - 0.9995*df.at[i ,'top_leading_line' + str(index)]
                self.profit += df.at[i, 'profit']
                self.trades += 1
                self.entry_point = 0
                self.exit_point = 0
                self.stop_loss = 0
                self.signal = 0
                df.at[i, 'final_signal'] = -3
                df = self.save_values_to_df(df, i)
                
            if df.at[i, 'final_signal'] != -3:
                
                if self.exit_point == 0 and (df.at[i-1, 'h_close'] > df.at[i-1, 'base_line' + str(index)] > df.at[i-1, 'h_open']) and (df.at[i, 'h_close'] > df.at[i ,'base_line' + str(index)]):
                    self.exit_point = 1.0003 * max(df.at[i, 'h_high'], df.at[i-1, 'h_high'])
                    df.at[i, 'exit_point'] = self.exit_point
                elif (self.exit_point != 0) and (df.at[i, 'h_close'] <= df.at[i ,'base_line' + str(index)]):
                    self.exit_point = 0
                    
                if self.stop_loss == 0:
                    if df.at[i, 'h_close'] > df.at[i,'bottom_leading_line' + str(index)]:
                        self.stop_loss = df.at[i, 'h_close']
                        df.at[i, 'stop_loss'] = self.stop_loss
                elif self.stop_loss != 0:
                    if df.at[i, 'h_close'] < df.at[i, 'bottom_leading_line' + str(index)]:
                        self.stop_loss = 0
                        
        #print(self.profit)
        #print(self.trades)

        #REMOVE!!!
        return df

            
    ###########################################################################

#df.to_excel('cj_strategy_base_line_for_s&p_for_2022_to_2023_v3.xlsx', index=False)