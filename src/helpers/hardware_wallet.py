"""
Hardware Wallet Integration for Futarchy Arbitrage Bot
Supports Ledger and Trezor for secure key management
"""

import logging
from typing import Optional, Dict, Any
from decimal import Decimal
from eth_account import Account
from eth_typing import HexStr, ChecksumAddress
from web3 import Web3
from ledgerblue.comm import getDongle
from ledgerblue.commException import CommException
import struct

logger = logging.getLogger(__name__)


class HardwareWalletError(Exception):
    """Base exception for hardware wallet errors"""
    pass


class LedgerWallet:
    """
    Ledger hardware wallet integration
    Uses Ethereum app on Ledger Nano S/X
    """
    
    def __init__(self, derivation_path: str = "m/44'/60'/0'/0/0"):
        """
        Initialize Ledger wallet
        
        Args:
            derivation_path: BIP44 derivation path
        """
        self.derivation_path = derivation_path
        self.dongle = None
        self.address: Optional[ChecksumAddress] = None
        
        logger.info(f"LedgerWallet initialized with path: {derivation_path}")
    
    def connect(self) -> bool:
        """
        Connect to Ledger device
        
        Returns:
            True if connection successful
        """
        try:
            self.dongle = getDongle(debug=False)
            logger.info("Connected to Ledger device")
            return True
        except CommException as e:
            logger.error(f"Failed to connect to Ledger: {e}")
            raise HardwareWalletError("Ledger connection failed. Ensure device is unlocked and Ethereum app is open.")
    
    def disconnect(self) -> None:
        """Disconnect from Ledger"""
        if self.dongle:
            self.dongle.close()
            logger.info("Disconnected from Ledger")
    
    def get_address(self, verify_on_device: bool = False) -> ChecksumAddress:
        """
        Get Ethereum address from Ledger
        
        Args:
            verify_on_device: Display address on device for verification
            
        Returns:
            Checksummed Ethereum address
        """
        if not self.dongle:
            self.connect()
        
        # Parse derivation path
        path = self._parse_derivation_path(self.derivation_path)
        
        # Build APDU command for GET_PUBLIC_KEY
        # CLA=0xE0, INS=0x02, P1=display, P2=chaincode
        apdu = bytearray([0xE0, 0x02, 0x01 if verify_on_device else 0x00, 0x00])
        apdu.append(len(path))
        apdu.extend(path)
        
        try:
            response = self.dongle.exchange(bytes(apdu))
            
            # Parse response: pubkey_len (1) + pubkey (65) + address_len (1) + address (40)
            pubkey_len = response[0]
            pubkey = response[1:1+pubkey_len]
            address_start = 1 + pubkey_len + 1
            address_hex = response[address_start:address_start+40].decode('ascii')
            
            self.address = Web3.to_checksum_address(f"0x{address_hex}")
            logger.info(f"Ledger address: {self.address}")
            
            return self.address
            
        except CommException as e:
            logger.error(f"Error getting address from Ledger: {e}")
            raise HardwareWalletError(f"Failed to get address: {e}")
    
    def sign_transaction(self, transaction: Dict[str, Any]) -> HexStr:
        """
        Sign transaction with Ledger
        
        Args:
            transaction: Transaction dict with to, value, data, nonce, gasPrice, gas
            
        Returns:
            Signed transaction hex
        """
        if not self.dongle:
            self.connect()
        
        # Encode transaction for signing
        from rlp import encode
        from eth_account._utils.legacy_transactions import serializable_unsigned_transaction_from_dict
        
        unsigned_tx = serializable_unsigned_transaction_from_dict(transaction)
        encoded_tx = encode(unsigned_tx)
        
        # Parse derivation path
        path = self._parse_derivation_path(self.derivation_path)
        
        # Build APDU for SIGN_TRANSACTION
        # Split transaction into chunks (max 255 bytes per APDU)
        chunk_size = 200
        chunks = [encoded_tx[i:i+chunk_size] for i in range(0, len(encoded_tx), chunk_size)]
        
        try:
            for i, chunk in enumerate(chunks):
                is_first = (i == 0)
                is_last = (i == len(chunks) - 1)
                
                apdu = bytearray([0xE0, 0x04, 0x00 if is_first else 0x80, 0x00])
                
                if is_first:
                    # First chunk includes derivation path
                    payload = path + chunk
                else:
                    payload = chunk
                
                apdu.append(len(payload))
                apdu.extend(payload)
                
                if is_last:
                    # Last chunk returns signature
                    response = self.dongle.exchange(bytes(apdu))
                else:
                    # Intermediate chunks
                    self.dongle.exchange(bytes(apdu))
            
            # Parse signature: v (1) + r (32) + s (32)
            v = response[0]
            r = int.from_bytes(response[1:33], 'big')
            s = int.from_bytes(response[33:65], 'big')
            
            # Reconstruct signed transaction
            from eth_account._utils.legacy_transactions import encode_transaction
            signed_tx = encode_transaction(unsigned_tx, vrs=(v, r, s))
            
            return signed_tx.hex()
            
        except CommException as e:
            logger.error(f"Error signing transaction: {e}")
            raise HardwareWalletError(f"Transaction signing failed: {e}")
    
    def sign_message(self, message: str) -> HexStr:
        """
        Sign arbitrary message with Ledger
        
        Args:
            message: Message to sign
            
        Returns:
            Signature hex
        """
        if not self.dongle:
            self.connect()
        
        # Ethereum signed message format
        message_bytes = f"\x19Ethereum Signed Message:\n{len(message)}{message}".encode('utf-8')
        
        path = self._parse_derivation_path(self.derivation_path)
        
        # APDU for personal_sign
        apdu = bytearray([0xE0, 0x08, 0x00, 0x00])
        payload = path + struct.pack(">I", len(message_bytes)) + message_bytes
        apdu.append(len(payload))
        apdu.extend(payload)
        
        try:
            response = self.dongle.exchange(bytes(apdu))
            
            v = response[0]
            r = response[1:33].hex()
            s = response[33:65].hex()
            
            return f"0x{r}{s}{v:02x}"
            
        except CommException as e:
            logger.error(f"Error signing message: {e}")
            raise HardwareWalletError(f"Message signing failed: {e}")
    
    def _parse_derivation_path(self, path: str) -> bytes:
        """
        Parse BIP44 derivation path to bytes
        
        Args:
            path: Path like "m/44'/60'/0'/0/0"
            
        Returns:
            Encoded path bytes
        """
        parts = path.replace("m/", "").split("/")
        result = bytes([len(parts)])
        
        for part in parts:
            if part.endswith("'"):
                # Hardened
                index = int(part[:-1]) | 0x80000000
            else:
                index = int(part)
            result += struct.pack(">I", index)
        
        return result


class TrezorWallet:
    """
    Trezor hardware wallet integration
    Requires trezor library
    """
    
    def __init__(self, derivation_path: str = "m/44'/60'/0'/0/0"):
        """
        Initialize Trezor wallet
        
        Args:
            derivation_path: BIP44 derivation path
        """
        self.derivation_path = derivation_path
        self.client = None
        self.address: Optional[ChecksumAddress] = None
        
        logger.info(f"TrezorWallet initialized with path: {derivation_path}")
    
    def connect(self) -> bool:
        """Connect to Trezor device"""
        try:
            from trezorlib import ethereum, tools
            from trezorlib.client import get_default_client
            
            self.client = get_default_client()
            logger.info("Connected to Trezor device")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Trezor: {e}")
            raise HardwareWalletError("Trezor connection failed. Install trezorlib: pip install trezor")
    
    def get_address(self, verify_on_device: bool = False) -> ChecksumAddress:
        """Get Ethereum address from Trezor"""
        if not self.client:
            self.connect()
        
        from trezorlib import ethereum, tools
        
        path = tools.parse_path(self.derivation_path)
        address = ethereum.get_address(
            self.client,
            path,
            show_display=verify_on_device
        )
        
        self.address = Web3.to_checksum_address(address)
        logger.info(f"Trezor address: {self.address}")
        
        return self.address
    
    def sign_transaction(self, transaction: Dict[str, Any]) -> HexStr:
        """Sign transaction with Trezor"""
        if not self.client:
            self.connect()
        
        from trezorlib import ethereum, tools
        
        path = tools.parse_path(self.derivation_path)
        
        # Convert transaction to Trezor format
        tx_data = {
            "nonce": transaction["nonce"],
            "gas_price": transaction["gasPrice"],
            "gas_limit": transaction["gas"],
            "to": transaction["to"],
            "value": transaction["value"],
            "data": transaction.get("data", b""),
            "chain_id": transaction.get("chainId", 1)
        }
        
        v, r, s = ethereum.sign_tx(self.client, path, **tx_data)
        
        # Reconstruct signed transaction
        from eth_account._utils.legacy_transactions import encode_transaction, serializable_unsigned_transaction_from_dict
        
        unsigned_tx = serializable_unsigned_transaction_from_dict(transaction)
        signed_tx = encode_transaction(unsigned_tx, vrs=(v, r, s))
        
        return signed_tx.hex()


class HardwareWalletManager:
    """
    Unified hardware wallet manager supporting multiple devices
    """
    
    def __init__(self, wallet_type: str = "ledger", derivation_path: str = "m/44'/60'/0'/0/0"):
        """
        Initialize hardware wallet manager
        
        Args:
            wallet_type: "ledger" or "trezor"
            derivation_path: BIP44 derivation path
        """
        self.wallet_type = wallet_type.lower()
        self.derivation_path = derivation_path
        
        if self.wallet_type == "ledger":
            self.wallet = LedgerWallet(derivation_path)
        elif self.wallet_type == "trezor":
            self.wallet = TrezorWallet(derivation_path)
        else:
            raise ValueError(f"Unsupported wallet type: {wallet_type}")
        
        logger.info(f"HardwareWalletManager initialized: {wallet_type}")
    
    def get_address(self, verify: bool = False) -> ChecksumAddress:
        """Get address from hardware wallet"""
        return self.wallet.get_address(verify_on_device=verify)
    
    def sign_and_send_transaction(
        self,
        web3: Web3,
        transaction: Dict[str, Any]
    ) -> HexStr:
        """
        Sign transaction with hardware wallet and broadcast
        
        Args:
            web3: Web3 instance
            transaction: Transaction dict
            
        Returns:
            Transaction hash
        """
        logger.info(f"Signing transaction with {self.wallet_type}")
        
        # Sign with hardware wallet
        signed_tx = self.wallet.sign_transaction(transaction)
        
        # Broadcast
        tx_hash = web3.eth.send_raw_transaction(signed_tx)
        logger.info(f"Transaction sent: {tx_hash.hex()}")
        
        return tx_hash.hex()
    
    def sign_message(self, message: str) -> HexStr:
        """Sign message with hardware wallet"""
        return self.wallet.sign_message(message)
