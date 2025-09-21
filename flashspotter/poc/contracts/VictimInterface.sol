// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IVictim {
    // example: lender that uses spot reserves for collateral factor
    function borrow(uint amount, address token) external;
    function deposit(address token, uint amount) external;
}
