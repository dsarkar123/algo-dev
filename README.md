
# How to Run the OI Tracker Program

This guide provides step-by-step instructions to set up and run the OI Tracker strategy.

## 1. Set Up Your Environment

Before running the program, you need to configure your environment and install the required dependencies.

### Create a `.env` File

The program uses a `.env` file to securely manage your broker credentials. Create a file named `.env` in the root directory of the project and add the following content:

```
BROKER_API_KEY="your_api_key"
BROKER_API_SECRET="your_api_secret"
BROKER_ID="your_broker_id"
BROKER_PASSWORD="your_password"
BROKER_TOTP_KEY="your_totp_secret"
BROKER_TOTP_ENABLE="true"
```

Replace the placeholder values with your actual Zerodha Kite Connect credentials. Set `BROKER_TOTP_ENABLE` to `"false"` if you do not wish to use TOTP authentication.

### Configure the Strategy

The settings for the OI Tracker are located in `strategy/configs/oi_tracker.yml`. You can modify this file to change various parameters, including:
- `index_symbol`: The Nifty symbol to track.
- `strike_difference`: The difference between consecutive strike prices.
- `strikes_to_track`: The number of strikes to display (ATM, ITM, OTM).
- `time_intervals`: The time intervals (in minutes) for which to calculate OI changes.
- `color_thresholds`: The percentage change thresholds for color-coding the output.
- `alert_threshold_percentage`: The percentage of colored cells in a table that will trigger an alert.

### Install Dependencies

This project uses `uv` as its package manager. To install the required dependencies, run the following command in your terminal:

```sh
pip install uv
uv pip install -r requirements.txt
```
*Note: If a `requirements.txt` file is not available, you may need to refer to the `pyproject.toml` file for a list of dependencies and install them manually.*

## 2. Run the OI Tracker

Once your environment is set up, you can run the OI Tracker strategy directly from the command line.

Navigate to the root directory of the project and execute the following command:

```sh
python strategy/oi_tracker.py
```

You can also specify a custom configuration file using the `--config-file` argument:

```sh
python strategy/oi_tracker.py --config-file path/to/your/config.yml
```

The program will start, and you will see the live OI and Nifty data tables printed in your console, updating every minute.

## 3. Stop the Program

To stop the OI Tracker, press `Ctrl + C` in the terminal where the script is running.
