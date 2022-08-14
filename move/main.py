import pandas as pd
from common import util
import util as mvutil
import time
import datetime as dt
from plotly.subplots import make_subplots
import plotly.graph_objects as go

move_symbols = mvutil.get_expired_move_symbols()
ts, mv_prices = util.get_historical_prices(move_symbols[1], 3600, 0, int(time.time()), verbose=True)
dates = [dt.datetime.fromtimestamp(t) for t in ts]

ul_ts, ul_prices = util.get_historical_prices('BTC/USD', 3600, ts[0], ts[-1], verbose=True)

start_price = ul_prices[0]
diff = [p - start_price for p in ul_prices]

print(f'move expired to {mv_prices[-1]}, price diff was {diff[-1]}')

# fix, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 6), sharex='col')
# ax1.plot(dates[:len(ul_prices)], ul_prices)
# ax1.grid()
# ax2.plot(dates, mv_prices)
# ax2.grid()
# ax3.plot(dates[:len(ul_prices)], diff)
# ax3.grid()
# plt.show()

fig = make_subplots(rows=3, cols=1, shared_xaxes=True)

fig.add_trace(
    go.Scatter(x=dates[:len(ul_prices)], y=ul_prices),
    row=1, col=1
)

fig.add_trace(
    go.Scatter(x=dates, y=mv_prices),
    row=2, col=1
)

fig.add_trace(
    go.Scatter(x=dates[:len(ul_prices)], y=diff),
    row=3, col=1
)

fig.update_yaxes(
    showline=True,
    showgrid=True,
    showticklabels=True,
    linecolor='rgb(204, 204, 204)',
    linewidth=2,
    mirror=True,
    # spikemode='across+toaxis',
    # spikesnap='cursor',
)

fig.update_xaxes(
    showline=True,
    showgrid=True,
    showticklabels=True,
    linecolor='rgb(204, 204, 204)',
    linewidth=2,
    mirror=True,
    showspikes=True,
    spikemode='across+toaxis',
    spikesnap='cursor',
)

# fig.update_layout(title_text="Side By Side Subplots")
# fig.update_yaxes(
#     showline=True,
#     showgrid=True,
#     showticklabels=True,
#     linecolor='rgb(204, 204, 204)',
#     linewidth=2,
#     mirror=True,
# ),
# fig.update_xaxes(
#     showline=True,
#     showgrid=True,
#     showticklabels=True,
#     linecolor='rgb(204, 204, 204)',
#     linewidth=2,
#     mirror=True,
# ),
# fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False,
#                  showspikes=True, spikemode='across', spikesnap='cursor', showline=False, spikedash='solid')
# fig.update_xaxes(showgrid=False, zeroline=False, rangeslider_visible=False, showticklabels=False,
#                  showspikes=True, spikemode='across', spikesnap='cursor', showline=False, spikedash='solid')
fig.update_layout(hoverdistance=0)
fig.show()
