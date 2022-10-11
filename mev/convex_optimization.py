import numpy as np
import cvxpy as cp
import itertools

# Problem data
global_indices = list(range(4))

# 0 = TOKEN-0
# 1 = TOKEN-1
# 2 = TOKEN-2
# 3 = TOKEN-3

local_indices = [
    [0, 1, 2, 3],  # TOKEN-0/TOKEN-1/TOKEN-2/TOKEN-3
    [0, 1],  # TOKEN-0/TOKEN-1
    [1, 2],  # TOKEN-1/TOKEN-2
    [2, 3],  # TOKEN-2/TOKEN-3
    [2, 3]  # TOKEN-2/TOKEN-3
]

reserves = list(map(np.array, [
    [4, 4, 4, 4],
    # balancer with 4 assets in pool TOKEN-0, TOKEN-1, TOKEN-2, TOKEN-3 (4 TOKEN-0, 4 TOKEN-1, 4 TOKEN-2 & 4 TOKEN-3 IN POOL)
    [10, 1],  # uniswapV2 TOKEN-0/TOKEN-1 (10 TOKEN-0 & 1 TOKEN-1 IN POOL)
    [1, 5],  # uniswapV2 TOKEN-1/TOKEN-2 (1 TOKEN-1 & 5 TOKEN-2 IN POOL)
    [40, 50],  # uniswapV2 TOKEN-2/TOKEN-3  (40 TOKEN-2 & 50 TOKEN-3 IN POOL)
    [10, 10]  # constant_sum TOKEN-2/TOKEN-3 (10 TOKEN-2 & 10 TOKEN-3 IN POOL)
]))

fees = [
    .998,  # balancer fees
    .997,  # uniswapV2 fees
    .997,  # uniswapV2 fees
    .997,  # uniswapV2 fees
    .999  # constant_sum fees
]

# "Market value" of tokens (say, in a centralized exchange)
market_value = [
    1.5,  # TOKEN-0
    10,  # TOKEN-1
    2,  # TOKEN-2
    3  # TOKEN-3
]

# Build local-global matrices
n = len(global_indices)
m = len(local_indices)

A = []
for l in local_indices:  # for each CFMM
    n_i = len(l)  # n_i = number of tokens avaiable for CFMM i
    A_i = np.zeros((n, n_i))  # Create matrix of 0's
    for i, idx in enumerate(l):
        A_i[idx, i] = 1
    A.append(A_i)

# Build variables

# tender delta
deltas = [cp.Variable(len(l), nonneg=True) for l in local_indices]

# receive lambda
lambdas = [cp.Variable(len(l), nonneg=True) for l in local_indices]

psi = cp.sum([A_i @ (L - D) for A_i, D, L in zip(A, deltas, lambdas)])

# Objective is to maximize "total market value" of coins out
obj = cp.Maximize(market_value @ psi)  # matrix multiplication

# Reserves after trade
new_reserves = [R + gamma_i * D - L for R, gamma_i, D, L in zip(reserves, fees, deltas, lambdas)]

# Trading function constraints
cons = [
    # Balancer pool with weights 4, 3, 2, 1
    cp.geo_mean(new_reserves[0], p=np.array([4, 3, 2, 1])) >= cp.geo_mean(reserves[0]),

    # Uniswap v2 pools
    cp.geo_mean(new_reserves[1]) >= cp.geo_mean(reserves[1]),
    cp.geo_mean(new_reserves[2]) >= cp.geo_mean(reserves[2]),
    cp.geo_mean(new_reserves[3]) >= cp.geo_mean(reserves[3]),

    # Constant sum pool
    cp.sum(new_reserves[4]) >= cp.sum(reserves[4]),
    new_reserves[4] >= 0,

    # Arbitrage constraint
    psi >= 0
]

# Set up and solve problem
prob = cp.Problem(obj, cons)
prob.solve()

# Trade Execution Ordering

current_tokens = [0, 0, 0, 0]
new_current_tokens = [0, 0, 0, 0]
tokens_required_arr = []
tokens_required_value_arr = []

pool_names = ["BALANCER 0/1/2/3", "UNIV2 0/1", "UNIV2 1/2", "UNIV2 2/3", "CONSTANT SUM 2/3"]

permutations = itertools.permutations(list(range(len(local_indices))), len(local_indices))
permutations2 = []
for permutation in permutations:
    permutations2.append(permutation)
    current_tokens = [0, 0, 0, 0]
    new_current_tokens = [0, 0, 0, 0]
    tokens_required = [0, 0, 0, 0]
    for pool_id in permutation:
        pool = local_indices[pool_id]
        for global_token_id in pool:
            local_token_index = pool.index(global_token_id)
            new_current_tokens[global_token_id] = current_tokens[global_token_id] + (
                    lambdas[pool_id].value[local_token_index] - deltas[pool_id].value[local_token_index])

            if new_current_tokens[global_token_id] < 0 and new_current_tokens[global_token_id] < current_tokens[
                global_token_id]:
                if current_tokens[global_token_id] < 0:
                    tokens_required[global_token_id] += (
                            current_tokens[global_token_id] - new_current_tokens[global_token_id])
                    new_current_tokens[global_token_id] = 0
                else:
                    tokens_required[global_token_id] += (-new_current_tokens[global_token_id])
                    new_current_tokens[global_token_id] = 0
            current_tokens[global_token_id] = new_current_tokens[global_token_id]

    tokens_required_value = []
    for i1, i2 in zip(tokens_required, market_value):
        tokens_required_value.append(i1 * i2)

    tokens_required_arr.append(tokens_required)
    tokens_required_value_arr.append(sum(tokens_required_value))

min_value = min(tokens_required_value_arr)
min_value_index = tokens_required_value_arr.index(min_value)

print("\n-------------------- ARBITRAGE TRADES + EXECUTION ORDER --------------------\n")
for pool_id in permutations2[min_value_index]:
    pool = local_indices[pool_id]
    print(f"\nTRADE POOL = {pool_names[pool_id]}")

    for global_token_id in pool:
        local_token_index = pool.index(global_token_id)
        if (lambdas[pool_id].value[local_token_index] - deltas[pool_id].value[local_token_index]) < 0:
            print(
                f"\tTENDERING {-(lambdas[pool_id].value[local_token_index] - deltas[pool_id].value[local_token_index])} TOKEN {global_token_id}")

    for global_token_id in pool:
        local_token_index = pool.index(global_token_id)
        if (lambdas[pool_id].value[local_token_index] - deltas[pool_id].value[local_token_index]) >= 0:
            print(
                f"\tRECEIVEING {(lambdas[pool_id].value[local_token_index] - deltas[pool_id].value[local_token_index])} TOKEN {global_token_id}")

print("\n-------------------- REQUIRED TOKENS TO KICK-START ARBITRAGE --------------------\n")
print(f"TOKEN-0 = {tokens_required_arr[min_value_index][0]}")
print(f"TOKEN-1 = {tokens_required_arr[min_value_index][1]}")
print(f"TOKEN-2 = {tokens_required_arr[min_value_index][2]}")
print(f"TOKEN-3 = {tokens_required_arr[min_value_index][3]}")

print(f"\nUSD VALUE REQUIRED = ${min_value}")

print("\n-------------------- TOKENS & VALUE RECEIVED FROM ARBITRAGE --------------------\n")
net_network_trade_tokens = [0, 0, 0, 0]
net_network_trade_value = [0, 0, 0, 0]

for pool_id in permutations2[min_value_index]:
    pool = local_indices[pool_id]
    for global_token_id in pool:
        local_token_index = pool.index(global_token_id)
        net_network_trade_tokens[global_token_id] += lambdas[pool_id].value[local_token_index]
        net_network_trade_tokens[global_token_id] -= deltas[pool_id].value[local_token_index]

for i in range(0, len(net_network_trade_tokens)):
    net_network_trade_value[i] = net_network_trade_tokens[i] * market_value[i]

print(f"RECEIVED {net_network_trade_tokens[0]} TOKEN-0 = ${net_network_trade_value[0]}")
print(f"RECEIVED {net_network_trade_tokens[1]} TOKEN-1 = ${net_network_trade_value[1]}")
print(f"RECEIVED {net_network_trade_tokens[2]} TOKEN-2 = ${net_network_trade_value[2]}")
print(f"RECEIVED {net_network_trade_tokens[3]} TOKEN-3 = ${net_network_trade_value[3]}")

print(f"\nSUM OF RECEIVED TOKENS USD VALUE = ${sum(net_network_trade_value)}")
print(f"CONVEX OPTIMISATION SOLVER RESULT: ${prob.value}\n")
