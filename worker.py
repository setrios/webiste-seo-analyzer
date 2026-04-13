import asyncio
import json
import os
import requests

import boto3
from botocore.client import Config
from bs4 import BeautifulSoup
import aio_pika
from dotenv import load_dotenv


load_dotenv()


def get_s3_client():
    return boto3.client(
        's3',
        endpoint_url=os.getenv('MINIO_ENDPOINT'),
        aws_access_key_id=os.getenv('MINIO_ACCESS_KEY'),
        aws_secret_access_key=os.getenv('MINIO_SECRET_KEY'),
        config=Config(signature_version='s3v4'),
    )


def ensure_bucket(s3_client, bucket: str) -> None:
    try:
        s3_client.head_bucket(Bucket=bucket)
    except Exception:
        s3_client.create_bucket(Bucket=bucket)


def upload_result(s3_client, bucket: str, key: str, data: dict) -> None:
    s3_client.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(data).encode(),
        ContentType='application/json',
    )


def analyze_url(url: str) -> dict:
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')

    description_tag = soup.find('meta', {'name': 'description'})
    description = description_tag['content'] if description_tag else None

    return {
        'title': soup.title.string if soup.title else None,
        'description': description,
        'h1_count': len(soup.find_all('h1')),
        'h2_count': len(soup.find_all('h2')),
        'link_count': len(soup.find_all('a')),
    }


async def publish_event(channel: aio_pika.Channel, event: dict) -> None:
    await channel.default_exchange.publish(
        aio_pika.Message(
            body=json.dumps(event).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        ),
        routing_key='seo.events'
    )


async def process_job(message: aio_pika.IncomingMessage, channel: aio_pika.Channel) -> None:
    async with message.process():
        job = json.loads(message.body)
        job_id = job['job_id']
        url = job['url']

        print(f'[worker] processing job {job_id}: {url}')

        # notify backend when starting
        await publish_event(channel, {'type': 'processing', 'job_id': job_id})
        await publish_event(channel, {'type': 'progress', 'job_id': job_id, 'progress': 10})

        try:
            # analyze_url is blocking, so run in thread to avoid blocking event loop
            result = await asyncio.to_thread(analyze_url, url)

            await publish_event(channel, {'type': 'progress', 'job_id': job_id, 'progress': 80})

            # upload to MinIO
            bucket = os.getenv('MINIO_BUCKET', 'seo-results')
            s3_key = f'jobs/{job_id}/result.json'
            s3_client = get_s3_client()
            await asyncio.to_thread(ensure_bucket, s3_client, bucket)
            await asyncio.to_thread(upload_result, s3_client, bucket, s3_key, result)

            await publish_event(channel, {
                'type': 'completed',
                'job_id': job_id,
                's3_key': s3_key,
            })

            print(f'[worker] job {job_id} completed, s3_key={s3_key}')

        except Exception as e:
            await publish_event(channel, {
                'type': 'failed',
                'job_id': job_id,
                'error': str(e),
            })
            print(f'[worker] job {job_id} failed: {e}')


async def main() -> None:
    rabbitmq_url = os.getenv('RABBITMQ_URL', 'amqp://guest:guest@localhost/')
    connection = await aio_pika.connect_robust(rabbitmq_url)
    channel = await connection.channel()

    await channel.declare_queue('seo.request', durable=True)
    await channel.declare_queue('seo.events', durable=True)

    queue = await channel.get_queue('seo.request')

    print('[worker] waiting for jobs...')

    async with queue.iterator() as it:
        async for message in it:
            await process_job(message, channel)


if __name__ == '__main__':
    asyncio.run(main())