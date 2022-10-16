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

contract TwoPoolArbitrageLight is IUniswapV2Callee {
    uint MAX_INT = 115792089237316195423570985008687907853269984665640564039457584007913129639935;

    function execute() external {
        IERC20(0xCE1bFFBD5374Dac86a2893119683F4911a2F7814).approve(0x60aE616a2155Ee3d9A68541Ba4544862310933d4, MAX_INT);
        IUniswapV2Pair(0xE5cddBfd3A807691967e528f1d6b7f00b1919e6F).swap(0, 29312834720491373000000, address(this), bytes("flash"));
    }

    function uniswapV2Call(
        address _sender,
        uint _amount0,
        uint _amount1,
        bytes calldata _data
    ) external override {
        address[] memory swapPath = new address[](2);
        swapPath[0] = 0xCE1bFFBD5374Dac86a2893119683F4911a2F7814;
        swapPath[1] = 0x3Ee97d514BBef95a2f110e6B9b73824719030f7a;

        uint amountReceivedAfterSwap = IUniswapV2Router(0x60aE616a2155Ee3d9A68541Ba4544862310933d4).swapExactTokensForTokens(
            29312834720491373000000,
            23971168849725104179576,
            swapPath,
            address(this),
            block.timestamp + 60
        )[1];

        require(amountReceivedAfterSwap == 24000490661890450756057, "Wrong amount received after swap");

        IERC20(0x3Ee97d514BBef95a2f110e6B9b73824719030f7a).transfer(msg.sender, 23971168849725104179576);
        IERC20(0x3Ee97d514BBef95a2f110e6B9b73824719030f7a).transfer(tx.origin, 24000490661890450756057 - 23971168849725104179576);
    }
}
