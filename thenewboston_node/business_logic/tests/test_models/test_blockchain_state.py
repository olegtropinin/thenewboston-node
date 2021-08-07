from hashlib import sha3_256

from thenewboston_node.business_logic.node import get_node_identifier


def test_normalized_blockchain_state(blockchain_genesis_state):
    del blockchain_genesis_state.account_states[get_node_identifier()]
    assert blockchain_genesis_state.get_normalized() == (
        b'{"account_states":{"4d3cf1d9e4547d324de2084b568f807ef12045075a7a01b8bec1e7f013fc3732":{'
        b'"balance":281474976710656'
        b'}}}'
    )


def test_get_next_block_identifier(blockchain_genesis_state):
    del blockchain_genesis_state.account_states[get_node_identifier()]
    assert blockchain_genesis_state.get_next_block_identifier() == sha3_256(
        b'{"account_states":{"4d3cf1d9e4547d324de2084b568f807ef12045075a7a01b8bec1e7f013fc3732":{'
        b'"balance":281474976710656'
        b'}}}'
    ).digest().hex()

    blockchain_genesis_state.next_block_identifier = 'next-block-identifier'
    assert blockchain_genesis_state.get_next_block_identifier() == 'next-block-identifier'
