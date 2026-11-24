import pandas as pd

def rollingZ_score(priceX: pd.Series, priceY: pd.Series, hedgeCoefficient: float, window: int) -> pd.Series:
    spread = priceY - hedgeCoefficient * priceX
    z_score = (spread - spread.rolling(window=window).mean()) / spread.rolling(window=window).std()
    return z_score

def signal_generator(zScore: pd.Series, entry: float, exit: float, stop: float) -> pd.DataFrame:
    current_position = 0
    positions = []
    stop_trading = False
    event_list = []
    
    for current_zscore in zScore:
        event = "N/A"
        if current_position == 0 and stop_trading == False: # Neutral
            if current_zscore > entry: # That means that the price between 
               current_position = -1
               event = "Short Entry"
            elif current_zscore < -entry: # That means that the price between 
                current_position = 1
                event = "Long Entry"

        elif current_position == 1: # Long
            if current_zscore >= exit: 
                current_position = 0
                event = "Exit"

            elif current_zscore < -stop:
                current_position = 0
                stop_trading = True
                event = "Hit stop"
            else:
                event = "Holding"

        elif current_position == -1: # Short
            if current_zscore <= exit: 
                current_position = 0
                event = "Exit"
            elif current_zscore > stop:
                current_position = 0
                stop_trading = True
                event = "Hit stop"
            else:
                event = "Holding"

        if stop_trading == True:
            current_position = 0
            if abs(current_zscore) < entry:
                stop_trading = False
                
        positions.append(current_position)
        event_list.append(event)

    signal = pd.DataFrame(
        {"Positions":positions, "Event":event_list},
        index=zScore.index
    )

    return signal


