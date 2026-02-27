import { NextRequest, NextResponse } from 'next/server'


const WINDOW_MS = 60_000   // 1 minute
const MAX_REQUESTS = 60    // max requests per window per IP

// Map<ip, timestamps[]>
const ipRequests = new Map<string, number[]>()

// Clean up old entries every minute to prevent unbounded memory growth
let lastCleanup = Date.now()

function cleanup(now: number) {
    if (now - lastCleanup < WINDOW_MS) return
    lastCleanup = now
    for (const [ip, timestamps] of ipRequests.entries()) {
        const recent = timestamps.filter(t => now - t < WINDOW_MS)
        if (recent.length === 0) {
            ipRequests.delete(ip)
        } else {
            ipRequests.set(ip, recent)
        }
    }
}

export function middleware(request: NextRequest) {
    const now = Date.now()
    cleanup(now)

    // Resolve the real client IP
    const forwarded = request.headers.get('x-forwarded-for')
    const ip = forwarded ? forwarded.split(',')[0].trim() : (request.headers.get('x-real-ip') ?? 'unknown')

    // Get existing timestamps within the window
    const timestamps = (ipRequests.get(ip) ?? []).filter(t => now - t < WINDOW_MS)

    if (timestamps.length >= MAX_REQUESTS) {
        const retryAfter = Math.ceil((timestamps[0] + WINDOW_MS - now) / 1000)
        return new NextResponse(
            JSON.stringify({ error: 'Too Many Requests', retryAfter }),
            {
                status: 429,
                headers: {
                    'Content-Type': 'application/json',
                    'Retry-After': String(retryAfter),
                    'X-RateLimit-Limit': String(MAX_REQUESTS),
                    'X-RateLimit-Remaining': '0',
                    'X-RateLimit-Reset': String(Math.ceil((timestamps[0] + WINDOW_MS) / 1000)),
                },
            }
        )
    }

    timestamps.push(now)
    ipRequests.set(ip, timestamps)

    const remaining = MAX_REQUESTS - timestamps.length
    const response = NextResponse.next()
    response.headers.set('X-RateLimit-Limit', String(MAX_REQUESTS))
    response.headers.set('X-RateLimit-Remaining', String(remaining))
    response.headers.set('X-RateLimit-Reset', String(Math.ceil((timestamps[0] + WINDOW_MS) / 1000)))
    return response
}

export const config = {
    // Apply to all routes except Next.js internals and static files
    matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}

