from sap_common import SAPClient


def main():
    print('Checking SAP AI Core OAuth and GPT deployment...')
    client = SAPClient()
    r = client.post({
        'messages': [{'role': 'user', 'content': 'Reply with exactly: SAP_OK'}],
        'max_completion_tokens': 100,
    })
    print('HTTP status:', r.status_code)
    if not r.ok:
        # Avoid printing raw upstream responses that could include sensitive details.
        print('Inference failed; response withheld. Check deployment, permissions, and API version.')
        return
    data = r.json()
    for choice in data.get('choices', []):
        msg = choice.get('message', {})
        print('Model response:', msg.get('content'))
        print('Finish reason:', choice.get('finish_reason'))
    if not data.get('choices'):
        print('No choices returned; investigate expected SAP response schema.')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print('Error:', type(e).__name__, str(e)[:240])
