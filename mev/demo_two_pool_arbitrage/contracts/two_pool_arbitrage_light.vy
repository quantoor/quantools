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

@external
@nonpayable
def execute():
  ERC20(0xCE1bFFBD5374Dac86a2893119683F4911a2F7814).approve(0x60aE616a2155Ee3d9A68541Ba4544862310933d4, MAX_UINT256)
  IUniswapV2Pair(0xE5cddBfd3A807691967e528f1d6b7f00b1919e6F).swap(0, 29312834720491373000000, self, b'flash')

@external
@nonpayable
def uniswapV2Call(
  _sender: address,
  _amount0: uint256,
  _amount1: uint256,
  _data: Bytes[32]
):
  assert ERC20(0xCE1bFFBD5374Dac86a2893119683F4911a2F7814).balanceOf(self) == 29312834720491373000000, "Wrong spell balance"

  # Swap amount_borrow for amount_repay on the other router
  # Vyper does not support "last" indexing using [-1], so use len instead
  amount_received_after_swap: uint256 = IUniswapV2Router(0x60aE616a2155Ee3d9A68541Ba4544862310933d4).swapExactTokensForTokens(
    29312834720491373000000,
    23971168849725104179576,
    [0xCE1bFFBD5374Dac86a2893119683F4911a2F7814, 0x3Ee97d514BBef95a2f110e6B9b73824719030f7a],
    self,
    block.timestamp + 60,
  )[1]

  assert amount_received_after_swap == 24000490661890450756057, "Wrong amount received after swap"

  # repay the flash borrow to the liquidity pool (msg.sender))
  # then send the remainder to the transaction originator (tx.origin)
  ERC20(0x3Ee97d514BBef95a2f110e6B9b73824719030f7a).transfer(msg.sender, 23971168849725104179576)
  ERC20(0x3Ee97d514BBef95a2f110e6B9b73824719030f7a).transfer(tx.origin, 24000490661890450756057 - 23971168849725104179576)