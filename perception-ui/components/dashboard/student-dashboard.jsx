"use client"

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import api from '@/api/axios';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';

export function StudentDashboard() {
  const [availableSets, setAvailableSets] = useState([]);
  const [submittedSets, setSubmittedSets] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchData = async () => {
    setIsLoading(true);
    try {
      const [availableRes, submittedRes] = await Promise.all([
        api.get('/api/student/question-sets'),
        api.get('/api/student/submissions')
      ]);
      setAvailableSets(availableRes.data);
      setSubmittedSets(submittedRes.data);
    } catch (error) {
      toast.error('Failed to load dashboard data.');
      console.error(error); 
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <Tabs defaultValue="available-sets">
      <TabsList className="grid w-full grid-cols-2">
        <TabsTrigger value="available-sets">Available Question Sets</TabsTrigger>
        <TabsTrigger value="my-submissions">My Submissions</TabsTrigger>
      </TabsList>
      
      <TabsContent value="available-sets" className="mt-4">
        <Card>
          <CardHeader>
            <CardTitle>Available Assignments</CardTitle>
            <CardDescription>Complete these assignments to get your score and feedback.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {isLoading ? (
              <Skeleton className="h-24 w-full" />
            ) : availableSets.length > 0 ? (
              availableSets.map((qs) => <AnswerQuestionSetItem key={qs.id} qs={qs} onSubmitted={fetchData} />)
            ) : (
              <p>No new assignments available. Great job!</p>
            )}
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="my-submissions" className="mt-4">
        <Card>
          <CardHeader>
            <CardTitle>Your Submitted Work</CardTitle>
            <CardDescription>Review your past submissions, scores, and feedback.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {isLoading ? (
              <Skeleton className="h-40 w-full" />
            ) : submittedSets.length > 0 ? (
              submittedSets.map((sub) => (
                <Card key={sub.id}>
                  <CardHeader>
                    <div className="flex justify-between items-start">
                        <CardTitle>{sub.question_set.title}</CardTitle>
                        <Badge variant="secondary">By: {sub.question_set.creator.username}</Badge>
                    </div>
                    <CardDescription>{sub.question_set.question}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="font-semibold">Your Answer:</p>
                    <p className="text-muted-foreground p-2 border rounded-md bg-secondary">{sub.student_answer}</p>
                    <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                           <p className="font-semibold">AI Score: <span className="font-normal">{sub.ai_score}/10</span></p>
                           <p className="font-semibold mt-2">AI Feedback:</p>
                           <p className="text-muted-foreground text-sm">{sub.ai_feedback}</p>
                        </div>
                        <div>
                           <p className="font-bold text-lg">Final Score: <span className="font-normal">{sub.final_score !== null ? `${sub.final_score}/10` : 'Pending Teacher Review'}</span></p>
                        </div>
                    </div>
                  </CardContent>
                </Card>
              ))
            ) : (
              <p>You haven't submitted any assignments yet.</p>
            )}
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );
}

function AnswerQuestionSetItem({ qs, onSubmitted }) {
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const { register, handleSubmit, formState: { isSubmitting } } = useForm();

  const onSubmit = async (data) => {
    try {
      await api.post('/api/student/submissions', {
        question_set_id: qs.id,
        answer: data.answer
      });
      toast.success("Answer submitted successfully! The AI is evaluating it now.");
      setIsDialogOpen(false);
      onSubmitted();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to submit answer.");
    }
  };

  return (
    <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
      <Card>
        <CardHeader>
          <div className="flex justify-between items-start">
            <CardTitle>{qs.title}</CardTitle>
            <Badge variant="secondary">By: {qs.creator.username}</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <DialogTrigger asChild>
            <Button>Start Assignment</Button>
          </DialogTrigger>
        </CardContent>
      </Card>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{qs.title}</DialogTitle>
          <p className="text-muted-foreground pt-2">{qs.question}</p>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Textarea 
            placeholder="Type your answer here..." 
            rows={10}
            {...register('answer', { required: true, minLength: 10 })}
          />
          <Button type="submit" className="w-full" disabled={isSubmitting}>
            {isSubmitting ? 'Submitting & Evaluating...' : 'Submit Final Answer'}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
