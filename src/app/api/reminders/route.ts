import { sql } from '@/lib/db'
import { NextResponse } from 'next/server'

export async function POST(req: Request) {
    const { email, message, daysBefore } = await req.json()

    if (!email || daysBefore === undefined) {
        return NextResponse.json({ error: 'Missing fields' }, { status: 400 })
    }

    if (message && message.length > 50) {
        return NextResponse.json({ error: 'Note must be 50 characters or less' }, { status: 400 })
    }


    const ip = req.headers.get('x-forwarded-for')?.split(',')[0].trim() ?? 'unknown'

    
    const existing = await sql`
        SELECT id FROM reminders WHERE ip = ${ip} AND sent = false LIMIT 1
    `
    if (existing.length > 0) {
        return NextResponse.json({ error: 'Der er allerede sat en påmindelse fra denne IP-adresse.' }, { status: 429 })
    }

    const sendAt = new Date()
    sendAt.setMonth(sendAt.getMonth() + 6)
    sendAt.setDate(sendAt.getDate() - daysBefore)

    await sql`
        INSERT INTO reminders (email, days_before, send_at, message, ip)
        VALUES (${email}, ${daysBefore}, ${sendAt.toISOString()}, ${message ?? null}, ${ip})
    `

    return NextResponse.json({ success: true, sendAt: sendAt.toISOString() })
}
