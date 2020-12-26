from Cryptodome.PublicKey import RSA

from yaaccu.signature import create_signature, check_signature


def test_cross_check():
    content = 'some_content'
    key = RSA.generate(1024)
    assert check_signature(
        content,
        create_signature(content, key.export_key().decode()),
        key.publickey().export_key().decode(),
        raise_exception=False
    )
    assert check_signature(
        content,
        create_signature(content + 'x', key.export_key().decode()),
        key.publickey().export_key().decode(),
        raise_exception=False
    ) is False
