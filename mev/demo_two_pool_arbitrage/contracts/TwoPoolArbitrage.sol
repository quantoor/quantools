// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

//import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/v4.0.0/contracts/token/ERC20/ERC20.sol";
// For some reason the previous import doesn't work, so the ERC20 interface is defined here
interface IERC20 {
    function totalSupply() external view returns (uint);

    function balanceOf(address account) external view returns (uint);

    function transfer(address recipient, uint amount) external returns (bool);

    function allowance(address owner, address spender) external view returns (uint);

    function approve(address spender, uint amount) external returns (bool);

    function transferFrom(
        address sender,
        address recipient,
        uint amount
    ) external returns (bool);

    event Transfer(address indexed from, address indexed to, uint value);
    event Approval(address indexed owner, address indexed spender, uint value);
}

interface IUniswapV2Pair {
    function token0() external view returns (address);

    function token1() external view returns (address);

    function swap(
        uint amount0Out,
        uint amount1Out,
        address to,
        bytes calldata data
    ) external;
}

interface IUniswapV2Router {
    function swapExactTokensForTokens(
        uint amountOut,
        uint amountInMax,
        address[] calldata path,
        address to,
        uint deadline
    ) external view returns (uint[] calldata);

    function getAmountsIn(
        uint amountOut,
        address[] calldata path
    ) external view returns (uint[] calldata);
}

interface IUniswapV2Callee {
    function uniswapV2Call(
        address sender,
        uint amount0,
        uint amount1,
        bytes calldata data
    ) external;
}

contract TwoPoolArbitrage is IUniswapV2Callee {
    uint deadline = 60;
    address sushiswapFactoryAddress;
    address sushiswapRouterAddress;
    address borrowPoolAddress;
    IUniswapV2Router swapRouter;
    address[] swapPath;
    uint MAX_INT = 115792089237316195423570985008687907853269984665640564039457584007913129639935;

    constructor(address _sushiswapFactoryAddress, address _sushiswapRouterAddress) {
        sushiswapFactoryAddress = _sushiswapFactoryAddress;
        sushiswapRouterAddress = _sushiswapRouterAddress;
    }

    function execute(
        address _borrowPoolAddress,
        address _borrowTokenAddress,
        uint _borrowTokenAmount,
        address[] calldata _swapPath,
        address _swapRouterAddress
    ) external {
        swapPath = _swapPath;
        swapRouter = IUniswapV2Router(_swapRouterAddress);
        borrowPoolAddress = _borrowPoolAddress;

        uint approval = IERC20(_borrowTokenAddress).allowance(address(this), _swapRouterAddress);
        if (approval < _borrowTokenAmount) {
            IERC20(_borrowTokenAddress).approve(_swapRouterAddress, MAX_INT);
        }

        uint amount0 = 0;
        uint amount1 = 0;
        if (_borrowTokenAddress == IUniswapV2Pair(borrowPoolAddress).token0()) {
            amount0 = _borrowTokenAmount;
        } else {
            amount1 = _borrowTokenAmount;
        }

        IUniswapV2Pair(borrowPoolAddress).swap(
            amount0,
            amount1,
            address(this),
            "0xquantoor"
        );
    }

    function uniswapV2Call(
        address _sender,
        uint _amount0,
        uint _amount1,
        bytes calldata _data
    ) external {
        // use the Pair interface to retrieve and store the addresses for token0 and token1
        address token0 = IUniswapV2Pair(msg.sender).token0();
        address token1 = IUniswapV2Pair(msg.sender).token1();

        // use the call amounts to determine which token was transferred from the LP, and to build the path array
        // before calling for the router swap
        uint borrowAmount = 0;
        address[] memory _path = new address[](2);

        if (_amount0 > 0) {
            borrowAmount = _amount0;
            _path[0] = token1;
            _path[1] = token0;
        } else {
            borrowAmount = _amount1;
            _path[0] = token0;
            _path[1] = token1;
        }

        // calculate amount_repay (INPUT) needed to withdraw amount_borrow (OUTPUT),
        // used to repay the flash borrow later
        uint repayAmount = IUniswapV2Router(sushiswapRouterAddress).getAmountsIn(
            borrowAmount,
            _path
        )[0];

        // swap amount_borrow for amount_repay on the other router
        uint amountReceivedAfterSwap = IUniswapV2Router(swapRouter).swapExactTokensForTokens(
            borrowAmount,
            repayAmount,
            swapPath,
            address(this),
            block.timestamp + deadline
        )[swapPath.length - 1];

        // repay the flash borrow to the liquidity pool (msg.sender)
        // then send the remainder to the transaction originator (tx.origin)
        if (_amount0 > 0) {
            IERC20(token1).transfer(msg.sender, repayAmount);
            IERC20(token1).transfer(tx.origin, amountReceivedAfterSwap - repayAmount);
        } else {
            IERC20(token0).transfer(msg.sender, repayAmount);
            IERC20(token0).transfer(tx.origin, amountReceivedAfterSwap - repayAmount);
        }
    }
}
