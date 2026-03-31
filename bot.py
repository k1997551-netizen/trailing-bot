import asyncio
import os
from metaapi_cloud_sdk import MetaApi

META_API_TOKEN = "eyJhbGciOiJSUzUxMiIsInR5cCI6IkpXVCJ9.eyJfaWQiOiJkN2Q5ZGNmZDQxNDg1MTQzMzYyZGJhMDk1YmVmODQwYyIsImFjY2Vzc1J1bGVzIjpbeyJpZCI6InRyYWRpbmctYWNjb3VudC1tYW5hZ2VtZW50LWFwaSIsIm1ldGhvZHMiOlsidHJhZGluZy1hY2NvdW50LW1hbmFnZW1lbnQtYXBpOnJlc3Q6cHVibGljOio6KiJdLCJyb2xlcyI6WyJyZWFkZXIiLCJ3cml0ZXIiXSwicmVzb3VyY2VzIjpbIio6JFVTRVJfSUQkOioiXX1dfQ"
MT4_LOGIN    = "289043543"
MT4_PASSWORD = os.environ.get("MT4_PASSWORD", "")
MT4_SERVER   = "Exness-Real38"

ACTIVATION_PROFIT = 2.0
BREAKEVEN_PROFIT  = 1.0
TRAILING_STEP     = 1.0
CHECK_INTERVAL    = 5

async def run_bot():
    print("البوت شغال - يراقب صفقاتك...")
    api = MetaApi(META_API_TOKEN)
    try:
        accounts = await api.metatrader_account_api.get_accounts()
        account = None
        for acc in accounts:
            if acc.login == MT4_LOGIN:
                account = acc
                break
        if not account:
            account = await api.metatrader_account_api.create_account({
                'name': 'Trailing Bot',
                'type': 'cloud',
                'login': MT4_LOGIN,
                'password': MT4_PASSWORD,
                'server': MT4_SERVER,
                'platform': 'mt4',
                'magic': 0,
            })
        await account.deploy()
        await account.wait_connected()
        connection = account.get_rpc_connection()
        await connection.connect()
        await connection.wait_synchronized()
        print("متصل وجاهز!")
        while True:
            try:
                positions = await connection.get_positions()
                for pos in positions:
                    profit       = pos.get('profit', 0)
                    open_price   = pos.get('openPrice', 0)
                    current_sl   = pos.get('stopLoss', 0)
                    current_tp   = pos.get('takeProfit', 0)
                    pos_id       = pos.get('id')
                    pos_type     = pos.get('type')
                    current_price = pos.get('currentPrice', 0)
                    symbol       = pos.get('symbol', '')
                    new_sl = current_sl
                    if profit >= BREAKEVEN_PROFIT:
                        if pos_type == 'POSITION_TYPE_BUY' and (current_sl == 0 or current_sl < open_price):
                            new_sl = open_price
                            print(f"Break Even! {symbol} SL={new_sl}")
                        elif pos_type == 'POSITION_TYPE_SELL' and (current_sl == 0 or current_sl > open_price):
                            new_sl = open_price
                            print(f"Break Even! {symbol} SL={new_sl}")
                    if profit >= ACTIVATION_PROFIT:
                        if pos_type == 'POSITION_TYPE_BUY':
                            trail_sl = current_price - (TRAILING_STEP / 10)
                            if trail_sl > new_sl:
                                new_sl = trail_sl
                                print(f"Trailing! {symbol} SL={new_sl} Profit=${profit:.2f}")
                        elif pos_type == 'POSITION_TYPE_SELL':
                            trail_sl = current_price + (TRAILING_STEP / 10)
                            if new_sl == 0 or trail_sl < new_sl:
                                new_sl = trail_sl
                                print(f"Trailing! {symbol} SL={new_sl} Profit=${profit:.2f}")
                    if new_sl != current_sl and new_sl != 0:
                        await connection.modify_position(pos_id, new_sl, current_tp)
                        print(f"تم تحريك SL بنجاح! {symbol}")
            except Exception as e:
                print(f"خطأ: {e}")
            await asyncio.sleep(CHECK_INTERVAL)
    except Exception as e:
        print(f"خطأ في الاتصال: {e}")

if __name__ == "__main__":
    asyncio.run(run_bot())
