"use client"

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import api from '@/api/axios';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';

export function TeacherDashboard() {
  const [questionSets, setQuestionSets] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm();

  const fetchQuestionSets = async () => {
    try {
      setIsLoading(true);
      const response = await api.get('/api/teacher/question-sets');
      setQuestionSets(response.data);
    } catch (error) {
      toast.error('Failed to fetch question sets.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchQuestionSets();
  }, []);

  const onCreateSet = async (data) => {
    try {
      const payload = { ...data };
      if (data.assigned_usernames) {
        payload.assigned_usernames = data.assigned_usernames.split(',').map(name => name.trim()).filter(name => name);
      } else {
        payload.assigned_usernames = [];
      }

      await api.post('/api/teacher/question-sets', payload);
      toast.success('New question set created!');
      reset();
      fetchQuestionSets();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create question set.');
    }
  };

  return (
    <Tabs defaultValue="my-sets">
      <TabsList className="grid w-full grid-cols-2">
        <TabsTrigger value="my-sets">My Question Sets</TabsTrigger>
        <TabsTrigger value="create-new">Create New</TabsTrigger>
      </TabsList>
      
      <TabsContent value="my-sets" className="mt-4">
        <Card>
          <CardHeader>
            <CardTitle>Your Created Question Sets</CardTitle>
            <CardDescription>View submissions for the question sets you've created.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {isLoading ? (
              <Skeleton className="h-24 w-full" />
            ) : questionSets.length > 0 ? (
              questionSets.map((qs) => <QuestionSetItem key={qs.id} qs={qs} />)
            ) : (
              <p>You haven't created any question sets yet.</p>
            )}
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="create-new" className="mt-4">
        <Card>
          <CardHeader>
            <CardTitle>Create a New Question Set</CardTitle>
            <CardDescription>Provide a question and a model answer to guide the AI evaluation.</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit(onCreateSet)} className="space-y-4">
              <div>
                <Label htmlFor="title">Title</Label>
                <Input id="title" {...register('title', { required: 'Title is required' })} />
                {errors.title && <p className="text-red-500 text-xs mt-1">{errors.title.message}</p>}
              </div>
              <div>
                <Label htmlFor="question">Question</Label>
                <Textarea id="question" {...register('question', { required: 'Question is required' })} />
                {errors.question && <p className="text-red-500 text-xs mt-1">{errors.question.message}</p>}
              </div>
              <div>
                <Label htmlFor="model_answer">Model Answer</Label>
                <Textarea id="model_answer" {...register('model_answer', { required: 'Model answer is required' })} />
                {errors.model_answer && <p className="text-red-500 text-xs mt-1">{errors.model_answer.message}</p>}
              </div>
              <div>
                <Label htmlFor="assigned_usernames">Assign to Students (Optional)</Label>
                <Input id="assigned_usernames" placeholder="Enter student usernames, separated by commas" {...register('assigned_usernames')} />
                <p className="text-xs text-muted-foreground mt-1">If left blank, the assignment will be public for all students.</p>
              </div>
              <Button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Creating...' : 'Create Set'}</Button>
            </form>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );
}

function QuestionSetItem({ qs }) {
  const [submissions, setSubmissions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  const fetchSubmissions = async () => {
    if (!isDialogOpen) return;
    setIsLoading(true);
    try {
      const response = await api.get(`/api/teacher/question-sets/${qs.id}/submissions`);
      setSubmissions(response.data);
    } catch (error) {
      toast.error("Failed to load submissions.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
      fetchSubmissions();
  }, [isDialogOpen]);

  const handleFinalizeScore = async (submissionId, finalScore) => {
    if (finalScore === '' || finalScore === null || finalScore < 0 || finalScore > 10) {
        toast.error("Please enter a valid score between 0 and 10.");
        return;
    }
    try {
        await api.put(`/api/teacher/submissions/${submissionId}/finalize`, { final_score: parseInt(finalScore) });
        toast.success("Score finalized!");
        fetchSubmissions(); 
    } catch (error) {
        toast.error("Failed to finalize score.");
    }
  };

  return (
    <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
      <Card>
        <CardHeader>
          <CardTitle>{qs.title}</CardTitle>
          <CardDescription>{qs.question}</CardDescription>
        </CardHeader>
        <CardContent>
            <div className="flex items-center justify-between">
                <DialogTrigger asChild>
                    <Button>View Submissions</Button>
                </DialogTrigger>
                <div className="flex items-center gap-2">
                    {qs.assigned_students.length > 0 ? (
                        qs.assigned_students.map(student => (
                            <Badge key={student.id} variant="secondary">{student.username}</Badge>
                        ))
                    ) : (
                        <Badge variant="outline">Public</Badge>
                    )}
                </div>
            </div>
        </CardContent>
      </Card>
      <DialogContent className="max-w-4xl h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>Submissions for: {qs.title}</DialogTitle>
        </DialogHeader>
        <div className="flex-grow overflow-y-auto pr-4">
          {isLoading ? (
            <p>Loading submissions...</p>
          ) : submissions.length > 0 ? (
            <div className="space-y-4">
              {submissions.map((sub) => (
                <Card key={sub.id}>
                  <CardHeader>
                    <CardTitle className="text-sm">Student: {sub.student.username}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="font-semibold">Answer:</p>
                    <p className="text-muted-foreground p-2 border rounded-md bg-secondary">{sub.student_answer}</p>
                    <div className="mt-4 grid grid-cols-2 gap-4">
                        <div>
                            <p className="font-semibold">AI Score: <span className="font-normal">{sub.ai_score}/10</span></p>
                            <p className="font-semibold mt-2">AI Feedback:</p>
                            <p className="text-muted-foreground text-sm">{sub.ai_feedback}</p>
                        </div>
                        <div className="space-y-2">
                           <p className="font-semibold">Final Score: <span className="font-normal">{sub.final_score !== null ? `${sub.final_score}/10` : 'Not graded'}</span></p>
                           <div className="flex items-center gap-2">
                                <Input type="number" min="0" max="10" placeholder="0-10" id={`score-${sub.id}`} defaultValue={sub.final_score}/>
                                <Button size="sm" onClick={() => handleFinalizeScore(sub.id, document.getElementById(`score-${sub.id}`).value)}>Finalize</Button>
                           </div>
                        </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <p>No submissions for this question set yet.</p>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
