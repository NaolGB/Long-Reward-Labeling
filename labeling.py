import pandas as pd

class Labeling():
    def __init__(self, df: pd.DataFrame, alpha: float, trend_reverse_factor: float, change_tolerance: float, forward_term: int, break_away_point: float) -> None:
        self.df = df
        self.alpha = alpha
        self.trend_reverse_factor = trend_reverse_factor
        self.change_tolerance = change_tolerance
        self.forward_term = forward_term
        self.break_away_point = break_away_point

        # generate close_ema
        self.df['close_ema'] = self.df['close'].ewm(alpha=self.alpha).mean()
        self.df.dropna(inplace=True)
        self.df.reset_index(drop=True, inplace=True)


    def percentage_change(self, start_index: int, end_index: int) -> float:
        # Given two indicies, return the percentage change at the second index form the first index
        return 100 * (self.df.loc[end_index, 'close_ema'] - self.df.loc[start_index, 'close_ema']) / self.df.loc[start_index, 'close_ema']


    def check_exit_long(self, first_index: int, second_index:int) -> list:
        """
            Checks whether the trend from first_index to second_index is broken, return True if there is a reversal
            returns the number of indexes to increase second_index by for the next index to check trend reversal from

            trend_reversal occurs when 
            * trend from second_index to second_index+(upto forward_term) > trend first_index to second_index
            second_index >= first_index + 1

            eg: first_index = 3, 
                second_index = 11, 
                trend from index 3 to 10 = -1.5 (% change), 
                forward_term = 10,
                trend_reversal_factor = 0.3,
                change_tolerance = 0.5

                anytime from index 11 to index 21 if the percentage change >= 0.45, then
                we conclude that the trend reverses at index 11

                in case there are hard turns to the other direction (down trend) in index 4, 5 or
                somewhere around index x, it might be due to the natural volatility of cryptocurrency market
                and the actual trend might be kept intact in later indices. For this reason, we check to see
                if the change from 3 to 11 is greater than a given change_tolerance (0.5) down.            
        """
            
        root_decrease = self.percentage_change(start_index=first_index, end_index=second_index)

        current_change = root_decrease
        next_point_index = second_index
        
        i = 0
        while (i < self.forward_term) or (current_change > 0):
            # check if the current trend is kept for forward_term amount of time 
            next_point_index += 1

            if next_point_index > len(self.df)-1:
                    break

            current_change = self.percentage_change(start_index=second_index, end_index=next_point_index)

            if current_change >= -(root_decrease*self.trend_reverse_factor):
                if abs(self.percentage_change(start_index=first_index, end_index=second_index)) > self.change_tolerance:
                    return [True, 0, 1]
            
            i += 1
            
        # if the change between the first_index and second_index is too much (mostly due to persistent change of price in the
        # preffered directoin), return the first_index + forward_term as the second index to figure out the new trend from 
        # because if the price has broken out of the trend then the algorithm will favor buy-and-hold strategy unless there is
        # a significant change in price in the other direction that will undi all the change since first_index
        if root_decrease <= -self.break_away_point:
            return [False, self.forward_term, 1]
                
            
        # return second_index + 1 because we want the second_index to be the next one for the new iteration 
        # second_index will be sent back to theis function with the next iteration to find the possible trend reversal starting 
        # at second_index
        return [False, 0, 1]


    def check_exit_short(self, first_index: int, second_index: int) -> list:
        """
            Checks whether the trend from first_index to second_index is broken, return True if there is a reversal
            returns the number of indexes to increase second_index by for the next index to check trend reversal from

            trend_reversal occurs when 
            * trend from second_index to second_index+(upto forward_term) < trend first_index to second_index
            second_index >= first_index + 1

            eg: first_index = 3, 
                second_index = 11, 
                trend from index 3 to 10 = 1.5 (% change), 
                forward_term = 10,
                trend_reversal_factor = 0.3,
                change_tolerance = 0.5

                anytime from index 11 to index 21 if the percentage change <= -0.45, then
                we conclude that the trend reverses at index 11

                in case there are hard turns to the other direction (down trend) in index 4, 5 or
                somewhere around index x, it might be due to the natural volatility of cryptocurrency market
                and the actual trend might be kept intact in later indices. For this reason, we check to see
                if the change from 3 to 11 is greater than a given change_tolerance (0.5) down.            
        """
        
        # the increase in closing price EMA from current candle to the next (eg: increase from time=14:00 -> 15:00)
        root_increase = self.percentage_change(start_index=first_index, end_index=second_index)

        current_change = root_increase
        next_point_index = second_index

        i = 0
        # for the totality of our forward term or until current change reverses to negative 
        while (i < self.forward_term) or (current_change < 0):
            # check if the current trend is kept for forward_term amount of time 
            next_point_index += 1

            # avoid 
            if next_point_index > len(self.df) - 1:
                break

            current_change = self.percentage_change(start_index=second_index, end_index=next_point_index)
            
            if current_change <= -(root_increase*self.trend_reverse_factor):
                if abs(self.percentage_change(start_index=first_index, end_index=second_index)) > self.change_tolerance:
                    return [True, 0, 1]
            
            i += 1
            
        # if the change between the first_index and second_index is too much (mostly due to persistent change of price in the
        # preffered directoin), return the first_index + forward_term as the second index to figure out the new trend from 
        # because if the price has broken out of the trend then the algorithm will favor buy-and-hold strategy unless there is
        # a significant change in price in the other direction that will undi all the change since first_index
        if root_increase >= self.break_away_point:
            return [False, self.forward_term, 1]

        
        # return second_index + 1 because we want the second_index to be the next one for the new iteration 
        # second_index will be sent back to theis function with the next iteration to find the possible trend reversal starting 
        # at second_index
        return [False, 0, 1]


    def label_position(self):
        # create initial position with ema
        if self.df.loc[0, 'close_ema'] < self.df.loc[1, 'close_ema']:
            self.df.loc[0, 'position'] = 1
        else:
            self.df.loc[0, 'position'] = 0

        time_n = 0
        time_n_1 = 1

        while (time_n < len(self.df) - 1) and (time_n_1 < len(self.df) - 1):
            # if entry
            if self.df.loc[time_n, 'position'] == 1:
                # if in long, exit into short
                # unitl we get a trend reversal, we continue holding the position
            
                change_position = False

                while change_position == False:
                    change_position, new_first_index_addition, new_second_index_addition = self.check_exit_long(
                        first_index=time_n, 
                        second_index=time_n_1
                    )

                    time_n += new_first_index_addition
                    time_n_1 += new_second_index_addition

                    # to avoid doubling and explosive growth of new_second_index_addition
                    # new_second_index_addition = 1 
                    if (time_n > len(self.df) - 1) or (time_n_1 > len(self.df) - 1):
                        break
                
                # enter new position (short)
                self.df.loc[time_n_1, 'position'] = 0

                # update indices to new position indices
                time_n = time_n_1
                time_n_1 += 1
            else:
                # if in short, exit into long
                # until we get a trend reversal, we continue holding the position
                change_position = False

                while change_position == False:
                    change_position, new_first_index_addition, new_second_index_addition = self.check_exit_short(
                        first_index=time_n, 
                        second_index=time_n_1
                    )

                    time_n += new_first_index_addition
                    time_n_1 += new_second_index_addition
                    # to avoid doubling and explosive growth of new_second_index_addition
                    # new_second_index_addition = 1
                    if (time_n > len(self.df) - 1) or (time_n_1 > len(self.df) - 1):
                        break
                    
                # enter new position
                self.df.loc[time_n_1, 'position'] = 1

                # update indices to new position indices
                time_n = time_n_1
                time_n_1 += 1
        
        # remove trailing terms after the last position is taken to avoid nan long_utility
        i = len(self.df) - 2
        while pd.isna(self.df.loc[i, 'position']):
            i -= 1

        self.df = self.df[:i+1].copy()


    def label_long_utility(self) -> pd.DataFrame:
        """
        long_utility: the utility value if stategy takes long at that price
        """

        self.label_position()

        i = len(self.df) - 1
        inflection_point_index = i

        while i >= 0:
            if pd.isnull(self.df.loc[i, 'position']):
                self.df.loc[i, 'long_utility'] = self.df.loc[inflection_point_index, 'close_ema'] - self.df.loc[i, 'close_ema']
            else:
                inflection_point_index = i
                self.df.loc[i, 'long_utility'] = self.df.loc[inflection_point_index, 'close_ema'] - self.df.loc[i, 'close_ema']

            i -= 1


        # relative (20 hour) standard scaling forlong_utility
        ema_window = 20
        for i in range(20, len(self.df)):
            x_min = min(self.df.loc[i-ema_window:i, 'long_utility'])
            x_max = max(self.df.loc[i-ema_window:i, 'long_utility'])
            x = self.df.loc[i, 'long_utility']

            self.df.loc[i, 'long_utility_context'] = (x - x_min) / (x_max - x_min)
        
        self.df['long_utility_context_ema'] = self.df['long_utility_context'].ewm(alpha=self.alpha).mean()

        
        self.df = self.df[ema_window:]
        self.df.reset_index(inplace=True, drop=True)

        return self.df