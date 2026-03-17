import json
from pathlib import Path

import pytest

from app import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    app.config['TESTING'] = True
    monkeypatch.setenv('FIELD_SHIELD_DATA_DIR', str(tmp_path / 'field_shield_data'))
    with app.test_client() as client:
        yield client


def _start_session(client):
    resp = client.post(
        '/api/field-shield/start',
        data=json.dumps(
            {
                'organizer_alias': 'medic-1',
                'location': 'Portland, OR',
                'trusted_contacts': [
                    {'name': 'Legal Team', 'channel': 'sms', 'target': '+15035550100'}
                ],
                'consent_ack': True,
            }
        ),
        content_type='application/json',
    )
    assert resp.status_code == 201
    return resp.get_json()['session_id']


def test_start_session_creates_session_file(client):
    response = client.post(
        '/api/field-shield/start',
        data=json.dumps({'organizer_alias': 'observer'}),
        content_type='application/json',
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data['status'] == 'active'
    assert 'session_id' in data


def test_start_session_validation_error_on_bad_contacts(client):
    response = client.post(
        '/api/field-shield/start',
        data=json.dumps({'trusted_contacts': 'not-a-list'}),
        content_type='application/json',
    )
    assert response.status_code == 400
    assert 'error' in response.get_json()


def test_checkin_and_incident_append_to_session(client):
    session_id = _start_session(client)

    checkin_response = client.post(
        '/api/field-shield/checkin',
        data=json.dumps(
            {
                'session_id': session_id,
                'status': 'ok',
                'note': 'All clear at rally point.',
                'battery_level': 88,
            }
        ),
        content_type='application/json',
    )
    assert checkin_response.status_code == 201

    incident_response = client.post(
        '/api/field-shield/incident',
        data=json.dumps(
            {
                'session_id': session_id,
                'incident_type': 'detention',
                'severity': 4,
                'description': 'Witnessed detention near courthouse.',
                'location': 'Downtown',
                'media': [
                    {
                        'type': 'video',
                        'name': 'clip-1.mp4',
                        'uri': 'file:///tmp/clip-1.mp4',
                        'sha256': 'abc123',
                        'size_bytes': 2048,
                    }
                ],
            }
        ),
        content_type='application/json',
    )
    assert incident_response.status_code == 201
    payload = incident_response.get_json()
    assert payload['incident']['incident_type'] == 'detention'
    assert len(payload['incident']['media']) == 1


def test_alert_stub_uses_env_provider_flags(client, monkeypatch):
    session_id = _start_session(client)
    monkeypatch.setenv('FIELD_SHIELD_SMS_WEBHOOK_URL', 'https://alerts.local/sms')

    response = client.post(
        '/api/field-shield/alert',
        data=json.dumps(
            {
                'session_id': session_id,
                'providers': ['sms', 'signal'],
                'message': 'Need legal observer backup.',
                'recipients': ['+15035550100'],
            }
        ),
        content_type='application/json',
    )
    assert response.status_code == 201
    data = response.get_json()['alert']
    assert len(data['dispatches']) == 2
    sms_dispatch = [d for d in data['dispatches'] if d['provider'] == 'sms'][0]
    signal_dispatch = [d for d in data['dispatches'] if d['provider'] == 'signal'][0]
    assert sms_dispatch['configured'] is True
    assert signal_dispatch['configured'] is False


def test_packet_export_generates_json_and_text_files(client):
    session_id = _start_session(client)

    client.post(
        '/api/field-shield/incident',
        data=json.dumps(
            {
                'session_id': session_id,
                'incident_type': 'surveillance',
                'description': 'Unmarked vehicle monitoring march route.',
                'severity': 3,
            }
        ),
        content_type='application/json',
    )

    response = client.get(f'/api/field-shield/session/{session_id}/packet')
    assert response.status_code == 200
    data = response.get_json()

    assert 'packet' in data
    assert 'text_summary' in data
    exports = data['packet']['exports']
    json_path = Path(exports['json_path'])
    txt_path = Path(exports['txt_path'])

    assert json_path.exists()
    assert txt_path.exists()
    assert exports['pdf_path'] is None


def test_field_shield_404_for_unknown_session(client):
    response = client.post(
        '/api/field-shield/checkin',
        data=json.dumps({'session_id': '11111111-1111-1111-1111-111111111111'}),
        content_type='application/json',
    )
    assert response.status_code == 404
