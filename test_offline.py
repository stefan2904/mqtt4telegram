from main import tryDecode


def test_hello():
	print("Hello, pytest!")
	assert True


def test_json_notJSON():
	data = "hello"
	res = tryDecode(None, data)
	assert type(res) is str
	assert res == data


def test_json_simple1():
	data = '{"key":"value"}'
	res = tryDecode(None, data, False)
	assert type(res) is str
	assert res == '{\n  "key": "value"\n}'

def test_json_simple2():
	data = '{"key":"value", "key2":"value2"}'
	res = tryDecode(None, data, False)
	assert type(res) is str
	assert res == '{\n  "key": "value",\n  "key2": "value2"\n}'


def test_json_asList1():
	data = '{"key":"value"}'
	res = tryDecode(None, data, True)
	assert type(res) is str
	assert res == '- <b>key</b>: value'

def test_json_asList1_list():
	data = '["value1", "value2"]'
	res = tryDecode(None, data, True)
	assert type(res) is str
	assert res == '- value1\n- value2'


def test_json_asList2():
	data = '{"key":"value", "key2":"value2"}'
	res = tryDecode(None, data, True)
	assert type(res) is str
	assert res == '- <b>key</b>: value\n- <b>key2</b>: value2'


def test_json_asList2_deep():
	data = '{"key":"value", "key2": {"deepkey":"deepvalue"}}'
	res = tryDecode(None, data, True)
	assert type(res) is str
	assert res == '- <b>key</b>: value\n- <b>key2</b>: {\'deepkey\': \'deepvalue\'}'

def test_json_asList2_list():
	data = '{"key":"value", "key2": ["deep1", "deep2"]}'
	res = tryDecode(None, data, True)
	assert type(res) is str
	assert res == '- <b>key</b>: value\n- <b>key2</b>: [\'deep1\', \'deep2\']'
