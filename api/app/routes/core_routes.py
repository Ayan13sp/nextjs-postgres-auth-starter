from fastapi import APIRouter, Depends, HTTPException, status
from beanie.odm.fields import PydanticObjectId
from typing import List, Optional

from app.db.database import User, QuestionSet, Submission
from app.models.teacher_models import QuestionSetCreate, QuestionSetOut, SubmissionReviewOut, ScoreUpdate
from app.models.student_models import SubmissionCreate, SubmissionResultOut, QuestionSetForStudentOut
from app.models.user_models import UserOut
from app.services.auth_dependencies import get_current_user
from app.services.ai_service import get_ai_evaluation

router = APIRouter()

# ----------------- Helper Converters -----------------

async def to_user_out(user_or_link) -> UserOut:
    if not user_or_link:
        return UserOut(
            id="unknown",
            username="Unknown User",
            email=None,
            role="unknown"
        )
    if isinstance(user_or_link, User):
        user = user_or_link
    else:
        user_id = None
        if hasattr(user_or_link, 'ref') and hasattr(user_or_link.ref, 'id'):
            user_id = user_or_link.ref.id
        elif hasattr(user_or_link, 'id'):
            user_id = user_or_link.id
        elif hasattr(user_or_link, 'to_ref'):
            ref = user_or_link.to_ref()
            user_id = ref.id if hasattr(ref, 'id') else ref
        else:
            user_id = user_or_link

        user = await User.get(user_id) if user_id else None

    if not user:
        return UserOut(
            id=str(user_id) if user_id else "unknown",
            username="Unknown User",
            email=None,
            role="unknown"
        )

    return UserOut(
        id=str(user.id),
        username=user.username,
        email=user.email,
        role=user.role
    )

async def to_question_set_out(qs: QuestionSet) -> QuestionSetOut:
    creator_out = await to_user_out(getattr(qs, 'creator', None))
    assigned_out = []
    if getattr(qs, 'assigned_students', None):
        for s in qs.assigned_students:
            user_out = await to_user_out(s)
            if user_out:
                assigned_out.append(user_out)
    return QuestionSetOut(
        id=str(qs.id),
        title=qs.title,
        question=qs.question,
        model_answer=qs.model_answer,
        creator=creator_out,
        assigned_students=assigned_out
    )

async def to_question_set_for_student_out(qs: QuestionSet) -> QuestionSetForStudentOut:
    creator_out = await to_user_out(getattr(qs, 'creator', None))
    return QuestionSetForStudentOut(
        id=str(qs.id),
        title=qs.title,
        question=qs.question,
        creator=creator_out
    )

async def to_submission_review_out(sub: Submission) -> SubmissionReviewOut:
    student_out = await to_user_out(getattr(sub, 'student', None))
    return SubmissionReviewOut(
        id=str(sub.id),
        student=student_out,
        student_answer=sub.student_answer,
        ai_score=sub.ai_score,
        ai_feedback=sub.ai_feedback,
        final_score=sub.final_score
    )

async def to_submission_result_out(sub: Submission) -> SubmissionResultOut:
    qs = None
    if isinstance(getattr(sub, 'question_set', None), QuestionSet):
        qs = sub.question_set
    else:
        qs_id = None
        target = getattr(sub, 'question_set', None)
        if hasattr(target, 'ref') and hasattr(target.ref, 'id'):
            qs_id = target.ref.id
        elif hasattr(target, 'id'):
            qs_id = target.id
        elif hasattr(target, 'to_ref'):
            ref = target.to_ref()
            qs_id = ref.id if hasattr(ref, 'id') else ref
        else:
            qs_id = target

        if qs_id:
            qs = await QuestionSet.get(qs_id)

    if qs:
        qset_out = await to_question_set_for_student_out(qs)
    else:
        qset_out = QuestionSetForStudentOut(
            id=str(getattr(sub, 'id', 'archived')),
            title="Archived Question Set",
            question="Question details no longer available",
            creator=UserOut(id="system", username="Teacher", email=None, role="teacher")
        )

    return SubmissionResultOut(
        id=str(sub.id),
        question_set=qset_out,
        student_answer=sub.student_answer,
        ai_score=sub.ai_score,
        ai_feedback=sub.ai_feedback,
        final_score=sub.final_score
    )

# ----------------- Teacher Routes -----------------

@router.get("/teacher/question-sets", response_model=List[QuestionSetOut])
async def get_teacher_question_sets(current_user: User = Depends(get_current_user)):
    if current_user.role != "teacher":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only teachers can view their question sets.")
    
    qsets = await QuestionSet.find({
        "$or": [
            {"creator.$id": current_user.id},
            {"creator": current_user.id}
        ]
    }).to_list()
    return [await to_question_set_out(qs) for qs in qsets]

@router.post("/teacher/question-sets", response_model=QuestionSetOut, status_code=status.HTTP_201_CREATED)
@router.post("/rubric", response_model=QuestionSetOut, status_code=status.HTTP_201_CREATED)
async def create_question_set(qs_data: QuestionSetCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "teacher":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only teachers can create question sets.")
    
    assigned_student_list = []
    if qs_data.assigned_usernames:
        students = await User.find({"username": {"$in": qs_data.assigned_usernames}, "role": "student"}).to_list()
        assigned_student_list = students

    question_set = QuestionSet(
        title=qs_data.title,
        question=qs_data.question,
        model_answer=qs_data.model_answer,
        creator=current_user,
        assigned_students=assigned_student_list
    )
    await question_set.insert()
    return await to_question_set_out(question_set)

@router.get("/teacher/question-sets/{id}/submissions", response_model=List[SubmissionReviewOut])
async def get_question_set_submissions(id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != "teacher":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only teachers can view submissions.")
    
    try:
        obj_id = PydanticObjectId(id)
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid question set ID format.")

    qs = await QuestionSet.get(obj_id)
    if not qs:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question set not found.")
    
    creator_id = getattr(getattr(qs, 'creator', None), 'ref', None)
    creator_id = creator_id.id if creator_id else getattr(getattr(qs, 'creator', None), 'id', None)
    if creator_id and creator_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied to question sets from other teachers.")
    
    submissions = await Submission.find({
        "$or": [
            {"question_set.$id": qs.id},
            {"question_set": qs.id}
        ]
    }).to_list()
    return [await to_submission_review_out(sub) for sub in submissions]

@router.put("/teacher/submissions/{id}/finalize", response_model=SubmissionReviewOut)
async def finalize_submission_score(id: str, score_data: ScoreUpdate, current_user: User = Depends(get_current_user)):
    if current_user.role != "teacher":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only teachers can finalize scores.")
    
    try:
        obj_id = PydanticObjectId(id)
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid submission ID format.")

    sub = await Submission.get(obj_id)
    if not sub:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Submission not found.")
    
    sub.final_score = score_data.final_score
    await sub.save()
    return await to_submission_review_out(sub)

# ----------------- Student Routes -----------------

@router.get("/student/question-sets", response_model=List[QuestionSetForStudentOut])
async def get_student_question_sets(current_user: User = Depends(get_current_user)):
    if current_user.role != "student":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only students can view available question sets.")
    
    try:
        all_qsets = await QuestionSet.find({
            "$or": [
                {"assigned_students": {"$size": 0}},
                {"assigned_students": []},
                {"assigned_students.$id": current_user.id},
                {"assigned_students": current_user.id}
            ]
        }).to_list()
        
        submissions = await Submission.find({
            "$or": [
                {"student.$id": current_user.id},
                {"student": current_user.id}
            ]
        }).to_list()
        
        submitted_qs_ids = set()
        for sub in submissions:
            target = getattr(sub, 'question_set', None)
            if hasattr(target, 'ref') and hasattr(target.ref, 'id'):
                submitted_qs_ids.add(target.ref.id)
            elif hasattr(target, 'id'):
                submitted_qs_ids.add(target.id)
        
        available_qsets = [qs for qs in all_qsets if qs.id not in submitted_qs_ids]
        return [await to_question_set_for_student_out(qs) for qs in available_qsets]
    except Exception as e:
        print(f"Error in get_student_question_sets: {e}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to load question sets: {str(e)}")

@router.get("/student/submissions", response_model=List[SubmissionResultOut])
async def get_student_submissions(current_user: User = Depends(get_current_user)):
    if current_user.role != "student":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only students can view their submissions.")
    
    try:
        submissions = await Submission.find({
            "$or": [
                {"student.$id": current_user.id},
                {"student": current_user.id}
            ]
        }).to_list()
        
        results = []
        for sub in submissions:
            out = await to_submission_result_out(sub)
            if out:
                results.append(out)
        return results
    except Exception as e:
        print(f"Error in get_student_submissions: {e}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Failed to load submissions: {str(e)}")

@router.post("/student/submissions", response_model=SubmissionResultOut, status_code=status.HTTP_201_CREATED)
@router.post("/evaluate", response_model=SubmissionResultOut, status_code=status.HTTP_201_CREATED)
async def submit_student_answer(sub_data: SubmissionCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != "student":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only students can submit answers.")

    try:
        obj_id = PydanticObjectId(sub_data.question_set_id)
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid question set ID format.")

    question_set = await QuestionSet.get(obj_id)
    if not question_set:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Question set not found.")

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
    return await to_submission_result_out(submission)

# ----------------- Results & Analytics Routes -----------------

@router.get("/results/{id}", response_model=SubmissionResultOut)
async def get_results(id: PydanticObjectId, current_user: User = Depends(get_current_user)):
    submission = await Submission.get(id)
    if not submission:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Result not found.")
    
    student_id = getattr(getattr(submission, 'student', None), 'ref', None)
    student_id = student_id.id if student_id else getattr(getattr(submission, 'student', None), 'id', None)
    if current_user.role == "student" and student_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Access denied.")
    
    return await to_submission_result_out(submission)

@router.get("/analytics")
async def get_analytics(current_user: User = Depends(get_current_user)):
    if current_user.role != "teacher":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only teachers can view analytics.")
    
    my_qsets = await QuestionSet.find({
        "$or": [
            {"creator.$id": current_user.id},
            {"creator": current_user.id}
        ]
    }).to_list()
    qset_ids = [qs.id for qs in my_qsets]
    
    submissions = await Submission.find({
        "$or": [
            {"question_set.$id": {"$in": qset_ids}},
            {"question_set": {"$in": qset_ids}}
        ]
    }).to_list()
    
    total_submissions = len(submissions)
    average_score = 0
    if total_submissions > 0:
        average_score = sum([sub.ai_score for sub in submissions]) / total_submissions
        
    return {
        "total_submissions": total_submissions,
        "average_score": round(average_score, 2),
        "total_rubrics": len(my_qsets)
    }

