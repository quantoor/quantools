# @version >=0.3.2

from vyper.interfaces import ERC20 as IERC20

interface IUniswapV2Pair:
  def token0() -> address: view
  def token1() -> address: view
  def swap(
    amount0Out: uint256,
    amount1Out: uint256,
    to: address,
    data: Bytes[1],
  ): nonpayable

interface IJoeCallee:
  def joeCall(
    sender: address,
    amount0: uint256,
    amount1: uint256,
    data: Bytes[1],
  ): nonpayable

implements: IJoeCallee

owner: address
flash_borrow_pool_address: address
flash_borrow_token_amounts: DynArray[uint256, 2]
flash_repay_token_amount: uint256
swap_pool_addresses: DynArray[address, 16]
swap_pool_amounts: DynArray[DynArray[uint256, 2], 16]

@external
@nonpayable
def __init__():
  self.owner = msg.sender

@external
@nonpayable
def withdraw(token_address: address):
  assert msg.sender == self.owner, "!OWNER"
  IERC20(token_address).transfer(
    self.owner,
    IERC20(token_address).balanceOf(self) - 1,
  )

@external
@nonpayable
def execute(
  flash_borrow_pool_address: address,
  flash_borrow_token_amounts: DynArray[uint256, 2],
  flash_repay_token_amount: uint256,
  swap_pool_addresses: DynArray[address, 16],
  swap_pool_amounts: DynArray[DynArray[uint256, 2], 16],
):

  assert msg.sender == self.owner, "!OWNER"

  self.flash_borrow_pool_address = flash_borrow_pool_address
  self.flash_borrow_token_amounts = flash_borrow_token_amounts
  self.flash_repay_token_amount = flash_repay_token_amount
  self.swap_pool_addresses = swap_pool_addresses
  self.swap_pool_amounts = swap_pool_amounts
 
  IUniswapV2Pair(flash_borrow_pool_address).swap(
    flash_borrow_token_amounts[0],
    flash_borrow_token_amounts[1], 
    self,
    b'x',
    ) 

  # try this one weird trick to save gas
  self.flash_borrow_pool_address = ZERO_ADDRESS
  self.flash_borrow_token_amounts = []
  self.flash_repay_token_amount = 0
  self.swap_pool_addresses = []
  self.swap_pool_amounts = []


@external
@nonpayable
def joeCall(
  _sender: address,
  _amount0: uint256,
  _amount1: uint256,
  _data: Bytes[32],
  ):

  # revert if any address other than the submitted LP activates this callback
  assert msg.sender == self.flash_borrow_pool_address, "!LP"

  # Use the Pair interface to retrieve and store the addresses for token0 and token1,
  token0_address: address = IUniswapV2Pair(msg.sender).token0()
  token1_address: address = IUniswapV2Pair(msg.sender).token1()

  # transfer the borrowed token to the first LP
  if _amount0 == 0:
    IERC20(token1_address).transfer(
      self.swap_pool_addresses[0], 
      _amount1,
    )
  
  if _amount1 == 0:
    IERC20(token0_address).transfer(
      self.swap_pool_addresses[0], 
      _amount0,
  )
  
  number_of_pools: uint256 = len(self.swap_pool_addresses)

  # loop through the LP addresses, calling swap() directly using the submitted amounts. Transfers the output from 
  # each swap to the next LP in the array. When we reach the last LP in the array, transfer the token back to
  # the contract and break the loop
  for i in range(16):
    if i < number_of_pools - 1:
      IUniswapV2Pair(self.swap_pool_addresses[i]).swap(
        self.swap_pool_amounts[i][0],
        self.swap_pool_amounts[i][1],
        self.swap_pool_addresses[i+1],
        b'',
      )
    elif i == number_of_pools - 1:
      IUniswapV2Pair(self.swap_pool_addresses[i]).swap(
        self.swap_pool_amounts[i][0],
        self.swap_pool_amounts[i][1],
        self,
        b'',
      )
    else:
      break

  # repay the flash loan
  if _amount0 == 0:
    IERC20(token0_address).transfer(
      msg.sender,
      self.flash_repay_token_amount,
    )

  if _amount1 == 0:
    IERC20(token1_address).transfer(
      msg.sender,
      self.flash_repay_token_amount,
    )