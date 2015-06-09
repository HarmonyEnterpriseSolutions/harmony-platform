_hop_headers = {
	'connection':1, 'keep-alive':1, 'proxy-authenticate':1,
	'proxy-authorization':1, 'te':1, 'trailers':1, 'transfer-encoding':1,
	'upgrade':1
}

def is_hop_by_hop(header_name):
    return header_name.lower() in _hop_headers
