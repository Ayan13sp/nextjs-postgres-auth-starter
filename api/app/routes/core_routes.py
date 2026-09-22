from fastapi import APIRouter, Depends, HTTPException, status
from beanie.odm.fields import PydanticObjectId
from app.db.database import User, QuestionSet, Submission
from app.models.teacher_models import QuestionSetCreate, QuestionSetOut
from app.models.student_models import SubmissionCreate, SubmissionResultOut
from app.models.user_models import UserOut
from app.services.auth_dependencies import get_current_user
from app.services.ai_service import get_ai_evaluation
from typing import List

router = APIRouter()

# 1. POST /rubric — Create/update a grading rubric (Question Set)
@router.post("/rubric", response_model=QuestionSetOut, status_code=status.HTTP_201_CREATED)
async def create_rubric(qs_data: QuestionSetCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "teacher":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only teachers can create rubrics.")
    
    assigned_student_list = []
    if qs_data.assigned_usernames:
        students = [s async for s in User.find({"username": {"$in": qs_data.assigned_usernames}, "role": "student"})]
        assigned_student_list = students

    question_set = QuestionSet(
        title=qs_data.title,
        question=qs_data.question,
        model_answer=qs_data.model_answer,
        creator=current_user,
        assigned_students=assigned_student_list
    )
    await question_set.insert()
    
    creator_out = UserOut.model_validate(current_user, from_attributes=True)
    assigned_students_out = [UserOut.model_validate(s, from_attributes=True) for s in assigned_student_list]
    
    return QuestionSetOut(
        **question_set.model_dump(exclude={'creator', 'assigned_students'}),
        creator=creator_out,
        assigned_students=assigned_students_out
    )

# 2. POST /evaluate — Submit a student answer for grading
@router.post("/evaluate", response_model=SubmissionResultOut, status_code=status.HTTP_201_CREATED)
async def evaluate_answer(sub_data: SubmissionCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "student":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only students can submit answers.")

    question_set = await QuestionSet.get(PydanticObjectId(sub_data.question_set_id))
    if not question_set:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Rubric/Question set not found.")

    evaluation = await get_ai_evaluation(question_set.model_answer, sub_data.answer)
    if evaluation.get("score") == -1:
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, evaluation.get("feedback", "AI evaluation failed"))

    submission = Submission(
        question_set=question_set,
        student=current_user,
        student_answer=sub_data.answer,
        ai_score=evaluation["score"],
        ai_feedback=evaluation["feedback"]
    )
    await submission.insert()
    
    # We construct the response using dict to bypass strict validation issues in simple refactor
    from app.models.student_models import QuestionSetForStudentOut
    creator_out = UserOut.model_validate(await User.get(question_set.creator.ref.id), from_attributes=True)
    qset_out = QuestionSetForStudentOut(**question_set.model_dump(exclude={'creator'}), creator=creator_out)

    return SubmissionResultOut(**submission.model_dump(exclude={'question_set', 'student'}), question_set=qset_out)

# 3. GET /results/{id} — Retrieve grading results
@router.get("/results/{id}", response_model=SubmissionResultOut)
async def get_results(id: PydanticObjectId, current_user: User = Depends(get_current_user)):
    submission = await Submission.get(id)
    if not submission:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Result not found.")
    
    # Check permissions
    if current_user.role == "student" and submission.student.ref.id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied.")
    
    # Construct response
    question_set = await QuestionSet.get(submission.question_set.ref.id)
    from app.models.student_models import QuestionSetForStudentOut
    creator_out = UserOut.model_validate(await User.get(question_set.creator.ref.id), from_attributes=True)
    qset_out = QuestionSetForStudentOut(**question_set.model_dump(exclude={'creator'}), creator=creator_out)

    return SubmissionResultOut(**submission.model_dump(exclude={'question_set', 'student'}), question_set=qset_out)

# 4. GET /analytics — Get aggregate performance stats
@router.get("/analytics")
async def get_analytics(current_user: User = Depends(get_current_user)):
    if current_user.role != "teacher":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only teachers can view analytics.")
    
    # Aggregate stats across all submissions for this teacher's question sets
    my_qsets = await QuestionSet.find(QuestionSet.creator.id == current_user.id).to_list()
    qset_ids = [qs.id for qs in my_qsets]
    
    submissions = await Submission.find({"question_set.$id": {"$in": qset_ids}}).to_list()
    
    total_submissions = len(submissions)
    average_score = 0
    if total_submissions > 0:
        average_score = sum([sub.ai_score for sub in submissions]) / total_submissions
        
    return {
        "total_submissions": total_submissions,
        "average_score": round(average_score, 2),
        "total_rubrics": len(my_qsets)
    }
