import config as cfg
from ftx_connector import FtxConnectorRest
from common import util


connector = FtxConnectorRest(cfg.API_KEY, cfg.API_SECRET, cfg.SUB_ACCOUNT)
end_ts = util.timestamp_now()
start_ts = end_ts - 3600 * 24 * 30 * 3

all_futures = connector._client.get_all_futures()
all_perps = [f['name'] for f in all_futures if 'PERP' in f['name']]
tot_funding = 0.

for perp in all_perps:
    payments = connector.get_funding_payments(perp, start_ts, end_ts)
    tot = sum([r.payment for r in payments])
    tot_funding += tot
    if tot != 0:
        print(perp, round(tot, 2))

print('tot funding paid:', tot_funding)
