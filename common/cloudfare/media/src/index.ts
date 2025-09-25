import { S3Client, HeadObjectCommand, GetObjectCommand } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";

export default {
  async fetch(req: Request, env: any) {
    const key = new URL(req.url).pathname.slice(1);          // /uploads/media/...

    const s3 = new S3Client({
      region: "us-east-1",
      endpoint: "https://s3.us-east-1.wasabisys.com",
      credentials: { accessKeyId: env.AWS_KEY, secretAccessKey: env.AWS_SECRET },
    });

    if (req.method === "HEAD") {
      const meta = await s3.send(new HeadObjectCommand({ Bucket: env.BUCKET, Key: key }));
      return new Response(null, {
        status: 200,
        headers: {
          "Content-Type":   meta.ContentType,
          "Content-Length": String(meta.ContentLength),
          "Cache-Control":  meta.CacheControl ?? "max-age=3600",
        },
      });
    }

    const url = await getSignedUrl(s3, new GetObjectCommand({ Bucket: env.BUCKET, Key: key }), { expiresIn: 900 }); // expires in 900 seconds (15 minutes)
    return Response.redirect(url, 302);
  },
};
