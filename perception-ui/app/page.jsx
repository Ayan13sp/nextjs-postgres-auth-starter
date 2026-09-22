import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { ArrowRight } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-background text-foreground">
      <div className="text-center max-w-4xl p-8">
        <div className="flex justify-center items-center mb-4">
          <img src="/logo192.png" alt="Perception Logo" className="h-16 w-16 mr-4" />
          <h1 className="text-5xl md:text-7xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-500 to-teal-400">
            Perception
          </h1>
        </div>
        <p className="text-xl md:text-2xl text-muted-foreground mb-8">
          AI-Powered Online Evaluation Portal. Fairer, faster, and more insightful feedback for descriptive answers.
        </p>
        <div className="flex justify-center gap-4">
          <Button asChild size="lg">
            <Link href="/login">Get Started <ArrowRight className="ml-2 h-5 w-5" /></Link>
          </Button>
          <Button asChild size="lg" variant="outline">
            <Link href="/about">Learn More</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
