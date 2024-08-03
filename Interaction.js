const Web3 = require('web3');
const fs = require('fs');
const path = require('path');

// Read the hash file path from command-line arguments
const hashFilePath = process.argv[2];
if (!hashFilePath) {
    console.error('No hash file path provided.');
    process.exit(1);
}

// Read hash from file
const dataHash = fs.readFileSync(hashFilePath, 'utf8').trim();
console.log('Read hash:', dataHash);

const contractABI = require('./build/contracts/BinaryHash.json').abi;

// Configure your Web3 provider
const web3 = new Web3(new Web3.providers.HttpProvider('http://127.0.0.1:7545'));

// Make sure to use the correct contract address here
const contractAddress = '0x468De9b90A58b0E4f2F854D8378763786c2E9e44';
const fromAddress = '0xe314383522734993a801A78214396D38F5f113D6';

const contract = new web3.eth.Contract(contractABI, contractAddress);

async function interactWithSmartContract(dataHash) {
    try {
        console.log('Hash to send:', dataHash);

        const encodedData = contract.methods.computeHash(dataHash).encodeABI();
        console.log('Encoded Data:', encodedData);

        const gas = await web3.eth.estimateGas({
            to: contractAddress,
            data: encodedData,
            from: fromAddress,
        });
        console.log('Estimated Gas:', gas);

        const gasPrice = await web3.eth.getGasPrice();
        console.log('Gas Price:', gasPrice);

        const tx = await web3.eth.sendTransaction({
            to: contractAddress,
            data: encodedData,
            gas,
            gasPrice,
            from: fromAddress,
        });

        console.log('Transaction sent:', tx);
    } catch (error) {
        console.error('Error sending transaction:', error);
    }
}

interactWithSmartContract(dataHash);
