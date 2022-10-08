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

interface IUniswapV2Pair{
    function swap(
        uint amount0Out,
        uint amount1Out,
        address to,
        bytes calldata data
    ) external;
}

interface IJoeCallee {
    function joeCall(
        address sender,
        uint amount0,
        uint amount1,
        bytes calldata data
    ) external;
}

contract FlashBorrow is IJoeCallee {
    address _poolAddress;
    address _borrowTokenAddress;
    uint _borrowTokenAmount;
    address _repayTokenAddress;
    uint _repayTokenAmount;

    function execute(
        address poolAddress,
        address borrowTokenAddress,
        uint borrowTokenAmount,
        address repayTokenAddress,
        uint repayTokenAmount
    ) external {
        _poolAddress = poolAddress;
        _borrowTokenAddress = borrowTokenAddress;
        _borrowTokenAmount = borrowTokenAmount;
        _repayTokenAddress = repayTokenAddress;
        _repayTokenAmount = repayTokenAmount;

        IUniswapV2Pair(poolAddress).swap(
            borrowTokenAmount,
            0,
            address(this),
            "0xquantoor"
    );
    }

    function joeCall(
        address sender,
        uint amount0,
        uint amount1,
        bytes calldata data
    ) external {
        IERC20(_repayTokenAddress).transfer(msg.sender, _repayTokenAmount);
    }
}
