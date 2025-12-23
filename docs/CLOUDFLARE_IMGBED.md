# CloudFlare ImgBed Integration

Open WebUI now supports CloudFlare ImgBed as a storage provider for file uploads. This integration allows you to use a CloudFlare ImgBed instance for hosting uploaded files instead of local storage or other cloud providers.

## What is CloudFlare ImgBed?

[CloudFlare ImgBed](https://github.com/MarSeventh/CloudFlare-ImgBed) is an open-source file hosting solution that supports:
- Multiple storage backends (Telegram, Cloudflare R2, S3, etc.)
- RESTful API for file uploads
- Authentication via API tokens
- File management capabilities
- WebDAV protocol support

## Configuration

To use CloudFlare ImgBed as your storage provider, set the following environment variables:

### Required Environment Variables

```bash
STORAGE_PROVIDER=cloudflare_imgbed
CLOUDFLARE_IMGBED_URL=https://your-imgbed-instance.com
```

### Optional Environment Variables

```bash
CLOUDFLARE_IMGBED_API_KEY=your-api-key-here
```

The API key is optional but recommended if your CloudFlare ImgBed instance requires authentication.

## Docker Compose Example

Add the following environment variables to your `docker-compose.yaml`:

```yaml
services:
  open-webui:
    environment:
      - STORAGE_PROVIDER=cloudflare_imgbed
      - CLOUDFLARE_IMGBED_URL=https://your-imgbed-instance.com
      - CLOUDFLARE_IMGBED_API_KEY=your-api-key-here
```

## Docker Run Example

```bash
docker run -d \
  -p 3000:8080 \
  -e STORAGE_PROVIDER=cloudflare_imgbed \
  -e CLOUDFLARE_IMGBED_URL=https://your-imgbed-instance.com \
  -e CLOUDFLARE_IMGBED_API_KEY=your-api-key-here \
  -v open-webui:/app/backend/data \
  --name open-webui \
  ghcr.io/open-webui/open-webui:main
```

## How It Works

1. When a file is uploaded to Open WebUI, it's temporarily stored locally
2. The file is then uploaded to your CloudFlare ImgBed instance via its `/upload` endpoint
3. CloudFlare ImgBed returns a URL for the uploaded file
4. Open WebUI stores this URL in its database for future retrieval
5. When a file is accessed, Open WebUI downloads it from CloudFlare ImgBed if needed

## Features

- **Upload**: Files are uploaded to CloudFlare ImgBed with automatic authentication
- **Download**: Files are downloaded from CloudFlare ImgBed on demand
- **Delete**: Individual files can be deleted from CloudFlare ImgBed
- **Local Caching**: Downloaded files are cached locally for performance

## Supported Storage Providers

Open WebUI supports the following storage providers:
- `local` - Local file system (default)
- `s3` - Amazon S3 and S3-compatible services
- `gcs` - Google Cloud Storage
- `azure` - Azure Blob Storage
- `cloudflare_imgbed` - CloudFlare ImgBed (new)

## Troubleshooting

### Error: CLOUDFLARE_IMGBED_URL must be configured

Make sure you've set the `CLOUDFLARE_IMGBED_URL` environment variable with your CloudFlare ImgBed instance URL.

### Upload Fails with 401 Unauthorized

Your CloudFlare ImgBed instance requires authentication. Set the `CLOUDFLARE_IMGBED_API_KEY` environment variable with your API key.

### Files Not Uploading

1. Verify your CloudFlare ImgBed instance is accessible from your Open WebUI container
2. Check the CloudFlare ImgBed logs for any errors
3. Ensure the API endpoint `/upload` is available and working

## Security Considerations

- Always use HTTPS for your CloudFlare ImgBed URL to encrypt file transfers
- Keep your API key secure and never commit it to version control
- Consider using environment variable files or secrets management for production deployments
- CloudFlare ImgBed supports various authentication mechanisms - configure according to your security requirements

## Additional Resources

- [CloudFlare ImgBed GitHub Repository](https://github.com/MarSeventh/CloudFlare-ImgBed)
- [CloudFlare ImgBed Documentation](https://cfbed.sanyue.de/en)
- [Open WebUI Documentation](https://docs.openwebui.com/)
