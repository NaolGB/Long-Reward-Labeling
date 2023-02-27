import pandas as pd
import numpy as np
import tensorflow as tf

class MLHelper():
    def __init__(self, df: pd.DataFrame, history_length: int) -> None:
        self.df = df
        self.train_features = []
        self.train_labels = []
        self.history_length = history_length

        self.lstm_model = tf.keras.Sequential([
            tf.keras.layers.LSTM(16, return_sequences=False, input_shape=(self.history_length, 1)),
            tf.keras.layers.Dense(units=8, activation='relu'),
            tf.keras.layers.Dense(units=1),
        ])

        self.lstm_model.compile(
            loss=tf.keras.losses.MeanAbsoluteError(),
            optimizer=tf.keras.optimizers.legacy.Adam(),
            metrics=[tf.keras.metrics.MeanAbsoluteError()]
        )

    def create_features_labels(self) -> tuple:
        """
        using featurs[0:127] (inclusive) predict target[128]
        """

        for i in range(self.history_length, len(self.df)): 
            # self.df.loc[i: i+1] returns including i+1
            # nd[i:i+2] retrns excluding i+2
            self.train_features.append(self.df['change'][i-self.history_length:i])
            self.train_labels.append(self.df['long_utility_context_ema'][i])

        # changing to numpy array for easy inputting to the model
        """
        to predict the change at index 128, stored in self.train_labels[128-history_length] (self.train_labels[0]), 
        the training data used will be from 0 to 127, stored in train_featurs[0, 0:128]
        """
        self.train_features = np.expand_dims(np.array(self.train_features), axis=2)
        self.train_labels = np.array(self.train_labels)

        # cehck to make all values are accounted for, no misalignment
        assert np.unique(np.isnan(self.train_features))[0] == False, "nan detected in self.train_features, check for misalignment"
        assert np.unique(np.isnan(self.train_labels))[0] == False, "nan detected in self.train_labels, check for misalignment"
        assert self.train_features.shape[0] == self.train_labels.shape[0], "train_features.shape and train_labels.shape not equal"

        return (self.train_features, self.train_labels)

    def train(self, x_train, y_train, x_eval, y_eval) -> dict:
        history = self.lstm_model.fit(
            x_train, 
            y_train, 
            validation_data=(x_eval, y_eval),
            callbacks=[tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=2, mode='min')],
            epochs=25,
            verbose = 0
        )

        return history.history