import FaqItem from '@/components/FaqItem'
import Header from "@/components/Header";

const faqs = [
    {
        question: 'Hvad er Abosammenligner?',
        answer: 'Abosammenligner er et værktøj der hjælper dig med at finde og sammenligne tilbud på tech-produkter i forbindelse med dit mobilabonnement. Det er altså ikke til at finde det billigste telefonabonnement overhovedet, men til at finde de abonnementer hvor man kan spare flest penge hvis man skal have ny telefon, iPad eller lignende.'
    },
    {
        question: 'Hvordan fungerer det?',
        answer: 'Abosammenligner samler data fra forskellige udbydere og præsenterer det på en overskuelig måde, så du nemt kan sammenligne tilbud. Både gode og dårlige tilbud bliver vist så du selv kan få et overblik og træffe en informeret beslutning.'
    },
    {
        question: 'Er det gratis at bruge?',
        answer: 'Ja, Abosammenligner er helt gratis at bruge.'
    },
    {
        question: 'Hvordan kører Abosammenligner så rundt?',
        answer: 'Abosammenligner får et lille beløb af abonnementudbyderen hvis du klikker på et tilbud og køber det. Det er samme som metode som kendte sider som Pricerunner og Ønskeskyen bruger. Det betyder at det er gratis for dig at bruge, og at Abosammenligner kan fortsætte med at være gratis i fremtiden.'
    }
]



export default function About() {
    return (
        <>
            <Header />

        <main className="flex flex-col items-center justify-center min-h-screen px-4 text-center">
            <h1 className="text-3xl font-bold mb-4">Om Abosammenligner</h1>
            <p className="text-base max-w-prose mb-12 ">
                Du har helt sikkert et mobilabonnement i forvejen. Det alene gør at du har muligheden for at spare penge.
                <br/><br/>
                Mange abonnementudbydere i Danmark tilbyder rabat på- eller rent ud gratis tech-produkter hvis du køber et abonnement og binder dig til at være kunde hos dem i 6 måneder.
                Håbet er at du glemmer at du har et dyrt abonnement og fortsætter med at betale for det i lang tid. Men det behøver du ikke.
                I visse tilfælde er der betydelige mængder penge at spare hvis man skifter sit abonnement hver 6-12 måned, og det er det Abosammenligner kan hjælpe dig med.
                Det kan være alt fra en gratis telefon, til rabat på en ny iPad eller et nyt smartwatch.

                <br/><br/>

                Abosammenligner er et værktøj som kan hjælpe dig med at finde gode tilbud på tech i forbindelse med mobilabonnementer.
                Vi samler data fra forskellige udbydere og præsenterer det på en måde, der gør det nemt for dig at sammenligne og finde det bedste tilbud. Målet
                er at hjælpe dig med at spare penge og få mest muligt ud af dit mobilabonnement.            </p>

            <h2 className="text-2xl font-bold mb-4">Ofte stillede spørgsmål</h2>
            <div className="w-full max-w-prose">
                {faqs.map((faq) => (
                    <FaqItem key={faq.question} question={faq.question} answer={faq.answer} />
                ))}
            </div>

        </main>
        </>
    )
}
