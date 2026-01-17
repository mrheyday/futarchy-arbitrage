require("dotenv/config");
require("@nomicfoundation/hardhat-ethers");
require("@nomicfoundation/hardhat-verify");

const GNOSIS_RPC = process.env.GNOSIS_RPC_URL || process.env.RPC_URL;
const BASE_RPC = process.env.BASE_RPC_URL || "https://mainnet.base.org";
const BASE_SEPOLIA_RPC = process.env.BASE_SEPOLIA_RPC_URL || "https://sepolia.base.org";
const { PRIVATE_KEY, GNOSISSCAN_API_KEY, BASESCAN_API_KEY } = process.env;

function getAccounts() {
  if (!PRIVATE_KEY) return [];
  const key = PRIVATE_KEY.startsWith("0x") ? PRIVATE_KEY : `0x${PRIVATE_KEY}`;
  return [key];
}

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: {
<<<<<<< Updated upstream
    version: "0.8.33",
    settings: { optimizer: { enabled: true, runs: 1000000 } },
    via_ir: true
  },
  networks: {
    gnosis: {
      url: GNOSIS_RPC || "https://rpc.gnosischain.com",
=======
    version: "0.8.20",
    settings: { optimizer: { enabled: true, runs: 1000000 } },
  },
  networks: {
    gnosis: {
      url: RPC_FALLBACK || "https://rpc.gnosischain.com",
>>>>>>> Stashed changes
      chainId: 100,
      accounts: getAccounts(),
    },
    base: {
      url: BASE_RPC,
      chainId: 8453,
      accounts: getAccounts(),
    },
    base_sepolia: {
      url: BASE_SEPOLIA_RPC,
      chainId: 84532,
      accounts: getAccounts(),
    },
  },
  etherscan: {
<<<<<<< Updated upstream
    apiKey: {
      gnosis: GNOSISSCAN_API_KEY || "",
      base: BASESCAN_API_KEY || "",
      base_sepolia: BASESCAN_API_KEY || "",
    },
=======
    apiKey: { gnosis: GNOSISSCAN_API_KEY || "" },
>>>>>>> Stashed changes
    customChains: [
      {
        network: "gnosis",
        chainId: 100,
        urls: {
          apiURL: "https://api.gnosisscan.io/api",
          browserURL: "https://gnosisscan.io",
<<<<<<< Updated upstream
        },
      },
      {
        network: "base",
        chainId: 8453,
        urls: {
          apiURL: "https://api.basescan.org/api",
          browserURL: "https://basescan.org",
        },
      },
      {
        network: "base_sepolia",
        chainId: 84532,
        urls: {
          apiURL: "https://api-sepolia.basescan.org/api",
          browserURL: "https://sepolia.basescan.org",
=======
>>>>>>> Stashed changes
        },
      },
    ],
  },
};
