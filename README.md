# quantools

A set of personal trading and quant research projects in the crypto markets.

In particular:

## Carry
Backtesting system for carry trades with futures. Historical market data from FTX. Available expirations (the ones without year are for 2022):
['0325', '0624', '0930', '1230', '20200327', '20200626', '20200925', '20201225', '20210326', '20210625', '20210924', '20211231']

Some backtesting results:

### AAVE future with expiry 2020-12-25

![AAVE](https://user-images.githubusercontent.com/35916369/229205932-6b5fcb54-adc8-4fe5-be90-5b56cb13307a.png)

### XAUT future with expiry 2021-09-24

![XAUT](https://user-images.githubusercontent.com/35916369/229205729-55ab4bf0-d7fe-426e-8c49-ced6a9982272.png)

### Distribution of the final PNL of each expiration for all the backtested futures

![profits_by_expiration](https://user-images.githubusercontent.com/35916369/229207737-e067823c-1ecb-4d4e-ab43-277c2f0563fa.png)

### Distribution of the final PNL of each future for all the backtested expirations

![profits_by_coin](https://user-images.githubusercontent.com/35916369/229207743-61314ed7-40e6-45e7-9002-610b465dc4b5.png)

## Carry live
Live trading system to monitor and systematically trade carry opportunities on FTX.

## MEV
Simple DeFi projects to learn the mechanics arbitrage on AMMs.
