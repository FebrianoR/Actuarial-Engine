import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL || "http://localhost:8000";

/**
 * Catch-all API proxy: /api/backend/... → backend /api/v1/...
 * Handles file uploads (multipart/form-data) properly by streaming
 * the request body without parsing it.
 */
async function proxy(
    request: NextRequest,
    { params }: { params: Promise<{ path: string[] }> }
) {
    const { path } = await params;
    const target = `${BACKEND}/api/v1/${path.join("/")}`;

    // Forward query string
    const url = new URL(request.url);
    const qs = url.search ? url.search : "";

    // Forward headers (except host)
    const headers = new Headers();
    request.headers.forEach((value, key) => {
        if (key.toLowerCase() !== "host" && key.toLowerCase() !== "transfer-encoding") {
            headers.set(key, value);
        }
    });

    const res = await fetch(`${target}${qs}`, {
        method: request.method,
        headers,
        body: request.body,
        // @ts-expect-error duplex needed for streaming request body
        duplex: "half",
    });

    // Stream response back
    const responseHeaders = new Headers();
    res.headers.forEach((value, key) => {
        responseHeaders.set(key, value);
    });

    return new NextResponse(res.body, {
        status: res.status,
        statusText: res.statusText,
        headers: responseHeaders,
    });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const DELETE = proxy;
export const PATCH = proxy;
