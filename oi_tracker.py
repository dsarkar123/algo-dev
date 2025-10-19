import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
from logger import logger
import pandas as pd
from datetime import datetime, timedelta
import time

class OiTracker:
    def __init__(self, broker, config):
        for k, v in config.items():
            setattr(self, f'strat_var_{k}', v)

        self.broker = broker
        self.broker.download_instruments()
        self.instruments = self.broker.instruments_df
        self.instruments['expiry'] = pd.to_datetime(self.instruments['expiry']).dt.date
        
        nifty_instrument = self.instruments[self.instruments['tradingsymbol'] == 'NIFTY 50']
        if not nifty_instrument.empty:
            self.nifty_instrument_token = nifty_instrument.iloc[0]['instrument_token']
        else:
            self.nifty_instrument_token = None
            logger.error("NIFTY 50 instrument not found.")


    def _nifty_quote(self):
        return self.broker.get_quote(self.strat_var_index_symbol)

    def _get_strikes_to_track(self):
        current_price = self._nifty_quote()[self.strat_var_index_symbol]['last_price']
        atm_strike = round(current_price / self.strat_var_strike_difference) * self.strat_var_strike_difference
        
        num_strikes = (self.strat_var_strikes_to_track - 1) // 2
        
        strikes = [atm_strike + i * self.strat_var_strike_difference for i in range(-num_strikes, num_strikes + 1)]
        return strikes

    def _get_instrument_token(self, strike, option_type):
        today = datetime.now().date()
        
        nifty_options = self.instruments[
            (self.instruments['name'] == self.strat_var_symbol_initials) &
            (self.instruments['instrument_type'] == option_type) &
            (self.instruments['strike'] == strike) &
            (self.instruments['expiry'] > today)
        ]
        
        if nifty_options.empty:
            return None, None
        
        closest_expiry_instrument = nifty_options.sort_values('expiry').iloc[0]
        return closest_expiry_instrument['instrument_token'], closest_expiry_instrument['tradingsymbol']

    def run(self):
        while True:
            self.strikes_to_track = self._get_strikes_to_track()
            now = datetime.now()
            self.display_tables(now)
            time.sleep(60)

    def get_oi_data(self, instrument_token, from_date, to_date):
        return self.broker.get_historical_data(instrument_token, from_date, to_date, self.strat_var_historical_data_interval, oi=True)

    def get_nifty_change(self, minutes, now):
        to_date = now
        from_date = to_date - timedelta(minutes=minutes)
        
        if not self.nifty_instrument_token:
            return "N/A", "N/A"

        past_data = self.broker.get_historical_data(self.nifty_instrument_token, from_date, from_date + timedelta(minutes=1), self.strat_var_historical_data_interval)
        past_price = past_data[0]['close'] if past_data else 0
        
        current_price = self._nifty_quote()[self.strat_var_index_symbol]['last_price']

        change = current_price - past_price
        percentage_change = (change / past_price) * 100 if past_price != 0 else 0

        return f"{percentage_change:.2f}% ({change:.2f})", percentage_change

    def display_tables(self, now):
        call_colored_cells = 0
        put_colored_cells = 0

        def get_color(percentage_change, minutes, option_type):
            nonlocal call_colored_cells, put_colored_cells
            thresholds = self.strat_var_color_thresholds
            if percentage_change > thresholds.get(minutes, 1000):
                if option_type == "CE":
                    call_colored_cells += 1
                else:
                    put_colored_cells += 1
                return '\033[91m'  # Red
            return '\033[0m'  # Reset

        headers = ["Strike", "Current OI"] + [f"{m}m" for m in self.strat_var_time_intervals]

        # Call Options Table
        print("\n--- Call Options ---")
        call_table_data = []
        for strike in self.strikes_to_track:
            instrument_token, tradingsymbol = self._get_instrument_token(strike, "CE")
            if instrument_token:
                row = [strike]
                to_date = datetime.now()
                from_date = to_date - timedelta(minutes=1)
                data = self.get_oi_data(instrument_token, from_date, to_date)
                current_oi = data[-1]['oi'] if data else "N/A"
                row.append(current_oi)

                for minutes in self.strat_var_time_intervals:
                    from_date = to_date - timedelta(minutes=minutes)
                    past_data = self.get_oi_data(instrument_token, from_date, from_date + timedelta(minutes=1))
                    past_oi = past_data[0]['oi'] if past_data else 0
                    
                    change = current_oi - past_oi
                    percentage_change = (change / past_oi) * 100 if past_oi != 0 else 0
                    change_str = f"{percentage_change:.2f}% ({change})"
                    
                    color = get_color(percentage_change, minutes, "CE")
                    row.append(f"{color}{change_str}{get_color(0,0, 'CE')}")
                call_table_data.append(row)
        print(pd.DataFrame(call_table_data, columns=headers).to_string(index=False))

        # Put Options Table
        print("\n--- Put Options ---")
        put_table_data = []
        for strike in self.strikes_to_track:
            instrument_token, tradingsymbol = self._get_instrument_token(strike, "PE")
            if instrument_token:
                row = [strike]
                to_date = datetime.now()
                from_date = to_date - timedelta(minutes=1)
                data = self.get_oi_data(instrument_token, from_date, to_date)
                current_oi = data[-1]['oi'] if data else "N/A"
                row.append(current_oi)

                for minutes in self.strat_var_time_intervals:
                    from_date = to_date - timedelta(minutes=minutes)
                    past_data = self.get_oi_data(instrument_token, from_date, from_date + timedelta(minutes=1))
                    past_oi = past_data[0]['oi'] if past_data else 0
                    
                    change = current_oi - past_oi
                    percentage_change = (change / past_oi) * 100 if past_oi != 0 else 0
                    change_str = f"{percentage_change:.2f}% ({change})"
                    
                    color = get_color(percentage_change, minutes, "PE")
                    row.append(f"{color}{change_str}{get_color(0,0, 'PE')}")
                put_table_data.append(row)
        print(pd.DataFrame(put_table_data, columns=headers).to_string(index=False))

        # Nifty Table
        print("\n--- Nifty ---")
        nifty_headers = ["Current Price"] + [f"{m}m" for m in self.strat_var_time_intervals]
        nifty_row = [self._nifty_quote()[self.strat_var_index_symbol]['last_price']]
        for minutes in self.strat_var_time_intervals:
            change_str, _ = self.get_nifty_change(minutes, now)
            nifty_row.append(change_str)
        print(pd.DataFrame([nifty_row], columns=nifty_headers).to_string(index=False))

        total_cells = len(self.strikes_to_track) * len(self.strat_var_time_intervals)
        if total_cells > 0:
            if (call_colored_cells / total_cells * 100) > self.strat_var_alert_threshold_percentage or \
               (put_colored_cells / total_cells * 100) > self.strat_var_alert_threshold_percentage:
                self.play_alert_sound()

    def play_alert_sound(self):
        try:
            import winsound
            winsound.Beep(1000, 500)
        except ImportError:
            print("\a")

if __name__ == "__main__":
    import argparse
    from brokers.zerodha import ZerodhaBroker
    import warnings
    warnings.filterwarnings("ignore")

    import logging
    logger.setLevel(logging.INFO)
    
    parser = argparse.ArgumentParser(description="OI Tracker Strategy")
    parser.add_argument('--config-file', type=str, default='strategy/configs/oi_tracker.yml', help='Path to the configuration file')
    args = parser.parse_args()

    with open(args.config_file, 'r') as f:
        config = yaml.safe_load(f)['default']

    if os.getenv("BROKER_TOTP_ENABLE") == "true":
        logger.info("Using TOTP login flow")
        broker = ZerodhaBroker(without_totp=False)
    else:
        logger.info("Using normal login flow")
        broker = ZerodhaBroker(without_totp=True)

    strategy = OiTracker(broker, config)
    strategy.run()
