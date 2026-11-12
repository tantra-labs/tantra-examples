def test_tantra_examples_import():
    import tantra_examples

    assert tantra_examples.__version__ == "0.1.0"
    assert tantra_examples.Backtest is not None
    assert tantra_examples.ScriptedFakeLlm is not None
