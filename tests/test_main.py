from types import SimpleNamespace

import main


def test_tryDecode_returns_plain_string_for_non_json():
    data = "hello"
    assert main.tryDecode(None, data) == data


def test_tryDecode_decodes_bytes_for_non_json():
    data = b"hello"
    assert main.tryDecode(None, data) == "hello"


def test_tryDecode_formats_json_when_json_as_list_false():
    data = '{"key":"value","key2":"value2"}'
    expected = '{\n  "key": "value",\n  "key2": "value2"\n}'
    assert main.tryDecode(None, data, json_as_list=False) == expected


def test_tryDecode_formats_dict_as_bullet_list():
    data = '{"key":"value","key2":"value2"}'
    expected = "- <b>key</b>: value\n- <b>key2</b>: value2"
    assert main.tryDecode(None, data, json_as_list=True) == expected


def test_tryDecode_formats_list_as_bullet_list():
    data = '["one", "two"]'
    assert main.tryDecode(None, data, json_as_list=True) == "- one\n- two"


def test_parser_todoist_extracts_action_and_item_content():
    topic = "failcloud/todoist/item:completed"
    payload = '{"item": {"content": "Buy milk"}}'
    assert main.parser_todoist(topic, payload) == "completed: Buy milk"


def test_getParser_uses_todoist_parser_for_todoist_topic():
    parser = main.getParser("failcloud/todoist/item:completed")
    assert parser is main.parser_todoist


def test_getParser_falls_back_to_tryDecode_for_short_topic():
    parser = main.getParser("status")
    assert parser is main.tryDecode


def test_mqtt2telegram_formats_and_sends_message(monkeypatch):
    sent = []

    class FakeBot:
        def sendMsgToOwner(self, msg):
            sent.append(msg)

    monkeypatch.setattr(main, "bot", FakeBot())

    main.mqtt2telegram("failcloud/todoist/item:completed", '{"item": {"content": "Pay rent"}}')

    assert len(sent) == 1
    assert "<b>mqtt2telegram:</b> <i>failcloud/todoist/item:completed</i>" in sent[0]
    assert "completed: Pay rent" in sent[0]
