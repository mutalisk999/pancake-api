import sha3
import bitcoin


def calc_addr_from_key(privkey):
    if privkey.startswith("0x"):
        privkey = privkey[2:]
    return "0x" + sha3.keccak_256(bytes.fromhex(bitcoin.privtopub(privkey)[2:])).digest()[-20:].hex()
