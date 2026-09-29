import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function AboutPage() {
  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      <div className="text-center">
        <h1 className="text-4xl font-bold">Perception</h1>
        <p className="text-muted-foreground text-lg mt-2">
          Fairer, faster, and more insightful feedback for descriptive answers.
        </p>
      </div>

      <Card>
        <CardHeader><CardTitle>🌍 Our Mission</CardTitle></CardHeader>
        <CardContent className="space-y-4 text-muted-foreground">
          <p>In today’s education landscape, automated assessments often fail to provide meaningful feedback for descriptive answers. Perception bridges this gap by leveraging Contextual AI-powered evaluation, ensuring that students receive accurate, personalized, and constructive feedback—just like a human evaluator.</p>
          <p>We aim to automate the grading process, provide AI-driven insights for students, and enhance efficiency without compromising on fairness and accuracy.</p>
        </CardContent>
      </Card>

      <div className="grid md:grid-cols-2 gap-8">
        <Card>
          <CardHeader><CardTitle>🏆 Strengths</CardTitle></CardHeader>
          <CardContent>
            <ul className="list-disc list-inside space-y-2">
              <li><strong>Efficient & Scalable:</strong> Evaluate large volumes of responses in real-time.</li>
              <li><strong>Fair & Unbiased:</strong> Eliminates human subjectivity in grading.</li>
              <li><strong>Saves Time:</strong> Teachers can focus on teaching rather than grading.</li>
              <li><strong>Detailed Feedback:</strong> Students receive insightful corrections and guidance.</li>
            </ul>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>🛠 Tech Stack</CardTitle></CardHeader>
          <CardContent>
            <ul className="list-disc list-inside space-y-2">
              <li><strong>Frontend:</strong> Next.js, Tailwind CSS, Shadcn UI</li>
              <li><strong>Backend:</strong> FastAPI (Python)</li>
              <li><strong>Database:</strong> MongoDB with Beanie ODM</li>
              <li><strong>AI Integration:</strong> LLM-based text evaluation with Groq</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
