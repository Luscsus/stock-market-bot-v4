closed = True
own_stock_position = False
own_stock_orders = False
own_stocks_today = False
today_stocks = {}
while True:
    symbols = {
        "A",
        "CPAH",
        "MSFT"
    }
    for key in symbols:
        import time
        from passwords/blob/master/passwords import secret_key, id_key, alpha_vantage_key, email, password, send_to_email
        import alpaca_trade_api as tradeapi
        from datetime import date
        import requests
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        url = "https://alpha-vantage.p.rapidapi.com/query"
        base_url = "https://paper-api.alpaca.markets"
        subject = "Stock market bot info"
        today = date.today()
        time_now = today.strftime("%d/%m/%Y")
        time_now_week = today.strftime("%Y-%m-%d")

        if key in today_stocks:
            today_stock = today_stocks[key]
            if today_stock == time_now:
                own_stocks_today = True

        api = tradeapi.REST(
            key_id=id_key,
            secret_key=secret_key,
            base_url=base_url
        )
        account = api.get_account()
        asset = api.get_asset(key)
        clock = api.get_clock()
        check_asset = api.get_asset(key)
        portfolio = api.list_positions()
        for position in portfolio:
            if position.symbol == key:
                num_stocks = position.qty
                portfolio_money_change = position.unrealized_pl
                own_stock_position = True
            else:
                own_stock_position = False
        orders = api.list_orders(
            status='open',
            limit=10
        )
        # Get only the closed orders for a particular stock
        orders_for_key = [o for o in orders if o.symbol == key]

        if orders_for_key == []:
            own_stock_orders = False
        else:
            own_stock_orders = True

        if check_asset.tradable:
            pass
        else:
            print("We can't trade this stock")

        if clock.is_open:
            run = True
            closed = True
        else:
            run = False
            if closed:
                stocks = True
                print("Market is not open.")
                balance_change = float(account.equity) - float(account.last_equity)
                print("Account equity today: " + account.equity)
                print("Account equity yesterday: " + account.last_equity)
                print(f"Today\'s portfolio balance change: $ {balance_change}")
                print(time_now)

                message = "Account equity today: " + str(account.equity) + " Balance change: " + str(balance_change)
                msg = MIMEMultipart()
                msg['From'] = email
                msg['To'] = send_to_email
                msg['Subject'] = subject

                msg.attach(MIMEText(message, 'plain'))

                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(email, password)
                text = msg.as_string()
                server.sendmail(email, send_to_email, text)
                server.quit()

                closed = False
            time.sleep(60)
        if run:
            print(key)
            stocks_num = False

            # Check if our account is restricted from trading.
            if account.trading_blocked:
                print('Account is currently restricted from trading.')

            if float(account.buying_power) >= 100:
                money = float(account.buying_power) / 5
            else:
                money = float(account.buying_power) / 3

            r = requests.get(
                "https://www.alphavantage.co/query?function=Global_Quote&symbol=" + key + "&apikey=" + alpha_vantage_key)
            result = r.json()
            p = requests.get(
                "https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY&symbol=" + key + "&apikey=" + alpha_vantage_key)
            result1 = p.json()
            price_high = result1["Weekly Time Series"][time_now_week]['2. high']
            price_low = result1["Weekly Time Series"][time_now_week]['3. low']
            price = result['Global Quote']['05. price']

            limit_buy = float(price_low) + (float(price_low) * 0.5 / 100)

            def buy_stock():
                api.submit_order(
                    symbol=key,
                    qty=1,
                    side='buy',
                    type='limit',
                    time_in_force='gtc',
                    limit_price=limit_buy
                )
                print("bought " + key)

            def sell_stock():
                api.submit_order(
                    symbol=key,
                    qty=num_stocks,
                    side='sell',
                    type='market',
                    time_in_force='gtc'
                )
                print("sold")

            if own_stock_position and own_stocks_today is False and own_stock_orders is False and float(portfolio_money_change) >= 2:
                sell_stock()
                today_stocks.update({key: time_now})

            if own_stock_orders is False and own_stock_position is False and float(money) > float(price):
                buy_stock()
                today_stocks.update({key: time_now})
            time.sleep(60)


