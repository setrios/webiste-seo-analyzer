import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

VALID_STATUSES = {'CREATED', 'QUEUED', 'PROCESSING', 'DONE', 'ERROR'}


class TestCreateJobContract:
    def test_response_has_required_fields(self, client, auth_headers):
        response = client.post('/jobs', json={'url': 'https://example.com'}, headers=auth_headers)

        assert response.status_code == 200
        body = response.json()
        assert isinstance(body['id'], int)
        assert isinstance(body['url'], str)
        assert body['status'] in VALID_STATUSES
        assert body['s3_key'] is None or isinstance(body['s3_key'], str)
        assert isinstance(body['progress'], int)
        assert 0 <= body['progress'] <= 100
        assert isinstance(body['created_at'], str)
        assert isinstance(body['updated_at'], str)
        assert isinstance(body['user_id'], int)

    def test_new_job_status_is_queued(self, client, auth_headers):
        response = client.post('/jobs', json={'url': 'https://new-url.com'}, headers=auth_headers)

        assert response.json()['status'] == 'QUEUED'

    def test_rabbitmq_publish_called_once(self, client, auth_headers):
        mock_channel = client.app_state_channel
        mock_channel.default_exchange.publish.reset_mock()

        client.post('/jobs', json={'url': 'https://mq-test.com'}, headers=auth_headers)

        mock_channel.default_exchange.publish.assert_called_once()


