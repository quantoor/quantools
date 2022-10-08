# @version >=0.3.2

from vyper.interfaces import ERC20 as IERC20

interface IUniswapV2Pair:
    def swap(
        amount0Out: uint256,
        amount1Out: uint256,
        to: address,
        data: Bytes[32]
    ): nonpayable

interface IJoeCallee:
    def joeCall(
      sender: address,
      amount0: uint256,
      amount1: uint256,
      data: Bytes[32]
    ): nonpayable

implements: IJoeCallee

flash_borrow_pool_address: address
flash_borrow_token_address: address
flash_borrow_token_amount: uint256
flash_repay_token_address: address
flash_repay_token_amount: uint256

@external
@nonpayable
def execute(
    flash_borrow_pool_address: address,
    flash_borrow_token_address: address,
    flash_borrow_token_amount: uint256,
    flash_repay_token_address: address,
    flash_repay_token_amount: uint256
):
    self.flash_borrow_pool_address = flash_borrow_pool_address
    self.flash_borrow_token_address = flash_borrow_token_address
    self.flash_borrow_token_amount = flash_borrow_token_amount
    self.flash_repay_token_address = flash_repay_token_address
    self.flash_repay_token_amount = flash_repay_token_amount

    IUniswapV2Pair(flash_borrow_pool_address).swap(
        flash_borrow_token_amount,
        0,
        self,
        b'quantoor'
    )

@external
@nonpayable
def joeCall(
    _sender: address,
    _amount0: uint256,
    _amount1: uint256,
    _data: Bytes[32]
  ):
    IERC20(self.flash_repay_token_address).transfer(msg.sender, self.flash_repay_token_amount)