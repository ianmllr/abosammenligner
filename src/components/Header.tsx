import Image from 'next/image'
import Link from 'next/link'

export default function Header() {
    return (
        <header className="bg-[#1a1f27] border-b border-[#334155] px-8 py-4">
            <div className="max-w-[1200px] mx-auto flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Image src="/favicon.ico" alt="Logo" width={32} height={32} />
                    <Link href="/" >
                    <span className="text-[#cdd6e0] text-xl font-semibold tracking-tight">Tech-tilbud</span>
                    </Link>
                </div>
                <nav className="text-[#7d8fa0] text-sm ">
                    <Link href="/about" className="px-3 py-1.5 rounded-md border border-[#334155] hover:border-[#4a90b8] hover:text-[#cdd6e0] transition-colors">
                        Om Tech-tilbud
                    </Link>
                </nav>
            </div>
        </header>
    )
}
