# @version >=0.3.2

from vyper.interfaces import ERC20

interface IUniswapV2Pair:
  def token0() -> address: view
  def token1() -> address: view
  def swap(
    amount0Out: uint256,
    amount1Out: uint256,
    to: address,
    data: Bytes[32],
  ): nonpayable

interface IUniswapV2Router:
  def swapExactTokensForTokens(
    amountOut: uint256,
    amountInMax: uint256,
    path: DynArray[address, 16],
    to: address,
    deadline: uint256
  ) -> DynArray[uint256, 16]: nonpayable
  def getAmountsIn(
    amountOut: uint256,
    path: DynArray[address, 16]
  ) -> DynArray[uint256, 16]: view

interface IUniswapV2Callee:
  def uniswapV2Call(
    sender: address,
    amount0: uint256,
    amount1: uint256,
    data: Bytes[32],
  ): nonpayable

implements: IUniswapV2Callee

deadline: constant(uint256) = 60  # 60 seconds expiration for router swap

# these values are set by the constructor during contract creation
sushiswap_factory_address: address
sushiswap_router_address: address

# these values are dynamic, controlled at execution time by arguments passed to the execute() function
flash_borrow_pool_address: address
swap_router: IUniswapV2Router
swap_path: DynArray[address, 16]

@external
@nonpayable
def __init__(
  _sushiswap_factory_address: address,
  _sushiswap_router_address: address,
):
  self.sushiswap_factory_address = _sushiswap_factory_address
  self.sushiswap_router_address = _sushiswap_router_address

@external
@nonpayable
def execute(
  flash_borrow_pool_address: address,
  flash_borrow_token_address: address,
  flash_borrow_token_amount: uint256,
  swap_path: DynArray[address, 16],
  swap_router_address: address,
):

  # build a path for the swap (may be up to 16 tokens long)
  self.swap_path = swap_path

  # create a pointer to the external router
  self.swap_router = IUniswapV2Router(swap_router_address)

  # store the flash borrowing pool address, needed to access the borrowing pool inside the callback
  self.flash_borrow_pool_address = flash_borrow_pool_address

  amount0: uint256 = 0
  amount1: uint256 = 0

  # sets "unlimited" approval whenever this contract attempts to interact with this token and the approval is less than the requested amount
  approval: uint256 = ERC20(flash_borrow_token_address).allowance(self,swap_router_address)
  if approval < flash_borrow_token_amount:
    ERC20(flash_borrow_token_address).approve(swap_router_address, MAX_UINT256)

  if flash_borrow_token_address == IUniswapV2Pair(flash_borrow_pool_address).token0():
    amount0 = flash_borrow_token_amount
  else:
    amount1 = flash_borrow_token_amount

  IUniswapV2Pair(flash_borrow_pool_address).swap(
    amount0,
    amount1,
    self,
    b'flash',
    )

@external
@nonpayable
def uniswapV2Call(
  _sender: address,
  _amount0: uint256,
  _amount1: uint256,
  _data: Bytes[32],
  ):

  # Use the Pair interface to retrieve and store the addresses for token0 and token1
  token0: address = IUniswapV2Pair(msg.sender).token0()
  token1: address = IUniswapV2Pair(msg.sender).token1()

  # use the call amounts to determine which token was transferred from the LP, and to build the path array
  # before calling for the router swap
  amount_borrow: uint256 = 0
  _path: DynArray[address, 2] = []

  if _amount0 > 0:
    amount_borrow = _amount0
    _path.append(token1)
    _path.append(token0)
  else:
    amount_borrow = _amount1
    _path.append(token0)
    _path.append(token1)

  # calculate amount_repay (INPUT) needed to withdraw amount_borrow (OUTPUT),
  # used to repay the flash borrow later
  amount_repay: uint256 = IUniswapV2Router(self.sushiswap_router_address).getAmountsIn(
    amount_borrow,
    _path
  )[0]

  # Swap amount_borrow for amount_repay on the other router
  # Vyper does not support "last" indexing using [-1], so use len instead
  amount_received_after_swap: uint256 = IUniswapV2Router(self.swap_router.address).swapExactTokensForTokens(
    amount_borrow,
    amount_repay,
    self.swap_path,
    self,
    block.timestamp + deadline,
  )[len(self.swap_path)-1]

  # repay the flash borrow to the liquidity pool (msg.sender))
  # then send the remainder to the transaction originator (tx.origin)
  if _amount0 > 0:
    ERC20(token1).transfer(msg.sender, amount_repay)
    ERC20(token1).transfer(tx.origin, amount_received_after_swap - amount_repay)
  else:
    ERC20(token0).transfer(msg.sender, amount_repay)
    ERC20(token0).transfer(tx.origin, amount_received_after_swap - amount_repay)