import tempfile
from datetime import datetime
from typing import Optional

from thenewboston_node.business_logic.utils.blockchain_state import make_blockchain_genesis_state
from thenewboston_node.core.utils.cryptography import KeyPair
from thenewboston_node.core.utils.types import hexstr

from ..blockchain.file_blockchain import FileBlockchain
from ..models import (
    Block, CoinTransferSignedChangeRequest, NodeDeclarationSignedChangeRequest,
    PrimaryValidatorScheduleSignedChangeRequest, RegularNode
)

TREASURY_KEY_PAIR = KeyPair(
    public=hexstr('00f3d2477317d53bcc2a410decb68c769eea2f0d74b679369b7417e198bd97b6'),
    private=hexstr('f94fbd639d9507f544fb27b79b5344a2d7b461e333053ed1be45b90c988e6355'),
)

REGULAR_NODE_KEY_PAIR = KeyPair(
    public=hexstr('accf7efe1b2ae044f25b98c38cffa3d6992b82e271c71353df549cbab7abaaf9'),
    private=hexstr('0e92ed657cafd81a51cc32b867af259d8aca2446dd31d1598f0467a15904187b'),
)

PV_KEY_PAIR = KeyPair(
    public=hexstr('657cf373f6f8fb72854bd302269b8b2b3576e3e2a686bd7d0a112babaa1790c6'),
    private=hexstr('5ef5773228743963817f79ea4a4b1e7c1a270f781af44fd141dc68193bce1228'),
)

PV_FIN_ACCOUNT_KEY_PAIR = KeyPair(
    public=hexstr('7a5dc06babda703a7d2d8ea18d3309a0c5e6830a25bac03e69633d283244e001'),
    private=hexstr('d41f52e67645aea0657e2c324efa88a7583310d1e8e7e616bb1233fffeba5151'),
)

PV2_KEY_PAIR = KeyPair(
    public=hexstr('b8a2d519d5cfa5ecc28966f3a1cb222aca7e25a553a260e50255159364eb4ff7'),
    private=hexstr('4f8df4b7d793d1b0719f653bfce58a67ce202bf1779153ba5fd77b3c22cf2dd6'),
)

USER_KEY_PAIR = KeyPair(
    public=hexstr('7584e5ad3f3d29f44179be133790dc94b52dd2e671b9b96694faa36bcc14c135'),
    private=hexstr('ba719a713651bf1a3ea07bd6eb9bc98721546df2425941d808c2a13c7966ab1f'),
)


def make_sample_blockchain(base_directory) -> FileBlockchain:
    blockchain = FileBlockchain(base_directory=base_directory)

    blockchain_state = make_blockchain_genesis_state(
        primary_validator_identifier=PV_KEY_PAIR.public,
        primary_validator_network_addresses=(
            'https://pv-non-existing.thenewboston.com:8555/', 'http://78.107.238.40:8555/'
        ),
        primary_validator_fee_amount=4,
        primary_validator_fee_account=PV_FIN_ACCOUNT_KEY_PAIR.public,
        treasury_account_number=TREASURY_KEY_PAIR.public,
    )

    blockchain.add_blockchain_state(blockchain_state)

    node = RegularNode(
        identifier=PV2_KEY_PAIR.public,
        network_addresses=['https://node42-non-existing.thenewboston.com:8555/', 'http://78.107.238.42:8555/'],
        fee_amount=3,
    )
    regular_node_scr = NodeDeclarationSignedChangeRequest.create(
        network_addresses=node.network_addresses, fee_amount=node.fee_amount, signing_key=PV2_KEY_PAIR.private
    )
    original_utcnow = blockchain.utcnow
    blockchain.utcnow = lambda: datetime.fromisoformat('2021-06-19T23:13:22.003468')  # type: ignore
    blockchain.add_block(Block.create_from_signed_change_request(blockchain, regular_node_scr, PV_KEY_PAIR.private))

    blockchain.utcnow = lambda: datetime.fromisoformat('2021-06-19T23:15:45.575678')  # type: ignore
    coin_transfer_scr = CoinTransferSignedChangeRequest.from_main_transaction(
        blockchain=blockchain,
        recipient=USER_KEY_PAIR.public,
        amount=1200,
        signing_key=TREASURY_KEY_PAIR.private,
        node=node,
        memo='For candy'
    )
    blockchain.add_block(Block.create_from_signed_change_request(blockchain, coin_transfer_scr, PV_KEY_PAIR.private))

    blockchain.utcnow = lambda: datetime.fromisoformat('2021-06-19T23:20:00')  # type: ignore
    pv_schedule_scr = PrimaryValidatorScheduleSignedChangeRequest.create(
        100,
        199,
        signing_key=PV2_KEY_PAIR.private,
    )
    blockchain.add_block(Block.create_from_signed_change_request(blockchain, pv_schedule_scr, PV_KEY_PAIR.private))

    blockchain.snapshot_blockchain_state()
    blockchain.utcnow = original_utcnow  # type: ignore
    return blockchain


class SamplesFactory:

    def __init__(self):
        self._blockchain: Optional[FileBlockchain] = None
        self.temporary_directory = tempfile.TemporaryDirectory()

    @property
    def blockchain(self):
        if (blockchain := self._blockchain) is None:
            self._blockchain = blockchain = make_sample_blockchain(self.temporary_directory.name)

        return blockchain

    def get_sample_blockchain(self) -> FileBlockchain:
        return self.blockchain

    def get_sample_blockchain_state(self):
        return self.blockchain.get_last_blockchain_state()

    def get_sample_blocks(self):
        blocks = {}
        for block in self.blockchain.yield_blocks():
            field_type = block.message.signed_change_request.get_field_type('message')
            blocks.setdefault(field_type, block)

        return blocks

    def close(self):
        self.temporary_directory.cleanup()
