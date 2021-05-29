import copy
from dataclasses import dataclass
from typing import Type, TypeVar

from dataclasses_json import dataclass_json

from thenewboston_node.business_logic.exceptions import ValidationError
from thenewboston_node.business_logic.models.node import PrimaryValidator, RegularNode
from thenewboston_node.core.logging import validates
from thenewboston_node.core.utils.cryptography import normalize_dict
from thenewboston_node.core.utils.dataclass import fake_super_methods

from .base import SignedRequestMessage
from .coin_transfer_transaction import CoinTransferTransaction

T = TypeVar('T', bound='CoinTransferSignedRequestMessage')


@fake_super_methods
@dataclass_json
@dataclass
class CoinTransferSignedRequestMessage(SignedRequestMessage):
    """Coin transfer request message"""

    balance_lock: str
    """Current sender's balance lock"""

    txs: list[CoinTransferTransaction]
    """List of `CoinTransferTransaction`_ objects"""

    @classmethod
    def from_transactions(cls: Type[T], blockchain, coin_sender: str, txs: list[CoinTransferTransaction]) -> T:
        return cls(
            balance_lock=blockchain.get_account_balance_lock(coin_sender),
            txs=copy.deepcopy(txs),
        )

    @classmethod
    def from_main_transaction(
        cls: Type[T], *, blockchain, coin_sender: str, recipient: str, amount: int,
        primary_validator: PrimaryValidator, node: RegularNode
    ) -> T:
        txs = [
            CoinTransferTransaction(recipient=recipient, amount=amount),
            CoinTransferTransaction(
                recipient=primary_validator.identifier, amount=primary_validator.fee_amount, fee=True
            ),
            CoinTransferTransaction(recipient=node.identifier, amount=node.fee_amount, fee=True),
        ]
        return cls.from_transactions(blockchain, coin_sender, txs)

    def get_total_amount(self) -> int:
        return sum(tx.amount for tx in self.txs)

    def get_amount(self, recipient):
        return sum(tx.amount for tx in self.txs if tx.recipient == recipient)

    def override_to_dict(self):  # this one turns into to_dict()
        dict_ = self.super_to_dict()
        # TODO(dmu) LOW: Implement a better way of removing optional fields or allow them in normalized message
        dict_['txs'] = [tx.to_dict() for tx in self.txs]
        return dict_

    def get_normalized(self) -> bytes:
        message_dict = self.to_dict()  # type: ignore

        for tx in message_dict['txs']:
            # This should fire when we add new fields to CoinTransferTransaction and forget to amend the sorting key
            assert len(tx) <= 3
        message_dict['txs'] = sorted(
            message_dict['txs'], key=lambda x: (x['recipient'], x.get('fee', False), x['amount'])
        )

        return normalize_dict(message_dict)

    @validates('transfer request message')
    def validate(self):
        self.validate_balance_lock()
        self.validate_transactions()

    @validates('transfer request message balance lock')
    def validate_balance_lock(self):
        if not self.balance_lock:
            raise ValidationError(f'{self.humanized_class_name} balance lock must be set')

    @validates('transfer request message transactions', is_plural_target=True)
    def validate_transactions(self):
        txs = self.txs
        if not isinstance(txs, list):
            raise ValidationError(f'{self.humanized_class_name} txs must be a list')

        if not txs:
            raise ValidationError(f'{self.humanized_class_name} txs must contain at least one transaction')

        for tx in self.txs:
            with validates(f'Validating transaction {tx} on {self.get_humanized_class_name(False)} level'):
                if not isinstance(tx, CoinTransferTransaction):
                    raise ValidationError(f'{self.humanized_class_name} txs must contain only Transactions types')
                tx.validate()
